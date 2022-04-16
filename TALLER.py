from time import sleep
from binance.client import Client
from binance.exceptions import BinanceAPIException
import sys
import pandas as pd
pd.core.common.is_list_like = pd.api.types.is_list_like
import yfinance as yahoo_finance
yahoo_finance.pdr_override()
sys.path.insert(1,'./')
import utilidades as ut
import pandas_ta as ta
import datetime as dt
import talib

ut.clear()

botlaburo = ut.creobot('laburo')
botamigos = ut.creobot('amigos') 
apalancamiento = 50
margen = 'CROSSED'
temporalidad='3m'
client = Client(ut.binance_api, ut.binance_secret)
par = 'ETHUSDT'
ventana = 250 #Ventana de búsqueda en minutos.  
posicion=[0,'NADA']
exchange=ut.binanceexchange(ut.binance_api,ut.binance_secret) #login


df=ut.binancehistoricdf(par,timeframe=temporalidad,limit=ventana) # para fractales.

ut.timeindex(df) #Formatea el campo time para luego calcular las señales

df.ta.strategy(ta.CommonStrategy)