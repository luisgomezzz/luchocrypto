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
from time import sleep
from binance.helpers import round_step_size
from binance.client import Client

binance_api="N7yU75L3CNJg2RW0TcJBAW2cUjhPGvyuSFUgnRHvMSMMiS8WpZ8Yd8yn70evqKl0"
binance_secret="2HfMkleskGwTb6KQn0AKUQfjBDd5dArBW3Ykd2uTeOiv9VZ6qSU2L1yWM1ZlQ5RH"
client = Client(binance_api, binance_secret) 
exchange = ccxt.binance({
         'enableRateLimit': True,  
         'apiKey': binance_api,
         'secret': binance_secret,
         'options': {  
         'defaultType': 'future',  
         },
         }) 

def get_tick_size(symbol: str) -> float:
    info = client.futures_exchange_info()

    for symbol_info in info['symbols']:
        if symbol_info['symbol'] == symbol:
            for symbol_filter in symbol_info['filters']:
                if symbol_filter['filterType'] == 'PRICE_FILTER':
                    return float(symbol_filter['tickSize'])

def get_rounded_price(symbol: str, price: float) -> float:
    return round_step_size(price, get_tick_size(symbol))

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

def binancecrearlimite(par,fraccionlimit,profitprice,posicionporc,lado):
   retorno = True   

   precioactual = getentryprice(exchange,par)
   
   if lado=='BUY':
      preciolimit = precioactual+fraccionlimit*(profitprice-precioactual)
      lado='SELL'
   else:
      preciolimit = profitprice + fraccionlimit*(precioactual-profitprice)
      lado='BUY'

   sizedesocupar=abs(truncate((get_positionamt(exchange,par)*posicionporc/100),get_quantityprecision(client,par)))

   preciolimit = get_rounded_price(par, preciolimit)  

   try:
      limitprice=truncate(preciolimit,get_priceprecision(client,par))
      print("Limit. Tamanio a desocupar: ",sizedesocupar,". precio: ",limitprice)
      client.futures_create_order(symbol=par, side=lado, type='LIMIT', timeInForce='GTC', quantity=sizedesocupar,price=limitprice)
      print("Limit creado. Tamanio a desocupar: ",sizedesocupar,". precio: ",limitprice)
      retorno= True         
   except BinanceAPIException as a:
      print(a.message,"No se pudo crear el Limit.")
      retorno= False      
      pass

   return retorno

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

def posicioncompleta(pair,side,client,ratio,stopprice=0):   
   serror = True
   porcentajeentrada=100
   micapital = balancetotal(exchange,client)
   size = (micapital*porcentajeentrada/100)/(currentprice(client,pair))
   stopdefaultporc = 1
   profitdefaultporc = 1   
   mensaje=''

   try:
      if posicionesabiertas(exchange)==False: #si no hay posiciones abiertas creo la alertada.
         if binancecreoposicion (pair,client,size,side)==True:

            precioactual = getentryprice(exchange,pair)

            #valores de stop y profit standard
            if side =='BUY':
               stoppricedefault = precioactual-(precioactual*stopdefaultporc/100)
               profitpricedefault = precioactual+(precioactual*profitdefaultporc/100)
               profitprice = ((precioactual-stopprice)/ratio)+precioactual
            else:
               stoppricedefault = precioactual+(precioactual*stopdefaultporc/100)
               profitpricedefault = precioactual-(precioactual*profitdefaultporc/100)
               profitprice = precioactual-((stopprice-precioactual)/ratio)

            if stopprice == 0:
               if binancestoploss (pair,client,side,stoppricedefault)==0:                  
                  binancetakeprofit(pair,client,side,profitpricedefault)
            else:
               if binancestoploss (pair,client,side,stopprice)==0:                  
                  if binancetakeprofit(pair,client,side,profitprice)==False:
                     binancetakeprofit(pair,client,side,profitpricedefault)
            
            if side =='BUY':
               fraccionlimit=1/4
               posicionporc=70
            else:
               fraccionlimit=3/4
               posicionporc=70

            binancecrearlimite(pair,fraccionlimit,profitprice,posicionporc,side)

            fraccionlimit=1/2
            posicionporc=20

            binancecrearlimite(pair,fraccionlimit,profitprice,posicionporc,side)            

            if stopprice>precioactual:
               mensaje=mensaje+"\nStopprice: "+str(truncate(stopprice,6))
               mensaje=mensaje+"\nEntryPrice: "+str(truncate(precioactual,6))
               mensaje=mensaje+"\nProfitprice: "+str(truncate(profitprice,6))
            else:
               mensaje=mensaje+"\nProfitprice: "+str(truncate(profitprice,6))
               mensaje=mensaje+"\nEntryPrice: "+str(truncate(precioactual,6))
               mensaje=mensaje+"\nStopprice: "+str(truncate(stopprice,6))

         else:
            mensaje="No se pudo crear la posición. "
            print(mensaje)
            serror=False
   except:
      mensaje="No se pudo crear la posición. Se detectaron posiciones abiertas. "
      print(mensaje)
      serror=False
      pass    

   return serror, mensaje       

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
   #df.ta.strategy(ta.CommonStrategy) # Runs and appends all indicators to the current DataFrame by default

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

