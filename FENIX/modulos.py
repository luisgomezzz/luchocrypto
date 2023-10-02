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
from binance.enums import HistoricalKlinesType
from numerize import numerize
import requests

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
            print(f"Error leyendo historial {symbol}. Intento otra vez. Falla {falla} \n")
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

def sigo_variacion_bitcoin(symbol,timeframe='15m',porc=0.8,ventana=2,tp_flag = True):
    # Si bitcoin varía en un porc% se entra al mercado con symbol para seguir la tendencia y obtener ganancias.
    try:
        data = obtiene_historial(symbol,timeframe)
        data_btc = obtiene_historial('BTCUSDT',timeframe)
        data['close_btc'] = data_btc.Close
        data['maximo_btc'] = data['close_btc'].rolling(ventana).max()
        data['minimo_btc'] = data['close_btc'].rolling(ventana).min()
        data['n_atr'] = 1.5
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
        data['cierra'] = False    
        return data
    except Exception as falla:
        _, _, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - par: "+symbol+"\n")
        pass   

def es_martillo(vela):
    out=0
    cuerpo = abs(vela['Open'] - vela['Close'])
    sombra_superior = vela['High'] - max(vela['Open'], vela['Close'])
    sombra_inferior = min(vela['Open'], vela['Close']) - vela['Low']
    condicion_largo = (vela.High-vela.Low) >= vela.atr/2
    if condicion_largo:
        if sombra_inferior>sombra_superior*3:
            if sombra_inferior > 2 * cuerpo: #martillo parado
                out = 1
        else:
            if sombra_superior>sombra_inferior*3:
                if sombra_superior > 2 * cuerpo: #martillo invertido
                    out = -1
    return out    

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
    data['martillo'] = data.apply(es_martillo, axis=1)  # 1: martillo parado * -1: martillo invertido   
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

def estrategia_triangulos(symbol, tp_flag = True, print_lines_flag = False):
    from scipy.stats import linregress
    #por defecto está habilitado el tp pero puede sacarse a mano durante el trade si el precio va a favor dejando al trailing stop como profit
    np.seterr(divide='ignore', invalid='ignore')
    timeframe = '1h'
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
    df['n_atr'] = 1.5 
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
        if abs(rmax)>=0.7 and abs(rmin)>=0.7 and abs(slmin)<=0.0001 and slmax<-0.001:
            df.loc[[candleid],'signal'] = 2 # desc
        if abs(rmax)>=0.7 and abs(rmin)>=0.7 and slmin>=0.001 and abs(slmax)<=0.0001:
            df.loc[[candleid],'signal'] = 3 # asc
        if abs(rmax)>=0.7 and abs(rmin)>=0.7 and slmin>=0.0001 and slmax<=-0.0001:
            df.loc[[candleid],'signal'] = 4 # comun
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
            # TENDENCIA
            if df.iloc[candleid].ema20 > df.iloc[candleid].ema50 > df.iloc[candleid].ema200:
                tendencia = 1
            else: 
                if df.iloc[candleid].ema20 < df.iloc[candleid].ema50 < df.iloc[candleid].ema200:
                    tendencia = -1
                else:
                    tendencia = 0
            #   señales
            if  (       df.iloc[candleid-1].Close > df.iloc[candleid-1].lower_line 
                    and df.iloc[candleid-1].Close > df.iloc[candleid-1].upper_line 
                    and df.iloc[candleid-1].lower_line!=0
                    and df.iloc[candleid-1].upper_line!=0
                    #and df.iloc[candleid-2].Close > df.iloc[candleid-2].lower_line 
                    #and df.iloc[candleid-2].Close > df.iloc[candleid-2].upper_line 
                    #and df.iloc[candleid-2].lower_line!=0
                    #and df.iloc[candleid-2].upper_line!=0
                    #and tendencia == 1
                ):
                df.loc[[candleid],"signal"] = 1
            elif (  df.iloc[candleid-1].Close < df.iloc[candleid-1].lower_line 
                and df.iloc[candleid-1].Close < df.iloc[candleid-1].upper_line 
                and df.iloc[candleid-1].lower_line!=0
                and df.iloc[candleid-1].upper_line!=0
                #and df.iloc[candleid-2].Close < df.iloc[candleid-2].lower_line 
                #and df.iloc[candleid-2].Close < df.iloc[candleid-2].upper_line 
                #and df.iloc[candleid-2].lower_line!=0
                #and df.iloc[candleid-2].upper_line!=0
                #and tendencia == -1
                ):
                df.loc[[candleid],"signal"] = -1
            
            # imprimo lugares donde se da la condición
            if print_lines_flag and df.iloc[candleid].signal in (1,-1):
                print(f"Candleid-1: {candleid-1} - linea superior {df.iloc[candleid-1].upper_line}")        
                print(f"Candleid-1: {candleid-1} - linea inferior {df.iloc[candleid-1].lower_line}")
                print(f"Precio Close-1: {df.iloc[candleid-1].Close}")
    df['take_profit'] =   np.where(
                            tp_flag,np.where(
                            df.signal == 1,
                            df.Close + 5*df.atr,
                            np.where(
                                    df.signal == -1,
                                    df.Close - 5*df.atr,  
                                    0
                                    )
                            ),np.NaN
                                    )
    df['stop_loss'] = np.where(
        df.signal == 1,
        df.Close - 1.5*df.atr,
        np.where(
            df.signal == -1,
            df.Close + 1.5*df.atr,
            0
        )
    ) 
    df['cierra'] = False
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

