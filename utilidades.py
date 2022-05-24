# Toda la info
# https://github.com/twopirllc/pandas-ta
#
#requirements.txt
## install
#pip3 install pipreqs
#
# Run in current directory
#python3 -m  pipreqs.pipreqs .
#

import math
import pandas as pd
import yfinance as yahoo_finance
yahoo_finance.pdr_override()
from mplfinance.original_flavor import candlestick2_ohlc
import ccxt
from os import system, name
import os
from binance.exceptions import BinanceAPIException
from bob_telegram_tools.bot import TelegramBot
from typing import Tuple
import numpy as np
import talib as tl
import pandas_ta as ta
import sys

binance_api="N7yU75L3CNJg2RW0TcJBAW2cUjhPGvyuSFUgnRHvMSMMiS8WpZ8Yd8yn70evqKl0"
binance_secret="2HfMkleskGwTb6KQn0AKUQfjBDd5dArBW3Ykd2uTeOiv9VZ6qSU2L1yWM1ZlQ5RH"

def currentprice(client,par):
   leido = False
   while leido == False:
      try:
         current=float(client.get_symbol_ticker(symbol=par)["price"])
         leido = True
      except:
         pass
   return current

def binancetakeprofit(pair,client,side,profitprice):

   created=True
   
   if side=='BUY':
      side='SELL'         
   else:
      side='BUY'

   try:
      profitprice=truncate(profitprice,get_priceprecision(client,pair))
      client.futures_create_order(symbol=pair, side=side, type='TAKE_PROFIT_MARKET', timeInForce='GTC', stopPrice=profitprice,closePosition=True)
      print("Take profit creado. ",profitprice)            
   except BinanceAPIException as a:
      print(a.message,"no se pudo crear el take profit.")
      created=False
      pass

   return created

def binancecrearlimite(exchange,par,client,posicionporc,distanciaporc,lado) -> bool:
   salida= True
   precio=currentprice(client,par)
   
   if lado=='BUY':
      precioprofit=precio-(precio*distanciaporc/100)
      lado='SELL'
   else:
      precioprofit=precio+(precio*distanciaporc/100)
      lado='BUY'

   sizedesocupar=abs(truncate((get_positionamt(exchange,par)*posicionporc/100),get_quantityprecision(client,par)))

   try:
      limitprice=truncate(precioprofit,get_priceprecision(client,par))
      print("Limit. Tamanio a desocupar: ",sizedesocupar,". precio: ",limitprice)
      client.futures_create_order(symbol=par, side=lado, type='LIMIT', timeInForce='GTC', quantity=sizedesocupar,price=limitprice)
      print("Limit creado. Tamanio a desocupar: ",sizedesocupar,". precio: ",limitprice)
      salida= True         
   except BinanceAPIException as a:
      print(a.message,"No se pudo crear el Limit.")
      salida= False      
      pass

   return salida

def binancestoploss (pair,client,side,stopprice)-> int:
   
   retorno=0 # 0: creado, 1: problema
   
   if side == 'BUY':
      side='SELL'
   else:
      side='BUY'

   try:
      preciostop=truncate(stopprice,get_priceprecision(client,pair))
      client.futures_create_order(symbol=pair,side=side,type='STOP_MARKET', timeInForce='GTC', closePosition='True', stopPrice=preciostop)
      print("Stop loss creado. ",preciostop)
   except BinanceAPIException as a:
      print(a.message,"no se pudo crear el stop loss.")
      retorno=1
      pass

   return retorno

def creobot(tipo):
    if tipo=='amigos':
        chatid = "-704084758" #grupo de amigos
    if tipo=='laburo':
        chatid="@gofrecrypto" #canal
    token = "2108740619:AAHcUBakZLdoHYnvUvkBp6oq7SoS63erb2g"
    return TelegramBot(token, chatid)

def get_positionamt(exchange,par) -> float:
   leido=False
   while leido == False:
      try:
         position = exchange.fetch_balance()['info']['positions']
         leido = True
      except:
         pass

   return float([p for p in position if p['symbol'] == par][0]['positionAmt'])

def get_positionnotional(exchange,par) -> float:
   leido=False
   while leido == False:
      try:
         position = exchange.fetch_balance()['info']['positions']
         leido = True
      except:
         pass   
   return float([p for p in position if p['symbol'] == par][0]['notional'])   

def get_quantityprecision(client,par):
   leido=False
   while leido == False:
      try:   
         info = client.futures_exchange_info()
         leido = True
      except:
         pass 

   for x in info['symbols']:
      if x['symbol'] == par:
         return x['quantityPrecision']  

def get_priceprecision(client,par):
   leido=False
   while leido == False:
      try: 
         info = client.futures_exchange_info()
         leido = True
      except:
         pass 
   for x in info['symbols']:
      if x['symbol'] == par:
         return x['pricePrecision']                

