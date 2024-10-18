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

def estrategia_adx (symbol,timeframe,length_sma = 50, order = 550, length_adx = 90, start_date='2023-09-01'):
    try:
        data = util.obtiene_historial2(symbol=symbol, timeframe=timeframe, start_date = start_date, end_date=None)
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
    except Exception as e:
        print(f"Error en {symbol}: {e}")
    return data

def es_martillo(vela):
    out = 0
    cuerpo = abs(vela['Open'] - vela['Close'])
    sombra_superior = vela['High'] - max(vela['Open'], vela['Close'])
    sombra_inferior = min(vela['Open'], vela['Close']) - vela['Low']
    condicion_largo = (vela.High-vela.Low) >= vela.atr
    if condicion_largo:
        if sombra_inferior>sombra_superior*3:
            if sombra_inferior > 2 * cuerpo: #martillo parado
                out = 1
        else:
            if sombra_superior>sombra_inferior*3:
                if sombra_superior > 2 * cuerpo: #martillo invertido
                    out = -1
    return out 

def color_vela(vela):
    color = 'negro'
    color = np.where(vela['Open'] > vela['Close'],'rojo','verde')
    return color

def estrategia_martillo (symbol,timeframe='15m',start_date='2024-09-01'):
    try:
        data = util.obtiene_historial2(symbol=symbol, timeframe=timeframe, start_date = start_date, end_date=None)
        multiplicador_tp = 7
        data['Indicator1'] = None
        data['Indicator2'] = None
        data['martillo'] = data.apply(es_martillo, axis=1)  # 1: martillo parado * -1: martillo invertido   
        data['disparo'] = np.where(data.martillo == 1,data.High,np.where(data.martillo == -1,data.Low,0))
                #relleno
        data['row_number'] = (range(len(data)))
        data.set_index('row_number', inplace=True)
        for i in range(0, len(data)-1):
            if data['martillo'].iloc[i] == 0:
                data.at[i, 'martillo'] = data['martillo'].iloc[i - 1]
                data.at[i, 'disparo'] = data['disparo'].iloc[i - 1]
        data.set_index('Open Time', inplace=True)
        ##################################    obligatorios ##############  --->>>  trade, stop_loss, take_profit, porcentajeentrada, cerrar
        ###########################################################################################################################
        porcentaje_perdida = 1
        data['trade'] = np.where((data.martillo == 1) & (data.Close > data.disparo),-1,np.where((data.martillo == -1) & (data.Close < data.disparo),-2,-1.5))
        data['stop_loss'] = np.where(data.trade==-1,data.Low,np.where(data.trade==-2,data.High,None))
        variacion_hasta_stop_loss = np.where(data.trade==-1,(((data.stop_loss/data.Close)-1)*-100),np.where(data.trade==-2,(((data.stop_loss/data.Close)-1)*100),0))
        data['take_profit'] = np.where(data.trade==-1,data.Close*(1+(variacion_hasta_stop_loss*multiplicador_tp/100)),np.where(data.trade==-2,data.Close*(1-(variacion_hasta_stop_loss*multiplicador_tp/100)),0))
        data['porcentajeentrada'] = 0.99 #np.where(variacion_hasta_stop_loss>0,np.where(((porcentaje_perdida/variacion_hasta_stop_loss))>=1,0.99,((porcentaje_perdida/variacion_hasta_stop_loss))),0)
        data['cerrar'] = None 
    except Exception as e:
        print(f"Error en {symbol}: {e}")
    return data