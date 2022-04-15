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


#df2=pd.DataFrame(df['time']/1000)
#df2=df2.set_axis(['time2'], axis=1, inplace=False)


def timeindex(df):
   # if you encounter a "year is out of range" error the timestamp
   # may be in milliseconds, try `ts /= 1000` in that case
   df2=pd.DataFrame(df['time']/1000) #df['time2']=df['time']/1000
   df3 = df2.rename(columns = {'time': 'time2'}, inplace = False)
   df4=pd.concat([df, df3])
   #df4 = df3.rename(columns = {'time': 'time2'}, inplace = False)
   #df5=pd.DataFrame(pd.to_datetime(df3['time2'],unit='s')) 
   print(df4)
   

   

df=ut.binancehistoricdf(par,timeframe=temporalidad,limit=ventana) # para fractales.
timeindex(df) #Formatea el campo time para luego calcular las señales
#df.ta.strategy() # Runs and appends all indicators to the current DataFrame by default