def binancecierrotodo(client,par,exchange,lado) -> bool:   
   print("FUNCION CIERROTODO")
   cerrado = False    
   mensaje=''
   
   while cerrado == False:
      try:        
         if posicionesabiertas(exchange) ==True:    
            pos = abs(get_positionamt(exchange,par))
            print(pos)
            client.futures_create_order(symbol=par, side=lado, type='MARKET', quantity=pos, reduceOnly='true')
            cerrado = True
            print("Posición cerrada.")
      except BinanceAPIException as a:
         try:        
            client.futures_create_order(symbol=par, side=lado, type='MARKET', quantity=pos)
            cerrado = True
            print("Posición cerrada sin reduceonly.")
         except BinanceAPIException as a:
            print("Error1 FUNCION CIERROTODO",a.status_code,a.message)   
            botlaburo = creobot('laburo')
            mensaje = "QUEDAN POSICIONES ABIERTAS!!! PRESIONE UNA TECLA LUEGO DE ARREGLARLO..."
            botlaburo.send_text(mensaje)
            input(mensaje)          
      except Exception as falla:
         print("Error2 FUNCION CIERROTODO: "+str(falla))
         pass     

   client.futures_cancel_all_open_orders(symbol=par) 
   print("Órdenes canceladas.") 
   return cerrado

def binancecreoposicion (par,client,size,lado) -> bool:         
   serror=True
            
   try:            
      tamanio=truncate(size,get_quantityprecision(client,par))
      client.futures_create_order(symbol=par, side=lado, type='MARKET', quantity=tamanio)
      print("Posición creada. ",tamanio)
   except BinanceAPIException as a:
      print("Falla al crear la posición.",tamanio, ". Error: ",a.message) 
      serror=False
      pass

   return serror

def binanceexchange(binance_api,binance_secret):
    #permite obtener el pnl y mi capital
    exchange = ccxt.binance({
        'enableRateLimit': True,  
        'apiKey': binance_api,
        'secret': binance_secret,
        'options': {  
            'defaultType': 'future',  
        },
    }) 
    return exchange

def binancehistoricdf(pair,timeframe,limit):
   ## Datos para indicadores
   leido = False
   while leido == False:
      try:
         exchange=ccxt.binance()
         barsindicators = exchange.fetch_ohlcv(pair,timeframe=timeframe,limit=limit)
         df = pd.DataFrame(barsindicators,columns=['time','open','high','low','close','volume'])
         leido = True
      except KeyboardInterrupt:
         print("\nSalida solicitada.")
         sys.exit()  
      except:
         pass
   return df

def timeindex(df):
    # if you encounter a "year is out of range" error the timestamp
    # may be in milliseconds, try `ts /= 1000` in that case
    df['time2']=df['time']/1000
    df['time3']=(pd.to_datetime(df['time2'],unit='s')) 
    df.set_index(pd.DatetimeIndex(df["time3"]), inplace=True)

def sound():
    duration = 1000  # milliseconds
    freq = 440  # Hz

    # for windows
    if name == 'nt':
        _ = system('cls')
    # for mac and linux(here, os.name is 'posix')
    else:
        _ = os.system('play -nq -t alsa synth %s sin %s' % (duration/1000, freq))

def clear():  
    # for windows
    if name == 'nt':
        _ = system('cls')
    # for mac and linux(here, os.name is 'posix')
    else:
        _ = system('clear')

def truncate(number, digits) -> float:
    stepper = 10.0 ** digits
    return math.trunc(stepper * number) / stepper

def posicioncompleta(pair,side,client,stopprice=0,profitprice=0) -> bool:   
   serror = True
   porcentajeentrada=100
   exchange= binanceexchange(binance_api,binance_secret)
   micapital = balancetotal(exchange,client)
   size = (micapital*porcentajeentrada/100)/(currentprice(client,pair))
   stopdefaultporc = 1
   profitdefaultporc = 2
   print("valores recibidos en la función posicioncompleta - stopprice: "+str(stopprice)+" profitprice: "+str(profitprice))

   try:
      if posicionesabiertas(exchange)==False: #si no hay posiciones abiertas creo la alertada.
         if binancecreoposicion (pair,client,size,side)==True:

            precioactual = currentprice(client,pair) 
            
            #valores de stop y profit standard
            if side =='BUY':
               stoppricedefault = precioactual-(precioactual*stopdefaultporc/100)
               profitpricedefault = precioactual+(precioactual*profitdefaultporc/100)
            else:
               stoppricedefault = precioactual+(precioactual*stopdefaultporc/100)
               profitpricedefault = precioactual-(precioactual*profitdefaultporc/100)

            if stopprice == 0:
               profitprice = profitdefaultporc
               if binancestoploss (pair,client,side,stoppricedefault)==0:                  
                  binancetakeprofit(pair,client,side,profitpricedefault)
            else:
               if profitprice == 0:
                  profitprice = profitdefaultporc
                  if binancestoploss (pair,client,side,stopprice)==0:                  
                     binancetakeprofit(pair,client,side,profitpricedefault)
               else:
                  if binancestoploss (pair,client,side,stopprice)==0:                  
                     if binancetakeprofit(pair,client,side,profitprice)==False:
                        binancetakeprofit(pair,client,side,profitpricedefault)

         else:
            print ("No se pudo crear la posición. ")
            serror=False
   except:
      print ("No se pudo crear la posición. Se detectaron posiciones abiertas. ")
      serror=False
      pass    

   return serror        

