# DOCUMENTACION DE BINANCE: https://binance-docs.github.io/apidocs/futures/en/#change-log

import constantes as cons
import requests
import hmac
import hashlib
import time
import pandas_ta as ta
from backtesting import Strategy
import numpy as np
import pandas as pd
from binance.exceptions import BinanceAPIException
import sys
import os
import warnings
import winsound as ws
import math
from binance.client import Client as binanceClient
import ccxt as ccxt

def sound(duration = 200, freq = 800):
    # milliseconds
    # Hz
    # for windows
    if os.name == 'nt':
        ws.Beep(freq, duration)
    # for mac and linux(here, os.name is 'posix')
    else:
        _ = os.system('play -nq -t alsa synth %s sin %s' % (duration/1000, freq))

def warn(*args, **kwargs):
    pass
warnings.warn = warn
np.seterr(divide='ignore')

API_KEY = cons.api_key
API_SECRET = cons.api_secret
BASE_URL = 'https://fapi.binance.com'

# Función para firmar los parámetros
def sign_request(params, secret):
    query_string = '&'.join([f"{key}={params[key]}" for key in sorted(params)])
    return hmac.new(secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

# Algunos endpoints
'/fapi/v1/symbolConfig' #: Query user symbol configuration.
'/fapi/v1/accountConfig' #Query user account configuration.
'/fapi/v3/account' # this endpoint only returns symbols that the user has positions or open orders in. Configuration-related fields have been removed and can now be queried from GET /fapi/v1/symbolConfig and GET /fapi/v1/accountConfig. The V3 endpoint also offers better performance.
'/fapi/v3/balance' # Query user account balance.
'/fapi/v3/positionRisk' #: Compared to GET /fapi/v2/positionRisk, this endpoint only returns symbols that the user has positions or open orders in. Configuration-related fields have been removed and can now be queried from GET /fapi/v1/symbolConfig. The V3 endpoint also offers better performance.
'/fapi/v1/ping' # Test

# Función para obtener información
def get_info(endpoint, **kwargs):
    timestamp = int(time.time() * 1000)
    params = {'timestamp': timestamp}
    # Añadir cualquier otro parámetro recibido en kwargs
    params.update(kwargs)
    # Añadir la firma a los parámetros
    params['signature'] = sign_request(params, API_SECRET)
    headers = {
        'X-MBX-APIKEY': API_KEY
    }
    response = requests.get(BASE_URL + endpoint, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

def obtiene_historial(symbol,timeframe,limit=1000):
    leido = False
    while leido == False:
        try:
            historical_data = get_info(endpoint='/fapi/v1/klines',symbol=symbol,interval=timeframe,limit=limit)
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
            data.drop(['Close Time','Quote Asset Volume','TB Base Volume','TB Quote Volume','Number of Trades','Ignore'],axis=1,inplace=True)
            data['atr'] = ta.atr(data.High, data.Low, data.Close)        
        except KeyboardInterrupt:        
            print("\nSalida solicitada. ")
            sys.exit()
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

def indicador(df_campo):
    indi=pd.Series(df_campo)
    return indi.to_numpy()

def crossover_dataframe(column1, column2):
    upward_crossover = (column1 > column2) & (column1.shift(1) <= column2.shift(1))
    return upward_crossover

class backtesting_config(Strategy):
    def init(self):
        self.indicador1 = self.I(indicador, self.data.Indicator1,name='indicador1', color='black', overlay=True, scatter=False)
        self.indicador2 = self.I(indicador, self.data.Indicator2,name='indicador2', color='grey', overlay=True, scatter=False)
        # Obligatorios
        self.trade = self.I(indicador, self.data.trade,name='trade', color='black', overlay=False, scatter=False)
        self.porcentajeentrada = self.I(indicador, self.data.porcentajeentrada, name='porcentajeentrada', color='Black', overlay=False, scatter=False)
        self.stop_loss = self.I(indicador, self.data.stop_loss, name='stop_loss', color='darkorange', overlay=True, scatter=True)
        self.take_profit = self.I(indicador, self.data.take_profit, name='take_profit', color='darkblue', overlay=True, scatter=True)        
    def next(self):
        # POR TURNOS    
        #if self.position:  
        #    if self.position.is_long:
        #        if self.trade == -2:
        #            self.position.close()
        #    elif self.trade == -1:
        #            self.position.close()
        #else:
            # PERPETUO
            if self.trade == -1:
                self.buy(
                    size=self.porcentajeentrada[-1]
                    ,sl=self.stop_loss[-1]
                    ,tp=self.take_profit[-1]
                )
            elif self.trade == -2:
                self.sell(
                    size=self.porcentajeentrada[-1]
                    ,sl=self.stop_loss[-1]
                    ,tp=self.take_profit[-1]
                )

def get_posiciones_abiertas(): 
    leido = False
    posiciones_abiertas = {}
    while leido == False:
        try:
            position = get_info('/fapi/v3/account')['positions']
            for i in range(len(position)):
                if float(position[i]['positionAmt'])!=0.0:
                    side = "BUY" if float(position[i]['positionAmt']) > 0 else "SELL"
                    posiciones_abiertas[position[i]['symbol']]=side
            leido = True
        except:
            pass
    return posiciones_abiertas

def get_positionamt(par): #monto en moneda local y con signo (no en usdt)
    leido = False
    positionamt = 0.0
    while leido == False:
        try:
            position = get_info('/fapi/v3/account')['positions']
            for i in range(len(position)):
                if position[i]['symbol']==par:
                    positionamt=float(position[i]['positionAmt'])
                    break
            leido = True
        except:
            pass
    return positionamt

def currentprice(symbol):
    leido = False
    current=0.0
    while leido == False:
        try:
            current=float(get_info('/fapi/v2/ticker/price',symbol='OPUSDT')['price'])
            leido = True
        except:
            pass
    return current

def get_quantityprecision(symbol):
    leido=False
    quantityprecision=0
    while leido == False:
        try:   
            info = get_info('/fapi/v1/exchangeInfo')
            leido = True
        except:
            pass 
    for x in info['symbols']:
        if x['symbol'] == symbol:
            quantityprecision= x['quantityPrecision']
            break
    return quantityprecision

def truncate(number, digits) -> float:
    stepper = 10.0 ** digits
    return math.trunc(stepper * number) / stepper

api_passphares=''
exchange_name = 'binance'
client = binanceClient(API_KEY, API_SECRET, api_passphares)
exchange_class = getattr(ccxt, exchange_name)
exchange =   exchange_class({            
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'password': api_passphares,
            'options': {  
            'defaultType': 'future',  
            },
            })

def crea_posicion(symbol,side,micapital,porcentajeentrada):   
    size = float(micapital*porcentajeentrada)
    try:
        tamanio=truncate((size/currentprice(symbol)),get_quantityprecision(symbol))
        client.futures_create_order(symbol=symbol,side=side,type='MARKET',quantity=tamanio)        
        print("Posición creada. ",tamanio)
    except Exception as falla:
        _, _, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - par: "+symbol+"\n")
        pass

def closeposition(symbol,side):
    if side=='SELL':
        lado='BUY'
    else:
        lado='SELL'
    quantity=abs(get_positionamt(symbol))
    if quantity!=0.0:
        client.futures_create_order(symbol=symbol, side=lado, type='MARKET', quantity=quantity, reduceOnly='true')  
        print(f"posición cerrada. ")