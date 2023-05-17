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

def get_cantidad_posiciones(): 
    leido = False
    cantidad_posiciones = 0
    while leido == False:
        try:
            if exchange_name =='binance':
                position = cons.exchange.fetch_balance()['info']['positions']
                for i in range(len(position)):
                    if float(position[i]['positionAmt'])!=0.0:
                        cantidad_posiciones=cantidad_posiciones+1
            leido = True
        except:
            pass
    return cantidad_posiciones