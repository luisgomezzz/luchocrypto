# Toda la info
# https://github.com/twopirllc/pandas-ta
#

import math
import pandas as pd
import pandas_datareader.data as web
import time
import yfinance as yahoo_finance
yahoo_finance.pdr_override()
from mplfinance.original_flavor import candlestick2_ohlc
from argparse import ArgumentParser
import matplotlib.pyplot as plt
import ccxt
from os import system, name
import os
from binance.exceptions import BinanceAPIException
from bob_telegram_tools.bot import TelegramBot
from typing import Tuple
import numpy as np
import talib as tl
import pandas_ta as ta

binance_api="N7yU75L3CNJg2RW0TcJBAW2cUjhPGvyuSFUgnRHvMSMMiS8WpZ8Yd8yn70evqKl0"
binance_secret="2HfMkleskGwTb6KQn0AKUQfjBDd5dArBW3Ykd2uTeOiv9VZ6qSU2L1yWM1ZlQ5RH"

def binancetakeprofit(pair,client,side,porc):
   created=True
   valor_actual=float(client.get_symbol_ticker(symbol=pair)["price"])
   print("Creo el TAKE_PROFIT_MARKET...")
   if side=='BUY':
      precioprofit=valor_actual+(valor_actual*porc/100)
      side='SELL'         
   else:
      precioprofit=valor_actual-(valor_actual*porc/100)
      side='BUY'
   try:
      client.futures_create_order(symbol=pair, side=side, type='TAKE_PROFIT_MARKET', timeInForce='GTC', stopPrice=precioprofit,closePosition=True)
      print("Take profit creado1. \033[K")            
   except BinanceAPIException as a:
      try:
         print(a.message)
         client.futures_create_order(symbol=pair, side=side, type='TAKE_PROFIT_MARKET', timeInForce='GTC', stopPrice=round(precioprofit,4),closePosition=True)
         print("Take profit creado2. \033[K")               
      except BinanceAPIException as a:
         try:
            print(a.message)
            client.futures_create_order(symbol=pair, side=side, type='TAKE_PROFIT_MARKET', timeInForce='GTC', stopPrice=round(precioprofit,3),closePosition=True)
            print("Take profit creado3. \033[K")
         except BinanceAPIException as a:
            try:
               print(a.message)
               client.futures_create_order(symbol=pair, side=side, type='TAKE_PROFIT_MARKET', timeInForce='GTC', stopPrice=round(precioprofit,2),closePosition=True)
               print("Take profit creado3. \033[K")
            except BinanceAPIException as a:
               try:
                  print(a.message)
                  client.futures_create_order(symbol=pair, side=side, type='TAKE_PROFIT_MARKET', timeInForce='GTC', stopPrice=round(precioprofit,1),closePosition=True)
                  print("Take profit creado3. \033[K")
               except BinanceAPIException as a:
                  try:
                     print(a.message)
                     client.futures_create_order(symbol=pair, side=side, type='TAKE_PROFIT_MARKET', timeInForce='GTC', stopPrice=math.trunc(precioprofit),closePosition=True)
                     print("Take profit creado3. \033[K")
                  except BinanceAPIException as a:
                     print(a.message,"no se pudo crear el take profit.")
                     created=False
                     pass
   return created

def binancecrearlimite(exchange,par,client,posicionporc,distanciaproc,lado,tamanio) -> bool:
   print("Creo el limit ...")
   precio=float(client.get_symbol_ticker(symbol=par)["price"])
   
   if lado=='BUY':
      precioprofit=precio-(precio*distanciaproc/100)
      lado='SELL'
   else:
      precioprofit=precio+(precio*distanciaproc/100)
      lado='BUY'

   if tamanio=='':
      sizedesocupar=abs(math.trunc(binancetamanioposicion(exchange,par)*posicionporc/100))
   else: 
      sizedesocupar=math.trunc(tamanio) # esto se hace porque el tamanio puede ir variando y la idea es que se tome una porcion del valor original.

   print("Limit a:", sizedesocupar)

   try:
      client.futures_create_order(symbol=par, side=lado, type='LIMIT', timeInForce='GTC', quantity=sizedesocupar,price=truncate(precioprofit,4))
      print("Limit creado1. \033[K")   
      return True         
   except BinanceAPIException as a:
      try:
         print(a.message)
         client.futures_create_order(symbol=par, side=lado, type='LIMIT', timeInForce='GTC', quantity=sizedesocupar,price=truncate(precioprofit,3))
         print("Limit creado2. \033[K")       
         return True        
      except BinanceAPIException as a:
         try:
            print(a.message)
            client.futures_create_order(symbol=par, side=lado, type='LIMIT', timeInForce='GTC', quantity=sizedesocupar,price=truncate(precioprofit,2))
            print("Limit creado3. \033[K")
            return True
         except BinanceAPIException as a:
            try:
               print(a.message)
               client.futures_create_order(symbol=par, side=lado, type='LIMIT', timeInForce='GTC', quantity=sizedesocupar,price=truncate(precioprofit,1))
               print("Limit creado4. \033[K")
               return True
            except BinanceAPIException as a:
               try:
                  print(a.message)
                  client.futures_create_order(symbol=par, side=lado, type='LIMIT', timeInForce='GTC', quantity=sizedesocupar,price=math.trunc(precioprofit))
                  print("Limit creado5. \033[K")
                  return True
               except BinanceAPIException as a:
                  print(a.message,"no se pudo crear el Limit.")
                  return False

