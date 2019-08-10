import serial
import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pandas as pd
import numpy as np
import threading
import os
import sys
import signal
from datetime import datetime

data = []

#plt.show()
print("ready")

df = pd.DataFrame(columns=["timestamp", "val"])
df.set_index("timestamp", inplace=True)

'''Open Data File with current Date'''
dateTimeObj = datetime.now()
datestr = dateTimeObj.strftime("%d-%b-%Y %H-%M-%S")
filename = datestr + ".txt"
os.chdir('./Data')
f = open(filename, "w+")
os.chdir('./..')
#plt.ion()
fig = plt.figure()
ax = fig.add_subplot(1,1,1)


def animate(_):
	global df
	ax.clear()
	print(df.tail())
	print(df.empty)
	if not df.empty:
		ax.plot(df.index, df["val"], marker='', linestyle='solid', linewidth=1)
	
ani = animation.FuncAnimation(fig, animate, interval=100)

def read_data():
	global df

	with serial.Serial('COM6', 57600, timeout=1) as ser:
		print("open")
		while ser.is_open:
			line = ser.readline()
			print(line)
			if line:
				df = df.append({"timestamp": time.time(), "val": int(line[:-2])}, ignore_index=True)
				try:
					f.write(str(time.time()) + "," + str(int(line[:-2])))
				except ValueError:
					pass

def stop(*args):
	thread.join()
	sys.exit()

thread = threading.Thread(target=read_data)
thread.start()
signal.signal(signal.SIGINT, stop)
plt.show()
		
f.close()