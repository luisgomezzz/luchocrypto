import ccxt as ccxt
from os import system, name
from binance.client import Client as binanceClient
from kucoin_futures.client import Trade as kucoinTrade
from kucoin.client import Client as kucoinClient
from kucoin_futures.client import Market
import sys
import pandas as pd
import variables as var
from requests import Request, Session
import json
import pprint

exchange_name=var.exchange_name

def clear():  
    # for windows
    if name == 'nt':
        _ = system('cls')
    # for mac and linux(here, os.name is 'posix')
    else:
        _ = system('clear')

#BINANCE
binance_key="N7yU75L3CNJg2RW0TcJBAW2cUjhPGvyuSFUgnRHvMSMMiS8WpZ8Yd8yn70evqKl0"
binance_secret="2HfMkleskGwTb6KQn0AKUQfjBDd5dArBW3Ykd2uTeOiv9VZ6qSU2L1yWM1ZlQ5RH"
binance_passphares=''
#KUCOIN
kucoin_key='63618000e26bf70001e2bd2c'
kucoin_secret='409d3eff-9622-4488-af21-fa0feabb24ec'
kucoin_passphares='santakucoin'

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

def lista_de_monedas ():
    lista_de_monedas = []
    if exchange_name =='binance':
        exchange_info = client.futures_exchange_info()['symbols'] #obtiene lista de monedas        
        for s in exchange_info:
            try:
                lista_de_monedas.append(s['symbol'])
            except Exception as ex:
                pass    
    if exchange_name =='kucoinfutures':
        exchange_info = clientmarket.get_contracts_list()
        for index in range(len(exchange_info)):
            try:
                lista_de_monedas.append(exchange_info[index]['symbol'])
            except Exception as ex:
                pass    
    return lista_de_monedas  

def timeindex(df):
    # if you encounter a "year is out of range" error the timestamp
    # may be in milliseconds, try `ts /= 1000` in that case
    df['time2']=df['time']/1000
    df['time3']=(pd.to_datetime(df['time2'],unit='s')) 
    df.set_index(pd.DatetimeIndex(df["time3"]), inplace=True)

def calculardf (par,temporalidad,ventana):
    leido = False
    while leido == False:
        try:
            barsindicators = exchange.fetch_ohlcv(par,timeframe=temporalidad,limit=ventana)
            df = pd.DataFrame(barsindicators,columns=['time','open','high','low','close','volume'])
            timeindex(df) #Formatea el campo time para luego calcular las señales
            leido = True
        except KeyboardInterrupt:
            print("\nSalida solicitada.")
            sys.exit()  
        except:
            pass
    return df      

def equipoliquidando ():
    listaequipoliquidando = lista_de_monedas()
    mazmorra=['1000SHIBUSDT','1000XECUSDT','BTCDOMUSDT','FOOTBALLUSDT'
    ,'DEFIUSDT','1000LUNCUSDT','LUNA2USDT','BLUEBIRDUSDT'] #Monedas que no quiero operar (muchas estan aqui porque fallan en algun momento al crear el dataframe)         
    lista=[]
    temporalidad='1d'
    ventana = 30
    variacionporc = 10
    for par in listaequipoliquidando:
        try:            
            sys.stdout.write("\r"+par+"\033[K")
            sys.stdout.flush()   
            if ('USDT' in par and '_' not in par and par not in mazmorra ):
                df=calculardf (par,temporalidad,ventana)
                df['liquidando'] = (df.close >= df.open*(1+variacionporc/100)) & (df.high - df.close >= df.close-df.open) 
                if True in set(df['liquidando']):
                    lista.append(par)                    
        except Exception as ex:
            pass        
        except KeyboardInterrupt as ky:
            print("\nSalida solicitada. ")
            sys.exit()           
    return lista      

def coinmarketcapgetInfo (simbolo='BTC',dato='market_cap'): 
    #'fully_diluted_market_cap': 17003944767.9,
    #'last_updated': '2022-11-05T13:06:00.000Z',
    #'market_cap': 17003944767.896461,
    #'market_cap_dominance': 1.6021,
    #'percent_change_1h': -0.36212297,
    #'percent_change_24h': 4.06218744,
    #'percent_change_30d': 96.57331683,
    #'percent_change_60d': 102.94371962,
    #'percent_change_7d': 18.32382645,
    #'percent_change_90d': 85.19554762,
    #'price': 0.12816647931159944,
    #'tvl': None,
    #'volume_24h': 2489967101.284444,
    #'volume_change_24h': -10.6394
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest' # Coinmarketcap API url
    parameters = { 'symbol': simbolo, 'convert': 'USD' }# API parameters to pass in for retrieving specific cryptocurrency data
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': '4c9c0645-49c7-48c3-9a42-e7a2f94d448f'
    }
    session = Session()
    session.headers.update(headers)
    response = session.get(url, params=parameters)
    info = json.loads(response.text)['data'][simbolo]['quote']['USD'][dato]
    return info