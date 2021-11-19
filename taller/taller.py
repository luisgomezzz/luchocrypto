#modulo de ordenes
from binance.client import Client
import os
import ccxt
from pprint import pprint
from datetime import datetime, date, time, timedelta
import pandas as pd
################
import sys
import math
sys.path.insert(1,'/home/lucho/PERSONALREPO/luchocrypto/')
import tradeando as tr
import matplotlib.pyplot as plt   # needs pip install
import talib.abstract as tl
import numpy as np
################3
os.system("clear")

binance_api="N7yU75L3CNJg2RW0TcJBAW2cUjhPGvyuSFUgnRHvMSMMiS8WpZ8Yd8yn70evqKl0"
binance_secret="2HfMkleskGwTb6KQn0AKUQfjBDd5dArBW3Ykd2uTeOiv9VZ6qSU2L1yWM1ZlQ5RH"
par ='LRCUSDT'

client = Client(binance_api, binance_secret)
exchange_info = client.futures_exchange_info()

print(tr.estrategia3emas (par))