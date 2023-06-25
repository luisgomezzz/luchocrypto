import sys
import pandas as pd
import constantes as cons
import os
import winsound as ws
import math
from binance.exceptions import BinanceAPIException
import json
import ccxt as ccxt
from requests import Session
import numpy as np
import pandas_ta as ta
import datetime as dt
from backtesting import Backtest, Strategy
import talib

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
                    if 'USDT' in s['symbol'] and '_' not in s['symbol'] and s['symbol'] not in mazmorra:
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

def coingeckoinfo (par,dato='market_cap'):
    '''
    {'id': 'binancecoin', 'symbol': 'bnb', 'name': 'BNB', 'image': 'https://assets.coingecko.com/coins/images/825/large/bnb-icon2_2x.png?1644979850', 
    'current_price': 282.13, 'market_cap': 45966534569, 'market_cap_rank': 4, 'fully_diluted_valuation': 56304980752, 
    'total_volume': 1748519199, 'high_24h': 291.05, 'low_24h': 272.34, 'price_change_24h': -3.749382261274775, 
    'price_change_percentage_24h': -1.31152, 'market_cap_change_24h': -772981310.7671661, 'market_cap_change_percentage_24h': -1.65381,
    'circulating_supply': 163276974.63, 'total_supply': 163276974.63, 'max_supply': 200000000.0, 'ath': 686.31, 
    'ath_change_percentage': -58.97972, 'ath_date': '2021-05-10T07:24:17.097Z', 'atl': 0.0398177, 'atl_change_percentage': 706934.61939, 
    'atl_date': '2017-10-19T00:00:00.000Z', 'roi': None, 'last_updated': '2022-11-12T14:45:04.478Z'}
    '''
    symbol = (par[0:par.find('USDT')]).lower()
    url = 'https://api.coingecko.com/api/v3/coins/list' 
    session = Session()
    response = session.get(url)
    info = json.loads(response.text)#[simbolo]['quote']['USD'][dato]
    id=''
    valor=0
    for i in range(len(info)):
        if info[i]['symbol']==symbol:
            id=info[i]['id']
            break
    if id!='':
        urldetalle="https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids="+id+"&order=market_cap_desc&per_page=100&page=1&sparkline=false"
        parameters = {}
        session = Session()
        response = session.get(urldetalle, params=parameters)
        info = json.loads(response.text)#[simbolo]['quote']['USD'][dato]
        valor = info[0][dato]
    else:
        valor = 0
    return valor

def capitalizacion(par):
    cap=0.0
    # Primeramente se busca en binance aunque sea de otro exchange... si no lo encuentra va a coingecko.
    #busqueda en binance
    clientcap = cons.binanceClient(cons.api_key, cons.api_secret,cons.api_passphares) 
    info = clientcap.get_products()
    lista=info['data']
    for i in range(len(lista)):
        if lista[i]['s']==par:
            cap = float(lista[i]['c']*lista[i]['cs'])
            break
    if cap==0.0:
        #busqueda en coingecko
        try:
            cap=float(coingeckoinfo (par,dato='market_cap'))
        except:
            cap=0.0
            pass
    return cap  

def get_bollinger_bands(df):
    mult = 2.0
    length = 20
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

def obtiene_historial(symbol):
    client = cons.client
    timeframe='30m'
    try:
        historical_data = client.get_historical_klines(symbol, timeframe)
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
        data.drop(['Open Time','Close Time','Quote Asset Volume', 'TB Base Volume', 'TB Quote Volume','Number of Trades',
                'Ignore'], axis=1, inplace=True)    
        data['ema20']=data.ta.ema(20)
        data['ema50']=data.ta.ema(50)
        data['ema200']=data.ta.ema(200)
        data['atr']=ta.atr(data.High, data.Low, data.Close)        
        data = get_bollinger_bands(data)
        data['avg_volume'] = data['Volume'].rolling(20).mean()
        data['vwap'] = vwap(data)
        return data
    except KeyboardInterrupt as ky:
        print("\nSalida solicitada. ")
        sys.exit()              
    except:
        print("Falla leyendo...")
        pass

def EMA(data,length):
    return data.ta.ema(length)

def backtesting(data): 
    balance=1000
    class Fenix(Strategy):
        def init(self):
            self.ema20 = self.I(EMA, data, 20, color="green")
            self.ema50 = self.I(EMA, data, 50,color="yellow")
            self.ema200 = self.I(EMA, data, 200, color="grey")
        def next(self):
            if not self.position:
                if self.data.signal[-1] ==1:
                    self.buy(size=balance, sl=self.data.stop_loss[-1] , tp=self.data.take_profit[-1])
                elif self.data.signal[-1] ==-1:
                    self.sell(size=balance, sl=self.data.stop_loss[-1] , tp=self.data.take_profit[-1])
            else:
                pass
    bt = Backtest(data, Fenix, cash=balance, commission=.002, exclusive_orders=True)
    output = bt.run()
    #bt.plot()
    return output

def estrategia(data):
    mult_take_profit = 1
    mult_stop_loss = 1
    data['signal'] = np.where(
        (data.ema20 > data.ema50) & 
        (data.ema50 > data.ema200) & 
        (data.Close.shift(1) < data.lower.shift(1)) & 
        (data.Volume > data.avg_volume),
        1,
        np.where(
            (data.ema20 < data.ema50) & 
            (data.ema50 < data.ema200) & 
            (data.Close.shift(1) > data.upper.shift(1)) & 
            (data.Volume > data.avg_volume),
            -1,
            0
        )
    )    
    data['take_profit'] = np.where(
        data.signal == 1,
        data.Close + (data.atr * mult_take_profit),
        np.where(
            data.signal == -1,
            data.Close - (data.atr * mult_take_profit),  
            0
        )
    )
    data['stop_loss'] = np.where(
        data.signal == 1,
        data.Close - (data.atr * mult_stop_loss),  
        np.where(
            data.signal == -1,
            data.Close + (data.atr * mult_stop_loss),  
            0
        )
    )
    return data

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
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - par: "+par+"\n")
        creado = False
        orderid = 0
        pass    
    return creado,orderid        