#modulo de ordenes
from binance.client import Client
import os
import math
import ccxt
from pprint import pprint
import datetime as dt
from datetime import datetime
from datetime import timedelta
import pandas as pd
import requests

os.system("clear")

binance_api="N7yU75L3CNJg2RW0TcJBAW2cUjhPGvyuSFUgnRHvMSMMiS8WpZ8Yd8yn70evqKl0"
binance_secret="2HfMkleskGwTb6KQn0AKUQfjBDd5dArBW3Ykd2uTeOiv9VZ6qSU2L1yWM1ZlQ5RH"
par ='BTCSTUSDT'
duration = 1000  # milliseconds
freq = 440  # Hz
os.system("clear")
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

comienzo = datetime.now() - timedelta(minutes=1)
comienzoms = int(comienzo.timestamp() * 1000)
finalms = int(datetime.now().timestamp() * 1000)

trades = client.get_aggregate_trades(symbol=par, startTime=comienzoms,endTime=finalms)

precioanterior = float(min(trades, key=lambda x:x['p'])['p'])

print(trades)           
print(precioanterior)
