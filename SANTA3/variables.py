from os import system, name
import os
from kucoin_futures.client import Trade as kucoinTrade
from kucoin.client import Client as kucoinClient
from kucoin_futures.client import Market
import ccxt as ccxt
from binance.client import Client as binanceClient
import inquirer

#EXCHANGE SELECT
questions = [
  inquirer.List('exchange',
                message="Seleccionar exchange: ",
                choices=['binance', 'kucoin'],
            ),
]
answers = inquirer.prompt(questions)
exchange_name=answers['exchange']

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
lanzadorfile = "lanzador.py"
f = open(os.path.join(pathroot, lanzadorfile), 'a',encoding="utf-8")
f.close() 

##PARAMETROS ESTRATEGIA 
temporalidad = '1m'
apalancamiento = 10
margen = 'CROSSED'
procentajeperdida = 10 #porcentaje de mi capital total maximo a perder (10)
#porcentaje de la cuenta para crear la posición. 
if exchange_name=='kucoin':
    porcentajeentrada = 20 
else:
    porcentajeentrada = 7
#con 5 soporta 18% de variacion. (con 6 compensaciones)
#con 7 soporta 15% de variacion. (con 6 compensaciones) 
#con 10 soporta 12% de variacion. (con 6 compensaciones) 
ventana = 30 #Ventana de búsqueda en minutos.   
cantidadcompensaciones = 6
maximavariaciondiaria = 20 #maxima variacion diaria de una moneda(20)
tradessimultaneos = 3 #Número máximo de operaciones en simultaneo... se puede ir variando colocando palabras en operando.txt
## VARIABLES GLOBALES 
operando=[] #lista de monedas que se están operando
incrementocompensacionporc = 30 #porcentaje de incremento del tamaño de la compensacion con respecto a su anterior

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

if exchange_name == 'kucoin':
    minvolumen24h =  float(10000000)
else:
    minvolumen24h = float(200000000)

mincapitalizacion = float(80000000)

if exchange_name == 'binance':
    api_key = binance_key
    api_secret = binance_secret
    api_passphares = binance_passphares
    client = binanceClient(api_key, api_secret,api_passphares) 
    balanceobjetivo = 24.00+24.88+71.53+71.62+106.01+105.3+103.14+101.55+102.03+102.49-100+400+400
    #los 400 son los que puse la primera vez para aprender.
if exchange_name == 'kucoin':
    api_key = kucoin_key
    api_secret = kucoin_secret
    api_passphares = kucoin_passphares
    exchange_name = 'kucoinfutures'
    client = kucoinClient(api_key, api_secret,api_passphares) 
    clienttrade = kucoinTrade(api_key, api_secret,api_passphares) 
    clientmarket = Market(url='https://api-futures.kucoin.com')
    balanceobjetivo = 100 #100 iniciales q transeferí desde binance

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
if exchange_name =='binance':
    print('''

            _     _                            
            | |   (_)                           
            | |__  _ _ __   __ _ _ __   ___ ___ 
            | '_ \| | '_ \ / _` | '_ \ / __/ _ 
            | |_) | | | | | (_| | | | | (_|  __/
            |_.__/|_|_| |_|\__,_|_| |_|\___\___|
                                                
                                                
    ''')
if exchange_name=='kucoinfutures':
    print('''

            _                    _       
            | |                  (_)      
            | | ___   _  ___ ___  _ _ __  
            | |/ / | | |/ __/ _ \| | '_ \ 
            |   <| |_| | (_| (_) | | | | |
            |_|\_\\__,_|\___\___/|_|_| |_|
                                                                               
                                    
    ''')