def estrategia_haz(symbol,tp_flag = True, debug = False, alerta = True):
    # Tener en cuenta que la ultima vela se trata de una manera distinta ya que el backtesting trabaja con el Close de cada vela
    # mientras que el programa verá un close distinto en cada instante a vela no cerrada.
    try:                
        np.seterr(divide='ignore', invalid='ignore')
        # temporalidad de 1h para encontrar martillos y soportes/resistencias
        data1h = obtiene_historial(symbol,'1h')        
        data1h['martillo'] = data1h.apply(es_martillo, axis=1)  # 1: martillo parado * -1: martillo invertido
        data1h['disparo'] = np.where(data1h.martillo==1,data1h.High,np.where(data1h.martillo==-1,data1h.Low,0))
        data1h['escape']  = np.where(data1h.martillo==1,data1h.Low, np.where(data1h.martillo==-1,data1h.High,0))
        data1h['date1h'] = data1h['Open Time']
        data1h['variacion_porc'] = ((data1h.Close/data1h.Close.shift(24))-1)*100
        data1h = data1h[:-1]        
        # Temporalidad de 5m para tradear
        data5m = obtiene_historial(symbol,'5m')
        resample = data1h.reindex(data5m.index, method='pad')
        data5m = data5m.join(resample[['martillo','disparo','escape','date1h','variacion_porc']])
        data5m['n_atr'] = 50
        data5m['signal'] = 0
        data5m['previous_martillo'] = 0
        previous_disparo = None  # Almacenar el valor del disparo de la fila anterior
        previous_escape = None  # Almacenar el valor del ESCAPE de la fila anterior
        previous_martillo = None
        for index, row in data5m.iterrows():
            # si no es unb martillo
            if row['martillo'] == 0:
                if previous_disparo is not None:
                    # si Close está dentro de los valores claves mantengo las ultimas claves
                    if  (previous_escape <= row['Close'] <= previous_disparo) or (previous_escape >= row['Close'] >= previous_disparo):
                        data5m.at[index, 'disparo'] = previous_disparo
                        data5m.at[index, 'escape'] = previous_escape
                        data5m.at[index, 'previous_martillo'] = previous_martillo
                    # Si cruzó algún valor clave
                    else:
                        # Limpio valores claves guardados si hubo un trade o simplemente salió por el escape.
                        data5m.at[index, 'disparo'] = previous_disparo
                        data5m.at[index, 'escape'] = previous_escape
                        data5m.at[index, 'previous_martillo'] = previous_martillo
                        previous_disparo = 0
                        previous_escape = 0
                        previous_martillo = 0
            # si es un martillo guardo los valores claves
            else: 
                previous_disparo = row['disparo']
                previous_escape = row['escape']
                previous_martillo = row['martillo']        
        data5m['signal'] = np.where((data5m.previous_martillo==1) & (data5m.Close > data5m.disparo) & (data5m.variacion_porc >= 5),
                                        1,
                                    np.where((data5m.previous_martillo==-1) & (data5m.Close < data5m.disparo) & (data5m.variacion_porc <= -5),
                                        -1,  
                                        0
                                        )
                            )
        # En el ultimo registro se define como sell o long si el anteultimo terminó con signal ya que se trabaja a vela cerrada.
        data5m.loc[data5m.index[-1], 'signal'] = np.where(data5m.signal.iloc[-2] == 1,
                                        1,
                                        np.where(data5m.signal.iloc[-2] == -1,
                                            -1,  
                                            0
                                            )
                                        )
        data5m['take_profit'] = np.where(tp_flag,
                                                np.where(data5m.signal == 1,
                                                    data5m.Close+data5m.atr*3,
                                                np.where(data5m.signal == -1,
                                                    data5m.Close-data5m.atr*3,  
                                                    0
                                                    )
                                                ),
                                        np.NaN
                                        )
        data5m['stop_loss'] =   np.where(data5m.signal == 1,
                                    data5m.Close-data5m.atr*1,
                                np.where(data5m.signal == -1,
                                    data5m.Close+data5m.atr*1,
                                    0
                                    )
                                )    
        data5m['cierra'] = False
        # Reemplazar valores no finitos (NA e inf) con 0
        data5m['porcentajeentrada'] = np.nan_to_num((data5m.Close/data5m.atr), nan=0, posinf=0, neginf=0)
        # Aplicar np.floor y convertir a enteros
        data5m['porcentajeentrada'] = np.floor(data5m['porcentajeentrada']).astype(int)
        
        ####################### alertas y valores
        if alerta:
            if data5m.disparo.iloc[-2] != 0 and data5m.martillo.iloc[-1] == 0: #significa que estamos en la ventana de posible atrape y no es un martillo actual
                print(f"\n{symbol} - CHG 24h: {round(data5m.variacion_porc.iloc[-2],2)}%  - lineas: {data5m.disparo.iloc[-2]} y {data5m.escape.iloc[-2]} - martillo: {previous_martillo}")
        if debug:
            df_str = data5m[['Open Time','martillo','disparo','escape','signal','take_profit','stop_loss','variacion_porc','porcentajeentrada']].to_string(index=False)
            print(df_str)
        if data5m.signal.iloc[-1] !=0:
            print(f"\nCRUZANDO!!! {symbol} - CHG 24h: {round(data5m.variacion_porc.iloc[-2],2)}%  - lineas: {data5m.disparo.iloc[-2]} y {data5m.escape.iloc[-2]} - martillo: {data5m.previous_martillo.iloc[-2]} - Porc de entrada: {data5m.porcentajeentrada.iloc[-2]}")
        return data5m
    except Exception as falla:
        _, _, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - symbol: "+symbol+"\n")
        pass

