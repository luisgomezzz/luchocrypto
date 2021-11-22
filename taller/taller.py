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

binance_api="N7yU75L3CNJg2RW0TcJBAW2cUjhPGvyuSFUgnRHvMSMMiS8WpZ8Yd8yn70evqKl0"
binance_secret="2HfMkleskGwTb6KQn0AKUQfjBDd5dArBW3Ykd2uTeOiv9VZ6qSU2L1yWM1ZlQ5RH"
par ='DYDXUSDT'
tr.clear()
chatid="@gofrecrypto" #canal
idgrupo = "-704084758" #grupo de amigos
token = "2108740619:AAHcUBakZLdoHYnvUvkBp6oq7SoS63erb2g"
botlaburo = TelegramBot(token, chatid)
df=tr.historicdf(par,timeframe='1m', limit=3)
###########################################################

# VWAP requires the DataFrame index to be a DatetimeIndex.
# Replace "datetime" with the appropriate column from your DataFrame
df.set_index(pd.DatetimeIndex(df["time"]), inplace=True)

print(df.ta.vwap(anchor='min'))


