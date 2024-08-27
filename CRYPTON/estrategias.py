import util
import pandas_ta as ta
from sklearn.preprocessing import MinMaxScaler
import numpy as np

def estrategia_divergencias (symbol,timeframe,limit,sma_length,sma_macd_length):
    scaler = MinMaxScaler()
    data = util.obtiene_historial(symbol=symbol,timeframe=timeframe,limit=limit)    
    data['sma'] = ta.sma(data.Close, length = sma_length) ##se puede variar
    data['sma_macd'] = ta.sma(ta.macd(data['Close'])['MACD_12_26_9'], length=sma_macd_length) ##se puede variar
    # Escalar los indicadores al rango del precio
    data[['Indicator1', 'Indicator2']] = scaler.fit_transform(data[['sma', 'sma_macd']])
    price_range = data['Close'].max() - data['Close'].min()
    data['Indicator1'] = data['Indicator1'] * price_range + data['Close'].min()
    data['Indicator2'] = data['Indicator2'] * price_range + data['Close'].min()
    porcentaje_perdida = 1
    ##################################    obligatorios ##############  --->>>  trade, stop_loss, take_profit, porcentajeentrada
    ###########################################################################################################################
    data['trade'] = np.where(util.crossover_dataframe(data.Indicator2, data.Indicator1),-1,np.where(util.crossover_dataframe(data.Indicator1, data.Indicator2),-2,-1.5))
    data['stop_loss'] = np.where(data.trade==-1,data.Close-data.atr*3,np.where(data.trade==-2,data.Close+data.atr*3,0))
    variacion_hasta_stop_loss = abs(((data.stop_loss/data.Close)-1)*100)
    data['take_profit'] = None #np.where(data.trade==-1,data.Close+data.atr*6,np.where(data.trade==-2,data.Close-data.atr*6,0))
    data['porcentajeentrada'] = np.where(((porcentaje_perdida/variacion_hasta_stop_loss))>=1,0.99,((porcentaje_perdida/variacion_hasta_stop_loss)))        ##
    return data