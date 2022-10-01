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
import winsound as ws
from datetime import timedelta
from datetime import datetime
from numerize import numerize

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

def currentprice(par):
   leido = False
   while leido == False:
      try:
         current=float(client.get_symbol_ticker(symbol=par)["price"])
         leido = True
      except:
         pass
   return current

def binancetakeprofit(pair,side,profitprice):
   created=True
   if side=='BUY':
      side='SELL'         
   else:
      side='BUY'

   try:
      profitprice=truncate(profitprice,get_priceprecision(pair))
      client.futures_create_order(symbol=pair, side=side, type='TAKE_PROFIT_MARKET', timeInForce='GTC', stopPrice=profitprice,closePosition=True)
      print("Take profit creado. ",profitprice)            
   except BinanceAPIException as a:
      print(a.message,"no se pudo crear el take profit.")
      created=False
      pass

   return created

def binancecrearlimite(par,preciolimit,posicionporc,lado):
   creado = True 
   order = 0  

   if lado=='BUY':
      lado='SELL'
   else:
      lado='BUY'

   sizedesocupar=abs(truncate((get_positionamt(par)*posicionporc/100),get_quantityprecision(par)))

   preciolimit = get_rounded_price(par, preciolimit)  

   try:
      limitprice=truncate(preciolimit,get_priceprecision(par))
      order=client.futures_create_order(symbol=par, side=lado, type='LIMIT', timeInForce='GTC', quantity=sizedesocupar,price=limitprice)
      print("Limit creado. Tamanio a desocupar: ",sizedesocupar,". precio: ",limitprice)
      creado= True
   except BinanceAPIException as a:
      print(a.message,"No se pudo crear el Limit.")
      creado = False      
      order = 0
      pass

   return creado,order

def binancestoploss (pair,side,stopprice):   
   creado = False
   stopid = 0
   if side == 'BUY':
      side='SELL'
   else:
      side='BUY'

   try:
      preciostop=truncate(stopprice,get_priceprecision(pair))
      order=client.futures_create_order(symbol=pair,side=side,type='STOP_MARKET', timeInForce='GTC', closePosition='True', stopPrice=preciostop)
      print("Stop loss creado. ",preciostop)
      creado = True
      stopid = order['orderId']
   except BinanceAPIException as a:
      print(a.message,"no se pudo crear el stop loss.")
      pass

   return creado,stopid

def creobot(tipo):
    if tipo=='amigos':
        chatid = "-704084758" #grupo de amigos
    if tipo=='laburo':
        chatid="@gofrecrypto" #canal
    token = "2108740619:AAHcUBakZLdoHYnvUvkBp6oq7SoS63erb2g"
    return TelegramBot(token, chatid)

def get_positionamt(par) -> float:
   leido=False
   while leido == False:
      try:
         position = exchange.fetch_balance()['info']['positions']
         leido = True
      except:
         pass

   return float([p for p in position if p['symbol'] == par][0]['positionAmt'])

def get_positionnotional(par) -> float:
   leido=False
   while leido == False:
      try:
         position = exchange.fetch_balance()['info']['positions']
         leido = True
      except:
         pass   
   return float([p for p in position if p['symbol'] == par][0]['notional'])   

def get_quantityprecision(par):
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

def get_priceprecision(par):
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

def binancecierrotodo(par,lado) -> bool:   
   print("FUNCION CIERROTODO")
   cerrado = False    
   
   while cerrado == False:
      try:        
         if posicionesabiertas() ==True:    
            pos = abs(get_positionamt(par))
            print(pos)
            client.futures_create_order(symbol=par, side=lado, type='MARKET', quantity=pos, reduceOnly='true')
            cerrado = True
            print("Posición cerrada.")
      except BinanceAPIException as a:
         print("Error1 FUNCION CIERROTODO",a.status_code,a.message)   
         pass          
      except Exception as falla:
         print("Error2 FUNCION CIERROTODO: "+str(falla))
         pass     

   client.futures_cancel_all_open_orders(symbol=par) 
   print("Órdenes canceladas.") 
   return cerrado

def binancecreoposicion (par,size,lado) -> bool:         
   serror=True
            
   try:            
      tamanio=truncate(size,get_quantityprecision(par))
      client.futures_create_order(symbol=par, side=lado, type='MARKET', quantity=tamanio)
      print("Posición creada. ",tamanio)
   except BinanceAPIException as a:
      print("Falla al crear la posición.",tamanio, ". Error: ",a.message) 
      serror=False
      pass

   return serror

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

