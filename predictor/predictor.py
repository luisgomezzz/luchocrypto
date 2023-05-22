import numpy as np
import pandas as pd
import pandas_ta as ta
import talib
import constantes as cons
from keras.layers import LSTM
from keras.layers import Dense
from keras import optimizers
from keras.models import Model
from keras.layers import Dense, LSTM, Input, Activation
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import util as ut
from time import sleep
import datetime as dt
from tensorflow import keras
import os
import json
from binance.exceptions import BinanceAPIException
import sys
import inquirer
ut.printandlog(cons.nombrelog,"PREDICTOR")

backcandles=100
umbralbajo=0.15
umbralalto=0.85

# 0: solo predice
# 1: entrena, guarda el modelo y predice
# 2: entrena y guarda el modelo
questions = [
    inquirer.List('modo',
                    message="Seleccionar modo: ",
                    choices=["Tradear.","Entrenar, guardar el modelo y tradear.","Entrenar y guardar el modelo."],
                ),
]
answers = inquirer.prompt(questions)
modo_seleccionado=answers['modo']
if modo_seleccionado == "Tradear.":
    modo_ejecucion=0
if modo_seleccionado == "Entrenar, guardar el modelo y tradear.":
    modo_ejecucion=1
if modo_seleccionado == "Entrenar y guardar el modelo.":
    modo_ejecucion=2

listamonedas = ['BTCUSDT'   ,'ETHUSDT'   ,'BCHUSDT'   ,'XRPUSDT'   ,'EOSUSDT'   ,'LTCUSDT'   ,'ETCUSDT'   ,'LINKUSDT'  ,
'ADAUSDT'   ,'BNBUSDT'   ,'ATOMUSDT'  ,'DOGEUSDT'  ,'KAVAUSDT'  ,'DOTUSDT'   ,'SOLUSDT'   ,'AVAXUSDT'  ,'FTMUSDT'   ,
'TOMOUSDT'  ,'FILUSDT'   ,'MATICUSDT' ,'LINAUSDT'  ,'MASKUSDT'  ,'DYDXUSDT'  ,'GALAUSDT'  ,'ARPAUSDT'  ,'ANTUSDT'   ,'GMTUSDT'   ,
'APEUSDT'   ,'JASMYUSDT' ,'OPUSDT'    ,'INJUSDT'   ,'LDOUSDT'   ,'APTUSDT'   ,'RNDRUSDT'  ,'CFXUSDT'   ,'STXUSDT'   ,
'IDUSDT'    ,'ARBUSDT'   ,'EDUUSDT'   ,'SUIUSDT'
]

def posicionpredictor(symbol,side,porcentajeentrada):   
    serror = True
    micapital = ut.balancetotal()
    size = float(micapital*porcentajeentrada/100)
    mensaje=''
    try:      
        if ut.creoposicion (symbol,size,side)==True:
           mensaje=mensaje+"EntryPrice: "+str(ut.truncate(ut.getentryprice(symbol),6))
        else:
           mensaje="No se pudo crear la posición. "
           print(mensaje)
           serror=False
    except BinanceAPIException as a:
        print(a.message,"No se pudo crear la posición.")
        serror=False
        pass     
    except Exception as falla:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - par: "+symbol+"\n")
        serror=False
        pass
    return serror, mensaje 

def get_bollinger_bands(df):
    mult = 2.0
    length = 20
    close = df['Close']
    basis = talib.SMA(close, length)
    dev = mult * talib.STDDEV(close, length)
    df['upper'] = basis + dev
    df['lower'] = basis - dev
    return df 

def checkhl(data_back, data_forward, hl):
    if hl == 'high' or hl == 'High':
        ref = data_back[len(data_back)-1]
        for i in range(len(data_back)-1):
            if ref < data_back[i]:
                return 0
        for i in range(len(data_forward)):
            if ref <= data_forward[i]:
                return 0
        return 1
    if hl == 'low' or hl == 'Low':
        ref = data_back[len(data_back)-1]
        for i in range(len(data_back)-1):
            if ref > data_back[i]:
                return 0
        for i in range(len(data_forward)):
            if ref >= data_forward[i]:
                return 0
        return 1
    