def binancestoploss (pair,client,side,stopprice)-> int:
         i=5 # decimales
         retorno=0 # 0: creado, 1: Order would immediately trigger, 2: Reach max stop order limit, 3: otros
         print("Stop loss")
         if side == 'BUY':
            side='SELL'
         else:
            side='BUY'

         while i>=0:
            try:
               if i!=0:       
                  stopprice = truncate(stopprice,i)
                  print("Intento con:",stopprice)
                  client.futures_create_order(symbol=pair,side=side,type='STOP_MARKET', timeInForce='GTC', closePosition='True', stopPrice=stopprice)
                  print("Stop loss creado correctamente. Precio:",stopprice)
                  i=-1
               else:
                  stopprice = math.trunc(stopprice)
                  print("Intento con:",stopprice)
                  client.futures_create_order(symbol=pair,side=side,type='STOP_MARKET', timeInForce='GTC', closePosition='True', stopPrice=stopprice)
                  print("Stop loss creado. Precio:",stopprice)
                  i=-1           
            except BinanceAPIException as a:  
               if a.message == "Order would immediately trigger.":                 
                  print("Se dispararía de inmediato.")
                  i=-1 #salgo del bucle
                  retorno = 1
               else:   
                  if a.message == "Reach max stop order limit.":
                     print("Número máximo de stop loss alcanzado.")
                     i=-1 #salgo del bucle
                     retorno = 2
                  else:
                     if i==-1: #otros errors.               
                        print("Except stoploss1")
                        print (a.status_code,a.message,stopprice)
                        retorno = 3
                     else: #aca entra si la presición no era la correcta y seguir sacando decimales.
                        i=i-1
               pass   
         return retorno

def creobot(tipo):
    if tipo=='amigos':
        chatid = "-704084758" #grupo de amigos
    if tipo=='laburo':
        chatid="@gofrecrypto" #canal
    token = "2108740619:AAHcUBakZLdoHYnvUvkBp6oq7SoS63erb2g"
    return TelegramBot(token, chatid)

def binancecierrotodo(client,par,exchange,lado) -> bool:
   
   print("FUNCION CIERROTODO")
   cerrado = False    
   mensaje=''
   
   try:      
      position = exchange.fetch_balance()['info']['positions']
      pos = abs(round(float([p for p in position if p['symbol'] == par][0]['notional']),1))
      print(pos)        
      print("Intento 0")
      client.futures_create_order(symbol=par, side=lado, type='MARKET', quantity=100000, reduceOnly='true')
   except BinanceAPIException as a:
      try:
         print(a.message)
         print("Intento 1")
         client.futures_create_order(symbol=par, side=lado, type='MARKET', quantity=100000, reduceOnly='true')               
         cerrado = True
      except BinanceAPIException as a:
         try:
            print(a.message)
            print("Intento 2")
            client.futures_create_order(symbol=par, side=lado, type='MARKET', quantity=10000, reduceOnly='true')               
            cerrado = True  
         except BinanceAPIException as a:
            try:
               print(a.message)
               print("Intento 3")
               client.futures_create_order(symbol=par, side=lado, type='MARKET', quantity=10000)               
               cerrado = True
            except BinanceAPIException as a:
               try:
                  print(a.message)
                  print("Intento 4")
                  client.futures_create_order(symbol=par, side=lado, type='MARKET', quantity=1000)               
                  cerrado = True  
               except BinanceAPIException as a:
                  try:
                     print(a.message)
                     print("Intento 5")
                     client.futures_create_order(symbol=par, side=lado, type='MARKET', quantity=100,reduceOnly='true')
                     cerrado = True         
                  except BinanceAPIException as a:
                     try:
                        print(a.message)
                        print("Intento 6")
                        client.futures_create_order(symbol=par, side=lado, type='MARKET', quantity=100)
                        cerrado = True  
                     except BinanceAPIException as a:
                        try:
                           print(a.message)
                           print("Intento 7")
                           client.futures_create_order(symbol=par, side=lado, type='MARKET', quantity=50,reduceOnly='true')
                           cerrado = True     
                        except BinanceAPIException as a:
                           try:
                              print(a.message)
                              print("Intento 8")
                              client.futures_create_order(symbol=par, side=lado, type='MARKET', quantity=50)
                              cerrado = True 
                           except BinanceAPIException as a:
                              try:
                                 print(a.message)
                                 print("Intento 9")
                                 client.futures_create_order(symbol=par, side=lado, type='MARKET', quantity=30)
                                 cerrado = True 
                              except BinanceAPIException as a:
                                 print(a.message)
                                 print("Except FUNCION CIERROTODO",a.status_code,a.message)   
                                 botlaburo = creobot('laburo')
                                 mensaje = "QUEDAN POSICIONES ABIERTAS!!! PRESIONE UNA TECLA LUEGO DE ARREGLARLO..."
                                 botlaburo.send_text(mensaje)
                                 input(mensaje)            

   client.futures_cancel_all_open_orders(symbol=par) 
   print("Órdenes canceladas.") 
   return cerrado