def waiting(segundossleep=0.0):
   global bar_i   
   print(bar[bar_i % len(bar)], end="\r")      
   bar_i += 1
   if segundossleep>0.0:
      sleep(segundossleep)

   
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

def getentryprice(exchange,par):
   leido = False
   while leido == False:
      try:
         all_positions = exchange.fetch_balance()['info']['positions']
         current_positions = [position for position in all_positions if (position['symbol']) == par]
         leido = True
      except:
         pass
   return float(current_positions[0]['entryPrice'])

def Supertrend(df, atr_period, multiplier):
    
    high = df['high']
    low = df['low']
    close = df['close']
    
    # calculate ATR
    price_diffs = [high - low, 
                   high - close.shift(), 
                   close.shift() - low]
    true_range = pd.concat(price_diffs, axis=1)
    true_range = true_range.abs().max(axis=1)
    # default ATR calculation in supertrend indicator
    atr = true_range.ewm(alpha=1/atr_period,min_periods=atr_period).mean() 
    # df['atr'] = df['tr'].rolling(atr_period).mean()
    
    # HL2 is simply the average of high and low prices
    hl2 = (high + low) / 2
    # upperband and lowerband calculation
    # notice that final bands are set to be equal to the respective bands
    final_upperband = upperband = hl2 + (multiplier * atr)
    final_lowerband = lowerband = hl2 - (multiplier * atr)
    
    # initialize Supertrend column to True
    supertrend = [True] * len(df)
    
    for i in range(1, len(df.index)):
        curr, prev = i, i-1
        
        # if current close price crosses above upperband
        if close[curr] > final_upperband[prev]:
            supertrend[curr] = True
        # if current close price crosses below lowerband
        elif close[curr] < final_lowerband[prev]:
            supertrend[curr] = False
        # else, the trend continues
        else:
            supertrend[curr] = supertrend[prev]
            
            # adjustment to the final bands
            if supertrend[curr] == True and final_lowerband[curr] < final_lowerband[prev]:
                final_lowerband[curr] = final_lowerband[prev]
            if supertrend[curr] == False and final_upperband[curr] > final_upperband[prev]:
                final_upperband[curr] = final_upperband[prev]

        # to remove bands according to the trend direction
        if supertrend[curr] == True:
            final_upperband[curr] = np.nan
        else:
            final_lowerband[curr] = np.nan
    
    return pd.DataFrame({
        'Supertrend': supertrend,
        'Final Lowerband': final_lowerband,
        'Final Upperband': final_upperband
    }, index=df.index)

def get_adx(high, low, close, lookback):
      plus_dm = high.diff()
      minus_dm = low.diff()
      plus_dm[plus_dm < 0] = 0
      minus_dm[minus_dm > 0] = 0
      
      tr1 = pd.DataFrame(high - low)
      tr2 = pd.DataFrame(abs(high - close.shift(1)))
      tr3 = pd.DataFrame(abs(low - close.shift(1)))
      frames = [tr1, tr2, tr3]
      tr = pd.concat(frames, axis = 1, join = 'inner').max(axis = 1)
      atr = tr.rolling(lookback).mean()
      
      plus_di = 100 * (plus_dm.ewm(alpha = 1/lookback).mean() / atr)
      minus_di = abs(100 * (minus_dm.ewm(alpha = 1/lookback).mean() / atr))
      dx = (abs(plus_di - minus_di) / abs(plus_di + minus_di)) * 100
      adx = ((dx.shift(1) * (lookback - 1)) + dx) / lookback
      adx_smooth = adx.ewm(alpha = 1/lookback).mean()
      return plus_di, minus_di, adx_smooth

def implement_adx_strategy(prices, pdi, ndi, adx):
      buy_price = []
      sell_price = []
      adx_signal = []
      signal = 0
      
      for i in range(len(prices)):
         if adx[i-1] < 25 and adx[i] > 25 and pdi[i] > ndi[i]:
               if signal != 1:
                  buy_price.append(prices[i])
                  sell_price.append(np.nan)
                  signal = 1
                  adx_signal.append(signal)
               else:
                  buy_price.append(np.nan)
                  sell_price.append(np.nan)
                  adx_signal.append(0)
         elif adx[i-1] < 25 and adx[i] > 25 and ndi[i] > pdi[i]:
               if signal != -1:
                  buy_price.append(np.nan)
                  sell_price.append(prices[i])
                  signal = -1
                  adx_signal.append(signal)
               else:
                  buy_price.append(np.nan)
                  sell_price.append(np.nan)
                  adx_signal.append(0)
         else:
               buy_price.append(np.nan)
               sell_price.append(np.nan)
               adx_signal.append(0)
               
      return buy_price, sell_price, adx_signal

