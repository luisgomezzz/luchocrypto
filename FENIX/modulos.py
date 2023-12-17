import sys
import pandas as pd
import constantes as cons
import os
import winsound as ws
import math
from binance.exceptions import BinanceAPIException
import json
import ccxt as ccxt
import numpy as np
import pandas_ta as ta
from backtesting import Backtest
import talib
from backtesting import Strategy
from binance.enums import HistoricalKlinesType
#from numerize import numerize
import requests
import ccxt
import yfinance as yf
import re

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

def set_atr_periods(data, periods: int = 100):
    """
    Set the lookback period for computing ATR. The default value
    of 100 ensures a _stable_ ATR.
    """
    h, l, c_prev = data.High, data.Low, pd.Series(data.Close).shift(1)
    tr = np.max([h - l, (c_prev - h).abs(), (c_prev - l).abs()], axis=0)
    atr = pd.Series(tr).rolling(periods).mean().bfill().values    
    return atr

def get_posiciones_abiertas(): 
    leido = False
    dict_posiciones = {}
    while leido == False:
        try:
            position = cons.exchange.fetch_balance()['info']['positions']
            for i in range(len(position)):
                if float(position[i]['positionAmt'])!=0.0:
                    dict_posiciones[position[i]['symbol']]=position[i]['positionSide']
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

class TrailingStrategy(Strategy):
    def init(self):
        super().init()        
    def next(self):        
        super().next()
        index = len(self.data)-1
        atr = set_atr_periods(self.data)
        for trade in self.trades:
            if trade.is_long:
                trade.sl = max(trade.sl or -np.inf,
                               self.data.Close[index] - atr[index] * self.data.n_atr[index])
            else:
                trade.sl = min(trade.sl or np.inf,
                               self.data.Close[index] + atr[index] * self.data.n_atr[index])
                
def backtesting(data, plot_flag=False):
    balance = 100    
    def ema(data):
        indi=ta.ema(data.Close.s,length=21)
        return indi.to_numpy()
    def sma(data):
        indi=ta.sma(data.Close.s,length=20)
        return indi.to_numpy()    
    class Fenix(TrailingStrategy):
        def init(self):
            super().init()
            self.ema = self.I(ema,self.data)
            self.sma = self.I(sma,self.data)
        def next(self):       
            super().next()
            if self.position:
                if self.data.cierra[-1]==True:
                    self.position.close()                    
            else:   
                if np.isnan(data.take_profit[-1]):
                    tp_value = None
                else:
                    tp_value = self.data.take_profit[-1]
                size= balance*self.data.porcentajeentrada[-1]/100
                if self.data.signal[-1]==1:
                    self.buy(size=size,sl=self.data.stop_loss[-1],tp=tp_value)
                elif self.data.signal[-1]==-1:
                    self.sell(size=size,sl=self.data.stop_loss[-1],tp=tp_value)
    bt = Backtest(data, Fenix, cash=balance)
    output = bt.run()
    if plot_flag:
        bt.plot()
    return output

def leeconfiguracion(parameter='cantidad_posiciones'):
    with open(os.path.join(cons.pathroot, "configuracion.json"), 'r') as openfile: 
        json_object = json.load(openfile)
    valor = json_object[parameter]        
    return valor 

def estrategia_bb(symbol,tp_flag=True):
    timeframe = '15m'
    ventana = 7
    data = obtiene_historial(symbol,timeframe)
    btc_data = obtiene_historial("BTCUSDT",timeframe)
    data['variacion_btc'] = ((btc_data['Close'].rolling(ventana).max()/btc_data['Close'].rolling(ventana).min())-1)*100
    data['n_atr'] = 50 # para el trailing stop. default 50 para que no tenga incidencia.
    data['atr']=ta.atr(data.High, data.Low, data.Close, length=14)
    get_bollinger_bands(data,mult = 1.5,length = 20)
    data['signal'] = np.where(
         (data.ema20.shift(1) > data.ema50.shift(1)) 
        &(data.ema50.shift(1) > data.ema200.shift(1)) 
        &(data.Close.shift(1) < data.lower.shift(1))
        &(data.variacion_btc.shift(1) < 0.8)        
        ,1,
        np.where(
             (data.ema20.shift(1) < data.ema50.shift(1)) 
            &(data.ema50.shift(1) < data.ema200.shift(1))
            &(data.Close.shift(1) > data.upper.shift(1))
            &(data.variacion_btc.shift(1) < 0.8)
            ,-1,
            0
        )
    )    
    data['take_profit'] = np.where(
                                tp_flag,np.where(
                                            data.signal == 1,
                                            data.upper,
                                            np.where(
                                                data.signal == -1,
                                                data.lower,
                                                0
                                                )   
                                            ),np.NaN
                                )
    data['stop_loss'] = np.where(
        data.signal == 1,
        data.Close - 1*data.atr,  
        np.where(
            data.signal == -1,
            data.Close + 1*data.atr,
            0
        )
    )
    data['cierra'] = False
    #if symbol != 'XRPUSDT':
    #    data['signal']=0
    #    data['take_profit']=0
    #    data['stop_loss']=0
    return data

def estrategia_santa(symbol,tp_flag = True):
    # esta estrategia solo se utiliza a modo de prueba y backtesting ya que el programa en realidad es santa3
    porcentajeentrada = 10
    #por defecto está habilitado el tp pero puede sacarse a mano durante el trade si el precio va a favor dejando al trailing stop como profit
    np.seterr(divide='ignore', invalid='ignore')
    timeframe = '1m'
    ventana = 30
    porc_alto = 100
    porc_bajo = 5
    data = obtiene_historial(symbol,timeframe)
    data['maximo'] = data['High'].rolling(ventana).max()
    data['minimo'] = data['Low'].rolling(ventana).min()
    data['n_atr'] = 50 # para el trailing stop. default 50 para que no tenga incidencia. 
    data['signal'] = np.where(
                            (data.Close.shift(1) <= data.minimo.shift(2)) # para que solo sea reentrada
                            &data.martillo.shift(1) == 1
                            &(data.Close.shift(1) <= data.maximo.shift(2)*(1-porc_bajo/100)) # variacion desde
                            &(data.Close.shift(1) >= data.maximo.shift(2)*(1-porc_alto/100)) # variacion hasta
                            ,1,
                            np.where(
                                    (data.Close.shift(1) >= data.maximo.shift(2)) 
                                    &data.martillo.shift(1) == -1
                                    &(data.Close.shift(1) >= data.minimo.shift(2)*(1+porc_bajo/100)) 
                                    &(data.Close.shift(1) <= data.minimo.shift(2)*(1+porc_alto/100)) 
                                    ,-1,
                                    0
                                    )
                            )  
    data['take_profit'] =   np.where(
                            tp_flag,np.where(
                            data.signal == 1,
                            data.Close*1.01,
                            np.where(
                                    data.signal == -1,
                                    data.Close*0.99,  
                                    0
                                    )
                            ),np.NaN
                                    )
    data['stop_loss'] = np.where(
        data.signal == 1,
        data.Close*0.87,    # stop con una varicion de 13% en contra
        np.where(
            data.signal == -1,
            data.Close*1.13,
            0
        )
    )
    data['cierra'] = False
    return data,porcentajeentrada   

