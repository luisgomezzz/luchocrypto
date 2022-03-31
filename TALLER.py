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


df=ut.binancehistoricdf(par,timeframe=temporalidad,limit=ventana) # para fractales.

if ut.will_frac(df)[0].iloc[-1]==True:
    posicion=[-1,'BEARS']
else:
    if ut.will_frac(df)[1].iloc[-1]==True:
        posicion=[-1,'BULLS']
    else:
        if ut.will_frac(df)[0].iloc[-2]==True:
            posicion=[-2,'BEARS']
        else:
            if ut.will_frac(df)[1].iloc[-2]==True:
                posicion=[-2,'BULLS']
            else:
                if ut.will_frac(df)[0].iloc[-3]==True:
                    posicion=[-3,'BEARS']
                else:
                    if ut.will_frac(df)[1].iloc[-3]==True:
                        posicion=[-3,'BULLS']
                    else:
                        if ut.will_frac(df)[0].iloc[-4]==True:
                            posicion=[-4,'BEARS']
                        else:
                            if ut.will_frac(df)[1].iloc[-4]==True:
                                posicion=[-4,'BULLS']        

print(posicion)

