import sys
import pandas as pd
import constantes as cons
import os
import winsound as ws
import math
from time import sleep
from binance.exceptions import BinanceAPIException
from binance.helpers import round_step_size
import json
import math
import ccxt as ccxt
from playsound import playsound
from requests import Session
from sklearn.preprocessing import MinMaxScaler
import numpy as np
import keras 
import pandas_ta as ta
import matplotlib.pyplot as plt

exchange_name=cons.exchange_name

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

def timeindex(df):
    # if you encounter a "year is out of range" error the timestamp
    # may be in milliseconds, try `ts /= 1000` in that case
    df['Indice']=(pd.to_datetime(df['Time']/1000,unit='s')) 
    df['Timestamp']=df.Indice
    df.set_index('Indice', inplace=True)

def calculardf (par,temporalidad):
    df = pd.DataFrame()
    while True:
        try:            
            barsindicators = cons.exchange.fetch_ohlcv(par,timeframe=temporalidad)
            df = pd.DataFrame(barsindicators,columns=['Time','Open','High','Low','Close','Volume'])
            timeindex(df) #Formatea el campo time para luego calcular las señales
            break
        except KeyboardInterrupt:
            print("\nSalida solicitada.")
            sys.exit()  
        except Exception as falla:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - par: "+par+"\n")
            print("\nIntento leer otra vez...\n")
            pass
    return df      

def sound(duration = 200, freq = 800):
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
      f = open(os.path.join(cons.pathroot,nombrelog), mode,encoding="utf-8")
      f.write("\n"+mensaje)
      f.close()   
   else:
      if pal==1: #solo log
         #escribo file
         f = open(os.path.join(cons.pathroot,nombrelog), mode,encoding="utf-8")
         f.write("\n"+mensaje)
         f.close()   

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
        if exchange_name=='binance':
            balance=float(cons.exchange.fetch_balance()['info']['totalWalletBalance'])
        if exchange_name=='kucoinfutures':
            balance=float(cons.exchange.fetch_balance()['info']['data']['marginBalance'])
        leido = True
      except:
         pass
   return balance

def getentryprice(par):
    leido = False
    entryprice=0.0
    while leido == False:
        try:
            if exchange_name=='binance':
                positions=cons.exchange.fetch_balance()['info']['positions']
                for index in range(len(positions)):
                    if positions[index]['symbol']==par:
                        entryprice=float(positions[index]['entryPrice'])
                        break
            if exchange_name=='kucoinfutures':
                position = cons.exchange.fetch_positions()
                for i in range(len(position)):
                    if position[i]['info']['symbol']==par:
                        entryprice=float(position[i]['info']['avgEntryPrice'])
                        break
            leido = True
        except:
            pass
    return entryprice

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

def leeconfiguracion(parameter='porcentajeentrada'):
    # Opening JSON file
    with open(os.path.join(cons.pathroot, "configuration.json"), 'r') as openfile: 
        # Reading from json file
        json_object = json.load(openfile)
    valor = json_object[parameter]        
    return valor 

def creoposicion (par,size,lado)->bool:         
    serror=True        
    try:
        apalancamiento=10
        if  exchange_name=='binance':    
            cons.client.futures_change_leverage(symbol=par, leverage=apalancamiento)
            try: 
                cons.client.futures_change_margin_type(symbol=par, marginType=cons.margen)
            except BinanceAPIException as a:
                if a.message!="No need to change margin type.":
                    print("Except 7",a.status_code,a.message)
                pass                    
            tamanio=truncate((size/currentprice(par)),get_quantityprecision(par))
            cons.client.futures_create_order(symbol=par,side=lado,type='MARKET',quantity=tamanio)
        if exchange_name=='kucoinfutures':
            cons.clienttrade.modify_auto_deposit_margin(par,status=True)
            multiplier=float(cons.clientmarket.get_contract_detail(par)['multiplier'])
            tamanio=str(int(size/(multiplier*currentprice(par))))
            cons.clienttrade.create_market_order(side=lado,symbol=par,type='market',size=tamanio,lever=apalancamiento)
            print("Con Kucoin espera para que de tiempo a actualizar...")
            waiting(5)
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