def backtestingsanta(data, plot_flag=False, debug = False):
    balance = 1000    
    output = None
    try:
        class Fenix(TrailingStrategy):
            def init(self):
                super().init()
            def next(self):       
                super().next()
                if self.position:                    
                    #print(f"Trades entry_price: {self.trades[0].entry_price} - entry_time: {self.trades[0].entry_time} - pl_pct: {self.trades[0].pl_pct}")
                    if ((self.position.is_long and self.data.Close[-1]<=self.trades[0].entry_price*0.87) or
                        (self.position.is_short and self.data.Close[-1]>=self.trades[0].entry_price*1.13) or
                        self.position.pl_pct>=.01):
                        self.position.close()
                else:   
                    if np.isnan(data.take_profit[-1]):
                        tp_value = None
                    else:
                        tp_value = self.data.take_profit[-1]
                    if self.data.signal[-1]==1:
                        self.buy(size=0.1,sl=self.data.stop_loss[-1],tp=tp_value)
                        current_price = self.data.Close[-1]
                        self.buy(limit=current_price*0.983, size=0.13)
                        self.buy(limit=current_price*0.966289, size=0.169)
                        self.buy(limit=current_price*0.949862087, size=0.2197)
                        self.buy(limit=current_price*0.933714432, size=0.28561)
                        self.buy(limit=current_price*0.917841286, size=0.371293)
                        self.buy(limit=current_price*0.902237984, size=0.4826809)
                        self.buy(limit=current_price*0.886899939, size=0.62748517)
                        self.buy(limit=current_price*0.87182264,  size=4294)      #ataque                  
                    elif self.data.signal[-1]==-1:
                        self.sell(size=0.1,sl=self.data.stop_loss[-1],tp=tp_value)
                        current_price = self.data.Close[-1]
                        self.sell(limit=current_price*1.017, size=0.13)
                        self.sell(limit=current_price*1.034289, size=0.169)
                        self.sell(limit=current_price*1.051871913, size=0.2197)
                        self.sell(limit=current_price*1.069753736, size=0.28561)
                        self.sell(limit=current_price*1.087939549, size=0.371293)
                        self.sell(limit=current_price*1.106434521, size=0.4826809)
                        self.sell(limit=current_price*1.125243908, size=0.62748517)
                        self.sell(limit=current_price*1.144373055, size=4294) # ataque
        bt = Backtest(data, Fenix, cash=balance)
        output = bt.run()
        if plot_flag:
            bt.plot()
    except Exception as falla:
        _, _, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        if debug == True:
            print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+"\n")
    return output

def closeposition(symbol,side):
    if side=='SELL':
        lado='BUY'
    else:
        lado='SELL'
    quantity=abs(get_positionamt(symbol))
    if quantity!=0.0:
        cons.client.futures_create_order(symbol=symbol, side=lado, type='MARKET', quantity=quantity, reduceOnly='true')    

def myfxbook_file_historico():
    # Función que toma datos bajados desde https://www.myfxbook.com/forex-market/currencies/ a un archivo "historico.csv"
    archivo_csv = 'historico.csv'
    column_names = ['Open Time', 'Open', 'High', 'Low', 'Close', 'Change(Pips)', 'Change(%)', 'Nada']
    data = pd.read_csv(archivo_csv, header=None, names=column_names)
    data['Open Time']=pd.to_datetime(data['Open Time'])
    data['timestamp']=data['Open Time']
    data.set_index('timestamp', inplace=True)
    data.drop(['Change(Pips)', 'Change(%)', 'Nada'], axis=1, inplace=True)
    data.sort_values(by='timestamp', ascending = True, inplace = True)
    data['Volume'] = 1
    numeric_columns = ['Open', 'High', 'Low', 'Close','Volume']
    data['ema20'] = ta.ema(data.Close, length=20)
    data['ema50'] = ta.ema(data.Close, length=50)
    data['ema200'] = ta.ema(data.Close, length=200)
    data['atr'] = ta.atr(data.High, data.Low, data.Close)   
    data[numeric_columns] = data[numeric_columns].apply(pd.to_numeric, axis=1)
    return data

def obtiene_historial_yfinance(symbol, timeframe= "1h"):
    try:
        data = yf.download(symbol,period="1mo",interval=timeframe,progress=False)
        data['Open Time'] = pd.to_datetime(data.index)
        data['timestamp']=pd.to_datetime(data.index)
        data.set_index('timestamp', inplace=True)
        data.drop(['Adj Close'], axis=1, inplace=True)
        numeric_columns = ['Open', 'High', 'Low', 'Close','Volume']
        data['ema20'] = ta.ema(data.Close, length=20)
        data['ema50'] = ta.ema(data.Close, length=50)
        data['ema200'] = ta.ema(data.Close, length=200)
        data['atr'] = ta.atr(data.High, data.Low, data.Close)   
        data[numeric_columns] = data[numeric_columns].apply(pd.to_numeric, axis=1)
        data = data.iloc[:-1]
        data = data.tail(1000) #para limitar y no sea enorme
        return data
    except Exception as falla:
        _, _, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - symbol: "+symbol+"\n")
        pass

