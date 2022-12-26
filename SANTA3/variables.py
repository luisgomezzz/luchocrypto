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
    lista_monedas_filtradas_file = "lista_monedas_filtradas_binance.txt"
    f = open(os.path.join(pathroot, lista_monedas_filtradas_file), 'a',encoding="utf-8")
    f.close() 
if exchange_name =='kucoin':
    lista_monedas_filtradas_file = "lista_monedas_filtradas_kucoin.txt"
    f = open(os.path.join(pathroot, lista_monedas_filtradas_file), 'a',encoding="utf-8")
    f.close()    
if exchange_name =='finandy':
    lista_monedas_filtradas_file = "lista_monedas_filtradas_finandy.txt"
    f = open(os.path.join(pathroot, lista_monedas_filtradas_file), 'a',encoding="utf-8")
    f.close()         
lanzadorfile = "lanzador.py"
f = open(os.path.join(pathroot, lanzadorfile), 'a',encoding="utf-8")
f.close() 

##PARAMETROS ESTRATEGIA 
temporalidad = '1m'
apalancamiento = 10
margen = 'CROSSED'
ventana = 30 #Ventana de búsqueda en minutos.   

#los porcentajes de pérdidas serán igual a los porcentajes de entrada
porcentajeentradabajo = 10 
porcentajeentradaalto = 20 
paso = 1.7 # distancia entre compensaciones.
incrementocompensacionporc = 30 #porcentaje de incremento del tamaño de la compensacion con respecto a su anterior
cantidadcompensaciones = 99 #la maxima cantidad que permita el saldo
variaciontrigger = 2 #porcentaje de variación (en la ventana de 30 min) por la cual se toma posición. 
maximavariaciondiaria = 40.0 #Máxima variación diaria de una moneda(20%). La maximavariaciondiaria tiene como propósito buscar si 
#la moneda tuvo una variación superior a la indicada en las últimas 12hs, en cuyo caso se evita ingresar a un trade demasiado riesgoso. 
tradessimultaneos = 3 #Número máximo de operaciones en simultaneo... se puede ir variando colocando palabras en operando.txt
## VARIABLES GLOBALES 
operando=[] #lista de monedas que se están operando
lista_monedas_filtradas_nueva = []
flagpuntodeataque = 0 # Ataque automatico. 0 desactivado - 1 activado 

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

mincapitalizacion = float(80000000)

if exchange_name == 'binance':
    api_key = binance_key
    api_secret = binance_secret
    api_passphares = binance_passphares
    client = binanceClient(api_key, api_secret,api_passphares) 
    balanceobjetivo = 0
if exchange_name == 'kucoin':
    api_key = kucoin_key
    api_secret = kucoin_secret
    api_passphares = kucoin_passphares
    exchange_name = 'kucoinfutures'
    client = kucoinClient(api_key, api_secret,api_passphares) 
    clienttrade = kucoinTrade(api_key, api_secret,api_passphares) 
    clientmarket = Market(url='https://api-futures.kucoin.com')
    balanceobjetivo = 0 
if exchange_name == 'finandy':
    api_key = finandy_key
    api_secret = finandy_secret
    api_passphares = finandy_passphares
    exchange_name = 'binance'
    client = binanceClient(api_key, api_secret,api_passphares) 
    balanceobjetivo = 24.00+24.88+71.53+71.62+106.01+105.3+103.14+101.55+102.03+102.49-100+400+400+45+63.59+1500+99.9
    #GOALS
    #400 prestamo compra de dpto. [done]
    #445 que puse la primera vez para aprender. 
    #1500 para llegar al capital base. <<---

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