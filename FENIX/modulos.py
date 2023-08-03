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
from backtesting import Backtest
import talib
from backtesting import Strategy

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

def obtiene_historial(symbol,timeframe):
    client = cons.client    
    leido = False
    while leido == False:
        try:
            historical_data = client.get_historical_klines(symbol, timeframe)
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
            data['ema20']=data.ta.ema(20)
            data['ema50']=data.ta.ema(50)
            data['ema200']=data.ta.ema(200)
            data['atr']=ta.atr(data.High, data.Low, data.Close)        
            data['n_atr'] = 50 # para el trailing stop. default 50 para que no tenga incidencia. En la estrategia se pone el valor real.
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
            print(f"Error leyendo historial {symbol}. Intento otra vez. \n")
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

def filtradodemonedas ():    # Retorna las monedas con mejor volumen para evitar manipulacion.
    lista = lista_de_monedas ()
    lista_filtrada = []
    for symbol in lista:
        try:  
            vol= volumeOf24h(symbol)
            if vol >= cons.minvolumen24h:
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
    class Fenix(TrailingStrategy):
        def init(self):
            super().init()
        def next(self):       
            super().next()
            if self.position:
                pass
            else:   
                if np.isnan(data.take_profit[-1]):
                    tp_value = None
                else:
                    tp_value = self.data.take_profit[-1]
                if self.data.signal[-1]==1:
                    self.buy(size=1000,sl=self.data.stop_loss[-1],tp=tp_value)
                elif self.data.signal[-1]==-1:
                    self.sell(size=1000,sl=self.data.stop_loss[-1],tp=tp_value)
    bt = Backtest(data, Fenix, cash=1000)
    output = bt.run()
    if plot_flag:
        bt.plot()
    return output

def estrategia_bb(symbol,tp_flag=True):
    timeframe = '15m'
    ventana = 7
    data = obtiene_historial(symbol,timeframe)
    btc_data = obtiene_historial("BTCUSDT",timeframe)
    data['variacion_btc'] = ((btc_data['Close'].rolling(ventana).max()/btc_data['Close'].rolling(ventana).min())-1)*100
    data['n_atr'] = 50 # para el trailing stop
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
    #if symbol != 'XRPUSDT':
    #    data['signal']=0
    #    data['take_profit']=0
    #    data['stop_loss']=0
    return data

def sigo_variacion_bitcoin(symbol,timeframe='15m',porc=0.8,ventana=2,tp_flag = True):
    # Si bitcoin varía en un porc% se entra al mercado con symbol para seguir la tendencia y obtener ganancias.
    try:
        data = obtiene_historial(symbol,timeframe)
        data_btc = obtiene_historial('BTCUSDT',timeframe)
        data['close_btc'] = data_btc.Close
        data['maximo_btc'] = data['close_btc'].rolling(ventana).max()
        data['minimo_btc'] = data['close_btc'].rolling(ventana).min()
        data.n_atr = 1.5
        data['atr']=ta.atr(data.High, data.Low, data.Close, length=4)
        data['signal'] = np.where(
            (data.close_btc.shift(1) >= data.maximo_btc.shift(2))
            &(data.close_btc.shift(1) >= data.minimo_btc.shift(2)*(1+porc/100))
            ,1,
            np.where(
                (data.close_btc.shift(1)  <= data.minimo_btc.shift(2))
                &(data.close_btc.shift(1) <= data.maximo_btc.shift(2)*(1-porc/100))        
                ,-1,
                0
            )
        )  
        data['take_profit'] =   np.where(
                                tp_flag,np.where(
                                data.signal == 1,
                                data.Close + 3*data.atr,
                                np.where(
                                        data.signal == -1,
                                        data.Close - 3*data.atr,  
                                        0
                                        )
                                ),np.NaN
                                        )
        data['stop_loss'] = np.where(
            data.signal == 1,
            data.Close - 5*data.atr,  # se exagera colocando 5 ya que el stop lo realiza el trailing
            np.where(
                data.signal == -1,
                data.Close + 5*data.atr,
                0
            )
        )    
        return data
    except Exception as falla:
        _, _, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - par: "+symbol+"\n")
        pass   