def get_positionamt(par): #monto en moneda local y con signo (no en usdt)
    leido = False
    positionamt = 0.0
    while leido == False:
        try:
            if exchange_name =='binance':
                position = cons.exchange.fetch_balance()['info']['positions']
                for i in range(len(position)):
                    if position[i]['symbol']==par:
                        positionamt=float(position[i]['positionAmt'])
                        break
            if exchange_name =='kucoinfutures':
                position = cons.exchange.fetch_positions()
                for i in range(len(position)):
                    if position[i]['info']['symbol']==par:
                        positionamt=float(position[i]['info']['currentQty'])
                        break
            leido = True
        except:
            pass
    return positionamt

def get_tick_size(symbol) -> float:
    tick_size = 0.0
    try:
        if exchange_name=='kucoinfutures':
            tick_size=float(cons.clientmarket.get_contract_detail(symbol)['tickSize'])
        if exchange_name=='binance':
            info = cons.client.futures_exchange_info()
            for symbol_info in info['symbols']:
                if symbol_info['symbol'] == symbol:
                    for symbol_filter in symbol_info['filters']:
                        if symbol_filter['filterType'] == 'PRICE_FILTER':
                            tick_size = float(symbol_filter['tickSize'])  
                            break
                    break
    except Exception as falla:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - par: "+symbol+"\n")
        pass  
    return tick_size

def get_rounded_price(symbol: str, price: float) -> float:
    return round_step_size(price, get_tick_size(symbol))

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

def creotakeprofit(par,preciolimit,posicionporc,lado):
    try:
        ### exchange details
        if exchange_name=='binance':
            sizedesocupar=abs(truncate((get_positionamt(par)*posicionporc/100),get_quantityprecision(par)))
        if exchange_name=='kucoinfutures':
            sizedesocupar=abs(int((get_positionamt(par)*posicionporc/100)))
            if sizedesocupar<1:
                sizedesocupar=1 # el size a desocupar no puede ser menor a 1 lot en kucoin
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

def creostoploss (symbol,side,stopprice,amount=0):   
    creado = False
    stopid = 0
    if side.upper() == 'BUY':
        side='SELL'
    else:
        if side.upper() =='SELL':
            side='BUY'
    try:
        if exchange_name=='binance':
            preciostop=truncate(stopprice,get_priceprecision(symbol))
            order=cons.client.futures_create_order(symbol=symbol,side=side,type='STOP_MARKET', timeInForce='GTC', closePosition='True', stopPrice=preciostop)
            print("\nStop loss creado. ",preciostop)
            creado = True
            stopid = order['orderId']
        if exchange_name=='kucoinfutures':
            preciostop=RoundToTickUp(symbol,stopprice)
            if amount==0:
                amount=abs(get_positionamt(symbol))
            else:
                amount=amount
            params ={'stopPrice': preciostop,
                    'closePosition': True}
            cons.exchange.create_order(
                symbol=symbol,
                side=side.lower(),
                type='market', # 'limit' for stop limit orders
                amount=amount,
                params=params,
            )
            print("\nStop loss creado. ",preciostop)
    except BinanceAPIException as a:
        print(a.message,"no se pudo crear el stop loss.")
        pass
    return creado,stopid    

def closeallopenorders (par):
    leido=False
    while leido==False:      
        try:
            if exchange_name=='binance':
                cons.client.futures_cancel_all_open_orders(symbol=par)
                leido=True
                print("\nÓrdenes binance cerradas. ")
            if exchange_name == 'kucoinfutures':
                cons.clienttrade.cancel_all_limit_order(par)
                cons.clienttrade.cancel_all_stop_order(par)
                leido=True
                print("\nÓrdenes kucoin cerradas. ")
        except:
            pass    