def sound(duration = 2000,freq = 440):
     # milliseconds
     # Hz
   # for windows
   if os.name == 'nt':
      ws.Beep(freq, duration)
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

def posicioncompletasanta(par,lado,porcentajeentrada):   
   serror = True
   micapital = balancetotal()
   size = (micapital*porcentajeentrada/100)/(currentprice(par))
   mensaje=''

   try:      
         if binancecreoposicion (par,size,lado)==True:
            precioactual = getentryprice(par)
            mensaje=mensaje+"\nEntryPrice: "+str(truncate(precioactual,6))
         else:
            mensaje="No se pudo crear la posición. "
            print(mensaje)
            serror=False
   except BinanceAPIException as a:
      print(a.message,"No se pudo crear la posición.")
      serror=False
      pass     
   except Exception as falla:
      exc_type, exc_obj, exc_tb = sys.exc_info()
      fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
      print("\nError3: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - par: "+par)
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

def closeallopenorders (pair):
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

   
def posicionesabiertas():
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

def balancetotal():
   leido = False
   while leido == False:
      try:
         balance=float(exchange.fetch_balance()['info']['totalWalletBalance'])+float((exchange.fetch_balance()['BNB']['total'])*float(client.get_symbol_ticker(symbol='BNBUSDT')["price"]))
         leido = True
      except:
         pass
   return balance

def getentryprice(par):
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
      return plus_di, minus_di, adx_smooth, adx

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

def compensaciones(par,client,lado,tamanio,distanciaporc):
   tamanioformateado = truncate(abs(tamanio),get_quantityprecision(par))
   
   if lado =='SELL':
      preciolimit = getentryprice(par)*(1+(distanciaporc/100))   
   else:
      preciolimit = getentryprice(par)*(1-(distanciaporc/100))
   preciolimit = get_rounded_price(par, preciolimit)  
   limitprice = truncate(preciolimit,get_priceprecision(par))
   
   try:
      order=client.futures_create_order(symbol=par, side=lado, type='LIMIT', timeInForce='GTC', quantity=tamanioformateado,price=limitprice)      
      return True,float(order['price']),float(order['origQty']),order['orderId']
   except BinanceAPIException as a:                                       
      print("Except 8",a.status_code,a.message)
      return False,0,0,0

def binancetrades(par,ventana):
   comienzo = datetime.now() - timedelta(minutes=ventana)
   comienzoms = int(comienzo.timestamp() * 1000)
   finalms = int(datetime.now().timestamp() * 1000)
   leido = False
   while leido == False:
      try:
         trades = client.get_aggregate_trades(symbol=par, startTime=comienzoms,endTime=finalms)      
         leido = True
      except:
         pass
   return trades

def get_positionamtusdt(par):
   precioactualusdt=currentprice(par)
   positionamt=get_positionamt(par)
   tamanioposusdt=positionamt*precioactualusdt
   return tamanioposusdt

def stoppriceinvalidation (par,lado,porcentajestoploss,porcentajeentrada):
   
   totalbalance = balancetotal()
   entryprice = getentryprice(par)
   if entryprice == 0:
      entryprice = currentprice(par)
      
   positionamount = abs(get_positionamtusdt(par))
   if positionamount == 0:
      positionamount = totalbalance*porcentajeentrada/100   

   if lado =='BUY':
      stoppriceporc = (entryprice*(positionamount)
      /
      ((positionamount)-(entryprice*totalbalance*porcentajestoploss/100))
      )
   else:
      stoppriceporc = (entryprice*(positionamount)
      /
      ((positionamount)+(entryprice*totalbalance*porcentajestoploss/100))
      )

   print("stoppriceporc: "+str(stoppriceporc))
   return stoppriceporc

def pnl(par):   
   precioentrada = getentryprice(par)
   if precioentrada !=0.0:
      try:
         tamanio = get_positionamtusdt(par)
         precioactual = currentprice(par)
         pnl = ((precioactual/precioentrada)-1)*tamanio
         #if lado == 'BUY':
         #   if precioactual<precioentrada:
         #      pnl=pnl*-1
         #else:
         #   if precioactual>precioentrada:
         #      pnl=pnl*-1
      except Exception as ex:
         pnl = 0
         pass               
   else:
      pnl = 0   

   return pnl

def preciostop(par,procentajeperdida):
   precioentrada = getentryprice(par)
   if precioentrada !=0.0:
      try:
         tamanio = get_positionamtusdt(par)
         micapital = balancetotal()
         perdida = (micapital*procentajeperdida/100)*-1
         preciostop = ((perdida/tamanio)+1)*precioentrada
      except Exception as ex:
         preciostop = 0
         pass
   else:
      preciostop = 0

   return preciostop