def estrategia_santa(symbol,tp_flag = True):
    #por defecto está habilitado el tp pero puede sacarse a mano durante el trade si el precio va a favor dejando al trailing stop como profit
    np.seterr(divide='ignore', invalid='ignore')
    timeframe = '15m'
    ventana = 2
    porc_alto = 5
    porc_bajo = 4
    ## variacion de btc aprox
    data = obtiene_historial(symbol,timeframe)
    #btc_data = obtiene_historial("BTCUSDT",timeframe)
    #data['variacion_btc'] = ((btc_data['High'].rolling(ventana).max()/btc_data['Low'].rolling(ventana).min())-1)*100 # aprox
    #variacion de symbol
    data['maximo'] = data['High'].rolling(ventana).max()
    data['minimo'] = data['Low'].rolling(ventana).min()
    data.n_atr = 1.5
    data['atr']=ta.atr(data.High, data.Low, data.Close, length=4)
    get_bollinger_bands(data)
    data['signal'] = np.where(
         (data.Close.shift(1) >= data.maximo.shift(2)) # para que solo sea reentrada
        &(data.Close.shift(1) >= data.minimo.shift(2)*(1+porc_bajo/100)) # variacion desde
        &(data.Close.shift(1) <= data.minimo.shift(2)*(1+porc_alto/100)) # variacion hasta
        #&(data.variacion_btc.shift(1) < 0.8) # bitcoin variacion pequeña
        &(data.Close.shift(1) > data.upper.shift(1))
        ,-1,
        np.where(
             (data.Close.shift(1) <= data.minimo.shift(2))
            &(data.Close.shift(1) <= data.maximo.shift(2)*(1-porc_bajo/100))
            &(data.Close.shift(1) >= data.maximo.shift(2)*(1-porc_alto/100))
            #&(data.variacion_btc.shift(1) < 0.8)
            &(data.Close.shift(1) < data.lower.shift(1))
            ,1,
            0
        )
    )  
    data['take_profit'] =   np.where(
                            tp_flag,np.where(
                            data.signal == 1,
                            data.Close + 3*data.atr,
                            np.where(
                                    data.signal == -1,
                                    data.Close - 3*data.atr,  
                                    0
                                    )
                            ),np.NaN
                                    )
    data['stop_loss'] = np.where(
        data.signal == 1,
        data.Close - 5*data.atr,    # se exagera colocando 5 ya que el stop lo realiza el trailing
        np.where(
            data.signal == -1,
            data.Close + 5*data.atr,
            0
        )
    )    
    return data    

def estrategia_triangulos(symbol, tp_flag = True, print_lines_flag = False):
    from scipy.stats import linregress
    #por defecto está habilitado el tp pero puede sacarse a mano durante el trade si el precio va a favor dejando al trailing stop como profit
    np.seterr(divide='ignore', invalid='ignore')
    timeframe = '15m'
    def pivotid(df1, l, n1, n2): #n1 n2 before and after candle l
        if l-n1 < 0 or l+n2 >= len(df1):
            return 0    
        pividlow=1
        pividhigh=1
        for i in range(l-n1, l+n2+1):
            if(df1.Low[l]>df1.Low[i]):
                pividlow=0
            if(df1.High[l]<df1.High[i]):
                pividhigh=0
        if pividlow and pividhigh:
            return 3
        elif pividlow:
            return 1
        elif pividhigh:
            return 2
        else:
            return 0
    def pointpos(x):
        if x['pivot']==1:
            return x['Low']-1e-3
        elif x['pivot']==2:
            return x['High']+1e-3
        else:
            return np.nan
    df = obtiene_historial(symbol,timeframe)
    df=df.copy()
    #Check if NA values are in data
    df=df[df['Volume']!=0]
    df.reset_index(drop=True, inplace=True)
    df.isna().sum()
    df["n_atr"] = 1.5
    df["pivot"] = df.apply(lambda x: pivotid(df, x.name,3,3), axis=1)
    df["pointpos"] = df.apply(lambda row: pointpos(row), axis=1)
    df["signal"]=0
    df["upper_line"]=0
    df["lower_line"]=0
    ### detecta la vela donde hay un triangulo a partir de la posicion que se elija en el rango
    backcandles= 20
    for candleid in range(0, len(df)):
        maxim = np.array([])
        minim = np.array([])
        xxmin = np.array([])
        xxmax = np.array([])
        for i in range(candleid-backcandles, candleid+1):
            if df.iloc[i].pivot == 1:
                minim = np.append(minim, df.iloc[i].Low)
                xxmin = np.append(xxmin, i) #could be i instead df.iloc[i].name
            if df.iloc[i].pivot == 2:
                maxim = np.append(maxim, df.iloc[i].High)
                xxmax = np.append(xxmax, i) # df.iloc[i].name        
        if (xxmax.size <3 and xxmin.size <3) or xxmax.size==0 or xxmin.size==0:
            continue        
        slmin, intercmin, rmin, pmin, semin = linregress(xxmin, minim)
        slmax, intercmax, rmax, pmax, semax = linregress(xxmax, maxim)            
        if abs(rmax)>=0.7 and abs(rmin)>=0.7 and abs(slmin)<=0.00001 and slmax<-0.0001:
            df.loc[[candleid],'signal'] = 2
        if abs(rmax)>=0.7 and abs(rmin)>=0.7 and slmin>=0.0001 and abs(slmax)<=0.00001:
            df.loc[[candleid],'signal'] = 3
        if abs(rmax)>=0.9 and abs(rmin)>=0.9 and slmin>=0.0001 and slmax<=-0.0001:
            df.loc[[candleid],'signal'] = 4
        if df.iloc[candleid].signal in (2,3,4):
            # Ecuación de la línea superior
            xssup = xxmax
            yssup = slmax*xxmax + intercmax
            pendiente = (yssup[1]-yssup[0])/(xssup[1]-xssup[0])
            intersecciony = yssup[0]-pendiente*xssup[0]
            df.loc[[candleid],"upper_line"]=pendiente*candleid+intersecciony      
            # Ecuación de la línea inferior
            xsinf = xxmin
            ysinf = slmin*xxmin + intercmin
            pendiente = (ysinf[1]-ysinf[0])/(xsinf[1]-xsinf[0])
            intersecciony = ysinf[0]-pendiente*xsinf[0]
            df.loc[[candleid],"lower_line"]=pendiente*candleid+intersecciony
            
            #   señales
            if (    df.iloc[candleid-1].Close < df.iloc[candleid-1].lower_line - df.iloc[candleid-1].atr/2
                and df.iloc[candleid-1].Close < df.iloc[candleid-1].upper_line - df.iloc[candleid-1].atr/2
                and df.iloc[candleid-1].lower_line!=0
                and df.iloc[candleid-1].upper_line!=0
                ):
                df.loc[[candleid],"signal"] = -1
            elif    (   df.iloc[candleid-1].Close > df.iloc[candleid-1].lower_line + df.iloc[candleid-1].atr/2
                    and df.iloc[candleid-1].Close > df.iloc[candleid-1].upper_line + df.iloc[candleid-1].atr/2
                    and df.iloc[candleid-1].lower_line!=0
                    and df.iloc[candleid-1].upper_line!=0
                    ):
                df.loc[[candleid],"signal"] = 1
            
            # imprimo lugares donde se da la condición
            if print_lines_flag and df.iloc[candleid].signal in (1,-1):
                print(f"Candleid-1: {candleid-1} - linea superior {df.iloc[candleid-1].upper_line}")        
                print(f"Candleid-1: {candleid-1} - linea inferior {df.iloc[candleid-1].lower_line}")
                print(f"Precio Close-1: {df.iloc[candleid-1].Close}")
    df['take_profit'] =   np.where(
                            tp_flag,np.where(
                            df.signal == 1,
                            df.Close + 3*df.atr,
                            np.where(
                                    df.signal == -1,
                                    df.Close - 3*df.atr,  
                                    0
                                    )
                            ),np.NaN
                                    )
    df['stop_loss'] = np.where(
        df.signal == 1,
        df.Close - 1.5*df.atr,    # se exagera colocando 5 ya que el stop lo realiza el trailing
        #df.lower_line,
        np.where(
            df.signal == -1,
            df.Close + 1.5*df.atr,
            #df.upper_line,
            0
        )
    ) 
    df["timestamp"] = df["Open Time"]   
    df.set_index('timestamp', inplace=True)
    return df        

