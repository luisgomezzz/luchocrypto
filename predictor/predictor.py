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

ut.printandlog(cons.nombrelog,"Arranca Predictor: ")

# definicion
backcandles = 100 #velas hacia atrás que estudia.
timeframe = '30m'
generar_modelos = 0 # 1:entrena, guarda el modelo y predice - 0: solo predice
listamonedas = ['BTCUSDT' , 'ETHUSDT' , 'XRPUSDT' , 'LTCUSDT' , 'LINKUSDT', 'ADAUSDT' , 'BNBUSDT' , 'ATOMUSDT'
, 'DOGEUSDT', 'RLCUSDT' , 'DOTUSDT' , 'SOLUSDT' , 'AVAXUSDT', 'FTMUSDT' , 'TOMOUSDT', 'FILUSDT' , 'MATICUSDT'
, 'ALPHAUSDT', 'HBARUSDT', 'LINAUSDT', 'DYDXUSDT', 'CTSIUSDT', 'OPUSDT' , 'INJUSDT' , 'ICPUSDT' , 'APTUSDT' 
, 'RNDRUSDT', 'CFXUSDT' , 'IDUSDT' , 'ARBUSDT']

def obtiene_historial(symbol,timeframe):
    client = cons.client
    historical_data = client.get_historical_klines(symbol, timeframe)
    data = pd.DataFrame(historical_data)
    data.columns = ['Open Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close Time', 'Quote Asset Volume', 'Number of Trades', 'TB Base Volume', 'TB Quote Volume', 'Ignore']
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
    data['EMAM']=ta.ema(data.Close, length=100)
    data['EMAS']=ta.ema(data.Close, length=150)
    data['macd'], data['macd_signal'], data['macd_hist'] = talib.MACD(data['Close'], fastperiod=12, slowperiod=26, signalperiod=9)
    data=get_bollinger_bands(data)
    data['Momentum6'] = ((data['Close'] - data['Close'].shift(6)) / data['Close'].shift(6)) * 100
    data['Variacion']=[((data.High[i]/data.Low[i])-1)*100 if data.Close[i]>=data.Open[i] else (((data.Low[i]/data.High[i])-1)*100) for i in range(len(data))]
    data['Variacion']=round(data['Variacion'].shift(-1),2)
    data['Target']=round(((data.High/data.Low)-1)*100,2)
    data['Target']=data['Target'].shift(-1)
    data.dropna(inplace=True)
    data.reset_index(inplace = True)
    data.drop(['Open Time','Close Time','Quote Asset Volume', 'TB Base Volume', 'TB Quote Volume','Number of Trades','Ignore','index'], axis=1, inplace=True)
    cantidadcamposentrenar=len(data.columns)-1
    data_set = data
    pd.set_option('display.max_columns', None)
    data_set.tail(30)
    sc = MinMaxScaler(feature_range=(0,1))
    data_set_scaled = sc.fit_transform(data_set)
    # multiple feature from data provided to the model
    X = []
    for j in range(cantidadcamposentrenar):#data_set_scaled[0].size):#2 columns are target not X
        X.append([])
        for i in range(backcandles, data_set_scaled.shape[0]):
            X[j].append(data_set_scaled[i-backcandles:i, j])
    #move axis from 0 to position 2
    X=np.moveaxis(X, [0], [2])
    X, yi =np.array(X), np.array(data_set_scaled[backcandles:,-1])
    y=np.reshape(yi,(len(yi),1))
    # split data into train test sets
    splitlimit = int(len(X)*0.8)
    X_train, X_test = X[:splitlimit], X[splitlimit:]
    y_train, y_test = y[:splitlimit], y[splitlimit:]
    #tendencia
    ema20=ta.ema(data.Close, length=20)
    ema50=ta.ema(data.Close, length=50)
    tendencia=[1 if ema20[i]>=ema50[i] else -1 for i in range(len(data))]
    return X_train,y_train,X_test,y_test,cantidadcamposentrenar,tendencia

def entrena_modelo(symbol):
    X_train,y_train,X_test,y_test,cantidadcamposentrenar,tendencia=obtiene_historial(symbol,timeframe)
    np.random.seed(10)
    lstm_input = Input(shape=(backcandles, cantidadcamposentrenar), name='lstm_input')
    lstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)
    lstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)
    dense_layer = Dense(1, name='dense_layer')(lstm_layer2)
    output_layer = Activation('linear', name='output')(dense_layer)
    model = Model(inputs=lstm_input, outputs=output_layer)
    adam = optimizers.Adam()
    model.compile(optimizer=adam, loss='mse')
    print('entrena '+symbol)
    model.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)
    model.save('predictor/modelos/model'+symbol+'.h5')

# programa principal
def main():
    if generar_modelos==1:
        for symbol in listamonedas:
            entrena_modelo(symbol)
    while True:
        for symbol in listamonedas:
            print('chequeo '+symbol)
            X_train,y_train,X_test,y_test,cantidadcamposentrenar,tendencia=obtiene_historial(symbol,timeframe)
            model = keras.models.load_model('predictor/modelos/model'+symbol+'.h5')
            y_pred = model.predict(X_test)
            deriv_y_pred = np.diff(y_pred, axis=0)
            sc = MinMaxScaler(feature_range=(0,1))
            deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)
            print(deriv_y_pred_scaled[-1])
            if float(deriv_y_pred_scaled[-1]) >= 0.7:
                ut.sound()
                ut.sound()
                ut.sound()
                ut.printandlog(cons.nombrelog,'Encontrado '+symbol+'. Tendencia: '+str(tendencia[-1])+'. Pendiente: '+str(deriv_y_pred_scaled[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))
        print("duermo x min")    
        sleep(300)

if __name__ == '__main__':
    main()
