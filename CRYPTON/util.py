# DOCUMENTACION DE BINANCE: https://binance-docs.github.io/apidocs/futures/en/#change-log

import constantes as cons
import requests
import hmac
import hashlib
import time
import pandas_ta as ta
from backtesting import Strategy, Backtest
import numpy as np
import pandas as pd
from binance.exceptions import BinanceAPIException
import sys
import os
import warnings

def warn(*args, **kwargs):
    pass
warnings.warn = warn
np.seterr(divide='ignore')

salida_solicitada_flag = False

def salida_solicitada():    
    global salida_solicitada_flag
    salida_solicitada_flag = True

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
            data.drop(['Close Time','Quote Asset Volume', 'TB Base Volume', 'TB Quote Volume','Number of Trades',
                    'Ignore'], axis=1, inplace=True)    
            data['ema20'] = ta.ema(data.Close, length=20)
            data['ema50'] = ta.ema(data.Close, length=50)
            data['ema200'] = ta.ema(data.Close, length=200)
            data['sma200'] = ta.sma(data.Close, length=200)
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

def indicador(df_campo):
    indi=pd.Series(df_campo)
    return indi.to_numpy()