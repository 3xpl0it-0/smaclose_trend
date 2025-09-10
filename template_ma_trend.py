import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt
import math

# set ticker, target volatility, rolling volatility window and sma window

ticker = 'SOLUSDT'
target_volatility = 0.2
rol_vol_window = 30
sma_window = 30

# reading in data and getting ticker only

df_ = pd.read_csv("binance_ohlcvf_data.csv")
df = df_[df_['asset']==ticker].copy()
df = df.reset_index(drop=True)

print(df.iloc[:-1].isna().any())

df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

cols_to_convert = ['open', 'high', 'low', 'close', 'volume', 'funding']
df[cols_to_convert] = df[cols_to_convert].astype(float)

# getting returns and scaling to target volatility

df["return"] = df["close"].pct_change()

df["next_ret"] = df['return'].shift(-1)

df["rolling_vol"] = (
    df["return"]
      .rolling(window=rol_vol_window)
      .std()
)

ret_target_vol = target_volatility/math.sqrt(365)

df['volscaled_next_ret'] = df['next_ret']*(ret_target_vol/df['rolling_vol'])

# creating feature

df["sma"] = df["close"].rolling(window=sma_window).mean()
df['feature'] = df['close']/df['sma']

# plotting feature

plt.figure(figsize=(12,6))
plt.scatter(df['timestamp'], df['feature'], s=10, alpha=0.5, color='blue')
plt.title("Feature (Close / SMA) Over Time")
plt.xlabel("Time")
plt.ylabel("Feature")
plt.grid(True, linestyle='--', alpha=0.5)
plt.show()

# putting feature into deciles

df['feature_decile'] = pd.qcut(df['feature'], 10, labels=range(1,11))

print(df['feature_decile'].value_counts().sort_index())
decile_avg = df.groupby('feature_decile', observed=False)['feature'].mean()
print(decile_avg)

## --- not volatility scaled returns ---

# scatter plot

plt.figure(figsize=(12,6))
plt.scatter(df['feature'], df['next_ret'], s=10, alpha=0.5, color='blue')
plt.title("Feature vs Returns")
plt.xlabel("Feature")
plt.ylabel("Returns")
plt.grid(True, linestyle='--', alpha=0.5)
plt.show()

# decile plot

decile_avg_ret = df.groupby('feature_decile', observed=False)['next_ret'].mean()

plt.figure(figsize=(8,5))
decile_avg_ret.plot(kind='bar', color='skyblue')
plt.title("Average Next Return by Feature Decile")
plt.xlabel("Feature Decile")
plt.ylabel("Average Next Return")
plt.xticks(rotation=0)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.show()

# cumulative returns

long_basket = df[df["feature_decile"].between(7, 10)].copy()

long_basket['cum_return'] = (1 + long_basket['next_ret']).cumprod()

plt.figure(figsize=(10,6))
plt.plot(long_basket['timestamp'], long_basket['cum_return'], color='blue', label='Cumulative Return')
plt.title(f"Cumulative Returns for {ticker}")
plt.xlabel("Date")
plt.ylabel("Cumulative Return")
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend()
plt.show()

### --- volatility scaled returns ---

# scatter plot

plt.figure(figsize=(12,6))
plt.scatter(df['feature'], df['volscaled_next_ret'], s=10, alpha=0.5, color='blue')
plt.title("Feature vs Vol-Scaled Returns")
plt.xlabel("Feature")
plt.ylabel("Vol-Scaled Returns")
plt.grid(True, linestyle='--', alpha=0.5)
plt.show()

# decile plot

voladj_decile_avg_ret = df.groupby('feature_decile', observed=False)['volscaled_next_ret'].mean()

plt.figure(figsize=(8,5))
voladj_decile_avg_ret.plot(kind='bar', color='skyblue')
plt.title("Average Vol-Scaled Next Return by Feature Decile")
plt.xlabel("Feature Decile")
plt.ylabel("Average Vol-Scaled Next Return")
plt.xticks(rotation=0)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.show()

# cumulative returns

voladj_long_basket = df[df["feature_decile"].between(7, 10)].copy()

voladj_long_basket['cum_return'] = (1 + voladj_long_basket['volscaled_next_ret']).cumprod()

plt.figure(figsize=(10,6))
plt.plot(voladj_long_basket['timestamp'], voladj_long_basket['cum_return'], color='blue', label='Cumulative Vol-Scaled Return')
plt.title(f"Cumulative Volatility-Scaled Returns for {ticker}")
plt.xlabel("Date")
plt.ylabel("Cumulative Return")
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend()
plt.show()

# cumulative returns when position sizing to decile

# trading deciles 7 to 10 so will take average increase in returns and increase positions relative to that

decile_ret_avg = df.groupby('feature_decile', observed=False)['volscaled_next_ret'].mean()
print(decile_ret_avg)

firstdiff = (decile_ret_avg[8] - decile_ret_avg[7])/decile_ret_avg[7]
seconddiff = (decile_ret_avg[9] - decile_ret_avg[8])/decile_ret_avg[8]
thirddiff = (decile_ret_avg[10] - decile_ret_avg[9])/decile_ret_avg[9]

avg_diff = (firstdiff+seconddiff+thirddiff)/3

df['featvolscaled_next_ret'] = None

for index in df.index:
    
    if df['feature_decile'].iloc[index] == 7:
        df.loc[index, 'featvolscaled_next_ret'] = df['volscaled_next_ret'].iloc[index]
    
    elif df['feature_decile'].iloc[index] == 8:
        df.loc[index, 'featvolscaled_next_ret'] = (1+avg_diff)*df['volscaled_next_ret'].iloc[index]

    elif df['feature_decile'].iloc[index] == 9:
        df.loc[index, 'featvolscaled_next_ret'] = (1+avg_diff*2)*df['volscaled_next_ret'].iloc[index]
        
    elif df['feature_decile'].iloc[index] == 10:
        df.loc[index, 'featvolscaled_next_ret'] = (1+avg_diff*3)*df['volscaled_next_ret'].iloc[index]

retadj_long_basket = df[df["feature_decile"].between(7, 10)].copy()

retadj_long_basket['cum_return'] = (1 + retadj_long_basket['featvolscaled_next_ret']).cumprod()

plt.figure(figsize=(10,6))
plt.plot(retadj_long_basket['timestamp'], retadj_long_basket['cum_return'], color='blue', label='Cumulative Vol+Signal-Scaled Return')
plt.title(f"Cumulative Volatility+Feature-Scaled Returns for {ticker}")
plt.xlabel("Date")
plt.ylabel("Cumulative Return")
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend()
plt.show()