def will_frac_roll(df: pd.DataFrame, period: int = 2) -> Tuple[pd.Series, pd.Series]:
    """Indicate bearish and bullish fractal patterns using rolling windows.
    :param df: OHLC data
    :param period: number of lower (or higher) points on each side of a high (or low)
    :return: tuple of boolean Series (bearish, bullish) where True marks a fractal pattern
    """

    window = 2 * period + 1 # default 5

    bears = df['high'].rolling(window, center=True).apply(lambda x: x[period] == max(x), raw=True)
    bulls = df['low'].rolling(window, center=True).apply(lambda x: x[period] == min(x), raw=True)

    return bears, bulls

def will_frac(df: pd.DataFrame, period: int = 2) -> Tuple[pd.Series, pd.Series]:
    """Indicate bearish and bullish fractal patterns using shifted Series.
    :param df: OHLC data
    :param period: number of lower (or higher) points on each side of a high (or low)
    :return: tuple of boolean Series (bearish, bullish) where True marks a fractal pattern
    """
    periods = [p for p in range(-period, period + 1) if p != 0] # default [-2, -1, 1, 2]

    highs = [df['high'] > df['high'].shift(p) for p in periods]
    bears = pd.Series(np.logical_and.reduce(highs), index=df.index)

    lows = [df['low'] < df['low'].shift(p) for p in periods]
    bulls = pd.Series(np.logical_and.reduce(lows), index=df.index)

    return bears, bulls      

def closeallopenorders (client,pair):
   leido=False
   while leido==False:
      
      try:
         client.futures_cancel_all_open_orders(symbol=pair)
         print("Órdenes cerradas. ")
         leido=True
      except:
         pass

def komucloud (df):
   high_9 = df.high.rolling(9).max()
   low_9 = df.low.rolling(9).min()
   df['tenkan_sen_line'] = (high_9 + low_9) /2
   # Calculate Kijun-sen
   high_26 = df.high.rolling(26).max()
   low_26 = df.low.rolling(26).min()
   df['kijun_sen_line'] = (high_26 + low_26) / 2
   # Calculate Senkou Span A
   df['senkou_spna_A'] = ((df.tenkan_sen_line + df.kijun_sen_line) / 2).shift(26)
   # Calculate Senkou Span B
   high_52 = df.high.rolling(52).max()
   low_52 = df.high.rolling(52).min()
   df['senkou_spna_B'] = ((high_52 + low_52) / 2).shift(26)
   # Calculate Chikou Span B
   df['chikou_span'] = df.close.shift(-26)
   df['SAR'] = tl.SAR(df.high, df.low, acceleration=0.02, maximum=0.2)
   df['signal'] = 0
   df.loc[(df.close > df.senkou_spna_A) & (df.close > df.senkou_spna_B) & (df.close > df.SAR), 'signal'] = 1
   df.loc[(df.close < df.senkou_spna_A) & (df.close < df.senkou_spna_B) & (df.close < df.SAR), 'signal'] = -1
      
def calculardf (par,temporalidad,ventana):
   df=binancehistoricdf(par,timeframe=temporalidad,limit=ventana) # para fractales.
   timeindex(df) #Formatea el campo time para luego calcular las señales
   df.ta.strategy(ta.CommonStrategy) # Runs and appends all indicators to the current DataFrame by default

   return df


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

def waiting():
   global bar_i   
   print(bar[bar_i % len(bar)], end="\r")      
   bar_i += 1
   
def posicionesabiertas(exchange):
   #devuelve True si hay posiciones abiertas, sino, devuelve False.
   leido = False
   while leido == False:
      try:
         if float(exchange.fetch_balance()['info']['totalPositionInitialMargin'])!=0.0:
             posicionabierta=True
         else:
             posicionabierta=False    
         leido = True
      except:
         pass
   return posicionabierta

def balancetotal(exchange,client):
   leido = False
   while leido == False:
      try:
         balance=float(exchange.fetch_balance()['info']['totalWalletBalance'])+float((exchange.fetch_balance()['BNB']['total'])*float(client.get_symbol_ticker(symbol='BNBUSDT')["price"]))
         leido = True
      except:
         pass
   return balance

