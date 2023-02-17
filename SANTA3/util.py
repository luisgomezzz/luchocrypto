import sys
import pandas as pd
import constantes as cons
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
from numerize import numerize

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

def timeindex(df):
    # if you encounter a "year is out of range" error the timestamp
    # may be in milliseconds, try `ts /= 1000` in that case
    df['time2']=df['time']/1000
    df['time3']=(pd.to_datetime(df['time2'],unit='s')) 
    df.set_index(pd.DatetimeIndex(df["time3"]), inplace=True)

def calculardf (par,temporalidad,ventana):
    df = pd.DataFrame()
    while True:
        try:            
            barsindicators = cons.exchange.fetch_ohlcv(par,timeframe=temporalidad,limit=ventana)
            df = pd.DataFrame(barsindicators,columns=['time','open','high','low','close','volume'])
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

def equipoliquidando ():
    listademonedas = lista_de_monedas()
    dict={'inicio':[0,0]}
    dict.clear()
    temporalidad='1d'
    ventana = 30
    variacionporc = 10
    for par in listademonedas:
        try:            
            sys.stdout.write("\r"+par+"\033[K")
            sys.stdout.flush()   
            if 'USDT' in par:
                df=calculardf (par,temporalidad,ventana)
                df['liquidando'] = (df.close >= df.open*(1+variacionporc/100)) & (df.high - df.close >= df.close-df.open) 
                if True in set(df['liquidando']):
                    dict[par]=[max(df.close),max(df.high)]
        except Exception as ex:
            pass        
        except KeyboardInterrupt as ky:
            print("\nSalida solicitada. ")
            sys.exit()           
    return dict      

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

def apalancamientoseguncapital(symbol):
    apalancamiento=0
    try:
        capitalapalancado = cons.apalancamientoreal*balancetotal()
        result= cons.client.futures_leverage_bracket()
        for x in range(len(result)):
            if result[x]['symbol'] == symbol:
                lista =  result[x]['brackets']
                for y in range(len(lista)):
                    if lista[y]['notionalCap'] > capitalapalancado:# and lista[y]['initialLeverage']>=cons.apalancamientoreal:
                        apalancamiento = lista[y]['initialLeverage']
                        break
    except:
        apalancamiento=0
        print("\nNo hay valores de apalancamiento y notionalcap compatibles con la estrategia. "+symbol+"\n")
    return(apalancamiento)

def creoposicion (par,size,lado)->bool:         
    serror=True        
    try:
        apalancamiento=apalancamientoseguncapital(par)
        if apalancamiento < cons.apalancamientoreal:
            micapital = balancetotal()
            size = float(micapital*5/100)
            printandlog(cons.nombrelog,"Porcentaje de entrada redefinido al 5%: "+str(size))
        printandlog(cons.nombrelog,"Apalancamiento: "+str(apalancamiento))        
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

def get_positionamtusdt(par):
    precioactualusdt=currentprice(par)
    positionamt=get_positionamt(par)
    tamanioposusdt=positionamt*precioactualusdt
    return tamanioposusdt    

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
        if exchange_name=='kucoinfutures':   ##revisar kucoin porque cambió la lógica de elección de leverage.
            apalancamiento=leeconfiguracion("apalancamiento")              
            tamanioformateado = int(tamanio)
            maxLeverage = cons.clientmarket.get_contract_detail(par)['maxLeverage']
            if maxLeverage < apalancamiento:
                apalancamiento=int(maxLeverage)
            else:
                apalancamiento=int(apalancamiento)
            i=0
            creada=False
            while creada==False:                        
                try:
                    order=cons.clienttrade.create_limit_order(symbol=par, side=lado, size=tamanioformateado,price=limitprice,lever=apalancamiento)
                    detalle=(cons.clienttrade.get_order_details(order['orderId']))
                    creada=True
                    return True,float(detalle['price']),float(detalle['size']),order['orderId']
                except ccxt.RateLimitExceeded as e:
                    now = cons.exchange.milliseconds()
                    datetime = cons.exchange.iso8601(now)
                    print(datetime, i, type(e).__name__, str(e))
                    cons.exchange.sleep(10000)
                    pass
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
        apalancamiento=apalancamientoseguncapital(par)
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

def get_preciostopvelavela (par,lado,temporalidad):
    porc=0.2 #porcentaje de distancia 
    cantidad = 0
    while cantidad!=2:# se asegura q traiga 2 registros para que pueda calcular el color de las velas
        df=calculardf (par,temporalidad,2) 
        cantidad=len(df)
    if df.open.iloc[-2]<df.close.iloc[-2]:
        colorvelaanterior='verde'
    else:
        if df.open.iloc[-2]>df.close.iloc[-2]:
            colorvelaanterior='rojo'
        else:        
            colorvelaanterior='nada'
    if lado=='SELL' and colorvelaanterior=='rojo':
        preciostopvelavela=df.high.iloc[-2]*(1+porc/100)
    else:
        if lado=='BUY' and colorvelaanterior=='verde':
            preciostopvelavela=df.low.iloc[-2]*(1-porc/100)
        else:
            preciostopvelavela=0.0
    return preciostopvelavela    

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
            print("Stop loss creado. ",preciostop)
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
                print("Órdenes binance cerradas. ")
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
    clientcap = cons.binanceClient(cons.binance_key, cons.binance_secret,cons.binance_passphares) 
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

def construye_tabla_formatos():
    for estilo in range(8):
        for colortexto in range(30,38):
            cad_cod = ''
            for colorfondo in range(40,48): 
                fmto = ';'.join([str(estilo), 
                                 str(colortexto),
                                 str(colorfondo)]) 
                cad_cod+="\033["+fmto+"m "+fmto+" \033[0m" 
            print(cad_cod)
        print('\n')

def rankingcap (lista_de_monedas):
    dict = {        
            'nada' : 0.0
    }
    dict.clear()
    for s in lista_de_monedas:
        try:  
            par = s
            dict[par] = capitalizacion(par)
        except Exception as ex:
            pass        
        except KeyboardInterrupt as ky:
            print("\nSalida solicitada. ")
            sys.exit()
    ranking= (sorted([(v, k) for k, v in dict.items()], reverse=True))      
    for index in range(len(lista_de_monedas)):
        print(str(ranking[index][1])+' - '+str(numerize.numerize(ranking[index][0])))

#descargar audio desde google translator
#from gtts import gTTS
#tts = gTTS('The team is liquidating tokens.')
#tts.save('liquidating.mp3')

def printenjson (dictionary={}):
    json_object = json.dumps(dictionary, indent=4)
    print(json_object)