def binancecreoposicion (par,client,size,lado) -> bool:
         serror=True
         i=4 #decimales
         print("Creando posición...")
         while i>=0:
            try:  
               if i==0:
                  print("Intento con:",math.trunc(size))
                  client.futures_create_order(symbol=par, side=lado, type='MARKET', quantity=str(math.trunc(size))) #cambio str
                  i=-2
               else:
                  size = truncate(size,i) #cambio 
                  print("Intento con:",size)
                  client.futures_create_order(symbol=par, side=lado, type='MARKET', quantity=str(size))   
                  i=-2
            except BinanceAPIException as a:
               print ("Except 6",a.status_code,a.message)
               i=i-1
               pass
 
         if i==-2:
            print("Posición creada correctamente.")
         else:
            print("Falla al crear la posición.",size) 
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

def binancetamanioposicion(exchange,par) -> float:
   position = exchange.fetch_balance()['info']['positions']
   return float([p for p in position if p['symbol'] == par][0]['notional'])

def binancehistoricdf(pair,timeframe,limit):
    ## Datos para indicadores
    exchange=ccxt.binance()
    barsindicators = exchange.fetch_ohlcv(pair,timeframe=timeframe,limit=limit)
    df = pd.DataFrame(barsindicators,columns=['time','open','high','low','close','volume'])
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

def posicionfuerte(pair,side,client,stopprice=0,porcprofit=0) -> bool:
   
   serror = True
   apalancamiento=10
   margen = 'CROSSED'
   porcentajeentrada=100
   exchange=binanceexchange(binance_api,binance_secret)
   micapital = float(exchange.fetch_balance()['info']['totalWalletBalance'])
   size = (micapital*porcentajeentrada/100)/(float(client.get_symbol_ticker(symbol=pair)["price"]))

   if apalancamiento>80:
      client.futures_change_leverage(symbol=pair, leverage=apalancamiento)

   '''
   try: 
       print("\rDefiniendo Cross/Isolated...")
       client.futures_change_margin_type(symbol=pair, marginType=margen)
   except BinanceAPIException as a:
       if a.message!="No need to change margin type.":
           print("Except 7",a.status_code,a.message)
       else:
           print("Done!")   
       pass  
   '''

   try:
      if float(exchange.fetch_balance()['info']['totalPositionInitialMargin'])==0.0: #si no hay posiciones abiertas creo la alertada.
         if binancecreoposicion (pair,client,size,side)==True:

            currentprice = float(client.get_symbol_ticker(symbol=pair)["price"]) 

            #valores de stop y profit standard
            if stopprice == 0:
               if side =='BUY':
                  stoppricedefault = currentprice-(currentprice*1/100)
                  stopprice = stoppricedefault
               else:
                  stoppricedefault = currentprice+(currentprice*1/100)
                  stopprice = stoppricedefault

            if porcprofit == 0:
               porcprofit = 3

            if binancestoploss (pair,client,side,stopprice)==1:
               binancestoploss (pair,client,side,stoppricedefault)

            binancetakeprofit(pair,client,side,porcprofit)
         else:
            serror=False
   except:
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
   while client.futures_get_open_orders(symbol=pair) !=[]:
      print("Cerrado órdenes abiertas...")
      try:
         client.futures_cancel_all_open_orders(symbol=pair)
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