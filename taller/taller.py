#taller de pruebas
from binance.client import Client
import ccxt
from pprint import pprint
from datetime import datetime, date, time, timedelta
import pandas as pd
import sys
import math
sys.path.insert(1,'./')
import tradeando as tr
import matplotlib.pyplot as plt
import talib.abstract as tl
import numpy as np
import pandas_ta as ta
from bob_telegram_tools.bot import TelegramBot
import pandas_datareader.data as web
import datetime
from datetime import datetime

binance_api="N7yU75L3CNJg2RW0TcJBAW2cUjhPGvyuSFUgnRHvMSMMiS8WpZ8Yd8yn70evqKl0"
binance_secret="2HfMkleskGwTb6KQn0AKUQfjBDd5dArBW3Ykd2uTeOiv9VZ6qSU2L1yWM1ZlQ5RH"
par ='COTIUSDT'
tr.clear()
chatid="@gofrecrypto" #canal
idgrupo = "-704084758" #grupo de amigos
token = "2108740619:AAHcUBakZLdoHYnvUvkBp6oq7SoS63erb2g"
botlaburo = TelegramBot(token, chatid)
client = Client(binance_api, binance_secret)
###############################################################################
df=tr.binancehistoricdf(par,timeframe='1m',limit=100)

tr.timeindex(df)
df.ta.strategy("volume")
#print(df.ta.ema(9).iloc[-1])
#print(df.ta.vwap().iloc[-1])
#print(df.ta.macd()['MACDh_12_26_9'].iloc[-1])
#print(df.ta.rsi().iloc[-1])

exchange = ccxt.binance({
      'enableRateLimit': True,  
      'apiKey': binance_api,
      'secret': binance_secret,
      'options': {  
         'defaultType': 'future',  
      },
   })       

print(ta.xsignals(df.ta.macd()['MACD_12_26_9'], df.ta.macd()['MACDs_12_26_9'], df.ta.macd()['MACDs_12_26_9'],above=True))


print(df.ta.macd())