def preciostopsanta(lado,cantidadtotalconataqueusdt,preciodondequedariaposicionalfinal,perdida):  
   if lado == 'SELL':
       cantidadtotalconataqueusdt=cantidadtotalconataqueusdt*-1
   if preciodondequedariaposicionalfinal !=0.0:
      perdida=abs(perdida)*-1
      cantidadtotalconataqueusdt = cantidadtotalconataqueusdt
      try:
         preciostop = ((perdida/cantidadtotalconataqueusdt)+1)*preciodondequedariaposicionalfinal
      except Exception as ex:
         preciostop = 0
         pass
   else:
      preciostop = 0

   return preciostop

def stopvelavela (par,lado,temporalidad):
   porc=0.2 #porcentaje de distancia 
   df=calculardf (par,temporalidad,2)
 
   if df.open.iloc[-2]<df.close.iloc[-2]:
      colorvelaanterior='verde'
   else:
      if df.open.iloc[-2]>df.close.iloc[-2]:
         colorvelaanterior='rojo'
      else:        
         colorvelaanterior='nada'

   if lado=='SELL' and colorvelaanterior=='rojo':
      stopvelavela=df.high.iloc[-2]*(1+porc/100)
   else:
      if lado=='BUY' and colorvelaanterior=='verde':
         stopvelavela=df.low.iloc[-2]*(1-porc/100)
      else:
         stopvelavela=0.0

   return stopvelavela

def capitalizacion(par):
   info = client.get_products()
   lista=info['data']
   df = pd.DataFrame(lista)
   cap=df.c.loc[df['s'] == par]*df.cs.loc[df['s'] == par]
   return float(cap)

##print(numerize.numerize(100000000)) muestra numero en notacion copada

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

def rankingcap (n=30):
   dict = {        
        'nada' : 0.0
   }
   dict.clear()
   lista_de_monedas = client.futures_exchange_info()['symbols'] #obtiene lista de monedas
   mazmorra=['1000SHIBUSDT','1000XECUSDT','BTCUSDT_220624','ETHUSDT_220624','ETHUSDT_220930','BTCUSDT_220930','BTCDOMUSDT','FOOTBALLUSDT'
   ,'ETHUSDT_221230'] #Monedas que no quiero operar (muchas estan aqui porque fallan en algun momento al crear el dataframe)         
   listanombres=[]
   for s in lista_de_monedas:
       try:  
           par = s['symbol']
           if ('USDT' in par and par not in mazmorra):
               dict[par] = capitalizacion(par)
       except Exception as ex:
           pass        
       except KeyboardInterrupt as ky:
           print("\nSalida solicitada. ")
           sys.exit()   

   ranking= (sorted([(v, k) for k, v in dict.items()], reverse=True))      

   for index in range(0, n):
      #print(ranking[index][1])
      listanombres.append(ranking[index][1])

   return listanombres

def maximasvariaciones(dias=90):
   lista=['BTCUSDT', 'ETHUSDT', 'BCHUSDT', 'XRPUSDT', 'EOSUSDT', 'LTCUSDT', 'ETCUSDT', 'LINKUSDT', 'ADAUSDT', 'BNBUSDT', 
   'ATOMUSDT', 'IOTAUSDT', 'NEOUSDT', 'ALGOUSDT', 'DOGEUSDT', 'DOTUSDT', 'CRVUSDT', 'SOLUSDT', 'UNIUSDT', 'AVAXUSDT', 
   'HNTUSDT', 'NEARUSDT', 'FILUSDT', 'RSRUSDT', 'MATICUSDT', 'AXSUSDT', 'CHZUSDT', 'SANDUSDT', 'DYDXUSDT', 'GMTUSDT', 
   'APEUSDT', 'OPUSDT','REEFUSDT','PEOPLEUSDT','ENSUSDT' ]
   dict = {        
        'nada' : 0.0
   }
   dict.clear()
   for par in lista:
      df=calculardf (par,'1d',dias)
      df['condicion']=(df.high>=(df.low*(1+5/100))) | (df.low <=(df.high*(1-5/100)))
      df['variacion']=np.where((df.condicion==True),(((df.high/df.low)-1)*100),np.NaN)
      dict[par] = truncate(df.variacion.max(),2)

   ranking= (sorted([(v, k) for k, v in dict.items()]))      
   for index in range(0, len(ranking)):
      print(ranking[index])