def pivot(data, LBL, LBR, highlow):
    df=data.copy()
    left = []
    right = []
    pivots=[]
    df['pivot']=0.0
    i=0
    last_value=0.0
    for index, row in df.iterrows():
        pivots.append(0.0)
        if i < LBL + 1:
            left.append(df.Close[i])
        if i > LBL:
            right.append(df.Close[i])
        if i > LBL + LBR:
            left.append(right[0])
            left.pop(0)
            right.pop(0)
            if checkhl(left, right, highlow):
                pivots[i - LBR] = df.Close[i - LBR]
                last_value = df.Close[i - LBR]
        df.at[index,'pivot'] = last_value
        i=i+1
    return df['pivot']

def obtiene_historial(symbol):
    client = cons.client
    #################################################################################################################  
    timeframe='30m'
    leido=False
    while leido==False:
        try:
            historical_data = client.get_historical_klines(symbol, timeframe)
            leido = True
        except:
            print("intento leer de nuevo...")
            pass
    data = pd.DataFrame(historical_data)
    data.columns = ['Open Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close Time', 'Quote Asset Volume', 
                        'Number of Trades', 'TB Base Volume', 'TB Quote Volume', 'Ignore']
    data['Open Time'] = pd.to_datetime(data['Open Time']/1000, unit='s')
    data['Close Time'] = pd.to_datetime(data['Close Time']/1000, unit='s')
    numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Quote Asset Volume', 'TB Base Volume', 'TB Quote Volume']
    data[numeric_columns] = data[numeric_columns].apply(pd.to_numeric, axis=1)
    # Adding indicators
    data['RSI']=ta.rsi(data.Close, length=15)
    data['EMAF']=ta.ema(data.Close, length=20)
    data['EMAM']=ta.ema(data.Close, length=50)
    data['EMAS']=ta.ema(data.Close, length=200)
    data['macd'], data['macd_signal'], data['macd_hist'] = talib.MACD(data['Close'], fastperiod=12, slowperiod=26, signalperiod=9)
    data=get_bollinger_bands(data)
    data['pivot_high'] = pivot(data, 24, 24, 'high')
    data['pivot_low'] = pivot(data, 24, 24, 'low')
    data['TARGET'] = data['Close'].shift(-1)

    data.dropna(inplace=True)
    data.reset_index(inplace = True)
    data.drop(['Open Time','Close Time','Quote Asset Volume', 'TB Base Volume', 'TB Quote Volume','Number of Trades',
            'Ignore','index'], axis=1, inplace=True)
    cantidad_campos_entrenar=len(data.columns)-1
    data_set = data
    pd.set_option('display.max_columns', None)
    #################################################################################################################
    sc = MinMaxScaler(feature_range=(0,1))
    data_set_scaled = sc.fit_transform(data_set)
    # multiple feature from data provided to the model
    X = []
    backcandles = 100
    for j in range(cantidad_campos_entrenar):
        X.append([])
        for i in range(backcandles, data_set_scaled.shape[0]):#backcandles+2
            X[j].append(data_set_scaled[i-backcandles:i, j])
    #move axis from 0 to position 2
    X=np.moveaxis(X, [0], [2])
    X, yi =np.array(X), np.array(data_set_scaled[backcandles:,-1])
    y=np.reshape(yi,(len(yi),1))
    # split data into train test sets
    splitlimit = int(len(X)*0.8)
    X_train, X_test = X[:splitlimit], X[splitlimit:]
    y_train, y_test = y[:splitlimit], y[splitlimit:]
    #################################################################################################################   
    return X_train,y_train,X_test,y_test,cantidad_campos_entrenar,data

def entrena_modelo(symbol):
    X_train,y_train,X_test,y_test,cantidad_campos_entrenar,data=obtiene_historial(symbol)
    print('entrena '+symbol)

    np.random.seed(10)
    lstm_input = Input(shape=(backcandles, cantidad_campos_entrenar), name='lstm_input')
    lstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)
    lstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)
    dense_layer = Dense(1, name='dense_layer')(lstm_layer2)
    output_layer = Activation('linear', name='output')(dense_layer)
    model = Model(inputs=lstm_input, outputs=output_layer)
    adam = optimizers.Adam()
    model.compile(optimizer=adam, loss='mse')
    history=model.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)
    
    model.save('predictor/modelos/model'+symbol+'.h5')

