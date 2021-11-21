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

binance_api="N7yU75L3CNJg2RW0TcJBAW2cUjhPGvyuSFUgnRHvMSMMiS8WpZ8Yd8yn70evqKl0"
binance_secret="2HfMkleskGwTb6KQn0AKUQfjBDd5dArBW3Ykd2uTeOiv9VZ6qSU2L1yWM1ZlQ5RH"
par ='LRCUSDT'
tr.clear()
historicdf=tr.historicdf(par)
###########################################################

print(ta.xsignals(historicdf.ta.sma(21), historicdf.ta.sma(50), historicdf.ta.sma(50),above=False)['TS_Entries'].iloc[-1])