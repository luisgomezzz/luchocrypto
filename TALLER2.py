#****************************************************************************************
# version 2.0
#
#****************************************************************************************

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
import pandas_ta as pta
from time import sleep
import indicadores as ind
import winsound as ws
from datetime import timedelta
import santaestrategia2 as s2


##CONFIG########################
client = ut.client
exchange = ut.exchange
botlaburo = ut.creobot('laburo')      
nombrelog = "log_fli.txt"

##PARAMETROS##########################################################################################
mazmorra=['1000SHIBUSDT','1000XECUSDT','BTCUSDT_220624','ETHUSDT_220624'] #Monedas que no quiero operar 
ventana = 40 #Ventana de búsqueda en minutos.   
lista_de_monedas = client.futures_exchange_info()['symbols'] #obtiene lista de monedas
saldo_inicial = ut.balancetotal()
posicioncreada = False
minvolumen24h=float(200000000)
vueltas=0
minutes_diff=0
lista_monedas_filtradas=[]
mensaje=''
balanceobjetivo = 24.00+24.88
temporalidad='1m'   
ratio = 1/(1.0) #Risk/Reward Ratio
mensajeposicioncompleta=''
porcentajelejosdeema5=1.00
porcentaje=5
par='RENUSDT'


df=ut.calculardf (par,temporalidad,ventana)
preciomenor=df.low.min()
precioactual=ut.currentprice(par)
preciomayor=df.close.max()

trades = ut.binancetrades(par,ventana)
preciomenor2 = float(min(trades, key=lambda x:x['p'])['p'])
precioactual2 = float(client.get_symbol_ticker(symbol=par)["price"])  
preciomayor2 = float(max(trades, key=lambda x:x['p'])['p'])   

print(df)
df = df[:-1]
print(df)