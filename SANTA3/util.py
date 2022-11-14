import sys
import pandas as pd
import variables as var
import os
import winsound as ws
import math
from time import sleep
from binance.exceptions import BinanceAPIException
from binance.helpers import round_step_size
from requests import Session
import json
import math
import ccxt as ccxt

exchange_name=var.exchange_name

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

def lista_de_monedas ():
    lista_de_monedas = []
    if exchange_name =='binance':
        exchange_info = var.client.futures_exchange_info()['symbols'] #obtiene lista de monedas        
        for s in exchange_info:
            try:
                if 'USDT' in s['symbol']:
                    lista_de_monedas.append(s['symbol'])
            except Exception as ex:
                pass    
    if exchange_name =='kucoinfutures':
        exchange_info = var.clientmarket.get_contracts_list()
        for index in range(len(exchange_info)):
            try:
                lista_de_monedas.append(exchange_info[index]['symbol'])
            except Exception as ex:
                pass   
    return lista_de_monedas  

def timeindex(df):
    # if you encounter a "year is out of range" error the timestamp
    # may be in milliseconds, try `ts /= 1000` in that case
    df['time2']=df['time']/1000
    df['time3']=(pd.to_datetime(df['time2'],unit='s')) 
    df.set_index(pd.DatetimeIndex(df["time3"]), inplace=True)

def calculardf (par,temporalidad,ventana):
    df = pd.DataFrame()
    try:
        barsindicators = var.exchange.fetch_ohlcv(par,timeframe=temporalidad,limit=ventana)
        df = pd.DataFrame(barsindicators,columns=['time','open','high','low','close','volume'])
        timeindex(df) #Formatea el campo time para luego calcular las señales
    except KeyboardInterrupt:
        print("\nSalida solicitada.")
        sys.exit()  
    except Exception as falla:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - par: "+par+"\n")
    return df      

def equipoliquidando ():
    listademonedas = lista_de_monedas()
    mazmorra=['1000SHIBUSDT','1000XECUSDT','BTCDOMUSDT','FOOTBALLUSDT'
    ,'DEFIUSDT','1000LUNCUSDT','LUNA2USDT','BLUEBIRDUSDT'] #Monedas que no quiero operar (muchas estan aqui porque fallan en algun momento al crear el dataframe)         
    listaequipoliquidando=[]
    temporalidad='1d'
    ventana = 30
    variacionporc = 10
    for par in listademonedas:
        try:            
            sys.stdout.write("\r"+par+"\033[K")
            sys.stdout.flush()   
            if ('USDT' in par and '_' not in par and par not in mazmorra ):
                df=calculardf (par,temporalidad,ventana)
                df['liquidando'] = (df.close >= df.open*(1+variacionporc/100)) & (df.high - df.close >= df.close-df.open) 
                if True in set(df['liquidando']):
                    listaequipoliquidando.append(par)                    
        except Exception as ex:
            pass        
        except KeyboardInterrupt as ky:
            print("\nSalida solicitada. ")
            sys.exit()           
    return listaequipoliquidando      

def volumeOf24h(par): #en usdt
    vol=0.0
    if exchange_name == 'binance':
        vol= var.client.futures_ticker(symbol=par)['quoteVolume']
    if exchange_name == 'kucoinfutures':
        datos=var.exchange.fetch_markets()
        for i in range(len(datos)):
            if datos[i]['id']==par:
                vol=datos[i]['info']['volumeOf24h']*currentprice(par)
                break
    return float(vol)

def sound(duration = 2000,freq = 440):
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
      f = open(os.path.join(var.pathroot,nombrelog), mode,encoding="utf-8")
      f.write("\n"+mensaje)
      f.close()   
   else:
      if pal==1: #solo log
         #escribo file
         f = open(os.path.join(var.pathroot,nombrelog), mode,encoding="utf-8")
         f.write("\n"+mensaje)
         f.close()   

