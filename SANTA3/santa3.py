#****************************************************************************************
# version 3.0
#
#****************************************************************************************

from this import d
import sys, os
sys.path.insert(1,'./')
import util as ut
import datetime as dt
from datetime import datetime
import threading
import numpy as np
from playsound import playsound

##CONFIG
client = ut.client
exchange = ut.exchange
nombrelog = "log_santa2.txt"
operandofile = "operando.txt"
lista_monedas_filtradas_file = "lista_monedas_filtradas.txt"
lanzadorfile = "lanzador.py"
## PARAMETROS FUNDAMENTALES 
temporalidad = '1m'
apalancamiento = 10
margen = 'CROSSED'
procentajeperdida = 10 #porcentaje de mi capital total maximo a perder (10)
porcentajeentrada = 6 #porcentaje de la cuenta para crear la posición (6)
ventana = 30 #Ventana de búsqueda en minutos.   
porcentaje = 15 #porcentaje de variacion para el cual se dispara el trade estandar.
cantidadcompensaciones = 2
## VARIABLES GLOBALES 
operando=[] #lista de monedas que se están operando
incrementocompensacionporc = 30 #porcentaje de incremento del tamaño de la compensacion con respecto a su anterior
balanceobjetivo = 24.00+24.88+71.53+71.62+106.01+105.3+103.14+101.55+102.03+102.49+400 #los 400 son los del prestamo del dpto que quiero recuperar
lista_monedas_filtradas_nueva = []
flagpuntodeataque = 0 # Ataque automatico. 0 desactivado - 1 activado 
###################################################################################################################
###################################################################################################################
###################################################################################################################

def filtradodemonedas ():
    
    lista_monedas_filtradas_aux = []
    lista_de_monedas = ut.lista_de_monedas ()
    minvolumen24h=float(200000000)
    mincapitalizacion = float(80000000)    
    mazmorra=['1000SHIBUSDT','1000XECUSDT','BTCUSDT_220624','ETHUSDT_220624','ETHUSDT_220930','BTCUSDT_220930','BTCDOMUSDT','FOOTBALLUSDT'
    ,'ETHUSDT_221230'] #Monedas que no quiero operar (muchas estan aqui porque fallan en algun momento al crear el dataframe)     
    for par in lista_de_monedas:
        try:  
            if (float(client.futures_ticker(symbol=par)['quoteVolume'])>minvolumen24h and 'USDT' in par and par not in mazmorra
                and ut.capitalizacion(par)>=mincapitalizacion):
                lista_monedas_filtradas_aux.append(par)
        except Exception as ex:
            pass        
        except KeyboardInterrupt as ky:
            print("\nSalida solicitada. ")
            sys.exit()   

    global lista_monedas_filtradas_nueva
    lista_monedas_filtradas_nueva = lista_monedas_filtradas_aux

