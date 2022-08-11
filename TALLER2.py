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



## define list of places
#places_list = ['Berlin', 'Cape Town', 'Sydney', 'Moscow']
#
#with open('operando.txt', 'w') as filehandle:
#    filehandle.writelines("%s\n" % place for place in places_list)
#
## define empty list
#places = []
#
## open file and read the content in a list
#with open('operando.txt', 'r') as filehandle:
#    places = [current_place.rstrip() for current_place in filehandle.readlines()]
#
#print(places)

##agrego
#with open('operando.txt', 'a') as filehandle:
#    filehandle.writelines("%s\n" % place for place in ['BTCUSDT'])
#
##leo
#with open('operando.txt', 'r') as filehandle:
#    places = [current_place.rstrip() for current_place in filehandle.readlines()]
#
#print(places)

#borro todo
#open("operando.txt", "a").close()

#leo
with open('operando.txt', 'r') as filehandle:
    operando = [current_place.rstrip() for current_place in filehandle.readlines()]

print(str(operando))

##agrego
#with open('operando.txt', 'a') as filehandle:
#    filehandle.writelines("%s\n" % place for place in [par])


# remove the item for all its occurrences
c = operando.count(par)
for i in range(c):
    operando.remove(par)

#borro todo
open("operando.txt", "w").close()
##agrego
with open('operando.txt', 'a') as filehandle:
    filehandle.writelines("%s\n" % place for place in operando)


print(str(operando))