def tendencia (symbol,timeframe='1d'):
    try:
        tendencia=0.0
        data= obtiene_historial(symbol,timeframe)
        len_df = len(data)
        if len_df >= 400:# si tiene historial mayor a 400 velas entonces tomo ema200
            longitud_ema = 200
        else:
            longitud_ema = int((len_df/2))
        emax = ta.ema(data.Close, length=longitud_ema)
        if longitud_ema>=200:
            comienzo = emax.iloc[-200]
        else:
            comienzo = emax[longitud_ema-1]
        final = emax.iloc[-1]
        tendencia=truncate((final/comienzo-1)*100,2)
        return tendencia
    except Exception as falla:
        _, _, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+"\n")
        pass    

def obiene_capitalizacion(symbol):
    API_KEY = '4c9c0645-49c7-48c3-9a42-e7a2f94d448f'
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
    HEADERS = {'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': API_KEY}
    PARAMS = {'convert': 'USD',
            'limit': 1500}
    resp = requests.get(url, headers=HEADERS, params=PARAMS)
    def get_data(resp):
        data = json.loads(resp.content)['data']
        rows = list()
        for item in data:
            rows.append([
                    item['cmc_rank'],
                    item['id'],
                    item['name'],
                    item['symbol'],
                    item['slug'], 
                    item['quote']['USD']['market_cap'],
                    item['quote']['USD']['volume_24h'],
                    item['date_added']])
        df = pd.DataFrame(rows, columns=['cmc_rank','id','name','symbol','slug','market_cap','volume_24h','date_added'])
        df.index.name = 'id'
        return(df)
    if resp.status_code == 200:
        df = get_data(resp)
        if not df.empty:
            df.to_csv('crypto_latests.csv')
            print("Archivo con datos de CoinMarketCap gruadado crypto_latests.csv")
            df2 = pd.read_csv('crypto_latests.csv', index_col=0)
        else:
            print("df de CoinMarketCap vacío. No se actualizó crypto_latests.csv")
    else:
        print(resp.status_code)
    ##toma valor desde el file    
    df2 = pd.read_csv('crypto_latests.csv', index_col=0)    
    for index, row in df2.iterrows():
        if row['symbol'] == (symbol[0:symbol.find('USDT')]).upper():       
            print(f"Symbol: {symbol} - Ranking: {row.cmc_rank} - Market cap: {numerize.numerize(row.market_cap)} - Vol24h: {numerize.numerize(row.volume_24h)} - date_added: {row.date_added}")

