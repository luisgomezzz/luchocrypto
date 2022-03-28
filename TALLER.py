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

botlaburo = ut.creobot('laburo')
botamigos = ut.creobot('amigos') 
apalancamiento = 50
margen = 'CROSSED'
temporalidad='1m'
client = Client(ut.binance_api, ut.binance_secret)
par = 'IOTAUSDT'
ventana = 240 #Ventana de búsqueda en minutos.  

suddendf=ut.binancehistoricdf(par,timeframe=temporalidad,limit=ventana) # Buscar valores mínimos y máximos N (ventana) minutos para atrás.
ut.timeindex(suddendf) #Formatea el campo time para luego calcular las señales
suddendf.ta.study() # Runs and appends all indicators to the current DataFrame by default

print(suddendf)

suddendf.ta.strategy() # Runs and appends all indicators to the current DataFrame by default

print(client.futures_ticker(symbol=par)['quoteVolume'])