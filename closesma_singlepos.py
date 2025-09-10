import requests
import pandas as pd
import numpy as np
import time
import requests
from datetime import datetime, timedelta, timezone
import math

## --- NOTES --- 
# anything hardcoded has been information aquired from previous analysis
# start and limit is given to binance api instead of start and end as i had issues with the latter before
# features are scaled to signals linearly based on strength; max strength is target volatility

# url's needed

BINANCE_BASE_URL = 'https://fapi.binance.com'
BINANCE_KLINE_URL = '/fapi/v1/klines'

# set ticker, data window, target volatility, rolling volatility window, sma window and lowest signal strength

ticker = 'BTCUSDT'
begin = 40
target_volatility = 0.2
rol_vol_window = 30
sma_window = 30
low_signal = 0.7

# feature minimums

seven_min = 1.035326
eight_min = 1.062604
nine_min = 1.094381
ten_min = 1.148069

# feature maximums

seven_max = 1.062350
eight_max = 1.094331
nine_max = 1.148014
ten_max = 1.545970

# portfolio size

account = 10000

# setting up time window

now = datetime.now(timezone.utc)

end_of_yesterday = datetime.combine(
    (now - timedelta(days=1)).date(),
    datetime.max.time(),
    tzinfo=timezone.utc
).replace(microsecond=0)

endtime = int(end_of_yesterday.timestamp())*1000

TICKER_DATES = [ticker, endtime-begin*86400000, endtime]

# data retrieval function

def get_kline(
    dates_ticker_data: list | None = None,
    base_url: str | None = None,
    kline_url: str | None = None
) -> list[tuple[str, int, int, int, int, int, int, int]]:
    
    if not dates_ticker_data:
        _dates_ticker_data = TICKER_DATES
    else:
        _dates_ticker_data = dates_ticker_data
    
    if not base_url:
        _base_url = BINANCE_BASE_URL
    else:
        _base_url = base_url
        
    if not kline_url:
        _kline_url = BINANCE_KLINE_URL
    else:
        _kline_url = kline_url
    
    kline = []
    url = f'{_base_url}{_kline_url}'
        
    try:                
        params = {
            "symbol": _dates_ticker_data[0],
            "startTime": _dates_ticker_data[1],
            "limit": 1000,
            "interval": "1d"
        }
        
        response = requests.get(url, params=params)    
        data = response.json()
        
        for i in data[:-1]:
            kline.append((_dates_ticker_data[0], i[0], i[1], i[2], i[3], i[4], i[7])) # open time, open, high, low, close, volume
                                    
    except requests.exceptions.RequestException as e:
        print(f"Warning: API request failed: {e}")
        print('because of this returning blank list')
        
        return []
    
        print('kline saved')
    
    return kline

tickerdata_list = get_kline()

columns = ["asset", "timestamp", "open", "high", "low", "close", "volume"]
df = pd.DataFrame(tickerdata_list, columns=columns)

cols_to_convert = ['open', 'high', 'low', 'close', 'volume']
df[cols_to_convert] = df[cols_to_convert].astype(float)

print('----------- checking for missing entries -----------')
print('')

for index in df.index[1:]:
    
    if df['timestamp'].iloc[index] - df['timestamp'].iloc[index-1] != 86400000 and df['asset'].iloc[index] == df['asset'].iloc[index-1]:
        print(f'problem: {df["timestamp"].iloc[index] - df["timestamp"].iloc[index-1]}')
        
print('----------- finished checking for missing entries -----------')
print('')

print('----------- checking for discrepencies in open - close -----------')
print('')

for index in df.index[1:]:
    
    open_ = float(df['open'].iloc[index])
    prev_close = float(df['close'].iloc[index-1])
    
    if open_ - prev_close > open_*0.005 and df['asset'].iloc[index] == df['asset'].iloc[index-1]:
        print(f'problem: (time: {df["timestamp"].iloc[index]} - {(open_ - prev_close)/prev_close}')
        print(f'asset: {df["asset"].iloc[index]} open: {open_} prev close: {prev_close}')

print('----------- finished checking for discrepencies in open - close -----------')
print('')

print('----------- checking for 0/Nan values -----------')
print('')

print(df.isna().any())

print('----------- finished checking for 0/Nan values -----------')
print('')

# making time readable

df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

# getting returns and scaling to target volatility

df["return"] = df["close"].pct_change()

df["next_ret"] = df['return'].shift(-1)

df["rolling_vol"] = (
    df["return"]
      .rolling(window=rol_vol_window)
      .std()
)

# target annulised volatility and position sizing

ret_target_vol = target_volatility/math.sqrt(365)
recent_vol_scaled = ret_target_vol/df['rolling_vol'].iloc[-1]
diff = (1-low_signal)/3

# creating feature

df["sma"] = df["close"].rolling(window=sma_window).mean()
df['feature'] = df['close']/df['sma']

if df['feature'].iloc[-1] >= seven_min:
    trade_position = 'long'
else:
    trade_position = 'no trade'

if seven_min <= df['feature'].iloc[-1] < eight_min:
    position_size = account*low_signal*recent_vol_scaled

elif eight_min <= df['feature'].iloc[-1] < nine_min:
        position_size = account*(low_signal+diff)*recent_vol_scaled
        
elif nine_min <= df['feature'].iloc[-1] < ten_min:
        position_size = account*(low_signal+diff*2)*recent_vol_scaled
        
elif ten_min <= df['feature'].iloc[-1]:
        position_size = account*(low_signal+diff*3)*recent_vol_scaled
else:
    position_size = 0
    
# return trade and sizing information
    
print(f'trade: {trade_position} | size: {position_size}')