def estrategia_oro(symbol,tp_flag = True):
    porcentajeentrada = 0.01
    archivo_csv = 'historico.csv'
    column_names = ['Open Time', 'Open', 'High', 'Low', 'Close', 'Change(Pips)', 'Change(%)', 'Nada']
    data = pd.read_csv(archivo_csv, header=None, names=column_names)
    data['Open Time']=pd.to_datetime(data['Open Time'])
    data['timestamp']=data['Open Time']
    data.set_index('timestamp', inplace=True)
    data.drop(['Change(Pips)', 'Change(%)', 'Nada'], axis=1, inplace=True)
    data.sort_values(by='timestamp', ascending = True, inplace = True)
    data['Volume'] = 1
    data['atr'] = ta.atr(data.High, data.Low, data.Close)
    data['n_atr'] = 50
    data['time_hour'] = pd.to_datetime(data['Open Time']).dt.hour
    numeric_columns = ['Open', 'High', 'Low', 'Close','time_hour','Volume']
    data[numeric_columns] = data[numeric_columns].apply(pd.to_numeric, axis=1)
    data['signal'] = np.where(
        (data.time_hour.shift(1) == 14)
        &(data.Close.shift(3) > data.Close.shift(1)) 
        ,1,
        np.where(
            (data.time_hour.shift(1) == 14)
            &(data.Close.shift(3) < data.Close.shift(1)) 
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
                                    data.Close*0.999,  
                                    0
                                    )
                            ),np.NaN
                                    )
    data['stop_loss'] = np.where(
        data.signal == 1,
        data.Close*0.995,    
        np.where(
            data.signal == -1,
            data.Close*1.005,
            0
        )
    )
    data['cierra'] = False
    return data,porcentajeentrada    

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

def backtesting_royal(data, plot_flag=False):
    balance = 100    
    def indicador(df_campo):
        indi=pd.Series(df_campo)
        return indi.to_numpy()
    class Fenix(Strategy):
        def init(self):
            super().init()
            #### varios
            self.tendencia = self.I(indicador,self.data.tendencia,name="tendencia")
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
            self.bajista_extremo_high = self.I(indicador,self.data.bajista_extremo_high,name="bajista_extremo_high", overlay=True, color="RED", scatter=False)
            self.bajista_extremo_low = self.I(indicador,self.data.bajista_extremo_low,name="bajista_extremo_low", overlay=True, color="RED", scatter=False)
            self.alcista_extremo_high = self.I(indicador,self.data.alcista_extremo_high,name="alcista_extremo_high", overlay=True, color="GREEN", scatter=False)
            self.alcista_extremo_low = self.I(indicador,self.data.alcista_extremo_low,name="alcista_extremo_low", overlay=True, color="GREEN", scatter=False)
            #####   BOSES ok!!!
            self.bos_bajista = self.I(indicador,self.data.bos_bajista,name="BOS bajista", overlay=True, color="RED", scatter=True)
            self.bos_alcista = self.I(indicador,self.data.bos_alcista,name="BOS alcista", overlay=True, color="GREEN", scatter=True)
            #####   IMBALANCES ok!!!
            self.imba_bajista_low = self.I(indicador,self.data.imba_bajista_low,name="imba_bajista_low", overlay=True, color="orange", scatter=True)
            self.imba_bajista_high = self.I(indicador,self.data.imba_bajista_high,name="imba_bajista_high", overlay=True, color="orange", scatter=True)
            self.imba_alcista_low = self.I(indicador,self.data.imba_alcista_low,name="imba_alcista_low", overlay=True, color="springgreen", scatter=True)
            self.imba_alcista_high = self.I(indicador,self.data.imba_alcista_high,name="imba_alcista_high", overlay=True, color="springgreen", scatter=True)
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