def currentprice(par):
    leido = False
    current=0.0
    while leido == False:
        try:
            if exchange_name=='binance':
                current=float(var.client.get_symbol_ticker(symbol=par)["price"])
            if exchange_name=='kucoinfutures':
                current=float(var.clientmarket.get_ticker(par)['price'])
            leido = True
        except:
            pass
    return current

def balancetotal():
   leido = False
   while leido == False:
      try:
        if exchange_name=='binance':
            balance=float(var.exchange.fetch_balance()['info']['totalWalletBalance'])
        if exchange_name=='kucoinfutures':
            balance=float(var.exchange.fetch_balance()['info']['data']['marginBalance'])
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
                positions=var.exchange.fetch_balance()['info']['positions']
                for index in range(len(positions)):
                    if positions[index]['symbol']==par:
                        entryprice=float(positions[index]['entryPrice'])
                        break
            if exchange_name=='kucoinfutures':
                position = var.exchange.fetch_positions()
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
            info = var.client.futures_exchange_info()
            leido = True
        except:
            pass 
    for x in info['symbols']:
        if x['symbol'] == par:
            quantityprecision= x['quantityPrecision']
            break
    return quantityprecision

def creoposicion (par,size,lado)->bool:         
    serror=True            
    try:
        if  exchange_name=='binance':      
            var.client.futures_change_leverage(symbol=par, leverage=var.apalancamiento)
            try: 
                var.client.futures_change_margin_type(symbol=par, marginType=var.margen)
            except BinanceAPIException as a:
                if a.message!="No need to change margin type.":
                    print("Except 7",a.status_code,a.message)
                pass                    
            tamanio=truncate((size/currentprice(par)),get_quantityprecision(par))
            var.client.futures_create_order(symbol=par,side=lado,type='MARKET',quantity=tamanio)
        if exchange_name=='kucoinfutures':
            var.clienttrade.modify_auto_deposit_margin(par,status=True)
            multiplier=float(var.clientmarket.get_contract_detail(par)['multiplier'])
            tamanio=str(int(size/(multiplier*currentprice(par))))
            maxLeverage = var.clientmarket.get_contract_detail(par)['maxLeverage']
            if maxLeverage < var.apalancamiento:
                apalancamiento=int(maxLeverage)
            else:
                apalancamiento=int(var.apalancamiento)
            var.clienttrade.create_market_order(side=lado,symbol=par,type='market',size=tamanio,lever=apalancamiento)
            print("Con Kucoin espera para que de tiempo a actualizar...")
            waiting(5)
        print("Posición creada. ",tamanio)
    except BinanceAPIException as a:
        print("Falla al crear la posición. Error: ",a.message) 
        serror=False
        pass
    except Exception as falla:
        exc_type, exc_obj, exc_tb = sys.exc_info()
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
                position = var.exchange.fetch_balance()['info']['positions']
                for i in range(len(position)):
                    if position[i]['symbol']==par:
                        positionamt=float(position[i]['positionAmt'])
                        break
            if exchange_name =='kucoinfutures':
                position = var.exchange.fetch_positions()
                for i in range(len(position)):
                    if position[i]['info']['symbol']==par:
                        positionamt=float(position[i]['info']['currentQty'])*float(var.clientmarket.get_contract_detail(par)['multiplier'])
                        break
            leido = True
        except:
            pass
    return positionamt

def get_positionamtusdt(par):
    precioactualusdt=currentprice(par)
    positionamt=get_positionamt(par)
    tamanioposusdt=positionamt*precioactualusdt
    return tamanioposusdt    

def get_tick_size(symbol) -> float:
    tick_size = 0.0
    try:
        if exchange_name=='kucoinfutures':
            tick_size=float(var.clientmarket.get_contract_detail(symbol)['tickSize'])
        if exchange_name=='binance':
            info = var.client.futures_exchange_info()
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
            info = var.client.futures_exchange_info()
            leido = True
        except:
            pass 
    for x in info['symbols']:
        if x['symbol'] == par:
            priceprecision= x['pricePrecision']  
            break         
    return priceprecision

