import sys
import pandas as pd
import constantes as cons
import os
import winsound as ws
import math
from binance.exceptions import BinanceAPIException
import ccxt as ccxt
import pandas_ta as ta
import talib
from binance.enums import HistoricalKlinesType
#from numerize import numerize
import requests
import ccxt

salida_solicitada_flag = False

def truncate(number, digits) -> float:
    stepper = 10.0 ** digits
    return math.trunc(stepper * number) / stepper

def currentprice(symbol):
    leido = False
    current=0.0
    while leido == False:
        try:
            current=float(cons.exchange.fetch_ticker(symbol)['close'])
            leido = True
        except:
            pass
    return current

def balancetotal():
   leido = False
   while leido == False:
      try:
        balance=float(cons.exchange.fetch_balance()['info']['totalWalletBalance'])
        leido = True
      except:
         pass
   return balance

def get_quantityprecision(par):
    leido=False
    quantityprecision=0
    while leido == False:
        try:   
            info = cons.client.futures_exchange_info()
            leido = True
        except:
            pass 
    for x in info['symbols']:
        if x['symbol'] == par:
            quantityprecision= x['quantityPrecision']
            break
    return quantityprecision

def getentryprice(par):
    leido = False
    entryprice=0.0
    while leido == False:
        try:
            positions=cons.exchange.fetch_balance()['info']['positions']
            for index in range(len(positions)):
                if positions[index]['symbol']==par:
                    entryprice=float(positions[index]['entryPrice'])
                    break
            leido = True
        except:
            pass
    return entryprice

def printandlog(nombrelog,mensaje,pal=0,mode='a'):
   if pal==0: #print y log
      print(mensaje)
      #escribo file
      f = open(os.path.join(cons.pathroot,nombrelog), mode,encoding="utf-8")
      f.write("\n"+mensaje)
      f.close()   
   else:
      if pal==1: #solo log
         #escribo file
         f = open(os.path.join(cons.pathroot,nombrelog), mode,encoding="utf-8")
         f.write("\n"+mensaje)
         f.close()   

def creoposicion (par,size,lado)->bool:         
    serror=True        
    try:
        apalancamiento=10
        cons.client.futures_change_leverage(symbol=par, leverage=apalancamiento)
        try: 
            cons.client.futures_change_margin_type(symbol=par, marginType=cons.margen)
        except BinanceAPIException as a:
            if a.message!="No need to change margin type.":
                print("Except 7",a.status_code,a.message)
            pass                    
        tamanio=truncate((size/currentprice(par)),get_quantityprecision(par))
        cons.client.futures_create_order(symbol=par,side=lado,type='MARKET',quantity=tamanio)        
        print("Posición creada. ",tamanio)
    except BinanceAPIException as a:
        print("Falla al crear la posición. Error: ",a.message) 
        serror=False
        pass
    except Exception as falla:
        _, _, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - par: "+par+"\n")
        serror=False
        pass
    return serror

def crea_posicion(symbol,side,porcentajeentrada):   
    micapital = balancetotal()
    size = float(micapital*porcentajeentrada/100)
    try:
        apalancamiento=10
        cons.client.futures_change_leverage(symbol=symbol, leverage=apalancamiento)
        try: 
            cons.client.futures_change_margin_type(symbol=symbol, marginType=cons.margen)
        except BinanceAPIException as a:
            if a.message!="No need to change margin type.":
                print("Except 7",a.status_code,a.message)
            pass                    
        tamanio=truncate((size/currentprice(symbol)),get_quantityprecision(symbol))
        cons.client.futures_create_order(symbol=symbol,side=side,type='MARKET',quantity=tamanio)        
        print("Posición creada. ",tamanio)
    except BinanceAPIException as a:
        print("Falla al crear la posición. Error: ",a.message) 
        pass
    except Exception as falla:
        _, _, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - par: "+symbol+"\n")
        pass

def lista_de_monedas ():
    lista_de_monedas = []
    mazmorra = cons.mazmorra
    try:
            exchange_info = cons.client.futures_exchange_info()['symbols'] #obtiene lista de monedas        
            for s in exchange_info:
                try:
                    if (    s['quoteAsset'] =='USDT' 
                        and s['status'] =='TRADING'
                        and s['contractType'] == 'PERPETUAL'
                        and s['symbol'] not in mazmorra):
                        lista_de_monedas.append(s['symbol'])
                except Exception as ex:
                    pass    
    except:
        print("\nError al obtener la lista de monedas...\n")
        pass
    return lista_de_monedas 

