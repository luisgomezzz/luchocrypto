from time import sleep
from binance.client import Client
from binance.exceptions import BinanceAPIException
import sys, os
import pandas as pd
pd.core.common.is_list_like = pd.api.types.is_list_like
import yfinance as yahoo_finance
yahoo_finance.pdr_override()
sys.path.insert(1,'./')
import utilidades as ut
import datetime as dt
from datetime import datetime
import numpy as np
from datetime import datetime, timedelta
import pandas_ta as pta
from finta import TA
import pandas_ta as ta
import indicadores as ind

client = Client(ut.binance_api, ut.binance_secret) 

##PARAMETROS##########################################################################################
mazmorra=['1000SHIBUSDT','DODOUSDT'] #Monedas que no quiero operar en orden de castigo
ventana = 240 #Ventana de búsqueda en minutos.   
exchange=ut.exchange #login
lista_de_monedas = client.futures_exchange_info()['symbols'] #obtiene lista de monedas
saldo_inicial=ut.balancetotal
posicioncreada = False
minvolumen24h=float(100000000)
vueltas=0
minutes_diff=0
lista_monedas_filtradas=[]
mensaje=''
porcentajevariacion = 0.30
balanceobjetivo = 24.00
dicciobuy = {'NADA': [0.0,0.0,str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))]}
dicciosell = {'NADA': [0.0,0.0,str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))]}
dicciobuy.clear()
dicciosell.clear()
ratio = 0.58 #Risk/Reward Ratio
temporalidad='1m'   
par='ALICEUSDT'
ut.clear() #limpia terminal
  
df=ut.calculardf (par,temporalidad,ventana)
df.fillna(0)


len = 14
th = 20

df['TrueRange'] = np.maximum(np.maximum(df.high-df.low, abs(df.high-(df.close.shift(1).fillna(0)))), abs(df.low-(df.close.shift(1).fillna(0))))

df['pluscalc1'] = df.high-df.high.shift(1).fillna(0)
df['pluscalc2'] = df.low.shift(1).fillna(0)-df.low
df.loc[df['pluscalc1'] > df['pluscalc2'], 'DirectionalMovementPlus'] = np.maximum(df.high-df.high.shift(1).fillna(0), 0)
df.loc[df['pluscalc1'] <= df['pluscalc2'], 'DirectionalMovementPlus'] = 0

df['minuscalc1'] = df.low.shift(1).fillna(0)-df.low
df['minuscalc2'] = df.high-df.high.shift(1).fillna(0)
df.loc[df['minuscalc1'] > df['minuscalc2'], 'DirectionalMovementMinus'] = np.maximum(df.low.shift(1).fillna(0)-df.low, 0)
df.loc[df['minuscalc1'] <= df['minuscalc2'], 'DirectionalMovementMinus'] = 0

df['SmoothedTrueRange'] = 0.0
df['SmoothedTrueRange'] = (df['SmoothedTrueRange'].shift(1).fillna(0)) - ((df['SmoothedTrueRange'].shift(1).fillna(0))/len) + df['TrueRange']

df['SmoothedDirectionalMovementPlus'] = 0.0
df['SmoothedDirectionalMovementPlus'] = (df['SmoothedDirectionalMovementPlus'].shift(1).fillna(0)) - ((df['SmoothedDirectionalMovementPlus'].shift(1).fillna(0))/len) + df['DirectionalMovementPlus']

df['SmoothedDirectionalMovementMinus'] = 0.0
df['SmoothedDirectionalMovementMinus'] = (df['SmoothedDirectionalMovementMinus'].shift(1).fillna(0)) - ((df['SmoothedDirectionalMovementMinus'].shift(1).fillna(0))/len) + df['DirectionalMovementMinus']

df['DIPlus'] = df['SmoothedDirectionalMovementPlus'] / df['SmoothedTrueRange'] * 100
df['DIMinus'] = df['SmoothedDirectionalMovementMinus'] / df['SmoothedTrueRange'] * 100
df['DX'] = abs(df['DIPlus']-df['DIMinus']) / (df['DIPlus']+df['DIMinus'])*100

#####################

df2=df[['DX','DIPlus','DirectionalMovementPlus','DirectionalMovementMinus','SmoothedTrueRange','SmoothedDirectionalMovementPlus','SmoothedDirectionalMovementMinus']].copy()

print(df2)


