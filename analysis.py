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
COM_PORT = "COM5"
COM_RATE = 57600
STATUS = "RUN"
DATA_DIR = "./data"

DATA_GYRO_ECHO = []

#plt.show()

'''Open Data File with current Date'''
datestr = datetime.now().strftime("%Y-%m-%d %H-%M-%S")

os.chdir(DATA_DIR)
data_file = open(datestr + ".txt", "w+")

logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh = logging.FileHandler(f"{datestr}.log")
ch = logging.StreamHandler()
logger.addHandler(fh)
logger.addHandler(ch)


fig = plt.figure()
ax = fig.add_subplot(1,1,1)


def animate(_):
    global df
    ax.clear()
    data = np.array(DATA_GYRO_ECHO)
    print(DATA_GYRO_ECHO)
    ax.plot(data[:,0], data[:,1], marker='', linestyle='solid', linewidth=1)
    
ani = animation.FuncAnimation(fig, animate, interval=100)

def read_gyro_echo(port, rate):
    global df, STATUS, DATA_GYRO_ECHO
    
    logging.info(f"Opening connection on {port} with rate {rate}")
    
    with serial.Serial(port, rate, timeout=1) as ser:
        logging.info("Commenication established")
        while ser.is_open and STATUS == "RUN":
            line = ser.readline()
            line = line.strip(b"\r\n")
            try:
                print(line)
                if line.startswith(b"I2C"):
                    logging.error("I2C Warning")
                    continue                    
                try:
                    line_split = line.split(b",")
                    '''data = {"timestamp": time.time(),
                                    "dis": int(line_split[0]),
                                    "gyro": float(line_split[1]),
                                    "accel": float(line_split[2])}'''
                    data = [time.time(),
                        int(line_split[0]),
                        float(line_split[1]),
                        float(line_split[2])]
                    print(DATA_GYRO_ECHO)
                    DATA_GYRO_ECHO.append(DATA_GYRO_ECHO)
                    data_file.write(",".join(map(str, data.values())) + "\n")
                except (ValueError, IndexError) as e:
                    print(e)
            except SerialException:
                logging.error("Serial connection failed!")
                time.sleep(1)
        

def stop(*args):
    global STATUS
    
    logging.warning("STOP Signal recieved")
    STATUS = "STOP"
    thread.join()
    sys.exit(0)

logging.info("Programm start")

signal.signal(signal.SIGINT, stop)
thread = threading.Thread(target=read_gyro_echo, args=(COM_PORT, COM_RATE))
thread.start()
plt.show()
stop()
f.close()