def pnl(par): 
    leido=False
    pnl=0.0  
    while leido == False:
        try:
            if exchange_name == 'kucoinfutures':
                #kucoin por ahora no tiene la funcion de pnl en ccxt
                pnl = cons.clienttrade.get_position_details(par)['unrealisedPnl']
                leido=True
            else:
                lista=[]
                lista.append(par)
                pnl=cons.exchange.fetchPositionsRisk(lista)[0]['unrealizedPnl'] 
                leido=True
        except:
            pass
    return pnl        

#descargar audio desde google translator
#from gtts import gTTS
#tts = gTTS('The team is liquidating tokens.')
#tts.save('liquidating.mp3')

def printenjson (dictionary={}):
    json_object = json.dumps(dictionary, indent=4)
    print(json_object)

def closeposition(symbol,side):
    if side=='SELL':
        lado='BUY'
    else:
        lado='SELL'
    quantity=abs(get_positionamt(symbol))
    if quantity!=0.0:
        try:
            cons.client.futures_create_order(symbol=symbol, side=lado, type='MARKET', quantity=quantity, reduceOnly='true')    
        except BinanceAPIException as a:
            print(a.message,"No se pudo cerrar la posición.")
            serror=False
            pass     
        except Exception as falla:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - par: "+symbol+"\n")
            serror=False
            pass 

def volumeOf24h(par): #en usdt
    vol=0.0
    if exchange_name == 'binance':
        vol= cons.client.futures_ticker(symbol=par)['quoteVolume']
    if exchange_name == 'kucoinfutures':
        datos=cons.exchange.fetch_markets()
        for i in range(len(datos)):
            if datos[i]['id']==par:
                vol=datos[i]['info']['volumeOf24h']*currentprice(par)
                break
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
    if exchange_name == 'kucoinfutures':
        if par == 'XBTUSDTM': # en kucoin BTC es 'XBTUSDTM'
            par = 'BTCUSDTM'
        par=par[0:-1]# si se eligió kucoin se le saca el ultimo caracter al símbolo.
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

def lista_de_monedas ():
    lista_de_monedas = []
    mazmorra = cons.mazmorra
    try:
        if exchange_name =='binance':
            exchange_info = cons.client.futures_exchange_info()['symbols'] #obtiene lista de monedas        
            for s in exchange_info:
                try:
                    if 'USDT' in s['symbol'] and '_' not in s['symbol'] and s['symbol'] not in mazmorra:
                        lista_de_monedas.append(s['symbol'])
                except Exception as ex:
                    pass    
        if exchange_name =='kucoinfutures':
            exchange_info = cons.clientmarket.get_contracts_list()
            for index in range(len(exchange_info)):
                try:
                    lista_de_monedas.append(exchange_info[index]['symbol'])
                except Exception as ex:
                    pass   
    except:
        print("\nError al obtener la lista de monedas...\n")
        pass
    return lista_de_monedas 

def get_posiciones_abiertas(): 
    leido = False
    dict_posiciones = {}
    while leido == False:
        try:
            if exchange_name =='binance':
                position = cons.exchange.fetch_balance()['info']['positions']
                for i in range(len(position)):
                    if float(position[i]['positionAmt'])!=0.0:
                        dict_posiciones[position[i]['symbol']]=position[i]['positionSide']
            leido = True
        except:
            pass
    return dict_posiciones

