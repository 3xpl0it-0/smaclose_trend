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

# url's needed

BINANCE_BASE_URL = 'https://fapi.binance.com'
BINANCE_KLINE_URL = '/fapi/v1/klines'

# set ticker, data window, target volatility, rolling volatility window and sma window

ticker = 'BTCUSDT'
begin = 40
target_volatility = 0.2
rol_vol_window = 30
sma_window = 30

# feature strengths

seven = 1.048807
eight = 1.077868
nine = 1.119436
ten = 1.219276

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
position_size = account*(ret_target_vol/df['rolling_vol'].iloc[-1])

# creating feature

df["sma"] = df["close"].rolling(window=sma_window).mean()
df['feature'] = df['close']/df['sma']

if df['feature'].iloc[-1] >= seven:
    trade_position = 'long'

else:
    trade_position = 'no trade'
    
# return trade and sizing information
    
print(f'trade: {trade_position} | size: {position_size}')








