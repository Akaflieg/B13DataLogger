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
GYRO_PORT = "COM5"
GYRO_RATE = 57600
MAST_PORT = "COM7"
MAST_RATE = 57600
DATA_DIR = "./data"

ECHO_THRESHOLD = 1000
CHART_DATAPOINTS = 50

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
logger.setLevel(logging.INFO)

fig = plt.figure()
axes = fig.subplots(3, 2)
plt.subplots_adjust(hspace=0.5)
axes[0,0].title.set_text("Elevator raw")
axes[0,0].set_ylim(0, 100)
axes[0,1].title.set_text("Load factor (g)")
axes[0,1].set_ylim(-20, 20)
axes[1,0].title.set_text("Pitch rate (deg/s)")
axes[1,0].set_ylim(-2, 4)
axes[1,1].title.set_text("Alpha raw")
axes[1,1].set_ylim(0, 1024)
axes[2,0].title.set_text("Beta raw")
axes[2,0].set_ylim(0, 1024)
axes[2,1].title.set_text("IAS (km/h)")
axes[2,1].set_ylim(0, 100)

def animate(_):
    global DATA
    
    gyro_data = np.array(DATA[GYRO_PORT])
    mast_data = np.array(DATA[MAST_PORT])
     
    gyro_data = gyro_data[-CHART_DATAPOINTS:]
    mast_data = mast_data[-CHART_DATAPOINTS:]
    
    if gyro_data.size != 0:
        gyro_data[:,1][gyro_data[:,1]>ECHO_THRESHOLD] = ECHO_THRESHOLD
        axes[0,0].clear()
        axes[0,1].clear()
        axes[0,0].plot(gyro_data[:,0], gyro_data[:,1], marker='', linestyle='solid', linewidth=1)
        axes[0,1].plot(gyro_data[:,0], gyro_data[:,2], marker='', linestyle='solid', linewidth=1)
    if mast_data.size != 0:
        axes[1,0].clear()
        axes[1,1].clear()
        axes[2,0].clear()
        axes[1,0].plot(mast_data[:,0], mast_data[:,0], marker='', linestyle='solid', linewidth=1)
        axes[1,1].plot(mast_data[:,0], mast_data[:,1], marker='', linestyle='solid', linewidth=1)
        axes[2,0].plot(mast_data[:,0], mast_data[:,2], marker='', linestyle='solid', linewidth=1)

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
        int(line_split[4]),
        float(sqrt(2*line_split[1]/1.225) * 3,6)]
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
    
    logging.warning("User STOP Signal recieved")
    STATUS = "STOP"
    gyro_thread.join()
    mast_thread.join()
    gyro_file.close()
    mast_file.close()
    sys.exit(0)

logging.info("Programm started")

signal.signal(signal.SIGINT, stop)
gyro_thread = threading.Thread(target=read_serial, args=(GYRO_PORT, GYRO_RATE, parse_gyro))
mast_thread = threading.Thread(target=read_serial, args=(MAST_PORT, MAST_RATE, parse_mast))
gyro_thread.start()
mast_thread.start()
plt.show()
stop()