def obtiene_historial(symbol):
    client = cons.client
    timeframe='30m'
    leido=False
    n_steps = cons.n_steps
    while leido==False:
        try:
            historical_data = client.get_historical_klines(symbol, timeframe)
            leido = True
        except KeyboardInterrupt as ky:
            print("\nSalida solicitada. ")
            sys.exit()              
        except:
            print("Intento leer de nuevo...")
            pass
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
    stock_data = data
    pd.set_option('display.max_columns', None)    
    X_feat = stock_data.iloc[:,0:3]
    X_ft = MinMaxScaler(feature_range=(0, 1)).fit_transform(X_feat.values)
    X_ft = pd.DataFrame(columns=X_feat.columns,data=X_ft,index=X_feat.index)
    def ltsm_split (data,n_steps):
        X, y = [], []
        for i in range(len(data)-n_steps+1):
            X.append(data[i:i + n_steps, :-1])
            y.append(data[i + n_steps-1, -1])
        return np.array(X),np.array(y)
    X1, y1 = ltsm_split(X_ft.values, n_steps=n_steps)
    train_split =0.8
    split_idx = int(np.ceil(len(X1)*train_split))
    X_train , X_test = X1[:split_idx], X1[split_idx:]
    y_train , y_test = y1[:split_idx], y1[split_idx:]       
    return X_train,y_train,X_test,y_test,data

def estrategia(symbol,plot=False):
    n_steps = cons.n_steps
    umbralbajo=0.3
    umbralalto=0.7
    _,_,X_test,y_test,data=obtiene_historial(symbol)
    # CARGA EL MODELO GUARDADO Y PREDICE
    lstm = keras.models.load_model('predictor/modelos/lstm'+symbol+'.h5')
    y_pred = lstm.predict(X_test,verbose = 0)
    # CALCULOS
    deriv_y_pred2 = (np.diff(np.diff(y_pred, axis=0), axis=0)).reshape(-1, 1)
    deriv_y_pred_scaled2 = MinMaxScaler(feature_range=(0, 1)).fit_transform(deriv_y_pred2)
    deriv_y_pred_scaled2 = np.insert(deriv_y_pred_scaled2, 0, deriv_y_pred_scaled2[0], axis=0)#para mover 1 posicion hacia adelante
    deriv_y_pred_scaled2 = np.insert(deriv_y_pred_scaled2, 0, deriv_y_pred_scaled2[0], axis=0)#para mover 1 posicion hacia adelante
    data['ema20']=data.ta.ema(20)
    data['ema50']=data.ta.ema(50)
    data['ema200']=data.ta.ema(200)
    data['atr']=ta.atr(data.High, data.Low, data.Close)
    data=data.tail(200)
    data_copy = data.copy()
    data_copy['deriv'] = deriv_y_pred_scaled2
    data=data_copy
    data['signal']=  np.where( (data.ema20 > data.ema50) & (data.ema50 > data.ema200) & (data.deriv >= umbralalto) & (data.deriv.shift(1) > umbralbajo),1,
                (np.where( (data.ema20 < data.ema50) & (data.ema50 < data.ema200) & (data.deriv <= umbralbajo) & (data.deriv.shift(1) < umbralalto),-1,
                        0)))
    data['take_profit']=np.where(data.signal==1,data.Close+data.atr,np.where(data.signal==-1,data.Close-data.atr,0))
    data['stop_loss']=data.ema200
    # GRAFICA
    if plot==True:
        plt.figure(figsize=(14, 5))
        time_index = range(n_steps-1, n_steps-1+len(y_pred))
        for i in time_index:
            plt.axvline(x=i, color='lightgray')
        plt.xlim(0,len(y_test))
        plt.axhline(y = umbralalto, color = 'orange', linestyle = '-')
        plt.axhline(y = umbralbajo, color = 'orange', linestyle = '-')
        plt.plot(y_test, label='Close',color = 'black')
        plt.plot( y_pred[:, -1, 0], label='Prediction',color = 'blue')
        plt.plot( deriv_y_pred_scaled2, label='Derivative 2 (Scaled)', color='red')
        plt.xlabel('Time Scale')
        plt.ylabel('Scaled USDT')
        plt.legend()
        plt.gcf().autofmt_xdate()
        plt.title(symbol)
        plt.show()

    return data