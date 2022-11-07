import sys
sys.path.insert(1,'./')
from kucoin_futures.client import Trade as kucoinTrade
from kucoin.client import Client as kucoinClient
from kucoin_futures.client import Market
import ccxt as ccxt
from binance.client import Client as binanceClient
from os import system, name

def clear():  
    # for windows
    if name == 'nt':
        _ = system('cls')
    # for mac and linux(here, os.name is 'posix')
    else:
        _ = system('clear')

#EXCHANGE SELECT
#exchange_name = 'kucoin'
exchange_name = 'binance'

##FILES
nombrelog = "log_santa2.txt"
operandofile = "operando.txt"
lista_monedas_filtradas_file = "lista_monedas_filtradas.txt"
lanzadorfile = "lanzador.py"
##PARAMETROS ESTRATEGIA 
temporalidad = '1m'
apalancamiento = 10
margen = 'CROSSED'
procentajeperdida = 10 #porcentaje de mi capital total maximo a perder (10)
porcentajeentrada = 10 #porcentaje de la cuenta para crear la posición (6)
ventana = 30 #Ventana de búsqueda en minutos.   
cantidadcompensaciones = 6
## VARIABLES GLOBALES 
operando=[] #lista de monedas que se están operando
incrementocompensacionporc = 30 #porcentaje de incremento del tamaño de la compensacion con respecto a su anterior
balanceobjetivo = 24.00+24.88+71.53+71.62+106.01+105.3+103.14+101.55+102.03+102.49+400 #los 400 son los del prestamo del dpto que quiero recuperar
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
    minvolumen24h = float(150000000)
else:
    minvolumen24h = float(200000000)

mincapitalizacion = float(80000000)

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