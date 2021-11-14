#modulo de ordenes
from binance.client import Client
import os
import ccxt
from pprint import pprint
import datetime as dt
import talib
import numpy as np
from datetime import datetime, date, time, timedelta

os.system("clear")

binance_api="N7yU75L3CNJg2RW0TcJBAW2cUjhPGvyuSFUgnRHvMSMMiS8WpZ8Yd8yn70evqKl0"
binance_secret="2HfMkleskGwTb6KQn0AKUQfjBDd5dArBW3Ykd2uTeOiv9VZ6qSU2L1yWM1ZlQ5RH"
par ='BTCUSDT'

client = Client(binance_api, binance_secret)
exchange_info = client.futures_exchange_info()
exchange = ccxt.binance({
   'enableRateLimit': True,  
   'apiKey': binance_api,
   'secret': binance_secret,
   'options': {  
      'defaultType': 'future',  
   },
})

#------------------------------------------------------------------------------------------

now = datetime.now() # current date and time
hoy = now.strftime("%d %b %Y")

haceNdias=(now-timedelta(days=300)).strftime("%d %b %Y")

candles = client.get_historical_klines(par,Client.KLINE_INTERVAL_1DAY,haceNdias,hoy)

all4th = [el[4] for el in candles]

np_float_data = np.array([float(x) for x in all4th])
np_out=talib.RSI(np_float_data)

print(np_out[-1])