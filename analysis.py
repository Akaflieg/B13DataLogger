import serial
from serial import SerialException
import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import threading
import os
import sys
import signal
import logging
from datetime import datetime

data = []

# PORT LINKS
GYRO_PORT = "COM5"
GYRO_RATE = 57600
MAST_PORT = "COM4"
MAST_RATE = 57600
STATUS = "RUN"
DATA_DIR = "./data"

DATA_GYRO_ECHO = []
DATA_MAST = []

#plt.show()

'''Open Data File with current Date'''
datestr = datetime.now().strftime("%Y-%m-%d %H-%M-%S")

os.chdir(DATA_DIR)
gyro_file = open(datestr + "-gyro.txt", "w+")
mast_file = open(datestr + "-mast.txt", "w+")

logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh = logging.FileHandler(f"{datestr}.log")
ch = logging.StreamHandler()
logger.addHandler(fh)
logger.addHandler(ch)


fig = plt.figure()
axes = fig.subplots(3, 2)


def animate(_):
    global DATA_GYRO_ECHO
    
    T = 1000
    PAST = 500
    
    print("plotting")
    
    # axes.clear()
    gyro_data = np.array(DATA_GYRO_ECHO)
    mast_data = np.array(DATA_MAST)
    print(mast_data)
    if gyro_data.size == 0:
        gyro_data = np.empty((1,4))
    if mast_data.size == 0:
        mast_data = np.empty((1,3))
     
    mast_data = np.hstack((mast_data[:, [0]], np.zeros((mast_data.shape[0], 3)), mast_data[:,1:]))
    gyro_data = np.hstack((gyro_data, np.zeros((gyro_data.shape[0], 2))))

    print(gyro_data)
    print(mast_data)    
    data = np.concatenate((gyro_data, mast_data), axis=0)
    data = data[-PAST:]
    print(data)
    data[:,1][data[:,1]>T] = T
    axes[0,0].clear()
    axes[0,1].clear()
    axes[1,0].clear()
    axes[1,1].clear()
    axes[2,0].clear()
    axes[0,0].plot(data[:,0], data[:,1], marker='', linestyle='solid', linewidth=1)
    axes[0,1].plot(data[:,0], data[:,2], marker='', linestyle='solid', linewidth=1)
    axes[1,0].plot(data[:,0], data[:,3], marker='', linestyle='solid', linewidth=1)
    axes[1,1].plot(data[:,0], data[:,4], marker='', linestyle='solid', linewidth=1)
    axes[2,0].plot(data[:,0], data[:,5], marker='', linestyle='solid', linewidth=1)

ani = animation.FuncAnimation(fig, animate, interval=100)

def read_gyro_echo(port, rate):
    global df, STATUS, DATA_GYRO_ECHO
    
    logging.info(f"Opening connection on {port} with rate {rate}")
    
    while STATUS == "RUN":
        try:
            ser = serial.Serial(port, rate, timeout=1)
            logging.info(f"Serial connection {port} established")
            while STATUS == "RUN":
                line = ser.readline()
                line = line.strip(b"\r\n")
                if line.startswith(b"I2C"):
                    logging.error("I2C Warning")
                    continue
                try:
                    line_split = line.split(b",")
                    data = [time.time(),
                        int(line_split[0]),
                        float(line_split[1]),
                        float(line_split[2])]
                    DATA_GYRO_ECHO.append(data)
                    gyro_file.write(",".join(map(str, data)) + "\n")
                except (ValueError, IndexError) as e:
                    print(e)
        except SerialException:
            logging.error(f"Serial connection {port} failed!")
            time.sleep(1)
    ser.close()
                
def read_mast(port, rate):
    '''
        Mast data collection
    '''
    global df, STATUS, DATA_MAST
    
    logging.info(f"Opening connection on {port} with rate {rate}")
    
    while STATUS == "RUN":
        try:
            ser = serial.Serial(port, rate, timeout=1)
            logging.info("Commenication established")
            while STATUS == "RUN":
                line = ser.readline()
                line = line.strip(b"\r\n")
                if line.startswith(b"I2C"):
                    logging.error("I2C Warning")
                    continue
                try:
                    line_split = line.split(b",")
                    data = [time.time(),
                        int(line_split[3]),
                        int(line_split[4])]
                    DATA_MAST.append(data)
                    mast_file.write(",".join(map(str, data)) + "\n")
                except (ValueError, IndexError) as e:
                    print(e)
        except SerialException:
            logging.error("Serial connection failed!")
            time.sleep(1)
    ser.close()

def stop(*args):
    global STATUS
    
    logging.warning("STOP Signal recieved")
    STATUS = "STOP"
    gyro_thread.join()
    mast_thread.join()
    gyro_file.close()
    mast_file.close()
    sys.exit(0)

logging.info("Programm start")

signal.signal(signal.SIGINT, stop)
gyro_thread = threading.Thread(target=read_gyro_echo, args=(GYRO_PORT, GYRO_RATE))
mast_thread = threading.Thread(target=read_mast, args=(MAST_PORT, MAST_RATE))
gyro_thread.start()
mast_thread.start()
plt.show()
stop()