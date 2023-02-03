from os import system, name
import os
from kucoin_futures.client import Trade as kucoinTrade
from kucoin.client import Client as kucoinClient
from kucoin_futures.client import Market
import ccxt as ccxt
from binance.client import Client as binanceClient
import inquirer
from colors import *
import sys
import json

RED   = "\033[1;31m"  
BLUE  = "\033[1;34m"
CYAN  = "\033[1;36m"
GREEN = "\033[0;32m"
RESET = "\033[0;0m"
BOLD    = "\033[;1m"
REVERSE = "\033[;7m"
YELLOW = "\33[33m"

#EXCHANGE SELECT
questions = [
  inquirer.List('exchange',
                message="Seleccionar exchange: ",
                choices=['finandy','binance', 'kucoin'],
            ),
]
answers = inquirer.prompt(questions)
exchange_name=answers['exchange']

if exchange_name=='binance':
    sys.stdout.write(YELLOW)
if exchange_name=='kucoin':
    sys.stdout.write(GREEN)
if exchange_name=='finandy':
    sys.stdout.write(BLUE)    

pathroot=os.path.dirname(os.path.abspath(__file__))+'/'
pathsound=pathroot+'sounds/' 

def clear():  
    # for windows
    if name == 'nt':
        _ = system('cls')
    # for mac and linux(here, os.name is 'posix')
    else:
        _ = system('clear')

##FILES
if exchange_name =='binance':
    nombrelog = "log_binace.txt"
if exchange_name =='kucoin':
    nombrelog = "log_kucoin.txt" 
if exchange_name =='finandy':
    nombrelog = "log_finandy.txt"
f = open(os.path.join(pathroot, nombrelog), 'a',encoding="utf-8")
f.close() 
operandofile = "operando.txt"
f = open(os.path.join(pathroot, operandofile), 'a',encoding="utf-8")
f.close() 
if exchange_name =='binance':
    dict_monedas_filtradas_file = "dict_monedas_filtradas_binance.txt"
    f = open(os.path.join(pathroot, dict_monedas_filtradas_file), 'a',encoding="utf-8")
    f.close() 
if exchange_name =='kucoin':
    dict_monedas_filtradas_file = "dict_monedas_filtradas_kucoin.txt"
    f = open(os.path.join(pathroot, dict_monedas_filtradas_file), 'a',encoding="utf-8")
    f.close()    
if exchange_name =='finandy':
    dict_monedas_filtradas_file = "dict_monedas_filtradas_finandy.txt"
    f = open(os.path.join(pathroot, dict_monedas_filtradas_file), 'a',encoding="utf-8")
    f.close()         
lanzadorfile = "lanzador.py"
f = open(os.path.join(pathroot, lanzadorfile), 'a',encoding="utf-8")
f.close() 

##PARAMETROS ESTRATEGIA 
temporalidad = '1m'
margen = 'CROSSED'
## VARIABLES GLOBALES 
operando=[] #lista de monedas que se están operando
dict_monedas_filtradas_nueva = []
flagpuntodeataque = 1 # Ataque automatico. 0 desactivado - 1 activado 

#BINANCE
binance_key="N7yU75L3CNJg2RW0TcJBAW2cUjhPGvyuSFUgnRHvMSMMiS8WpZ8Yd8yn70evqKl0"
binance_secret="2HfMkleskGwTb6KQn0AKUQfjBDd5dArBW3Ykd2uTeOiv9VZ6qSU2L1yWM1ZlQ5RH"
binance_passphares=''
#KUCOIN
kucoin_key='63618000e26bf70001e2bd2c'
kucoin_secret='409d3eff-9622-4488-af21-fa0feabb24ec'
kucoin_passphares='santakucoin'
#FINANDY
finandy_key="qycthSI8s5HH0b95MxH3lFKPPUeZu8mCSgztp00x2d7SdHmfOp2U9qBeCCbxPyDg"
finandy_secret="zeJqYkyWzBIdGDMmyfUnofQiThirgEgOCDYvS3rzcq4yle1afD7YEQkciCI43yNs"
finandy_passphares=''

if exchange_name == 'kucoin':
    minvolumen24h =  float(10000000)
