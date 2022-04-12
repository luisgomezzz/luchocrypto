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
par = 'APEUSDT'
ventana = 250 #Ventana de búsqueda en minutos.  
posicion=[0,'NADA']
exchange=ut.binanceexchange(ut.binance_api,ut.binance_secret) #login


df=ut.binancehistoricdf(par,timeframe=temporalidad,limit=ventana) # para fractales.

###CODIGO
ut.timeindex(df) #Formatea el campo time para luego calcular las señales
df.ta.study() # Runs and appends all indicators to the current DataFrame by default

high_9 = df.high.rolling(9).max()
low_9 = df.low.rolling(9).min()
df['tenkan_sen_line'] = (high_9 + low_9) /2
# Calculate Kijun-sen
high_26 = df.high.rolling(26).max()
low_26 = df.low.rolling(26).min()
df['kijun_sen_line'] = (high_26 + low_26) / 2
# Calculate Senkou Span A
df['senkou_spna_A'] = ((df.tenkan_sen_line + df.kijun_sen_line) / 2).shift(26)
# Calculate Senkou Span B
high_52 = df.high.rolling(52).max()
low_52 = df.high.rolling(52).min()
df['senkou_spna_B'] = ((high_52 + low_52) / 2).shift(26)
# Calculate Chikou Span B
df['chikou_span'] = df.close.shift(-26)

df['SAR'] = talib.SAR(df.high, df.low, acceleration=0.02, maximum=0.2)

df['signal'] = 0
df.loc[(df.close > df.senkou_spna_A) & (df.close > df.senkou_spna_B) & (df.close > df.SAR), 'signal'] = 1

df.loc[(df.close < df.senkou_spna_A) & (df.close < df.senkou_spna_B) & (df.close < df.SAR), 'signal'] = -1

#print(df['signal'])
print(df.ta.ema(200).iloc[-1])

help(ta.tsignals)