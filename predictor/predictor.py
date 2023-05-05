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
ut.printandlog(cons.nombrelog,"PREDICTOR")

backcandles=100
generar_modelos = 0 # 1:entrena, guarda el modelo y predice - 0: solo predice
listamonedas = ['BTCUSDT' , 'ETHUSDT' , 'XRPUSDT' , 'LTCUSDT' , 'LINKUSDT', 'ADAUSDT' , 'BNBUSDT' , 'ATOMUSDT'
, 'DOGEUSDT', 'RLCUSDT' , 'DOTUSDT' , 'SOLUSDT' , 'AVAXUSDT', 'FTMUSDT' , 'TOMOUSDT', 'FILUSDT' , 'MATICUSDT'
, 'ALPHAUSDT', 'HBARUSDT', 'LINAUSDT', 'DYDXUSDT', 'CTSIUSDT', 'OPUSDT' , 'INJUSDT' , 'ICPUSDT' , 'APTUSDT' 
, 'RNDRUSDT', 'CFXUSDT' , 'IDUSDT' , 'ARBUSDT']
# Crea el file json si no existe
pathroot=os.path.dirname(os.path.abspath(__file__))+'/'
posiciones={}
if os.path.isfile(os.path.join(pathroot, "posiciones.json")) == False:
    with open(pathroot+"posiciones.json","w") as j:
        json.dump(posiciones,j, indent=4)
# Lee el json
with open(pathroot+"posiciones.json","r") as j:
    posiciones=json.load(j)        

def obtiene_historial(symbol):
    client = cons.client

    #################################################################################################################  
    timeframe='30m'
    backcandles = 100 
    historical_data = client.get_historical_klines(symbol, timeframe)
    data = pd.DataFrame(historical_data)
    data.columns = ['Open Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close Time', 'Quote Asset Volume', 
                        'Number of Trades', 'TB Base Volume', 'TB Quote Volume', 'Ignore']
    data['Open Time'] = pd.to_datetime(data['Open Time']/1000, unit='s')
    data['Close Time'] = pd.to_datetime(data['Close Time']/1000, unit='s')
    numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Quote Asset Volume', 'TB Base Volume', 'TB Quote Volume']
    data[numeric_columns] = data[numeric_columns].apply(pd.to_numeric, axis=1)

    # Adding indicators
    def get_bollinger_bands(df):
        mult = 2.0
        length = 20
        close = df['Close']
        basis = talib.SMA(close, length)
        dev = mult * talib.STDDEV(close, length)
        df['upper'] = basis + dev
        df['lower'] = basis - dev
        return df

    data['RSI']=ta.rsi(data.Close, length=15)
    data['EMAF']=ta.ema(data.Close, length=20)
    data['EMAM']=ta.ema(data.Close, length=50)
    data['EMAS']=ta.ema(data.Close, length=200)
    data['macd'], data['macd_signal'], data['macd_hist'] = talib.MACD(data['Close'], fastperiod=12, slowperiod=26, signalperiod=9)
    data=get_bollinger_bands(data)
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
    return X_train,y_train,X_test,y_test,cantidad_campos_entrenar

def entrena_modelo(symbol):
    X_train,y_train,X_test,y_test,cantidad_campos_entrenar=obtiene_historial(symbol)
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
    if generar_modelos==1:
        for symbol in listamonedas:
            entrena_modelo(symbol)
    while True:
        for symbol in listamonedas:
            print('chequeo '+symbol)
            X_train,y_train,X_test,y_test,cantidad_campos_entrenar=obtiene_historial(symbol)
            model = keras.models.load_model('predictor/modelos/model'+symbol+'.h5')

            y_pred = model.predict(X_test)
            deriv_y_pred = np.diff(y_pred, axis=0)
            sc = MinMaxScaler(feature_range=(0,1))
            deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)  

            print(deriv_y_pred_scaled[-1])
            
            tendencia=''
            if symbol not in posiciones:
                if float(deriv_y_pred_scaled[-1]) >= 0.85:
                    tendencia='BUY'
                else:
                    if float(deriv_y_pred_scaled[-1]) <= 0.15:
                        tendencia='SELL'
                if tendencia !='' and len(posiciones)<4:            
                    posiciones[symbol]=tendencia
                    with open(pathroot+"posiciones.json","w") as j:
                        json.dump(posiciones,j, indent=4)
                    ut.printandlog(cons.nombrelog,'Entra en Trade '+symbol+'. Lado: '+str(tendencia)+'. deriv_y_pred_scaled: '+str(deriv_y_pred_scaled[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))
                    ut.sound()
                    ut.sound()
            else:
                if posiciones[symbol]=='BUY':
                    if deriv_y_pred[-1] < 0:
                        posiciones.pop(symbol)
                        with open(pathroot+"posiciones.json","w") as j:
                            json.dump(posiciones,j, indent=4)                        
                        ut.printandlog(cons.nombrelog,'Sale del trade '+symbol+'. deriv_y_pred: '+str(deriv_y_pred[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))
                        ut.sound()
                        ut.sound()
                else:
                    if deriv_y_pred[-1] > 0:
                        posiciones.pop(symbol)
                        with open(pathroot+"posiciones.json","w") as j:
                            json.dump(posiciones,j, indent=4)                           
                        ut.printandlog(cons.nombrelog,'Sale del trade '+symbol+'. deriv_y_pred: '+str(deriv_y_pred[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))
                        ut.sound()
                        ut.sound()
        print("posiciones:")                    
        print(posiciones)
        print("duermo x min")    
        ut.printandlog(cons.nombrelog,"####################################################################")
        sleep(60)

if __name__ == '__main__':
    main()