def adx(df): #me quedo con este ya que devuelve el momento de entrar (adx_signal) aunque se puede con df.ta.adx() y pta.adx(df['high'], df['low'], df['close'])
   df['plus_di'] = pd.DataFrame(get_adx(df['high'], df['low'], df['close'], 14)[0]).rename(columns = {0:'plus_di'})
   df['minus_di'] = pd.DataFrame(get_adx(df['high'], df['low'], df['close'], 14)[1]).rename(columns = {0:'minus_di'})
   df['adx'] = pd.DataFrame(get_adx(df['high'], df['low'], df['close'], 14)[2]).rename(columns = {0:'adx'})
   df = df.dropna()
   df.tail()

   buy_price, sell_price, adx_signal = implement_adx_strategy(df['close'], df['plus_di'], df['minus_di'], df['adx'])

   position = []
   for i in range(len(adx_signal)):
      if adx_signal[i] > 1:
         position.append(0)
      else:
         position.append(1)
         
   for i in range(len(df['close'])):
      if adx_signal[i] == 1:
         position[i] = 1
      elif adx_signal[i] == -1:
         position[i] = 0
      else:
         position[i] = position[i-1]
         
   close_price = df['close']
   plus_di = df['plus_di']
   minus_di = df['minus_di']
   adx = df['adx']
   adx_signal = pd.DataFrame(adx_signal).rename(columns = {0:'adx_signal'}).set_index(df.index)
   position = pd.DataFrame(position).rename(columns = {0:'adx_position'}).set_index(df.index)
   frames = [close_price, plus_di, minus_di, adx, adx_signal, position]
   strategy = pd.concat(frames, join = 'inner', axis = 1)
   
   return strategy

def osovago(df):
   # parameter setup
   length = 20
   mult = 2
   length_KC = 20
   mult_KC = 1.5

   # calculate BB
   m_avg = df['close'].rolling(window=length).mean()
   m_std = df['close'].rolling(window=length).std(ddof=0)
   df['upper_BB'] = m_avg + mult * m_std
   df['lower_BB'] = m_avg - mult * m_std

   # calculate true range
   df['tr0'] = abs(df["high"] - df["low"])
   df['tr1'] = abs(df["high"] - df["close"].shift())
   df['tr2'] = abs(df["low"] - df["close"].shift())
   df['tr'] = df[['tr0', 'tr1', 'tr2']].max(axis=1)

   # calculate KC
   range_ma = df['tr'].rolling(window=length_KC).mean()
   df['upper_KC'] = m_avg + range_ma * mult_KC
   df['lower_KC'] = m_avg - range_ma * mult_KC

   # calculate bar value
   highest = df['high'].rolling(window = length_KC).max()
   lowest = df['low'].rolling(window = length_KC).min()
   m1 = (highest + lowest)/2
   df['value'] = (df['close'] - (m1 + m_avg)/2)
   fit_y = np.array(range(0,length_KC))
   df['value'] = df['value'].rolling(window = length_KC).apply(lambda x: 
                              np.polyfit(fit_y, x, 1)[0] * (length_KC-1) + 
                              np.polyfit(fit_y, x, 1)[1], raw=True)

   # check for 'squeeze'
   df['squeeze_on'] = (df['lower_BB'] > df['lower_KC']) & (df['upper_BB'] < df['upper_KC'])
   df['squeeze_off'] = (df['lower_BB'] < df['lower_KC']) & (df['upper_BB'] > df['upper_KC'])

   df['noSqz'] = ~df['squeeze_on'] & ~df['squeeze_off']   
   

   # buying window for long position:
   # 1. black cross becomes gray (the squeeze is released)
   #df['long_cond1'] = (df.squeeze_off.shift(periods=1) == False) & (df.squeeze_off == True) 
   # 2. bar value is positive => the bar is light green k
   df['long_cond2'] = df.value > 0
   df['long_cond3'] = df.value > df.value.shift(periods=1)

   # buying window for short position:
   # 1. black cross becomes gray (the squeeze is released)
   #df['short_cond1'] = (df.squeeze_off.shift(periods=1) == False) & (df.squeeze_off == True) 
   # 2. bar value is negative => the bar is light red 
   df['short_cond2'] = df.value < 0
   df['short_cond3'] = df.value < df.value.shift(periods=1)
   
   df['enter_long'] = df.long_cond2 & df.long_cond3 #and long_cond1 
   df['enter_short'] = df.short_cond2 & df.short_cond3 #and short_cond1 
   df['gray']= ~df.noSqz & ~df.squeeze_on 
   df['gray']= df['gray'] & (df.gray.shift(periods=1)==False)
   df = df.dropna()
   df.tail()

   #print(df)
   
   enter_long=df['enter_long'].iloc[-1]
   enter_short=df['enter_short'].iloc[-1]
   gray=df['gray'].iloc[-1]
   value=df['value'].iloc[-1]

   return enter_long,enter_short,gray,value