else:
    minvolumen24h = float(100000000)

mincapitalizacion = float(10000000)

if exchange_name == 'binance':
    api_key = binance_key
    api_secret = binance_secret
    api_passphares = binance_passphares
    client = binanceClient(api_key, api_secret,api_passphares) 
if exchange_name == 'kucoin':
    api_key = kucoin_key
    api_secret = kucoin_secret
    api_passphares = kucoin_passphares
    exchange_name = 'kucoinfutures'
    client = kucoinClient(api_key, api_secret,api_passphares) 
    clienttrade = kucoinTrade(api_key, api_secret,api_passphares) 
    clientmarket = Market(url='https://api-futures.kucoin.com')
if exchange_name == 'finandy':
    api_key = finandy_key
    api_secret = finandy_secret
    api_passphares = finandy_passphares
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

clear() #limpia terminal
if answers['exchange'] =='binance':
    print('''

            _     _                            
            | |   (_)                           
            | |__  _ _ __   __ _ _ __   ___ ___ 
            | '_ \| | '_ \ / _` | '_ \ / __/ _ 
            | |_) | | | | | (_| | | | | (_|  __/
            |_.__/|_|_| |_|\__,_|_| |_|\___\___|
                                                
                                                
    ''')
if answers['exchange']=='kucoin':
    print('''

            _                    _       
            | |                  (_)      
            | | ___   _  ___ ___  _ _ __  
            | |/ / | | |/ __/ _ \| | '_ \ 
            |   <| |_| | (_| (_) | | | | |
            |_|\_\\__,_|\___\___/|_|_| |_|
                                                                               
                                    
    ''')

if answers['exchange']=='finandy':
    print('''

   __ _                       _       
  / _(_)                     | |      
 | |_ _ _ __   __ _ _ __   __| |_   _ 
 |  _| | '_ \ / _` | '_ \ / _` | | | |
 | | | | | | | (_| | | | | (_| | |_| |
 |_| |_|_| |_|\__,_|_| |_|\__,_|\__, |
                                 __/ |
                                |___/ 
           
    ''')

# Data to be written
dictionary = {
    "ventana" : 30, #Ventana de búsqueda en minutos.   
    "porcentajeentrada" : 8, 
    "procentajeperdida" : 13,
    "incrementocompensacionporc" : 30, #porcentaje de incremento del tamaño de la compensacion con respecto a su anterior
    "cantidadcompensaciones" : 7,
    "variaciontrigger" : 5, #porcentaje de variación (en la ventana de 30 min) por la cual se toma posición. 
    "maximavariaciondiaria" : 50, #Máxima variación diaria de una moneda(20%). La maximavariaciondiaria tiene como propósito buscar si la moneda tuvo una variación superior a la indicada en las últimas 12hs, en cuyo caso se evita ingresar a un trade demasiado riesgoso. 
    "tradessimultaneos" : 2, #Número máximo de operaciones en simultaneo... se puede ir variando colocando palabras en operando.txt  
    "distanciaentrecompensacionesalta" : 1.7, #porcentaje de distancia entre compensaciones para monedas por debajo del top de capitalización
    "distanciaentrecompensacionesbaja" : 1, #porcentaje de distancia entre compensaciones para monedas del top de capitalización.
    "reservas": 2437, #valor ahorrado. Ir sumando los depósitos que se realicen a este valor.
    "sideflag": 0 # 0 ambos | 1 solo shorts | 2 solo longs
}
# Serializing json
json_object = json.dumps(dictionary, indent=4)

if os.path.isfile(os.path.join(pathroot, "configuration.json")) == False:# si no existe el archivo lo crea con los parametros por defecto
    # Writing to configuration.json
    with open(os.path.join(pathroot, "configuration.json"), "w") as outfile:
        outfile.write(json_object)

url_stream = "wss://stream.binance.com:9443/ws/"

apalancamientoreal=10 # Este es el valor que, multiplicado por mi capital total, dará el capital total disponible para usar en posición 
# y compensaciones. Durante el código pueden usarse apalancamientos distintos para poder usar todo el capital apalancado
# (apalancamientoreal*balancetotal) en la estrategia.

#monedas que no quiero operar
mazmorra=['TUSDT']