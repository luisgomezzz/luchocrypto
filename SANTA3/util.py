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
import os
import winsound as ws
import math
from time import sleep

exchange_name=var.exchange_name

bar = [
      " [=     ]",
      " [ =    ]",
      " [  =   ]",
      " [   =  ]",
      " [    = ]",
      " [     =]",
      " [    = ]",
      " [   =  ]",
      " [  =   ]",
      " [ =    ]",
   ]

bar_i = 0

def waiting(segundossleep=0.0):
    global bar_i   
    print(bar[bar_i % len(bar)], end="\r")      
    bar_i += 1
    if segundossleep>0.0:
        sleep(segundossleep)

def truncate(number, digits) -> float:
    stepper = 10.0 ** digits
    return math.trunc(stepper * number) / stepper

def clear():  
    # for windows
    if name == 'nt':
        _ = system('cls')
    # for mac and linux(here, os.name is 'posix')
    else:
        _ = system('clear')

if exchange_name == 'binance':
    api_key = var.binance_key
    api_secret = var.binance_secret
    api_passphares = var.binance_passphares
    client = binanceClient(api_key, api_secret,api_passphares) 
if exchange_name == 'kucoin':
    api_key = var.kucoin_key
    api_secret = var.kucoin_secret
    api_passphares = var.kucoin_passphares
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
                if 'USDT' in s['symbol']:
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

def volumeOf24h(par):
    vol=0.0
    if exchange_name == 'binance':
        vol= client.futures_ticker(symbol=par)['quoteVolume']
    if exchange_name == 'kucoinfutures':
        datos=exchange.fetch_markets()
        for i in range(len(datos)):
            if datos[i]['id']==par:
                vol=datos[i]['info']['volumeOf24h']
    return float(vol)

def capitalizacion(par):#Para todos los exchanges se usa binance por su mayor estabilidad
    if exchange_name == 'kucoinfutures':
        par=par[0:-1]
    cap=0.0
    clientcap = binanceClient(var.binance_key, var.binance_secret,var.binance_passphares) 
    info = clientcap.get_products()
    lista=info['data']
    df = pd.DataFrame(lista)
    try:
        cap=float(df.c.loc[df['s'] == par]*df.cs.loc[df['s'] == par])
    except:
        cap=0.0
    return cap

def sound(duration = 2000,freq = 440):
    # milliseconds
    # Hz
    # for windows
    if os.name == 'nt':
        ws.Beep(freq, duration)
    # for mac and linux(here, os.name is 'posix')
    else:
        _ = os.system('play -nq -t alsa synth %s sin %s' % (duration/1000, freq))


def printandlog(nombrelog,mensaje,pal=0,mode='a'):
   if pal==0: #print y log
      print(mensaje)
      #escribo file
      f = open(nombrelog, mode,encoding="utf-8")
      f.write("\n"+mensaje)
      f.close()   
   else:
      if pal==1: #solo log
         #escribo file
         f = open(nombrelog, mode,encoding="utf-8")
         f.write("\n"+mensaje)
         f.close()   

def currentprice(par):
    leido = False
    current=0.0
    while leido == False:
        try:
            if exchange_name=='binance':
                current=float(client.get_symbol_ticker(symbol=par)["price"])
            if exchange_name=='kucoinfutures':
                current=float(clientmarket.get_ticker(par)['price'])
            leido = True
        except:
            pass
    return current

def balancetotal():
   leido = False
   while leido == False:
      try:
        if exchange_name=='binance':
            balance=float(exchange.fetch_balance()['info']['totalWalletBalance'])
        if exchange_name=='kucoinfutures':
            balance=float(exchange.fetch_balance()['info']['data']['marginBalance'])
        leido = True
      except:
         pass
   return balance