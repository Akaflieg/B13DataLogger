import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import math
from pandas.tseries.offsets import DateOffset

    
timestamp = "2019-08-16 17-09-28"

FREQ = 20

def normalise_datetime(raw):
    df = raw.copy()
    df["datetime"] = pd.to_datetime(df['timestamp'],unit='s')
    df.set_index("datetime", inplace=True)
    return df
    
def calc_datarate(df):
    rate = df.index.to_series().diff()
    return rate
    
def resample(df, freq=20):
    return df.resample("50ms", base=0).ffill().dropna()
    

gyro_raw = pd.read_csv(f"./data/{timestamp}-gyro.csv")
gyro = normalise_datetime(gyro_raw)
gyro = resample(gyro)

mast_raw = pd.read_csv(f"./data/{timestamp}-mast.csv")
mast = normalise_datetime(mast_raw)
mast = resample(mast)
    
combined = mast.merge(gyro, how="inner", sort=True, left_index=True, right_index=True)
# combined = combined.dropna()
print(combined)

data_rate = calc_datarate(combined)
#mast_rel["time"] = mast[["timestamp"]] - mast[["timestamp"]].iloc[0]


ax1 = combined[["alpha"]].plot(linewidth=1)
ax2 = ax1.twinx()
ax2.spines['right'].set_position(('axes', 1.0))
combined[["elevator"]].plot(ax=ax2, color="red", linewidth=1)
print(mast)
print(gyro)
data_rate.plot()
mast[["alpha"]].plot()
# plt.show()
combined.to_csv(f"{timestamp}-combined.csv")