def compensaciones(par,client,lado,tamanio,distanciaporc):
    if lado =='SELL':
        preciolimit = getentryprice(par)*(1+(distanciaporc/100))   
    else:
        preciolimit = getentryprice(par)*(1-(distanciaporc/100))
    limitprice=RoundToTickUp(par,preciolimit)
    try:
        if exchange_name=='binance':
            tamanioformateado = truncate(abs(tamanio),get_quantityprecision(par))
            order=client.futures_create_order(symbol=par, side=lado, type='LIMIT', timeInForce='GTC', quantity=tamanioformateado,price=limitprice)      
            return True,float(order['price']),float(order['origQty']),order['orderId']
        if exchange_name=='kucoinfutures':                
            tamanioformateado = int(tamanio)
            maxLeverage = var.clientmarket.get_contract_detail(par)['maxLeverage']
            if maxLeverage < var.apalancamiento:
                apalancamiento=int(maxLeverage)
            else:
                apalancamiento=int(var.apalancamiento)
            i=0
            creada=False
            while creada==False:                        
                try:
                    order=var.clienttrade.create_limit_order(symbol=par, side=lado, size=tamanioformateado,price=limitprice,lever=apalancamiento)
                    detalle=(var.clienttrade.get_order_details(order['orderId']))
                    creada=True
                    return True,float(detalle['price']),float(detalle['size']),order['orderId']
                except ccxt.RateLimitExceeded as e:
                    now = var.exchange.milliseconds()
                    datetime = var.exchange.iso8601(now)
                    print(datetime, i, type(e).__name__, str(e))
                    var.exchange.sleep(10000)
                except Exception as e:
                    print(type(e).__name__, str(e))
                    raise e
                i += 1
    except BinanceAPIException as a:                                       
        print("Except 8",a.status_code,a.message)
        return False,0,0,0     
    except Exception as falla:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - par: "+par+"\n")
        return False,0,0,0

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
        order=var.client.futures_create_order(symbol=par, side=lado, type='LIMIT', timeInForce='GTC', quantity=sizedesocupar,price=limitprice)
        print("\nLimit creado. Tamanio a desocupar: ",sizedesocupar,". precio: ",limitprice)
        creado= True
    except BinanceAPIException as a:
        print(a.message,"No se pudo crear el Limit.")
        creado = False      
        order = 0
        pass
    return creado,order        

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

def creostoploss (pair,side,stopprice):   
    creado = False
    stopid = 0
    if side == 'BUY':
        side='SELL'
    else:
        side='BUY'
    try:
        if exchange_name=='binance':
            preciostop=truncate(stopprice,get_priceprecision(pair))
            order=var.client.futures_create_order(symbol=pair,side=side,type='STOP_MARKET', timeInForce='GTC', closePosition='True', stopPrice=preciostop)
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
            if exchange_name=='binance':
                var.client.futures_cancel_all_open_orders(symbol=par)
                leido=True
                print("\nÓrdenes binance cerradas. ")
            if exchange_name == 'kucoinfutures':
                var.clienttrade.cancel_all_limit_order(par)
                var.clienttrade.cancel_all_stop_order(par)
                leido=True
                print("\nÓrdenes kucoin cerradas. ")
        except:
            pass    

def pnl(par):   
    precioentrada = getentryprice(par)
    if precioentrada !=0.0:
        try:
            tamanio = get_positionamtusdt(par)
            precioactual = currentprice(par)
            pnl = ((precioactual/precioentrada)-1)*tamanio
        except Exception as ex:
            pnl = 0
            pass               
    else:
        pnl = 0   
    return pnl        

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
    if exchange_name == 'kucoinfutures':# si se eligió kucoin se le saca el ultimo caracter al símbolo.
        par=par[0:-1]
    clientcap = var.binanceClient(var.binance_key, var.binance_secret,var.binance_passphares) 
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