####################################################################################

def smart_money(df,symbol,refinado,file_source):
    try:
        # Devuelve un dataframe con timeframe de 15m con BOSes, imbalances y orders blocks.
        #
        # Se debe tener en cuenta los boses son marcados una vez que se genera el rompimiento, esto significa que no se ve la línea de
        # bos hasta que no se produce el quiebre. Ocurre lo mismo con todas las señales que dependan de los boses.
        # Los imbalances no mitigados sí se pueden ver online.
        #  
        if refinado:
            df_refinar = obtiene_historial(symbol,'15m') #historial de temporalidad inferior para refinar
            parametros_refinado = {"start":15,"stop":75,"step":15} # 5m = {"start":5,"stop":20,"step":5} --- 1m = {"start":1,"stop":6,"step":1}
        
        if file_source:
            df_imbalance = myfxbook_file_historico() 
            refinado = False
        else:
            df_imbalance = obtiene_historial(symbol,'15m') #historial para imbalances        
        

        largo = 1 # Parámetro de longitud para los puntos pivote High y Low
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
        df_imbalance['row_number'] = (range(len(df_imbalance)))
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
                ##relleno
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
        multiplicador_imbalance = 0.5
        ## BAJISTA
        decisional_bajista_condicion =  (
                                        #(df.High >= df.High.shift(-1))&
                                        (df.color =='verde')
                                        #& ~np.isnan(df.bos_bajista)
                                        & (
                                            ((df.Low) >= (df.High.shift(-2)+df.atr*multiplicador_imbalance))
                                            |
                                            ((df.Low.shift(-1)) >= (df.High.shift(-3)+df.atr*multiplicador_imbalance))
                                            |
                                            ((df.Low.shift(-2)) >= (df.High.shift(-4)+df.atr*multiplicador_imbalance))                                          
                                          )
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
        high_guardado = np.nan
        low_guardado = np.nan                                          
        for i in range(0, len(df)-1):
            if np.isnan(df['decisional_bajista_high'].iloc[i]):# and df.High.iloc[i] < df.bajista_extremo_low.iloc[i]:    
                df.at[i, 'decisional_bajista_high'] = high_guardado
                df.at[i, 'decisional_bajista_low'] = low_guardado
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
                                print(f"fecha_actual_refinar: {fecha_actual_refinar}")
                                if df_refinar.High[fecha_actual_refinar] > pico_maximo_refinar and df_refinar.Close[fecha_actual_refinar] > df_refinar.Open[fecha_actual_refinar]:
                                    pico_maximo_refinar = df_refinar.High[fecha_actual_refinar]
                                    fecha_del_maximo_refinar = fecha_actual_refinar
                                fecha_actual_refinar = fecha_inicio_refinar + pd.DateOffset(minutes=i)
                            high_guardado = df_refinar.High[fecha_del_maximo_refinar]
                            low_guardado = df_refinar.Low[fecha_del_maximo_refinar]
                            print(f"fecha elegida: {fecha_del_maximo_refinar}")
                except Exception as falla:
                        _, _, exc_tb = sys.exc_info()
                        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                        #print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - symbol: "+symbol+"\n")
                        pass
        
        ### ALCISTA
        decisional_alcista_condicion =  (
                                        #(df.Low <= df.Low.shift(-1))&
                                        (df.color == 'rojo')
                                        #& ~np.isnan(df.bos_alcista)
                                        &(
                                            ((df.High) <= (df.Low.shift(-2)-df.atr*multiplicador_imbalance))
                                            |
                                            ((df.High.shift(-1)) <= (df.Low.shift(-3)-df.atr*multiplicador_imbalance))
                                            |
                                            ((df.High.shift(-2)) <= (df.Low.shift(-4)-df.atr*multiplicador_imbalance))
                                        )
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
        high_guardado=np.nan
        low_guardado=np.nan                                          
        for i in range(0, len(df)-1):
            if np.isnan(df['decisional_alcista_high'].iloc[i]):# and df.Low.iloc[i] > df.alcista_extremo_high.iloc[i]:    
                df.at[i, 'decisional_alcista_high'] = high_guardado
                df.at[i, 'decisional_alcista_low'] = low_guardado
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
        df['tendencia'] = np.nan
        v_contador_bajista = 0
        v_ultimo_bos_bajista = 0
        v_contador_alcista = 0
        v_ultimo_bos_alcista = 0
        v_tendencia_guardada = 0
        for i in range(0, len(df)-1):
            if not np.isnan(df['bos_bajista'].iloc[i]) and df['bos_bajista'].iloc[i] !=v_ultimo_bos_bajista:
                v_ultimo_bos_bajista = df['bos_bajista'].iloc[i]
                v_contador_bajista=v_contador_bajista+1
            if not np.isnan(df['bos_alcista'].iloc[i]) and df['bos_alcista'].iloc[i] !=v_ultimo_bos_alcista:
                v_ultimo_bos_alcista = df['bos_alcista'].iloc[i]
                v_contador_alcista=v_contador_alcista+1 
            if  v_contador_bajista == 2:
                v_tendencia_guardada  = -1
                v_contador_bajista = 0
                v_ultimo_bos_bajista = 0
                v_contador_alcista = 0
                v_ultimo_bos_alcista = 0
            if  v_contador_alcista == 2:
                v_tendencia_guardada  = 1
                v_contador_bajista = 0
                v_ultimo_bos_bajista = 0
                v_contador_alcista = 0
                v_ultimo_bos_alcista = 0  
            df.at[i, 'tendencia'] = v_tendencia_guardada         

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

def estrategia_royal(symbol,debug = False, refinado = True, file_source=False):
    try:                
        np.seterr(divide='ignore', invalid='ignore')
        
        if file_source:
            data = myfxbook_file_historico()
            refinado = False
        else:
            data = obtiene_historial(symbol,'1h')
        
        
        data = smart_money(data,symbol,refinado,file_source)          
        data['signal'] = np.where((data.tendencia == 1)
                                  &(data.Low > data.decisional_alcista_low)
                                  &(data.Low <= data.decisional_alcista_high)
                                  &(data.Low.shift(1) > data.decisional_alcista_high.shift(1))
                                  ,1,
                                  np.where((data.tendencia == -1)
                                  &(data.High < data.decisional_bajista_high)
                                  &(data.High >= data.decisional_bajista_low)
                                  &(data.High.shift(1) < data.decisional_bajista_low.shift(1))
                                  ,-1,
                                  0
                                )
                                )
        data['take_profit'] =   np.where(
                                data.signal == -1,
                                data.Close-data.atr*3,
                                np.where(
                                data.signal == 1,
                                data.Close+data.atr*3,
                                0
                                )
                                )
        data['stop_loss'] = np.where(
                                data.signal == -1,
                                data.decisional_bajista_high,
                                np.where(
                                data.signal == 1,
                                data.decisional_alcista_low,
                                0
                                )
                                )

        data['cierra'] = False
        # Reemplazar valores no finitos (NA e inf) con 0
        data['porcentajeentrada'] = np.nan_to_num((data.Close/data.atr), nan=0, posinf=0, neginf=0)
        # Aplicar np.floor y convertir a enteros
        data['porcentajeentrada'] = np.floor(data['porcentajeentrada']).astype(int)
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
