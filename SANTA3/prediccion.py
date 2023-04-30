import numpy as np
import pandas as pd
import pandas_ta as ta
import talib
import constantes as cons
from keras.layers import LSTM
from keras.layers import Dense
from keras import optimizers
from keras.models import Model
from keras.layers import Dense, LSTM, Input, Activation, concatenate
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import util as ut
from time import sleep
import datetime as dt

backcandles = 100
def preparardata(backcandles):
    client = cons.client
    timeframe='30m'
    symbol = 'CFXUSDT'
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
        # calcular indicadores
        close = df['Close']
        basis = talib.SMA(close, length)
        dev = mult * talib.STDDEV(close, length)
        df['upper'] = basis + dev
        df['lower'] = basis - dev
        # imprimir resultados
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
    campos=len(data.columns)-1
    data_set = data
    pd.set_option('display.max_columns', None)
    data_set.tail(30)
    sc = MinMaxScaler(feature_range=(0,1))
    data_set_scaled = sc.fit_transform(data_set)
    # multiple feature from data provided to the model
    X = []
    print(data_set_scaled.shape[0])
    for j in range(campos):#data_set_scaled[0].size):#2 columns are target not X
        X.append([])
        for i in range(backcandles, data_set_scaled.shape[0]):#backcandles+2
            X[j].append(data_set_scaled[i-backcandles:i, j])
    #move axis from 0 to position 2
    X=np.moveaxis(X, [0], [2])
    X, yi =np.array(X), np.array(data_set_scaled[backcandles:,-1])
    y=np.reshape(yi,(len(yi),1))
    print(X)
    print(X.shape)
    print(y)
    print(y.shape)
    # split data into train test sets
    splitlimit = int(len(X)*0.8)
    X_train, X_test = X[:splitlimit], X[splitlimit:]
    y_train, y_test = y[:splitlimit], y[splitlimit:]
    return X_train,y_train,X_test,y_test,campos

X_train,y_train,X_test,y_test,campos=preparardata(backcandles)

#entrenar
np.random.seed(10)
lstm_input = Input(shape=(backcandles, campos), name='lstm_input')
lstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)
lstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)
dense_layer = Dense(1, name='dense_layer')(lstm_layer2)
output_layer = Activation('linear', name='output')(dense_layer)
model = Model(inputs=lstm_input, outputs=output_layer)
adam = optimizers.Adam()
model.compile(optimizer=adam, loss='mse')
model.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)

while True:
    print("chequeo")
    X_train,y_train,X_test,y_test,campos=preparardata(backcandles)
    #predecir
    y_pred = model.predict(X_test)
    deriv_y_pred = np.diff(y_pred, axis=0)
    sc = MinMaxScaler(feature_range=(0,1))
    deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)
    print(deriv_y_pred_scaled[-1])
    if float(deriv_y_pred_scaled[-1]) >= 0.6:
        ut.sound()
        ut.sound()
        ut.sound()
        print("encontrado: "+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))
    print("duermo 15 min")    
    sleep(900)