def backtesting_smart(data, plot_flag=False, symbol='NADA'):
    balance = 100000 # se coloca 100.000 ya que con valores menores no acepta tradear con BTC o ETH
    def indicador(df_campo):
        indi=pd.Series(df_campo)
        return indi.to_numpy()
        
    class Fenix(Strategy):
        def init(self):
            super().init()
            self.decisional_alcista_high_guardado = 0.0
            self.decisional_bajista_low_guardado = 0.0
            self.tp_multiplicador = 18
            ########################################### INDICADORES #####################################################
            #### varios
            #self.posicion = self.I(indicador,self.data.posicion,name="posicion")
            #self.buy_side_liquidity = self.I(indicador,self.data.buy_side_liquidity,name="buy_side_liquidity")
            #self.sell_side_liquidity = self.I(indicador,self.data.sell_side_liquidity,name="sell_side_liquidity")            
            self.cruce_bos_killzone = self.I(indicador,self.data.cruce_bos_killzone,name="cruce_bos_killzone")
            #self.tendencia = self.I(indicador,self.data.tendencia,name="tendencia")
            self.sentido = self.I(indicador,self.data.sentido,name="sentido")
            #####   PIVOTS ok!!!
            #self.pivot_high = self.I(indicador,self.data.pivot_high)
            #self.pivot_low = self.I(indicador,self.data.pivot_low)
            #self.techo_del_minimo = self.I(indicador,self.data.techo_del_minimo)
            #self.piso_del_maximo = self.I(indicador,self.data.piso_del_maximo)
            ######  DECISIONALES
            self.decisional_bajista_high = self.I(indicador,self.data.decisional_bajista_high,name="Decisional_bajista_high", overlay=True, color="rosybrown", scatter=False)
            self.decisional_bajista_low = self.I(indicador,self.data.decisional_bajista_low,name="Decisional_bajista_Low", overlay=True, color="rosybrown", scatter=False)
            self.decisional_alcista_high = self.I(indicador,self.data.decisional_alcista_high,name="Decisional_alcista_high", overlay=True, color="mediumturquoise", scatter=False)
            self.decisional_alcista_low = self.I(indicador,self.data.decisional_alcista_low,name="Decisional_alcista_Low", overlay=True, color="mediumturquoise", scatter=False)
            #####   EXTREMOS ok!!
            #self.bajista_extremo_high = self.I(indicador,self.data.bajista_extremo_high,name="bajista_extremo_high", overlay=True, color="RED", scatter=False)
            #self.bajista_extremo_low = self.I(indicador,self.data.bajista_extremo_low,name="bajista_extremo_low", overlay=True, color="RED", scatter=False)
            #self.alcista_extremo_high = self.I(indicador,self.data.alcista_extremo_high,name="alcista_extremo_high", overlay=True, color="GREEN", scatter=False)
            #self.alcista_extremo_low = self.I(indicador,self.data.alcista_extremo_low,name="alcista_extremo_low", overlay=True, color="GREEN", scatter=False)
            #####   BOSES ok!!!
            #self.bos_bajista = self.I(indicador,self.data.bos_bajista,name="BOS bajista", overlay=True, color="RED", scatter=True)
            #self.bos_alcista = self.I(indicador,self.data.bos_alcista,name="BOS alcista", overlay=True, color="GREEN", scatter=True)
            #####   IMBALANCES ok!!!
            #self.imba_bajista_low = self.I(indicador,self.data.imba_bajista_low,name="imba_bajista_low", overlay=True, color="orange", scatter=True)
            #self.imba_bajista_high = self.I(indicador,self.data.imba_bajista_high,name="imba_bajista_high", overlay=True, color="orange", scatter=True)
            #self.imba_alcista_low = self.I(indicador,self.data.imba_alcista_low,name="imba_alcista_low", overlay=True, color="springgreen", scatter=True)
            #self.imba_alcista_high = self.I(indicador,self.data.imba_alcista_high,name="imba_alcista_high", overlay=True, color="springgreen", scatter=True)
        def next(self):       
            super().next()
            if self.position:
                self.decisional_alcista_high_guardado = 0.0
                self.decisional_bajista_low_guardado = 0.0
            else:   
                # ALCISTA
                if (self.data.Close[-1] > self.data.decisional_alcista_high[-1] 
                    and self.data.trend == 'Alcista'
                    and self.data.decisional_alcista_high[-1] != self.decisional_alcista_high_guardado
                    and self.data.decisional_alcista[-1] != True
                    and self.data.decisional_alcista[-2] != True
                    and self.data.decisional_alcista[-3] != True
                    and self.data.decisional_alcista[-4] != True
                    ):
                        try:
                            # para evaluar sin usar el apalancamiento
                            if self.data.porcentajeentrada_alcista[-1]>=100:
                                size = 0.99
                            else:
                                size = self.data.porcentajeentrada_alcista[-1]/100
                            for order in self.orders:
                                order.cancel()
                            self.buy(limit = self.data.decisional_alcista_high[-1]+self.data.offset[-1],
                                     size = size,
                                     sl = self.data.decisional_alcista_low[-1] - self.data.offset[-1],
                                     tp = self.data.decisional_alcista_high[-1] + self.data.atr[-1]*self.tp_multiplicador
                                     )
                            self.decisional_alcista_high_guardado = self.data.decisional_alcista_high[-1]           
                        except Exception as falla:
                            _, _, exc_tb = sys.exc_info()
                            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                            print("\n*******Error: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+"*****\n")
                            pass
                # BAJISTA
                else:
                    if (self.data.Close[-1] < self.data.decisional_bajista_low[-1] 
                        and self.data.trend == 'Bajista'
                        and self.data.decisional_bajista_low[-1] != self.decisional_bajista_low_guardado
                        and self.data.decisional_bajista[-1] != True
                        and self.data.decisional_bajista[-2] != True
                        and self.data.decisional_bajista[-3] != True
                        and self.data.decisional_bajista[-4] != True
                        ):
                            try:
                                # para evaluar sin usar el apalancamiento
                                if self.data.porcentajeentrada_bajista[-1]>=100:
                                    size = 0.99
                                else:
                                    size = self.data.porcentajeentrada_bajista[-1]/100
                                for order in self.orders:
                                    order.cancel()
                                self.sell(limit = self.data.decisional_bajista_low[-1] ,
                                        size = size
                                        ,sl = self.data.decisional_bajista_high[-1] + self.data.offset[-1]
                                        ,tp = self.data.decisional_bajista_low[-1] - self.data.atr[-1]*self.tp_multiplicador
                                        )
                                self.decisional_bajista_low_guardado = self.data.decisional_bajista_low[-1]           
                            except Exception as falla:
                                _, _, exc_tb = sys.exc_info()
                                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                                print("\n*******Error: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+"*****\n")
                                pass
    try:
        bt = Backtest(data, Fenix, cash=balance)
        output = bt.run()
        if plot_flag:
            bt.plot(filename="graficos/"+symbol)
        return output
    except Exception as falla:
        _, _, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - symbol: "+symbol+"\n")
        pass

####################################################################################

def smart_money(symbol,refinado,fuente,timeframe,largo):
    try:
        # Devuelve un dataframe con timeframe de 15m con BOSes, imbalances y orders blocks.
        #
        # Se debe tener en cuenta los boses son marcados una vez que se genera el rompimiento, esto significa que no se ve la línea de
        # bos hasta que no se produce el quiebre. Ocurre lo mismo con todas las señales que dependan de los boses.
        # Los imbalances no mitigados sí se pueden ver online.
        #  
        # largo es el parámetro de longitud para los puntos pivote High y Low
        #
        # FUENTE
        # 0 Binance
        # 1 File
        # 2 yfinance
        timeframe_refinado = '15m'

        if fuente == 1: 
            # Si la data se toma de un file
            df = myfxbook_file_historico()
            df_imbalance = myfxbook_file_historico()
            refinado = False
        else:
            if fuente == 0:
                # La data se saca de binance
                df = obtiene_historial(symbol, timeframe)
                df_imbalance = obtiene_historial(symbol,timeframe) #historial para imbalances  
            else:
                # La data se saca de yahoo
                if fuente == 2:
                    df = obtiene_historial_yfinance(symbol, timeframe)
                    df_imbalance = obtiene_historial_yfinance(symbol, timeframe)

        if refinado:
            if fuente == 0:
                df_refinar = obtiene_historial(symbol,timeframe_refinado) #historial de temporalidad inferior para refinar
                parametros_refinado = {"start":15,"stop":75,"step":15} # 5m = {"start":5,"stop":20,"step":5} --- 1m = {"start":1,"stop":6,"step":1} --- 15m {"start":15,"stop":75,"step":15}
            else:
                if fuente ==2:
                    df_refinar = obtiene_historial_yfinance(symbol,timeframe_refinado) #historial de temporalidad inferior para refinar
                    parametros_refinado = {"start":15,"stop":75,"step":15} # 5m = {"start":5,"stop":20,"step":5} --- 1m = {"start":1,"stop":6,"step":1} --- 15m {"start":15,"stop":75,"step":15}


        df['pivot_high'] = np.NaN
        df['pivot_low'] = np.NaN
        df['row_number'] = (range(len(df)))
        df.set_index('row_number', inplace=True)

        ##################################################################################### PIVOTS
        for i in range(largo, len(df) - largo):
            ## PIVOTS SUPERIORES
            if (
                df['High'].iloc[i] == df['High'].iloc[i - largo:i + largo + 1].max()
                and df['High'].iloc[i] > df['High'].iloc[i - 1]
                and df['High'].iloc[i] > df['High'].iloc[i + 1]
                ):
                df.at[i, 'pivot_high'] = df['High'].iloc[i]
            ## PIVOTS INFERIORES
            if (
                df['Low'].iloc[i] == df['Low'].iloc[i - largo:i + largo + 1].min()
                and df['Low'].iloc[i] < df['Low'].iloc[i - 1]
                and df['Low'].iloc[i] < df['Low'].iloc[i + 1]
                ):
                df.at[i, 'pivot_low'] = df['Low'].iloc[i]
        ## RELLENO DE PIVOTS
        for i in range(0, len(df)-1):
            if np.isnan(df['pivot_low'].iloc[i]):
                df.at[i, 'pivot_low'] = df['pivot_low'].iloc[i - 1]
            if np.isnan(df['pivot_high'].iloc[i]):
                df.at[i, 'pivot_high'] = df['pivot_high'].iloc[i - 1]   
        
        ###################################################################################### IMBALANCES
        df_imbalance = df_imbalance.copy()
        df_imbalance['row_number'] = range(len(df_imbalance))
        df_imbalance.set_index('row_number', inplace=True)
        df_imbalance['imba_bajista_high'] = np.where(
                                        ((df_imbalance.Low.shift(1)) >= (df_imbalance.High.shift(-1)+df_imbalance.atr))
                                        ,df_imbalance.Low.shift(1),np.NaN)
        df_imbalance['imba_bajista_low'] = np.where(np.isnan(df_imbalance['imba_bajista_high']),np.NaN,df_imbalance.High.shift(-1))
        df_imbalance['imba_alcista_high'] = np.where(
                                        ((df_imbalance.High.shift(1)) <= (df_imbalance.Low.shift(-1)-df_imbalance.atr))
                                        ,df_imbalance.Low.shift(-1),np.NaN)
        df_imbalance['imba_alcista_low'] = np.where(np.isnan(df_imbalance['imba_alcista_high']),np.NaN,df_imbalance.High.shift(1))
        df_imbalance['timestamp']=df_imbalance['Open Time']
        df_imbalance.set_index('timestamp', inplace=True)    
        df_imbalance=df_imbalance[['imba_bajista_high','imba_bajista_low','imba_alcista_high','imba_alcista_low','Open Time']]
        df=pd.merge(df,df_imbalance, on=["Open Time"], how='left')        
            ## RELLENO Y BORRADO DE IMBALANCES MITIGADOS
            # imbalance alcista
        imbalance_creado = False
        imba_alcista_high = np.nan
        imba_alcista_low = np.nan
        for i in range(0, len(df)-1):
            if not np.isnan(df['imba_alcista_high'].iloc[i]): 
                # un imbalance detectado en timeframe de 4h. Guardo los valores
                imba_alcista_high=df['imba_alcista_high'].iloc[i]
                imba_alcista_low=df['imba_alcista_low'].iloc[i]   
                imbalance_creado = False
            if imbalance_creado == False:     
                # no es un imbalance detectado asi que estiro el dibujo
                if df.Close.iloc[i] > imba_alcista_low: ## ya se creó el imbalance detectado. Dibujo
                    df.at[i, 'imba_alcista_high'] = imba_alcista_high
                    df.at[i, 'imba_alcista_low'] = imba_alcista_low
                    imbalance_creado = True
            else:
                if df.Close.iloc[i] > imba_alcista_low: ## ya se completó el imbalance detectado. Dibujo mientras no sea mitigado
                    df.at[i, 'imba_alcista_high'] = imba_alcista_high
                    df.at[i, 'imba_alcista_low'] = imba_alcista_low
                else:
                    # se mitigó el imbalance, no dibujo
                    imba_alcista_high = np.nan
                    imba_alcista_low = np.nan
            # imbalance bajista
        imbalance_creado = False
        imba_bajista_high = np.nan
        imba_bajista_low = np.nan
        for i in range(0, len(df)-1):
            if not np.isnan(df['imba_bajista_high'].iloc[i]): 
                # un imbalance detectado en timeframe de 4h. Guardo los valores
                imba_bajista_high=df['imba_bajista_high'].iloc[i]
                imba_bajista_low=df['imba_bajista_low'].iloc[i]   
                imbalance_creado = False
            if imbalance_creado == False:     
                # no es un imbalance detectado asi que estiro el dibujo
                if df.Close.iloc[i] < imba_bajista_high: ## ya se creó el imbalance detectado. Dibujo
                    df.at[i, 'imba_bajista_high'] = imba_bajista_high
                    df.at[i, 'imba_bajista_low'] = imba_bajista_low
                    imbalance_creado = True
            else:
                if df.Close.iloc[i] < imba_bajista_high: ## ya se completó el imbalance detectado. Dibujo mientras no sea mitigado
                    df.at[i, 'imba_bajista_high'] = imba_bajista_high
                    df.at[i, 'imba_bajista_low'] = imba_bajista_low
                else:
                    # se mitigó el imbalance, no dibujo
                    imba_bajista_high = np.nan
                    imba_bajista_low = np.nan
        ######################################################################################################## BOSES
        ### BOS BAJISTA
        pico_maximo = 0
        piso_del_maximo = 0
        df['piso_del_maximo'] = np.NaN
        for i in range(0, len(df)-1):
            if df['pivot_high'].iloc[i]>pico_maximo:
                pico_maximo = df['pivot_high'].iloc[i]
                piso_del_maximo = df['pivot_low'].iloc[i]
                df.at[i, 'piso_del_maximo'] = piso_del_maximo
            if df['Close'].iloc[i] < piso_del_maximo:
                pico_maximo = 0
                piso_del_maximo = 0                
                ##relleno
        for i in range(0, len(df)-1):
            if np.isnan(df['piso_del_maximo'].iloc[i]):
                df.at[i, 'piso_del_maximo'] = df['piso_del_maximo'].iloc[i - 1]
        df['bos_bajista']=df.piso_del_maximo
        bos=0
        for i in range(len(df)-1, 0,-1):
            if (df['Close'].iloc[i] < df['piso_del_maximo'].iloc[i]):
                bos = df['piso_del_maximo'].iloc[i]
            if df['bos_bajista'].iloc[i]!=bos:
                df.at[i, 'bos_bajista'] = np.NaN
        ### BOS ALCISTA
        pico_minimo = float('inf')
        techo_del_minimo = float('inf')
        df['techo_del_minimo'] = np.NaN
        for i in range(0, len(df)-1):
            if df['pivot_low'].iloc[i]<pico_minimo:
                pico_minimo = df['pivot_low'].iloc[i]
                techo_del_minimo = df['pivot_high'].iloc[i]
                df.at[i, 'techo_del_minimo'] = techo_del_minimo
            if df['Close'].iloc[i] > techo_del_minimo:
                pico_minimo = float('inf')
                techo_del_minimo = float('inf')               
        ## RELLENO
        for i in range(0, len(df)-1):
            if np.isnan(df['techo_del_minimo'].iloc[i]):
                df.at[i, 'techo_del_minimo'] = df['techo_del_minimo'].iloc[i - 1]
        df['bos_alcista']=df.techo_del_minimo
        bos=0
        for i in range(len(df)-1, 0,-1):
            if (df['Close'].iloc[i] > df['techo_del_minimo'].iloc[i]):
                bos = df['techo_del_minimo'].iloc[i]
            if df['bos_alcista'].iloc[i]!=bos:
                df.at[i, 'bos_alcista'] = np.NaN          
        ################################################################################################### EXTREMOS
    
        ##   extremos BAJISTAS
        df['bajista_extremo_high']=np.nan
        df['bajista_extremo_low']=np.nan
        indice_guardado = 0
        pico_maximo = float('-inf')        
        # recorre todo el dataframe principal
        for i in range(0, len(df)-1): 
            #si estamos sobre un bos bajista busco la vela con high mas alto y guardo el indice
            if not np.isnan(df.bos_bajista.iloc[i]): 
                if df.High.iloc[i] > pico_maximo:
                    pico_maximo=df.High.iloc[i]
                    indice_guardado=i                    
            else: # terminó el bos bajista
                if indice_guardado!=0:
                    # Marca el high y low de la vela con mayor high detectado en el dataframe principal para ese BOS
                    df.at[indice_guardado, 'bajista_extremo_high'] =df.High.iloc[indice_guardado]
                    df.at[indice_guardado, 'bajista_extremo_low'] =df.Low.iloc[indice_guardado]                    
                    try:
                        # refinacion los valores anteriormente guardados para 5m en caso de que se pueda
                        fecha_inicio_refinar = df['Open Time'].iloc[indice_guardado]
                        fecha_actual_refinar = fecha_inicio_refinar
                        fecha_del_maximo_refinar = fecha_actual_refinar
                        pico_maximo_refinar = float('-inf')
                        if refinado:
                            # busca el high mas alto en velas verdes
                            for i in range(parametros_refinado['start'], parametros_refinado['stop'], parametros_refinado['step']):
                                if df_refinar.High[fecha_actual_refinar] > pico_maximo_refinar and df_refinar.Close[fecha_actual_refinar] > df_refinar.Open[fecha_actual_refinar]:
                                    pico_maximo_refinar = df_refinar.High[fecha_actual_refinar]
                                    fecha_del_maximo_refinar = fecha_actual_refinar
                                fecha_actual_refinar = fecha_inicio_refinar + pd.DateOffset(minutes=i)
                            df.at[indice_guardado, 'bajista_extremo_high'] =df_refinar.at[fecha_del_maximo_refinar, 'High']
                            df.at[indice_guardado, 'bajista_extremo_low'] =df_refinar.at[fecha_del_maximo_refinar, 'Low']
                    except Exception as falla:
                        _, _, exc_tb = sys.exc_info()
                        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                        #print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - symbol: "+symbol+"\n")
                        pass
                indice_guardado = 0
                pico_maximo = float('-inf')
        #   extremos ALCISTAS
        df['alcista_extremo_high']=np.nan
        df['alcista_extremo_low']=np.nan
        indice_guardado = 0
        pico_minimo = float('inf')
        # recorre todo el dataframe principal
        for i in range(0, len(df)-1): 
            #si estamos sobre un bos alcista busco la vela con low mas bajo y guardo el indice
            if not np.isnan(df.bos_alcista.iloc[i]): 
                if df.Low.iloc[i] < pico_minimo:
                    pico_minimo=df.Low.iloc[i]
                    indice_guardado=i
            else: # terminó el bos bajista
                if indice_guardado!=0:
                    # Marca el high y low de la vela con mayor high detectado en el dataframe de 15 min para ese BOS
                    df.at[indice_guardado, 'alcista_extremo_high'] =df.High.iloc[indice_guardado]
                    df.at[indice_guardado, 'alcista_extremo_low'] =df.Low.iloc[indice_guardado]                    
                    try:
                        # refinacion los valores anteriormente guardados para 5m en caso de que se pueda
                        fecha_inicio_refinar = df['Open Time'].iloc[indice_guardado]
                        fecha_actual_refinar = fecha_inicio_refinar
                        fecha_del_minimo_refinar = fecha_actual_refinar
                        pico_minimo_refinar = float('inf')
                        if refinado:
                            # busca el high mas alto en velas rojas
                            for i in range(parametros_refinado['start'], parametros_refinado['stop'], parametros_refinado['step']):
                                if df_refinar.Low[fecha_actual_refinar] < pico_minimo_refinar and df_refinar.Close[fecha_actual_refinar] < df_refinar.Open[fecha_actual_refinar]:
                                    pico_minimo_refinar = df_refinar.Low[fecha_actual_refinar]
                                    fecha_del_minimo_refinar = fecha_actual_refinar
                                fecha_actual_refinar = fecha_inicio_refinar + pd.DateOffset(minutes=i)
                            df.at[indice_guardado, 'alcista_extremo_high'] =df_refinar.at[fecha_del_minimo_refinar, 'High']
                            df.at[indice_guardado, 'alcista_extremo_low'] =df_refinar.at[fecha_del_minimo_refinar, 'Low']
                    except Exception as falla:
                        _, _, exc_tb = sys.exc_info()
                        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                        #print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - symbol: "+symbol+"\n")
                        pass
                indice_guardado = 0
                pico_minimo = float('inf')
        #relleno
        for i in range(0, len(df)-1):
            if np.isnan(df['bajista_extremo_high'].iloc[i]):
                df.at[i, 'bajista_extremo_high'] = df['bajista_extremo_high'].iloc[i - 1]
                df.at[i, 'bajista_extremo_low'] = df['bajista_extremo_low'].iloc[i - 1]
            if np.isnan(df['alcista_extremo_high'].iloc[i]):
                df.at[i, 'alcista_extremo_high'] = df['alcista_extremo_high'].iloc[i - 1]
                df.at[i, 'alcista_extremo_low'] = df['alcista_extremo_low'].iloc[i - 1]                

        ####################################################################################################### DECISIONALES
        df['color'] = np.where(df.Close > df.Open,'verde','rojo')
        df['tamanio_cuerpo'] = np.where(df.color == 'verde',df.Close-df.Open,df.Open-df.Close)        
        multiplicador_imbalance = 0.75
        ## BAJISTA
        decisional_bajista_condicion =  (
                                        (df.color == 'verde')
                                        & (
                                            ((df.Low) >= (df.High.shift(-2) + df.atr*multiplicador_imbalance))
                                            |
                                            ((df.Low.shift(-1)) >= (df.High.shift(-3) + df.atr*multiplicador_imbalance))
                                            |
                                            ((df.Low.shift(-2)) >= (df.High.shift(-4) + df.atr*multiplicador_imbalance))
                                          )
                                        & (df.tamanio_cuerpo < df.tamanio_cuerpo.shift(-2))
										& (df.High > (df.High.shift(-4) + df.atr*multiplicador_imbalance))
                                        & (df.Close > (df.Close.shift(-20) + df.atr*3)) # que luego del decisional el precio se mantenga lejos un tiempo. 
                                        )
        df['decisional_bajista_low'] = np.where(
                                    decisional_bajista_condicion
                                    ,df.Low,
                                    np.NaN)                                    
        df['decisional_bajista_high'] = np.where(                                
                                    decisional_bajista_condicion
                                    ,df.High,
                                    np.NaN)        
        ###refinado y relleno
        df['decisional_bajista'] = np.where(np.isnan(df.decisional_bajista_low),False,True) # creo un campo para identificar cuando se detecta el decisional 
        high_guardado = np.nan
        low_guardado = np.nan                                          
        for i in range(0, len(df)-1):
            if  ((df['decisional_bajista'].iloc[i]) == False): # no es un decisional asi que copio
                    df.at[i, 'decisional_bajista_high'] = high_guardado
                    df.at[i, 'decisional_bajista_low'] = low_guardado
                    if (df.High.iloc[i] >= high_guardado 
                        and df.decisional_bajista.iloc[i-1] != True
                        and df.decisional_bajista.iloc[i-2] != True
                        and df.decisional_bajista.iloc[i-3] != True
                        ): # borro decisional si fue mitigado
                        high_guardado = np.nan
                        low_guardado = np.nan
            else:
                high_guardado = df['decisional_bajista_high'].iloc[i]
                low_guardado = df['decisional_bajista_low'].iloc[i]
                indice_guardado = i
                try:
                        # refinacion los valores anteriormente guardados para la temporalidad de refinacion seleccionada en caso de que se pueda
                        fecha_inicio_refinar = df['Open Time'].iloc[indice_guardado]
                        fecha_actual_refinar = fecha_inicio_refinar
                        fecha_del_maximo_refinar = fecha_actual_refinar
                        pico_maximo_refinar = 0
                        if refinado:
                            # busca el high mas alto en velas verdes
                            for i in range(parametros_refinado['start'], parametros_refinado['stop'], parametros_refinado['step']):
                                if df_refinar.High[fecha_actual_refinar] > pico_maximo_refinar and df_refinar.Close[fecha_actual_refinar] > df_refinar.Open[fecha_actual_refinar]:
                                    pico_maximo_refinar = df_refinar.High[fecha_actual_refinar]
                                    fecha_del_maximo_refinar = fecha_actual_refinar
                                fecha_actual_refinar = fecha_inicio_refinar + pd.DateOffset(minutes=i)
                            high_guardado = df_refinar.High[fecha_del_maximo_refinar]
                            low_guardado = df_refinar.Low[fecha_del_maximo_refinar]
                except Exception as falla:
                        _, _, exc_tb = sys.exc_info()
                        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                        #print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - symbol: "+symbol+"\n")
                        pass
        
        ### ALCISTA
        decisional_alcista_condicion =  (
                                        (df.color == 'rojo')
                                        &(
                                            ((df.High) <= (df.Low.shift(-2) - df.atr*multiplicador_imbalance))
                                            |
                                            ((df.High.shift(-1)) <= (df.Low.shift(-3) - df.atr*multiplicador_imbalance))
                                            |
                                            ((df.High.shift(-2)) <= (df.Low.shift(-4) - df.atr*multiplicador_imbalance))
                                        )
                                        & (df.tamanio_cuerpo < df.tamanio_cuerpo.shift(-2))
										& (df.Low < (df.Low.shift(-4) - df.atr*multiplicador_imbalance))
                                        & (df.Close < (df.Close.shift(-20) - df.atr*3)) # que luego del decisional el precio se mantenga lejos un tiempo. 
                                        )
        df['decisional_alcista_low'] = np.where(
                                    decisional_alcista_condicion
                                    ,df.Low,
                                    np.NaN)                                    
        df['decisional_alcista_high'] = np.where(                                
                                    decisional_alcista_condicion
                                    ,df.High,
                                    np.NaN)  
        ###refinado y relleno
        df['decisional_alcista'] = np.where(np.isnan(df.decisional_alcista_low),False,True) # creo un campo para identificar cuando se detecta el decisional 
        high_guardado=np.nan
        low_guardado=np.nan
        for i in range(0, len(df)-1):
            if  ((df['decisional_alcista'].iloc[i]) == False): # no es un decisional asi que copio
                    df.at[i, 'decisional_alcista_high'] = high_guardado
                    df.at[i, 'decisional_alcista_low'] = low_guardado
                    if (df.Low.iloc[i] <= low_guardado 
                        and df.decisional_alcista.iloc[i-1] != True
                        and df.decisional_alcista.iloc[i-2] != True
                        and df.decisional_alcista.iloc[i-3] != True
                        ): # borro decisional si fue mitigado                        
                        high_guardado = np.nan
                        low_guardado = np.nan
            else:
                high_guardado = df['decisional_alcista_high'].iloc[i]
                low_guardado = df['decisional_alcista_low'].iloc[i]
                indice_guardado = i
                try:
                        # refinacion los valores anteriormente guardados para 5m en caso de que se pueda
                        fecha_inicio_refinar = df['Open Time'].iloc[indice_guardado]
                        fecha_actual_refinar = fecha_inicio_refinar
                        fecha_del_minimo_refinar = fecha_actual_refinar
                        pico_minimo_refinar = 0
                        if refinado:
                            # busca el low mas bajo en velas rojas
                            for i in range(parametros_refinado['start'], parametros_refinado['stop'], parametros_refinado['step']):
                                if df_refinar.Low[fecha_actual_refinar] < pico_minimo_refinar and df_refinar.Close[fecha_actual_refinar] < df_refinar.Open[fecha_actual_refinar]:
                                    pico_minimo_refinar = df_refinar.Low[fecha_actual_refinar]
                                    fecha_del_minimo_refinar = fecha_actual_refinar
                                fecha_actual_refinar = fecha_inicio_refinar + pd.DateOffset(minutes=i)
                            high_guardado = df_refinar.High[fecha_del_minimo_refinar]
                            low_guardado = df_refinar.Low[fecha_del_minimo_refinar]
                except Exception as falla:
                        _, _, exc_tb = sys.exc_info()
                        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                        #print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - symbol: "+symbol+"\n")
                        pass
        #################################################################################################### TENDENCIA
        # alcista = -1
        # neutral = -2
        # bajista = -3        
        cantidad_ruptura = 3
        df['tendencia'] = np.nan
        v_contador_bajista = 0
        v_ultimo_bos_bajista = -2
        v_contador_alcista = 0
        v_ultimo_bos_alcista = -2
        v_tendencia_guardada = -2
        for i in range(0, len(df)-1):
            if not np.isnan(df['bos_bajista'].iloc[i]) and df['bos_bajista'].iloc[i] !=v_ultimo_bos_bajista:
                v_ultimo_bos_bajista = df['bos_bajista'].iloc[i]
                v_contador_bajista=v_contador_bajista+1
            if not np.isnan(df['bos_alcista'].iloc[i]) and df['bos_alcista'].iloc[i] !=v_ultimo_bos_alcista:
                v_ultimo_bos_alcista = df['bos_alcista'].iloc[i]
                v_contador_alcista=v_contador_alcista+1 
            if  v_contador_bajista == cantidad_ruptura:
                v_tendencia_guardada  = -3
                v_contador_bajista = 0
                v_ultimo_bos_bajista = -2
                v_contador_alcista = 0
                v_ultimo_bos_alcista = -2
            if  v_contador_alcista == cantidad_ruptura:
                v_tendencia_guardada  = -1
                v_contador_bajista = 0
                v_ultimo_bos_bajista = -2
                v_contador_alcista = 0
                v_ultimo_bos_alcista = -2
            df.at[i, 'tendencia'] = v_tendencia_guardada         
        
        # Calcular el precio promedio de cada vela (promedio entre el precio de apertura y cierre)
        average = (df['Open'] + df['Close']) / 2
        # Calcular la tendencia general
        df['trend'] = 'Alcista' if average.iloc[-1] > average.iloc[0] else 'Bajista'

        ########################################### INDICADORES #########################################################

        #################################################################################################### CRUCE DE BOS
        # alcista = -1
        # neutral = -2
        # bajista = -3    
        kill_inicio = 8
        kill_fin = 16
        df['cruce_bos_killzone'] = -2
        for i in range(0, len(df)-1):                
            if ((df.Close.iloc[i-1] < df['bos_bajista'].iloc[i-1] ) # bajista
                and kill_fin > df["Open Time"].dt.hour.iloc[i] >= kill_inicio # mercados abiertos
                and df['Open Time'].dt.dayofweek.iloc[i] not in (5,6) # no sab y dom
                ):
                df.at[i, 'cruce_bos_killzone'] = -3                
            if ((df.Close.iloc[i-1] > df['bos_alcista'].iloc[i-1]) # alcista
                and kill_fin > df["Open Time"].dt.hour.iloc[i] >= kill_inicio # mercados abiertos
                and df['Open Time'].dt.dayofweek.iloc[i] not in (5,6) # no sab y dom
                ):
                df.at[i, 'cruce_bos_killzone'] = -1
        #######################################################################################################  SENTIDO
        ultimo = -2
        df['sentido'] = -2
        for i in range(0, len(df)-1):
            if  (kill_fin > df["Open Time"].dt.hour.iloc[i] >= kill_inicio # mercados abiertos
                and df['Open Time'].dt.dayofweek.iloc[i] not in (5,6) # no sab y dom
                ):
                if df.cruce_bos_killzone.iloc[i] == -1 and ultimo == -3:
                    df.at[i, 'sentido'] = -1
                else:
                    if df.cruce_bos_killzone.iloc[i] == -3 and ultimo == -1:
                        df.at[i, 'sentido'] = -3
                    else:
                        df.at[i, 'sentido'] = -2
                if df.cruce_bos_killzone.iloc[i] != -2:
                    ultimo=df.cruce_bos_killzone.iloc[i]
            else:
                ultimo=-2

        #################### ACUMULACION DE LOQUIDEZ

        df['num_valores_iguales'] = (df['bos_bajista'] != df['bos_bajista'].shift(1)).cumsum()
        df['sell_side_liquidity'] = -(df.groupby('num_valores_iguales').cumcount() + 1)
        df = df.drop('num_valores_iguales', axis=1)

        df['num_valores_iguales'] = (df['bos_alcista'] != df['bos_alcista'].shift(1)).cumsum()
        df['buy_side_liquidity'] = (df.groupby('num_valores_iguales').cumcount() + 1)
        df = df.drop('num_valores_iguales', axis=1)
        
        ########################################################### POSICION
        
        pileta_vaciada = 0
        ventana_analisis_valida = 0
        largo_bos = 50
        ventana_analisis_limite = 5
        df['posicion'] = -2
        for i in range(0, len(df)-1):
             if  (kill_fin > df["Open Time"].dt.hour.iloc[i] >= kill_inicio # mercados abiertos
                and df['Open Time'].dt.dayofweek.iloc[i] not in (5,6) # no sab y dom
                ):
                if ((abs(df.sell_side_liquidity.iloc[i-1]) >= largo_bos and abs(df.sell_side_liquidity.iloc[i]) == 1)
                    or 
                    (abs(df.buy_side_liquidity.iloc[i-1]) >= largo_bos and abs(df.buy_side_liquidity.iloc[i]) == 1)                    
                    ): # se vació la pileta grande
                        pileta_vaciada = 1
                        ventana_analisis_valida = 0
                else:
                    if pileta_vaciada == 1:
                        ventana_analisis_valida = ventana_analisis_valida + 1
                        if ventana_analisis_valida == ventana_analisis_limite: # reinicio
                            pileta_vaciada = 0
                            ventana_analisis_valida = 0
                        else:
                            if df.cruce_bos_killzone.iloc[i] == -1:
                                df.at[i, 'posicion'] = -1
                                pileta_vaciada = 0
                                ventana_analisis_valida = 0
                            else:
                                if df.cruce_bos_killzone.iloc[i] == -3:
                                    df.at[i, 'posicion'] = -3
                                    pileta_vaciada = 0
                                    ventana_analisis_valida = 0

        ########################################## INDICE
        df['timestamp']=df['Open Time']
        df.set_index('timestamp', inplace=True)
        return df
    except Exception as falla:
        _, _, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - symbol: "+symbol+"\n")
        pass
##########################################################################################

def estrategia_smart(symbol, debug = False, refinado = True, fuente = 0, timeframe = '1h', balance = 100, largo = 1):
    try:
        porcentaje_perdida = 1 # porcentaje que se está dispuesto a perder por trade
        data = smart_money(symbol,refinado,fuente,timeframe,largo)     
        data['offset'] = data.atr/3   
        data['cierra'] = False        
        data['variacion_alcista'] = abs((((data.decisional_alcista_low - data.offset)/(data.decisional_alcista_high + data.offset))-1)*-100)                       
        data['variacion_bajista'] = abs((((data.decisional_bajista_high + data.offset)/(data.decisional_bajista_low - data.offset))-1)*100)        
        data['porcentajeentrada_alcista'] = np.where(((porcentaje_perdida/data.variacion_alcista)*100)>100,100,((porcentaje_perdida/data.variacion_alcista)*100))
        data['porcentajeentrada_bajista'] = np.where(((porcentaje_perdida/data.variacion_bajista)*100)>100,100,((porcentaje_perdida/data.variacion_bajista)*100))
    
        ####################### alertas y valores
        if debug:
            df_str = data[list(data.columns)].to_string(index=False)
            print(df_str)
        return data
    except Exception as falla:
        _, _, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - symbol: "+symbol+"\n")
        pass

def estrategia_alex(symbol, debug = False, refinado = True, fuente = 0, timeframe = '1h', balance = 100, largo = 10):
    try:
        data = smart_money(symbol,refinado,fuente,timeframe,largo)     
        offset = data.atr/3        
        data['signal'] = np.where(
                                  data.sentido == -1
                                  ,1,
                                  np.where(
                                  data.sentido == -3
                                  ,-1,
                                  0
                                )
                                )
        data['take_profit'] =   np.where(
                                data.signal == 1,                                
                                data.Low + data.atr*6,
                                np.where(
                                data.signal == -1,
                                data.High - data.atr*6,
                                0
                                )
                                )
        data['stop_loss'] = np.where(
                                data.signal == 1,
                                data.Close - data.atr*3,
                                np.where(
                                data.signal == -1,
                                data.Close + data.atr*3,
                                0
                                )
                                )
        data['cierra'] = False
        porcentaje_perdida = 1
        data['porcentajeentrada'] = 100
        ####################### alertas y valores
        if debug:
            df_str = data[list(data.columns)].to_string(index=False)
            print(df_str)
        return data
    except Exception as falla:
        _, _, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - symbol: "+symbol+"\n")
        pass