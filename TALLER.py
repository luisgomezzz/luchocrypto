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

ut.clear()

botlaburo = ut.creobot('laburo')
botamigos = ut.creobot('amigos') 
apalancamiento = 50
margen = 'CROSSED'
temporalidad='5m'
client = Client(ut.binance_api, ut.binance_secret)
par = 'LINKUSDT'
ventana = 240 #Ventana de búsqueda en minutos.  
posicion=[0,'NADA']
exchange=ut.binanceexchange(ut.binance_api,ut.binance_secret) #login

saldo_inicial=float(exchange.fetch_balance()['info']['totalWalletBalance'])

print(saldo_inicial)