def volumeOf24h(par): #en usdt
    vol=0.0
    vol= cons.client.futures_ticker(symbol=par)['quoteVolume']
    return float(vol)

def get_bollinger_bands(df,mult = 2.0,length = 20):
    # calcular indicadores
    close = df['Close']
    basis = talib.SMA(close, length)
    dev = mult * talib.STDDEV(close, length)
    df['upper'] = basis + dev
    df['lower'] = basis - dev
    # imprimir resultados
    return df

def vwap(df):
    v = df['Volume'].values
    tp = (df['Low'] + df['Close'] + df['High']).div(3).values
    return (tp * v).cumsum() / v.cumsum()

def salida_solicitada():    
    global salida_solicitada_flag
    salida_solicitada_flag = True

def obtiene_historial(symbol,timeframe,limit=1000):
    client = cons.client    
    leido = False
    while leido == False:
        try:
            historical_data = client.get_historical_klines(symbol, timeframe,limit=limit,klines_type=HistoricalKlinesType.FUTURES)
            leido = True
            data = pd.DataFrame(historical_data)
            data.columns = ['Open Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close Time', 'Quote Asset Volume', 
                                'Number of Trades', 'TB Base Volume', 'TB Quote Volume', 'Ignore']
            data['Open Time'] = pd.to_datetime(data['Open Time']/1000, unit='s')
            data['Close Time'] = pd.to_datetime(data['Close Time']/1000, unit='s')
            numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Quote Asset Volume', 'TB Base Volume', 'TB Quote Volume']
            data[numeric_columns] = data[numeric_columns].apply(pd.to_numeric, axis=1)
            data['timestamp']=data['Open Time']
            data.set_index('timestamp', inplace=True)
            data.dropna(inplace=True)
            data.drop(['Close Time','Quote Asset Volume', 'TB Base Volume', 'TB Quote Volume','Number of Trades',
                    'Ignore'], axis=1, inplace=True)    
            data['ema20'] = ta.ema(data.Close, length=20)
            data['ema50'] = ta.ema(data.Close, length=50)
            data['ema200'] = ta.ema(data.Close, length=200)
            data['atr'] = ta.atr(data.High, data.Low, data.Close)        
        except KeyboardInterrupt:        
            salida_solicitada()
        except BinanceAPIException as e:
            if e.message=="Invalid symbol.":                
                leido = True
            else:
                print("\nError binance - Par:",symbol,"-",e.status_code,e.message)          
            pass        
        except Exception as falla:
            _, _, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            #print(f"Error leyendo historial {symbol}. Intento otra vez. Falla {falla} \n")
            pass  
    return data

def EMA(data,length):
    return data.ta.ema(length)

def get_posiciones_abiertas(): 
    leido = False
    dict_posiciones = {}
    while leido == False:
        try:
            position = cons.exchange.fetch_balance()['info']['positions']
            for i in range(len(position)):
                if float(position[i]['positionAmt'])!=0.0:
                    side = "BUY" if float(position[i]['positionAmt']) > 0 else "SELL"
                    dict_posiciones[position[i]['symbol']]=side
            leido = True
        except:
            pass
    return dict_posiciones

def get_positionamt(par): #monto en moneda local y con signo (no en usdt)
    leido = False
    positionamt = 0.0
    while leido == False:
        try:
            position = cons.exchange.fetch_balance()['info']['positions']
            for i in range(len(position)):
                if position[i]['symbol']==par:
                    positionamt=float(position[i]['positionAmt'])
                    break
            leido = True
        except:
            pass
    return positionamt

def sound(duration = 200, freq = 800):
    # milliseconds
    # Hz
    # for windows
    if os.name == 'nt':
        ws.Beep(freq, duration)
    # for mac and linux(here, os.name is 'posix')
    else:
        _ = os.system('play -nq -t alsa synth %s sin %s' % (duration/1000, freq))

def get_priceprecision(par):
    leido=False
    priceprecision=0
    while leido == False:
        try: 
            info = cons.client.futures_exchange_info()
            leido = True
        except:
            pass 
    for x in info['symbols']:
        if x['symbol'] == par:
            priceprecision= x['pricePrecision']  
            break         
    return priceprecision

