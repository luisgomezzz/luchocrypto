import util
import pandas_ta as ta
from sklearn.preprocessing import MinMaxScaler
import numpy as np
from scipy.signal import argrelextrema

def estrategia_divergencias (symbol,timeframe,sma_length,sma_macd_length,umbral,largo):
    # Divergencias cuando adx es alto. Adx significa que hay tendencia (No está en rangueando)
    scaler = MinMaxScaler()
    data = util.obtiene_historial2(symbol=symbol, timeframe=timeframe, start_date='2024-01-01', end_date=None)
    data['sma'] = ta.sma(data.Close, length = sma_length) ##se puede variar
    data['sma_macd'] = ta.sma(ta.macd(data['Close'])['MACD_12_26_9'], length=sma_macd_length) ##se puede variar
    # Escalar los indicadores al rango del precio
    data[['Indicator1', 'Indicator2']] = scaler.fit_transform(data[['sma', 'sma_macd']])
    price_range = data['Close'].max() - data['Close'].min()
    data['Indicator1'] = data['Indicator1'] * price_range + data['Close'].min()
    data['Indicator2'] = data['Indicator2'] * price_range + data['Close'].min()
    porcentaje_perdida = 1
    data['adx'] = ta.adx(high=data.High, low=data.Low, close=data.Close, length=largo).iloc[:, 0]
    ##################################    obligatorios ##############  --->>>  trade, stop_loss, take_profit, porcentajeentrada
    ###########################################################################################################################
    data['trade'] = np.where(util.crossover_dataframe(data.Indicator2, data.Indicator1) & (data.adx >=umbral)
                             ,-1,np.where(util.crossover_dataframe(data.Indicator1, data.Indicator2) & (data.adx >=umbral)
                                          ,-2,-1.5))
    data['stop_loss'] = np.where(data.trade==-1,data.Close-data.atr*3,np.where(data.trade==-2,data.Close+data.atr*3,0))
    variacion_hasta_stop_loss = np.where(data.trade==-1,(((data.stop_loss/data.Close)-1)*-100),np.where(data.trade==-2,(((data.stop_loss/data.Close)-1)*100),0))
    data['take_profit'] = None#np.where(data.trade==-1,data.Close+data.atr*9,np.where(data.trade==-2,data.Close-data.atr*9,0))
    data['porcentajeentrada'] = np.where(((porcentaje_perdida/variacion_hasta_stop_loss))>=1,0.99,((porcentaje_perdida/variacion_hasta_stop_loss)))
    return data

def estrategia_lucho (symbol,timeframe):
    data = util.obtiene_historial2(symbol=symbol, timeframe=timeframe, start_date='2024-01-01', end_date=None)
    data['Indicator1'] = ta.ema(data.Close, length = 200)
    data['Indicator2'] = ta.sma(data.Close, length = 200)    
    ##################################    obligatorios ##############  --->>>  trade, stop_loss, take_profit, porcentajeentrada
    ###########################################################################################################################
    porcentaje_perdida = 1
    data['trade'] = np.where(util.crossover_dataframe(data.Indicator1, data.Indicator2) 
                             ,-1,np.where(util.crossover_dataframe(data.Indicator2, data.Indicator1) 
                                          ,-2,-1.5))
    data['stop_loss'] = np.where(data.trade==-1,data.Close-data.atr*4,np.where(data.trade==-2,data.Close+data.atr*4,0))
    variacion_hasta_stop_loss = np.where(data.trade==-1,(((data.stop_loss/data.Close)-1)*-100),np.where(data.trade==-2,(((data.stop_loss/data.Close)-1)*100),0))
    data['take_profit'] = np.where(data.trade==-1,data.Close+data.atr*8,np.where(data.trade==-2,data.Close-data.atr*8,0))
    data['porcentajeentrada'] = np.where(((porcentaje_perdida/variacion_hasta_stop_loss))>=1,0.99,((porcentaje_perdida/variacion_hasta_stop_loss)))
    return data

def estrategia_adx (symbol,timeframe,length_sma = 50, order = 550, length_adx = 100):
    data = util.obtiene_historial2(symbol=symbol, timeframe=timeframe, start_date='2023-09-01', end_date=None)
    multiplicador_tp = 7
    data['Indicator1'] = None
    data['Indicator2'] = ta.sma(data.Close, length = length_sma)
    data['adx'] = ta.adx(high=data.High, low=data.Low, close=data.Close, length = length_adx).iloc[:, 0]
    # Encontrar los índices de los mínimos locales en la columna 'adx'
    min_indices = argrelextrema(data['adx'].values, np.less,order=order)[0]
    data['pico_inferior'] = np.nan
    # Marcar los picos inferiores en la columna 'pico_inferior' usando iloc
    data.iloc[min_indices, data.columns.get_loc('pico_inferior')] = data.iloc[min_indices, data.columns.get_loc('adx')]
    umbral=np.ceil(data['pico_inferior'].iloc[min_indices].mean())
    data['adx_condicion'] = np.where((data.adx >= umbral) & (data.adx.shift(1) < umbral), True, False)
    ##################################    obligatorios ##############  --->>>  trade, stop_loss, take_profit, porcentajeentrada, cerrar
    ###########################################################################################################################
    porcentaje_perdida = 1
    data['trade'] = np.where(data.adx_condicion, np.where((data.Close < data.Indicator2), -2, np.where((data.Close > data.Indicator2), -1, -1.5)), -1.5)
    data['stop_loss'] = np.where((data.trade!=-1.5) & data.Indicator2.notna(), data.Indicator2
                                 ,np.where(data.trade==-1,data.Close-data.atr*4
                                           ,np.where(data.trade==-2,data.Close+data.atr*4,0)))
    variacion_hasta_stop_loss = np.where(data.trade==-1,(((data.stop_loss/data.Close)-1)*-100),np.where(data.trade==-2,(((data.stop_loss/data.Close)-1)*100),0))
    data['take_profit'] = np.where(data.trade==-1,data.Close*(1+(variacion_hasta_stop_loss*multiplicador_tp/100)),np.where(data.trade==-2,data.Close*(1-(variacion_hasta_stop_loss*multiplicador_tp/100)),0))
    data['porcentajeentrada'] = np.where(((porcentaje_perdida/variacion_hasta_stop_loss))>=1,0.99,((porcentaje_perdida/variacion_hasta_stop_loss)))
    data['cerrar'] = np.where(util.crossover_dataframe(data.Close, data.Indicator2) | util.crossover_dataframe(data.Indicator2, data.Close), True, False)
    #print(f'umbral: {umbral}')
    return data