# programa principal
def main():
    try:
        if modo_ejecucion in [0,1,2]:

            if modo_ejecucion in [1,2]:
                for symbol in listamonedas:
                    entrena_modelo(symbol)
                print("Fin del entrenamiento de modelos. ")
            
            if modo_ejecucion in [0,1]:

                while True:
                    # Lee archivo de configuracion
                    with open(cons.pathroot+"configuracion.json","r") as j:
                        dic_configuracion=json.load(j) 
                    cantidad_posiciones = dic_configuracion['cantidad_posiciones']
                    # Lee archivo de posiciones
                    with open(cons.pathroot+"posiciones.json","r") as j:
                        posiciones=json.load(j)        
                    for symbol in listamonedas:
                        print('chequeo '+symbol)
                        
                        X_train,y_train,X_test,y_test,cantidad_campos_entrenar,data=obtiene_historial(symbol)
                        
                        if len(data)>=800:# chequea que haya suficiente historial para que la prediccion sea coherente.                            

                            model = keras.models.load_model('predictor/modelos/model'+symbol+'.h5')

                            y_pred = model.predict(X_test)
                            deriv_y_pred = np.diff(y_pred, axis=0, prepend=0)
                            deriv_y_pred2 = np.diff(deriv_y_pred, axis=0, prepend=0)
                            sc = MinMaxScaler(feature_range=(0,1))
                            deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)
                            deriv_y_pred_scaled2 = sc.fit_transform(deriv_y_pred2)                    

                            print(f"derivada 1ra: {deriv_y_pred_scaled[-1]}, derivada 2da: {deriv_y_pred_scaled2[-1]}")
                            # CREA POSICION
                            side=''
                            if symbol not in posiciones:
                                data['atr']=ta.atr(data.High, data.Low, data.Close)
                                atr=data.atr.iloc[-1]
                                ###BUY###
                                if  deriv_y_pred_scaled2[-1] >= umbralalto and y_test[-1] > 0.5:
                                    side='BUY'
                                    atr=atr*1
                                else:
                                    ###SELL###
                                    if deriv_y_pred_scaled2[-1] <= umbralbajo and y_test[-1] < 0.5:
                                        side='SELL'
                                        atr=atr*-1
                                if side !='' and ut.get_cantidad_posiciones() < cantidad_posiciones and ut.get_positionamt(symbol)==0.0:    
                                    posiciones[symbol]=side
                                    with open(cons.pathroot+"posiciones.json","w") as j:
                                        json.dump(posiciones,j, indent=4)
                                    ut.printandlog(cons.nombrelog,'Entra en Trade '+symbol+'. Side: '+str(side)+'. deriv_y_pred_scaled2: '+str(deriv_y_pred_scaled2[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))
                                    ut.sound()
                                    ut.sound() 
                                    posicionpredictor(symbol,side,porcentajeentrada=90) 
                                    # STOP LOSS Y TAKE PROFIT 
                                    entry_price = ut.getentryprice(symbol)
                                    if entry_price!=0.0:
                                        profit_price = entry_price + 3*atr
                                        stop_price = entry_price - 1.5*atr                                        
                                        ut.creostoploss (symbol,side,stop_price)                                       
                                        ut.creotakeprofit(symbol,preciolimit=profit_price,posicionporc=100,lado=posiciones[symbol])  

                            # CERRAR POSICION
                            else: 
                                if ut.get_positionamt(symbol)==0.0: 
                                    # Se cerró la posición por limit o manual y se elimina del diccionario. 
                                    # TAMBIEN SE CIERRAN LAS ORDENES QUE PUEDEN HABER QUEDADO ABIERTAS.
                                    posiciones.pop(symbol)
                                    with open(cons.pathroot+"posiciones.json","w") as j:
                                        json.dump(posiciones,j, indent=4)
                                    ut.closeallopenorders(symbol)              

                    sleep(60)

    except Exception as falla:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - par: "+symbol+"\n")
        pass  

if __name__ == '__main__':
    main()