def crea_stoploss (symbol,side,stopprice,amount=0):   
    creado = False
    stopid = 0
    if side.upper() == 'BUY':
        side='SELL'
    else:
        if side.upper() =='SELL':
            side='BUY'
    try:        
        preciostop=truncate(stopprice,get_priceprecision(symbol))
        order=cons.client.futures_create_order(symbol=symbol,side=side,type='STOP_MARKET', timeInForce='GTC', closePosition='True', stopPrice=preciostop)
        print("\nStop loss creado. ",preciostop)
        creado = True
        stopid = order['orderId']        
    except BinanceAPIException as a:
        print(a.message,"no se pudo crear el stop loss.")
        pass
    return creado,stopid    

def closeallopenorders (par):
    leido=False
    while leido==False:      
        try:
            cons.client.futures_cancel_all_open_orders(symbol=par)
            leido=True
            print("\nÓrdenes binance cerradas. ")
        except:
            pass         

def get_tick_size(symbol) -> float:
    tick_size = 0.0
    try:
            info = cons.client.futures_exchange_info()
            for symbol_info in info['symbols']:
                if symbol_info['symbol'] == symbol:
                    for symbol_filter in symbol_info['filters']:
                        if symbol_filter['filterType'] == 'PRICE_FILTER':
                            tick_size = float(symbol_filter['tickSize'])  
                            break
                    break
    except Exception as falla:
        _, _, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - par: "+symbol+"\n")
        pass  
    return tick_size

def obtienecantidaddecimales(numero):
    try :
        int(numero.rstrip('0').rstrip('.'))
        return 0
    except: 
        return len(str(float(numero)).split('.')[-1])

def RoundToTickUp(par,numero):
    resolucion= get_tick_size(par)
    cantidaddecimales=obtienecantidaddecimales(resolucion)
    convertido=truncate((math.floor(numero / resolucion) * resolucion),cantidaddecimales)
    return float(convertido)

def crea_takeprofit(par,preciolimit,posicionporc,lado):
    try:
        ### exchange details        
        sizedesocupar=abs(truncate((get_positionamt(par)*posicionporc/100),get_quantityprecision(par)))
        ####################
        apalancamiento=10
        creado = True 
        orderid = 0  
        if lado=='BUY':
            lado='SELL'
        else:
            lado='BUY'        
        limitprice=RoundToTickUp(par,preciolimit)
        params={"leverage": apalancamiento}
        order=cons.exchange.create_order (par, 'limit', lado, sizedesocupar, limitprice, params)
        orderid = order['id']
        print("\nTAKE PROFIT creado. Tamanio a desocupar: ",sizedesocupar,". precio: ",limitprice)
    except BinanceAPIException as a:
        print(a.message,"No se pudo crear el Limit.")
        creado = False      
        orderid = 0
        pass
    except Exception as falla:
        _, _, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - par: "+par+"\n")
        creado = False
        orderid = 0
        pass    
    return creado,orderid

def obtiene_capitalizacion(symbol):
    market_cap = 0
    url = f'https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}'    
    try:
        response = requests.get(url)
        data = response.json()
        market_cap = float(data['quoteVolume'])
    except Exception as falla:
        _, _, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        #print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - par: "+symbol+"\n")
        pass  
    return market_cap

def filtradodemonedas ():    # Retorna las monedas con mejor volumen para evitar manipulacion.
    lista = lista_de_monedas ()
    lista_filtrada = []
    for symbol in lista:
        try:  
            mensaje = f"Filtrando monedas... {symbol}                                                  "
            sys.stdout.write("\r"+mensaje)
            sys.stdout.flush()              
            vol= volumeOf24h(symbol)
            cap = obtiene_capitalizacion(symbol)
            if vol >= cons.minvolumen24h and cap >= cons.mincapitalizacion:
                lista_filtrada.append(symbol)
        except Exception as falla:
            _, _, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - par: "+symbol+"\n")
            pass     
        except KeyboardInterrupt as ky:
            print("\nSalida solicitada. ")
            sys.exit()   
    return lista_filtrada

def closeposition(symbol,side):
    if side=='SELL':
        lado='BUY'
    else:
        lado='SELL'
    quantity=abs(get_positionamt(symbol))
    if quantity!=0.0:
        cons.client.futures_create_order(symbol=symbol, side=lado, type='MARKET', quantity=quantity, reduceOnly='true')    

