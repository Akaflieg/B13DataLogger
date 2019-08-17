import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import math
from pandas.tseries.offsets import DateOffset
# import scipy.signal

'''data_dir = Path("./data")
files = [file for file in data_dir.iterdir() if file.is_file()]
runs = set([filename.name[:19] for filename in files])
print(runs)

print("Select run")
for run in list(runs)[-10:]:
    print(run)  '''
    
timestamp = "2019-08-16 17-09-28"

FREQ = 20

def normalise_datetime(raw):
    df = raw.copy()
    df["datetime"] = pd.to_datetime(df['timestamp'],unit='s')
    df.set_index("datetime", inplace=True)
    return df
    
def calc_datarate(df):
    rate = df[["timestamp"]].diff()
    return 1 / rate
    
def resample(df, freq=20):
    return df.resample("50ms", base=0).mean().dropna()
    

gyro_raw = pd.read_csv(f"./data/{timestamp}-gyro.csv")
gyro = normalise_datetime(gyro_raw)
gyro = resample(gyro)

mast_raw = pd.read_csv(f"./data/{timestamp}-mast.csv")
mast = normalise_datetime(mast_raw)
mast = resample(mast)
    
combined = mast.merge(gyro, sort=True, left_index=True, right_index=True)

print(combined)

gyro_rate = calc_datarate(gyro)
mast_rate = calc_datarate(mast)
#mast_rel = mast.copy()
#mast_rel["time"] = mast[["timestamp"]] - mast[["timestamp"]].iloc[0]
#mast_rel.set_index("time", inplace=True)
#gload = mast_raw[["accel", "elevator"]]
#gload["time"] = mast_raw[["timestamp"]] - mast_raw[["timestamp"]].iloc[0]
#gload.set_index("time", inplace=True)



# mast = mast_rel.asfreq(freq="10S")
# idx = pd.date_range(mast.first_valid_index(), mast.last_valid_index(), freq='50ms')
# idx = mast.asfreq('50ms').index
# idx = idx.floor('50ms')



#y = mast.reindex(mast.index.union(idx)).interpolate('index').reindex(idx)
#y = y.dropna()
#mast_it = mast.resample("1s").interpolate("linear")
#y[["elevator"]].plot()
#mast[["elevator"]].plot()
# mast = mast_raw.resample(DateOffset(milliseconds=round(1/FREQ)))

ax1 = combined[["alpha"]].plot(linewidth=1)
ax2 = ax1.twinx()
ax2.spines['right'].set_position(('axes', 1.0))
combined[["elevator"]].plot(ax=ax2, color="red", linewidth=1)
print(mast)
# data_rate.plot()
# mast[["ias"]].plot()
plt.show()