def dibuja_patrones_triangulos (df,candleid):
    from scipy.stats import linregress
    import plotly.graph_objects as go
    #dibuja
    df.reset_index(drop=True, inplace=True)    
    dfpl = df[0:1000]
    fig = go.Figure(data=[go.Candlestick(x=dfpl.index,
                    open=dfpl['Open'],
                    high=dfpl['High'],
                    low=dfpl['Low'],
                    close=dfpl['Close'])])
    fig.add_scatter(x=dfpl.index, y=dfpl['pointpos'], mode="markers",
                    marker=dict(size=5, color="MediumPurple"),
                    name="pivot")
    backcandles = 20
    maxim = np.array([])
    minim = np.array([])
    xxmin = np.array([])
    xxmax = np.array([])
    for i in range(candleid-backcandles, candleid+1):
        if df.iloc[i].pivot == 1:
            minim = np.append(minim, df.iloc[i].Low)
            xxmin = np.append(xxmin, i) #could be i instead df.iloc[i].name
        if df.iloc[i].pivot == 2:
            maxim = np.append(maxim, df.iloc[i].High)
            xxmax = np.append(xxmax, i) # df.iloc[i].name            
    slmin, intercmin, rmin, pmin, semin = linregress(xxmin, minim)
    slmax, intercmax, rmax, pmax, semax = linregress(xxmax, maxim)
    print(rmin, rmax)
    dfpl = df[candleid-backcandles-50:candleid+backcandles+50]
    fig = go.Figure(data=[go.Candlestick(x=dfpl.index,
                    open=dfpl['Open'],
                    high=dfpl['High'],
                    low=dfpl['Low'],
                    close=dfpl['Close'])])
    fig.add_scatter(x=dfpl.index, y=dfpl['pointpos'], mode="markers",
                    marker=dict(size=4, color="MediumPurple"),
                    name="pivot")
    xxmin = np.append(xxmin, xxmin[-1]+15)
    xxmax = np.append(xxmax, xxmax[-1]+15)
    fig.add_trace(go.Scatter(x=xxmin, y=slmin*xxmin + intercmin, mode='lines', name='min slope'))
    fig.add_trace(go.Scatter(x=xxmax, y=slmax*xxmax + intercmax, mode='lines', name='max slope'))
    fig.update_layout(xaxis_rangeslider_visible=False)
    fig.show()
    print(f"linea superior. X: {xxmax} - y: {slmax*xxmax + intercmax}")
    print(f"linea inferior. X: {xxmin} - y: {slmin*xxmin + intercmin}")
