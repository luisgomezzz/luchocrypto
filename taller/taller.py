#modulo de ordenes
from binance.client import Client
import os
import ccxt
from pprint import pprint
from datetime import datetime, date, time, timedelta
import pandas as pd
################
import sys
sys.path.insert(1,'/home/lucho/PERSONALREPO/luchocrypto/')
import tradeando as tr
import pandas_ta as ta
import matplotlib.pyplot as plt   # needs pip install
################3
os.system("clear")

binance_api="N7yU75L3CNJg2RW0TcJBAW2cUjhPGvyuSFUgnRHvMSMMiS8WpZ8Yd8yn70evqKl0"
binance_secret="2HfMkleskGwTb6KQn0AKUQfjBDd5dArBW3Ykd2uTeOiv9VZ6qSU2L1yWM1ZlQ5RH"
par ='ETHUSDT'

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


