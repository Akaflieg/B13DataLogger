import os
import sys
import time
import serial
import signal
import logging
import threading
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from datetime import datetime

# CONFIG
GYRO_PORT = "COM"
GYRO_RATE = 57600
MAST_PORT = "COM7"
MAST_RATE = 57600
DATA_DIR = "./data"

ECHO_THRESHOLD = 1000
CHART_DATAPOINTS = 500

STATUS = "RUN"

timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")

os.chdir(DATA_DIR)
gyro_file = open(timestamp + "-gyro.txt", "w+")
mast_file = open(timestamp + "-mast.txt", "w+")

# 0-Gyro 1-Mast
DATA = {GYRO_PORT: [], MAST_PORT: []}
FILES = {GYRO_PORT: gyro_file, MAST_PORT: mast_file}

logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
fh = logging.FileHandler(f"{timestamp}.log")
ch = logging.StreamHandler()
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

fig = plt.figure()
axes = fig.subplots(3, 2)

def animate(_):
    global DATA
    
    # axes.clear()
    gyro_data = np.array(DATA[GYRO_PORT])
    mast_data = np.array(DATA[MAST_PORT])
    if gyro_data.size == 0:
        gyro_data = np.empty((1,4))
    if mast_data.size == 0:
        mast_data = np.empty((1,3))
     
    # Pad data for concatination
    gyro_data = np.hstack((gyro_data, np.zeros((gyro_data.shape[0], 2))))
    mast_data = np.hstack((mast_data[:, [0]], np.zeros((mast_data.shape[0], 3)), mast_data[:,1:]))
    
    data = np.concatenate((gyro_data, mast_data), axis=0)
    data = data[-CHART_DATAPOINTS:]
    data[:,1][data[:,1]>ECHO_THRESHOLD] = ECHO_THRESHOLD
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

def read_serial(port, rate, parse_func):
    global df, STATUS, DATA
    
    logging.info(f"Opening connection on {port} with rate {rate}")
    
    serial_connection = None
    
    while STATUS == "RUN":
        try:
            serial_connection = serial.Serial(port, rate, timeout=1)
            logging.info(f"Serial connection {port} established")
            while STATUS == "RUN":
                line = serial_connection.readline()
                line = line.strip(b"\r\n")
                if line.startswith(b"I2C"):
                    logging.error("I2C Warning")
                    continue
                try:
                    data = parse_func(line)
                    DATA[port].append(data)
                    FILES[port].write(",".join(map(str, data)) + "\n")
                except (ValueError, IndexError) as e:
                    logging.warning(f"Invalid value recieved on {port}: {line}")
        except serial.SerialException:
            logging.error(f"Serial connection {port} failed!")
            time.sleep(1)
    if serial_connection:
        serial_connection.close()
               
def parse_mast(raw):
    print(raw)
    line_split = raw.split(b",")
    data = [time.time(),
        int(line_split[3]),
        int(line_split[4])]
    return data
    
def parse_gyro(raw):
    line_split = raw.split(b",")
    data = [time.time(),
        int(line_split[0]),
        float(line_split[1]),
        float(line_split[2])]
        
    return data

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
gyro_thread = threading.Thread(target=read_serial, args=(GYRO_PORT, GYRO_RATE, parse_gyro))
mast_thread = threading.Thread(target=read_serial, args=(MAST_PORT, MAST_RATE, parse_mast))
gyro_thread.start()
mast_thread.start()
plt.show()
stop()