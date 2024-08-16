from os import system, name
import os
import ccxt as ccxt
from binance.client import Client as binanceClient
import json

pathroot=os.path.dirname(os.path.abspath(__file__))+'/'

def clear():  
    # for windows
    if name == 'nt':
        _ = system('cls')
    # for mac and linux(here, os.name is 'posix')
    else:
        _ = system('clear')

clear() #limpia terminal        

##FILES
nombrelog = "log_finandy.txt"
f = open(os.path.join(pathroot, nombrelog), 'a',encoding="utf-8")
f.close() 

api_key="NYRJeyPdSulRAL1Chx79V36zXcZ6TmhKGZGkoU2vQSq9elCyJqjq8c8ixywv5Yn0"
api_secret="5Omvt1ChDkW0ddH51s8X6tXb4rei6TfL3kCllnDFl2Tm3Q3noECOyL6uVzBpxMqJ"
api_passphares=''
exchange_name = 'binance'
client = binanceClient(api_key, api_secret,api_passphares)
exchange_class = getattr(ccxt, exchange_name)
exchange =   exchange_class({            
            'apiKey': api_key,
            'secret': api_secret,
            'password': api_passphares,
            'options': {  
            'defaultType': 'future',  
            },
            })

margen = 'CROSSED'

# Crea el file de posiciones si no existe
posiciones={}
if os.path.isfile(os.path.join(pathroot, "posiciones.json")) == False:
    with open(pathroot+"posiciones.json","w") as j:
        json.dump(posiciones,j, indent=4)

# Crea el file de configuracion si no existe
configuracion= {
    "cantidad_posiciones": 5,
    "restriccionhoraria": 1
}

if os.path.isfile(os.path.join(pathroot, "configuracion.json")) == False:
    with open(pathroot+"configuracion.json","w") as j:
        json.dump(configuracion,j, indent=4)

minvolumen24h = float(100000000)
mincapitalizacion = float(100000000)

#monedas que no quiero operar
#BELUSDT moneda que ya ha hecho manipulaciones.
mazmorra=[]