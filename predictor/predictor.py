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
ut.printandlog(cons.nombrelog,"arranca prediccion: ")

# definicion

backcandles = 100
timeframe = '30m'

def preparardata(symbol,timeframe):
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
    cantidadcamposentrenar=len(data.columns)-1
    data_set = data
    pd.set_option('display.max_columns', None)
    data_set.tail(30)
    sc = MinMaxScaler(feature_range=(0,1))
    data_set_scaled = sc.fit_transform(data_set)
    # multiple feature from data provided to the model
    X = []
    #print(data_set_scaled.shape[0])
    for j in range(cantidadcamposentrenar):#data_set_scaled[0].size):#2 columns are target not X
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
    return X_train,y_train,X_test,y_test,cantidadcamposentrenar

######################################################################################################################
symbol='BTCUSDT'
X_train,y_train,X_test,y_test,cantidadcamposentrenar=preparardata(symbol,timeframe)
np.random.seed(10)
lstm_input = Input(shape=(backcandles, cantidadcamposentrenar), name='lstm_input')
lstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)
lstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)
dense_layer = Dense(1, name='dense_layer')(lstm_layer2)
output_layer = Activation('linear', name='output')(dense_layer)
modelBTCUSDT = Model(inputs=lstm_input, outputs=output_layer)
adam = optimizers.Adam()
modelBTCUSDT.compile(optimizer=adam, loss='mse')
print('entrena '+symbol)
modelBTCUSDT.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)

symbol='ETHUSDT'
X_train,y_train,X_test,y_test,cantidadcamposentrenar=preparardata(symbol,timeframe)
np.random.seed(10)
lstm_input = Input(shape=(backcandles, cantidadcamposentrenar), name='lstm_input')
lstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)
lstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)
dense_layer = Dense(1, name='dense_layer')(lstm_layer2)
output_layer = Activation('linear', name='output')(dense_layer)
modelETHUSDT = Model(inputs=lstm_input, outputs=output_layer)
adam = optimizers.Adam()
modelETHUSDT.compile(optimizer=adam, loss='mse')
print('entrena '+symbol)
modelETHUSDT.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)

symbol='XRPUSDT'
X_train,y_train,X_test,y_test,cantidadcamposentrenar=preparardata(symbol,timeframe)
np.random.seed(10)
lstm_input = Input(shape=(backcandles, cantidadcamposentrenar), name='lstm_input')
lstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)
lstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)
dense_layer = Dense(1, name='dense_layer')(lstm_layer2)
output_layer = Activation('linear', name='output')(dense_layer)
modelXRPUSDT = Model(inputs=lstm_input, outputs=output_layer)
adam = optimizers.Adam()
modelXRPUSDT.compile(optimizer=adam, loss='mse')
print('entrena '+symbol)
modelXRPUSDT.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)

symbol='LTCUSDT'
X_train,y_train,X_test,y_test,cantidadcamposentrenar=preparardata(symbol,timeframe)
np.random.seed(10)
lstm_input = Input(shape=(backcandles, cantidadcamposentrenar), name='lstm_input')
lstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)
lstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)
dense_layer = Dense(1, name='dense_layer')(lstm_layer2)
output_layer = Activation('linear', name='output')(dense_layer)
modelLTCUSDT = Model(inputs=lstm_input, outputs=output_layer)
adam = optimizers.Adam()
modelLTCUSDT.compile(optimizer=adam, loss='mse')
print('entrena '+symbol)
modelLTCUSDT.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)

symbol='LINKUSDT'
X_train,y_train,X_test,y_test,cantidadcamposentrenar=preparardata(symbol,timeframe)
np.random.seed(10)
lstm_input = Input(shape=(backcandles, cantidadcamposentrenar), name='lstm_input')
lstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)
lstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)
dense_layer = Dense(1, name='dense_layer')(lstm_layer2)
output_layer = Activation('linear', name='output')(dense_layer)
modelLINKUSDT = Model(inputs=lstm_input, outputs=output_layer)
adam = optimizers.Adam()
modelLINKUSDT.compile(optimizer=adam, loss='mse')
print('entrena '+symbol)
modelLINKUSDT.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)

symbol='ADAUSDT'
X_train,y_train,X_test,y_test,cantidadcamposentrenar=preparardata(symbol,timeframe)
np.random.seed(10)
lstm_input = Input(shape=(backcandles, cantidadcamposentrenar), name='lstm_input')
lstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)
lstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)
dense_layer = Dense(1, name='dense_layer')(lstm_layer2)
output_layer = Activation('linear', name='output')(dense_layer)
modelADAUSDT = Model(inputs=lstm_input, outputs=output_layer)
adam = optimizers.Adam()
modelADAUSDT.compile(optimizer=adam, loss='mse')
print('entrena '+symbol)
modelADAUSDT.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)

symbol='BNBUSDT'
X_train,y_train,X_test,y_test,cantidadcamposentrenar=preparardata(symbol,timeframe)
np.random.seed(10)
lstm_input = Input(shape=(backcandles, cantidadcamposentrenar), name='lstm_input')
lstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)
lstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)
dense_layer = Dense(1, name='dense_layer')(lstm_layer2)
output_layer = Activation('linear', name='output')(dense_layer)
modelBNBUSDT = Model(inputs=lstm_input, outputs=output_layer)
adam = optimizers.Adam()
modelBNBUSDT.compile(optimizer=adam, loss='mse')
print('entrena '+symbol)
modelBNBUSDT.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)

symbol='ATOMUSDT'
X_train,y_train,X_test,y_test,cantidadcamposentrenar=preparardata(symbol,timeframe)
np.random.seed(10)
lstm_input = Input(shape=(backcandles, cantidadcamposentrenar), name='lstm_input')
lstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)
lstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)
dense_layer = Dense(1, name='dense_layer')(lstm_layer2)
output_layer = Activation('linear', name='output')(dense_layer)
modelATOMUSDT = Model(inputs=lstm_input, outputs=output_layer)
adam = optimizers.Adam()
modelATOMUSDT.compile(optimizer=adam, loss='mse')
print('entrena '+symbol)
modelATOMUSDT.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)

symbol='DOGEUSDT'
X_train,y_train,X_test,y_test,cantidadcamposentrenar=preparardata(symbol,timeframe)
np.random.seed(10)
lstm_input = Input(shape=(backcandles, cantidadcamposentrenar), name='lstm_input')
lstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)
lstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)
dense_layer = Dense(1, name='dense_layer')(lstm_layer2)
output_layer = Activation('linear', name='output')(dense_layer)
modelDOGEUSDT = Model(inputs=lstm_input, outputs=output_layer)
adam = optimizers.Adam()
modelDOGEUSDT.compile(optimizer=adam, loss='mse')
print('entrena '+symbol)
modelDOGEUSDT.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)

symbol='RLCUSDT'
X_train,y_train,X_test,y_test,cantidadcamposentrenar=preparardata(symbol,timeframe)
np.random.seed(10)
lstm_input = Input(shape=(backcandles, cantidadcamposentrenar), name='lstm_input')
lstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)
lstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)
dense_layer = Dense(1, name='dense_layer')(lstm_layer2)
output_layer = Activation('linear', name='output')(dense_layer)
modelRLCUSDT = Model(inputs=lstm_input, outputs=output_layer)
adam = optimizers.Adam()
modelRLCUSDT.compile(optimizer=adam, loss='mse')
print('entrena '+symbol)
modelRLCUSDT.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)

symbol='DOTUSDT'
X_train,y_train,X_test,y_test,cantidadcamposentrenar=preparardata(symbol,timeframe)
np.random.seed(10)
lstm_input = Input(shape=(backcandles, cantidadcamposentrenar), name='lstm_input')
lstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)
lstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)
dense_layer = Dense(1, name='dense_layer')(lstm_layer2)
output_layer = Activation('linear', name='output')(dense_layer)
modelDOTUSDT = Model(inputs=lstm_input, outputs=output_layer)
adam = optimizers.Adam()
modelDOTUSDT.compile(optimizer=adam, loss='mse')
print('entrena '+symbol)
modelDOTUSDT.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)

symbol='SOLUSDT'
X_train,y_train,X_test,y_test,cantidadcamposentrenar=preparardata(symbol,timeframe)
np.random.seed(10)
lstm_input = Input(shape=(backcandles, cantidadcamposentrenar), name='lstm_input')
lstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)
lstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)
dense_layer = Dense(1, name='dense_layer')(lstm_layer2)
output_layer = Activation('linear', name='output')(dense_layer)
modelSOLUSDT = Model(inputs=lstm_input, outputs=output_layer)
adam = optimizers.Adam()
modelSOLUSDT.compile(optimizer=adam, loss='mse')
print('entrena '+symbol)
modelSOLUSDT.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)

symbol='AVAXUSDT'
X_train,y_train,X_test,y_test,cantidadcamposentrenar=preparardata(symbol,timeframe)
np.random.seed(10)
lstm_input = Input(shape=(backcandles, cantidadcamposentrenar), name='lstm_input')
lstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)
lstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)
dense_layer = Dense(1, name='dense_layer')(lstm_layer2)
output_layer = Activation('linear', name='output')(dense_layer)
modelAVAXUSDT = Model(inputs=lstm_input, outputs=output_layer)
adam = optimizers.Adam()
modelAVAXUSDT.compile(optimizer=adam, loss='mse')
print('entrena '+symbol)
modelAVAXUSDT.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)

symbol='FTMUSDT'
X_train,y_train,X_test,y_test,cantidadcamposentrenar=preparardata(symbol,timeframe)
np.random.seed(10)
lstm_input = Input(shape=(backcandles, cantidadcamposentrenar), name='lstm_input')
lstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)
lstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)
dense_layer = Dense(1, name='dense_layer')(lstm_layer2)
output_layer = Activation('linear', name='output')(dense_layer)
modelFTMUSDT = Model(inputs=lstm_input, outputs=output_layer)
adam = optimizers.Adam()
modelFTMUSDT.compile(optimizer=adam, loss='mse')
print('entrena '+symbol)
modelFTMUSDT.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)

symbol='TOMOUSDT'
X_train,y_train,X_test,y_test,cantidadcamposentrenar=preparardata(symbol,timeframe)
np.random.seed(10)
lstm_input = Input(shape=(backcandles, cantidadcamposentrenar), name='lstm_input')
lstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)
lstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)
dense_layer = Dense(1, name='dense_layer')(lstm_layer2)
output_layer = Activation('linear', name='output')(dense_layer)
modelTOMOUSDT = Model(inputs=lstm_input, outputs=output_layer)
adam = optimizers.Adam()
modelTOMOUSDT.compile(optimizer=adam, loss='mse')
print('entrena '+symbol)
modelTOMOUSDT.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)

symbol='FILUSDT'
X_train,y_train,X_test,y_test,cantidadcamposentrenar=preparardata(symbol,timeframe)
np.random.seed(10)
lstm_input = Input(shape=(backcandles, cantidadcamposentrenar), name='lstm_input')
lstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)
lstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)
dense_layer = Dense(1, name='dense_layer')(lstm_layer2)
output_layer = Activation('linear', name='output')(dense_layer)
modelFILUSDT = Model(inputs=lstm_input, outputs=output_layer)
adam = optimizers.Adam()
modelFILUSDT.compile(optimizer=adam, loss='mse')
print('entrena '+symbol)
modelFILUSDT.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)

symbol='MATICUSDT'
X_train,y_train,X_test,y_test,cantidadcamposentrenar=preparardata(symbol,timeframe)
np.random.seed(10)
lstm_input = Input(shape=(backcandles, cantidadcamposentrenar), name='lstm_input')
lstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)
lstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)
dense_layer = Dense(1, name='dense_layer')(lstm_layer2)
output_layer = Activation('linear', name='output')(dense_layer)
modelMATICUSDT = Model(inputs=lstm_input, outputs=output_layer)
adam = optimizers.Adam()
modelMATICUSDT.compile(optimizer=adam, loss='mse')
print('entrena '+symbol)
modelMATICUSDT.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)

symbol='ALPHAUSDT'
X_train,y_train,X_test,y_test,cantidadcamposentrenar=preparardata(symbol,timeframe)
np.random.seed(10)
lstm_input = Input(shape=(backcandles, cantidadcamposentrenar), name='lstm_input')
lstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)
lstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)
dense_layer = Dense(1, name='dense_layer')(lstm_layer2)
output_layer = Activation('linear', name='output')(dense_layer)
modelALPHAUSDT = Model(inputs=lstm_input, outputs=output_layer)
adam = optimizers.Adam()
modelALPHAUSDT.compile(optimizer=adam, loss='mse')
print('entrena '+symbol)
modelALPHAUSDT.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)

symbol='HBARUSDT'
X_train,y_train,X_test,y_test,cantidadcamposentrenar=preparardata(symbol,timeframe)
np.random.seed(10)
lstm_input = Input(shape=(backcandles, cantidadcamposentrenar), name='lstm_input')
lstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)
lstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)
dense_layer = Dense(1, name='dense_layer')(lstm_layer2)
output_layer = Activation('linear', name='output')(dense_layer)
modelHBARUSDT = Model(inputs=lstm_input, outputs=output_layer)
adam = optimizers.Adam()
modelHBARUSDT.compile(optimizer=adam, loss='mse')
print('entrena '+symbol)
modelHBARUSDT.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)

symbol='LINAUSDT'
X_train,y_train,X_test,y_test,cantidadcamposentrenar=preparardata(symbol,timeframe)
np.random.seed(10)
lstm_input = Input(shape=(backcandles, cantidadcamposentrenar), name='lstm_input')
lstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)
lstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)
dense_layer = Dense(1, name='dense_layer')(lstm_layer2)
output_layer = Activation('linear', name='output')(dense_layer)
modelLINAUSDT = Model(inputs=lstm_input, outputs=output_layer)
adam = optimizers.Adam()
modelLINAUSDT.compile(optimizer=adam, loss='mse')
print('entrena '+symbol)
modelLINAUSDT.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)

symbol='DYDXUSDT'
X_train,y_train,X_test,y_test,cantidadcamposentrenar=preparardata(symbol,timeframe)
np.random.seed(10)
lstm_input = Input(shape=(backcandles, cantidadcamposentrenar), name='lstm_input')
lstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)
lstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)
dense_layer = Dense(1, name='dense_layer')(lstm_layer2)
output_layer = Activation('linear', name='output')(dense_layer)
modelDYDXUSDT = Model(inputs=lstm_input, outputs=output_layer)
adam = optimizers.Adam()
modelDYDXUSDT.compile(optimizer=adam, loss='mse')
print('entrena '+symbol)
modelDYDXUSDT.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)

symbol='CTSIUSDT'
X_train,y_train,X_test,y_test,cantidadcamposentrenar=preparardata(symbol,timeframe)
np.random.seed(10)
lstm_input = Input(shape=(backcandles, cantidadcamposentrenar), name='lstm_input')
lstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)
lstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)
dense_layer = Dense(1, name='dense_layer')(lstm_layer2)
output_layer = Activation('linear', name='output')(dense_layer)
modelCTSIUSDT = Model(inputs=lstm_input, outputs=output_layer)
adam = optimizers.Adam()
modelCTSIUSDT.compile(optimizer=adam, loss='mse')
print('entrena '+symbol)
modelCTSIUSDT.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)

symbol='OPUSDT'
X_train,y_train,X_test,y_test,cantidadcamposentrenar=preparardata(symbol,timeframe)
np.random.seed(10)
lstm_input = Input(shape=(backcandles, cantidadcamposentrenar), name='lstm_input')
lstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)
lstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)
dense_layer = Dense(1, name='dense_layer')(lstm_layer2)
output_layer = Activation('linear', name='output')(dense_layer)
modelOPUSDT = Model(inputs=lstm_input, outputs=output_layer)
adam = optimizers.Adam()
modelOPUSDT.compile(optimizer=adam, loss='mse')
print('entrena '+symbol)
modelOPUSDT.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)

symbol='INJUSDT'
X_train,y_train,X_test,y_test,cantidadcamposentrenar=preparardata(symbol,timeframe)
np.random.seed(10)
lstm_input = Input(shape=(backcandles, cantidadcamposentrenar), name='lstm_input')
lstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)
lstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)
dense_layer = Dense(1, name='dense_layer')(lstm_layer2)
output_layer = Activation('linear', name='output')(dense_layer)
modelINJUSDT = Model(inputs=lstm_input, outputs=output_layer)
adam = optimizers.Adam()
modelINJUSDT.compile(optimizer=adam, loss='mse')
print('entrena '+symbol)
modelINJUSDT.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)

symbol='ICPUSDT'
X_train,y_train,X_test,y_test,cantidadcamposentrenar=preparardata(symbol,timeframe)
np.random.seed(10)
lstm_input = Input(shape=(backcandles, cantidadcamposentrenar), name='lstm_input')
lstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)
lstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)
dense_layer = Dense(1, name='dense_layer')(lstm_layer2)
output_layer = Activation('linear', name='output')(dense_layer)
modelICPUSDT = Model(inputs=lstm_input, outputs=output_layer)
adam = optimizers.Adam()
modelICPUSDT.compile(optimizer=adam, loss='mse')
print('entrena '+symbol)
modelICPUSDT.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)

symbol='APTUSDT'
X_train,y_train,X_test,y_test,cantidadcamposentrenar=preparardata(symbol,timeframe)
np.random.seed(10)
lstm_input = Input(shape=(backcandles, cantidadcamposentrenar), name='lstm_input')
lstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)
lstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)
dense_layer = Dense(1, name='dense_layer')(lstm_layer2)
output_layer = Activation('linear', name='output')(dense_layer)
modelAPTUSDT = Model(inputs=lstm_input, outputs=output_layer)
adam = optimizers.Adam()
modelAPTUSDT.compile(optimizer=adam, loss='mse')
print('entrena '+symbol)
modelAPTUSDT.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)

symbol='RNDRUSDT'
X_train,y_train,X_test,y_test,cantidadcamposentrenar=preparardata(symbol,timeframe)
np.random.seed(10)
lstm_input = Input(shape=(backcandles, cantidadcamposentrenar), name='lstm_input')
lstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)
lstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)
dense_layer = Dense(1, name='dense_layer')(lstm_layer2)
output_layer = Activation('linear', name='output')(dense_layer)
modelRNDRUSDT = Model(inputs=lstm_input, outputs=output_layer)
adam = optimizers.Adam()
modelRNDRUSDT.compile(optimizer=adam, loss='mse')
print('entrena '+symbol)
modelRNDRUSDT.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)

symbol='CFXUSDT'
X_train,y_train,X_test,y_test,cantidadcamposentrenar=preparardata(symbol,timeframe)
np.random.seed(10)
lstm_input = Input(shape=(backcandles, cantidadcamposentrenar), name='lstm_input')
lstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)
lstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)
dense_layer = Dense(1, name='dense_layer')(lstm_layer2)
output_layer = Activation('linear', name='output')(dense_layer)
modelCFXUSDT = Model(inputs=lstm_input, outputs=output_layer)
adam = optimizers.Adam()
modelCFXUSDT.compile(optimizer=adam, loss='mse')
print('entrena '+symbol)
modelCFXUSDT.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)

symbol='IDUSDT'
X_train,y_train,X_test,y_test,cantidadcamposentrenar=preparardata(symbol,timeframe)
np.random.seed(10)
lstm_input = Input(shape=(backcandles, cantidadcamposentrenar), name='lstm_input')
lstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)
lstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)
dense_layer = Dense(1, name='dense_layer')(lstm_layer2)
output_layer = Activation('linear', name='output')(dense_layer)
modelIDUSDT = Model(inputs=lstm_input, outputs=output_layer)
adam = optimizers.Adam()
modelIDUSDT.compile(optimizer=adam, loss='mse')
print('entrena '+symbol)
modelIDUSDT.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)

symbol='ARBUSDT'
X_train,y_train,X_test,y_test,cantidadcamposentrenar=preparardata(symbol,timeframe)
np.random.seed(10)
lstm_input = Input(shape=(backcandles, cantidadcamposentrenar), name='lstm_input')
lstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)
lstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)
dense_layer = Dense(1, name='dense_layer')(lstm_layer2)
output_layer = Activation('linear', name='output')(dense_layer)
modelARBUSDT = Model(inputs=lstm_input, outputs=output_layer)
adam = optimizers.Adam()
modelARBUSDT.compile(optimizer=adam, loss='mse')
print('entrena '+symbol)
modelARBUSDT.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)


######################################################################################################################

# programa principal
def main():
    while True:
        symbol='BTCUSDT'
        print('chequeo '+symbol)
        X_train,y_train,X_test,y_test,campos=preparardata(symbol,timeframe)
        y_pred = modelBTCUSDT.predict(X_test)
        deriv_y_pred = np.diff(y_pred, axis=0)
        sc = MinMaxScaler(feature_range=(0,1))
        deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)
        print(deriv_y_pred_scaled[-1])
        if float(deriv_y_pred_scaled[-1]) >= 0.6:
            ut.sound()
            ut.sound()
            ut.sound()
            ut.printandlog(cons.nombrelog,'Encontrado '+symbol+'. Pendiente: '+str(deriv_y_pred_scaled[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))

        symbol='ETHUSDT'
        print('chequeo '+symbol)
        X_train,y_train,X_test,y_test,campos=preparardata(symbol,timeframe)
        y_pred = modelETHUSDT.predict(X_test)
        deriv_y_pred = np.diff(y_pred, axis=0)
        sc = MinMaxScaler(feature_range=(0,1))
        deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)
        print(deriv_y_pred_scaled[-1])
        if float(deriv_y_pred_scaled[-1]) >= 0.6:
            ut.sound()
            ut.sound()
            ut.sound()
            ut.printandlog(cons.nombrelog,'Encontrado '+symbol+'. Pendiente: '+str(deriv_y_pred_scaled[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))

        symbol='XRPUSDT'
        print('chequeo '+symbol)
        X_train,y_train,X_test,y_test,campos=preparardata(symbol,timeframe)
        y_pred = modelXRPUSDT.predict(X_test)
        deriv_y_pred = np.diff(y_pred, axis=0)
        sc = MinMaxScaler(feature_range=(0,1))
        deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)
        print(deriv_y_pred_scaled[-1])
        if float(deriv_y_pred_scaled[-1]) >= 0.6:
            ut.sound()
            ut.sound()
            ut.sound()
            ut.printandlog(cons.nombrelog,'Encontrado '+symbol+'. Pendiente: '+str(deriv_y_pred_scaled[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))

        symbol='LTCUSDT'
        print('chequeo '+symbol)
        X_train,y_train,X_test,y_test,campos=preparardata(symbol,timeframe)
        y_pred = modelLTCUSDT.predict(X_test)
        deriv_y_pred = np.diff(y_pred, axis=0)
        sc = MinMaxScaler(feature_range=(0,1))
        deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)
        print(deriv_y_pred_scaled[-1])
        if float(deriv_y_pred_scaled[-1]) >= 0.6:
            ut.sound()
            ut.sound()
            ut.sound()
            ut.printandlog(cons.nombrelog,'Encontrado '+symbol+'. Pendiente: '+str(deriv_y_pred_scaled[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))

        symbol='LINKUSDT'
        print('chequeo '+symbol)
        X_train,y_train,X_test,y_test,campos=preparardata(symbol,timeframe)
        y_pred = modelLINKUSDT.predict(X_test)
        deriv_y_pred = np.diff(y_pred, axis=0)
        sc = MinMaxScaler(feature_range=(0,1))
        deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)
        print(deriv_y_pred_scaled[-1])
        if float(deriv_y_pred_scaled[-1]) >= 0.6:
            ut.sound()
            ut.sound()
            ut.sound()
            ut.printandlog(cons.nombrelog,'Encontrado '+symbol+'. Pendiente: '+str(deriv_y_pred_scaled[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))

        symbol='ADAUSDT'
        print('chequeo '+symbol)
        X_train,y_train,X_test,y_test,campos=preparardata(symbol,timeframe)
        y_pred = modelADAUSDT.predict(X_test)
        deriv_y_pred = np.diff(y_pred, axis=0)
        sc = MinMaxScaler(feature_range=(0,1))
        deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)
        print(deriv_y_pred_scaled[-1])
        if float(deriv_y_pred_scaled[-1]) >= 0.6:
            ut.sound()
            ut.sound()
            ut.sound()
            ut.printandlog(cons.nombrelog,'Encontrado '+symbol+'. Pendiente: '+str(deriv_y_pred_scaled[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))

        symbol='BNBUSDT'
        print('chequeo '+symbol)
        X_train,y_train,X_test,y_test,campos=preparardata(symbol,timeframe)
        y_pred = modelBNBUSDT.predict(X_test)
        deriv_y_pred = np.diff(y_pred, axis=0)
        sc = MinMaxScaler(feature_range=(0,1))
        deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)
        print(deriv_y_pred_scaled[-1])
        if float(deriv_y_pred_scaled[-1]) >= 0.6:
            ut.sound()
            ut.sound()
            ut.sound()
            ut.printandlog(cons.nombrelog,'Encontrado '+symbol+'. Pendiente: '+str(deriv_y_pred_scaled[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))

        symbol='ATOMUSDT'
        print('chequeo '+symbol)
        X_train,y_train,X_test,y_test,campos=preparardata(symbol,timeframe)
        y_pred = modelATOMUSDT.predict(X_test)
        deriv_y_pred = np.diff(y_pred, axis=0)
        sc = MinMaxScaler(feature_range=(0,1))
        deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)
        print(deriv_y_pred_scaled[-1])
        if float(deriv_y_pred_scaled[-1]) >= 0.6:
            ut.sound()
            ut.sound()
            ut.sound()
            ut.printandlog(cons.nombrelog,'Encontrado '+symbol+'. Pendiente: '+str(deriv_y_pred_scaled[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))

        symbol='DOGEUSDT'
        print('chequeo '+symbol)
        X_train,y_train,X_test,y_test,campos=preparardata(symbol,timeframe)
        y_pred = modelDOGEUSDT.predict(X_test)
        deriv_y_pred = np.diff(y_pred, axis=0)
        sc = MinMaxScaler(feature_range=(0,1))
        deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)
        print(deriv_y_pred_scaled[-1])
        if float(deriv_y_pred_scaled[-1]) >= 0.6:
            ut.sound()
            ut.sound()
            ut.sound()
            ut.printandlog(cons.nombrelog,'Encontrado '+symbol+'. Pendiente: '+str(deriv_y_pred_scaled[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))

        symbol='RLCUSDT'
        print('chequeo '+symbol)
        X_train,y_train,X_test,y_test,campos=preparardata(symbol,timeframe)
        y_pred = modelRLCUSDT.predict(X_test)
        deriv_y_pred = np.diff(y_pred, axis=0)
        sc = MinMaxScaler(feature_range=(0,1))
        deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)
        print(deriv_y_pred_scaled[-1])
        if float(deriv_y_pred_scaled[-1]) >= 0.6:
            ut.sound()
            ut.sound()
            ut.sound()
            ut.printandlog(cons.nombrelog,'Encontrado '+symbol+'. Pendiente: '+str(deriv_y_pred_scaled[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))

        symbol='DOTUSDT'
        print('chequeo '+symbol)
        X_train,y_train,X_test,y_test,campos=preparardata(symbol,timeframe)
        y_pred = modelDOTUSDT.predict(X_test)
        deriv_y_pred = np.diff(y_pred, axis=0)
        sc = MinMaxScaler(feature_range=(0,1))
        deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)
        print(deriv_y_pred_scaled[-1])
        if float(deriv_y_pred_scaled[-1]) >= 0.6:
            ut.sound()
            ut.sound()
            ut.sound()
            ut.printandlog(cons.nombrelog,'Encontrado '+symbol+'. Pendiente: '+str(deriv_y_pred_scaled[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))

        symbol='SOLUSDT'
        print('chequeo '+symbol)
        X_train,y_train,X_test,y_test,campos=preparardata(symbol,timeframe)
        y_pred = modelSOLUSDT.predict(X_test)
        deriv_y_pred = np.diff(y_pred, axis=0)
        sc = MinMaxScaler(feature_range=(0,1))
        deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)
        print(deriv_y_pred_scaled[-1])
        if float(deriv_y_pred_scaled[-1]) >= 0.6:
            ut.sound()
            ut.sound()
            ut.sound()
            ut.printandlog(cons.nombrelog,'Encontrado '+symbol+'. Pendiente: '+str(deriv_y_pred_scaled[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))

        symbol='AVAXUSDT'
        print('chequeo '+symbol)
        X_train,y_train,X_test,y_test,campos=preparardata(symbol,timeframe)
        y_pred = modelAVAXUSDT.predict(X_test)
        deriv_y_pred = np.diff(y_pred, axis=0)
        sc = MinMaxScaler(feature_range=(0,1))
        deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)
        print(deriv_y_pred_scaled[-1])
        if float(deriv_y_pred_scaled[-1]) >= 0.6:
            ut.sound()
            ut.sound()
            ut.sound()
            ut.printandlog(cons.nombrelog,'Encontrado '+symbol+'. Pendiente: '+str(deriv_y_pred_scaled[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))

        symbol='FTMUSDT'
        print('chequeo '+symbol)
        X_train,y_train,X_test,y_test,campos=preparardata(symbol,timeframe)
        y_pred = modelFTMUSDT.predict(X_test)
        deriv_y_pred = np.diff(y_pred, axis=0)
        sc = MinMaxScaler(feature_range=(0,1))
        deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)
        print(deriv_y_pred_scaled[-1])
        if float(deriv_y_pred_scaled[-1]) >= 0.6:
            ut.sound()
            ut.sound()
            ut.sound()
            ut.printandlog(cons.nombrelog,'Encontrado '+symbol+'. Pendiente: '+str(deriv_y_pred_scaled[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))

        symbol='TOMOUSDT'
        print('chequeo '+symbol)
        X_train,y_train,X_test,y_test,campos=preparardata(symbol,timeframe)
        y_pred = modelTOMOUSDT.predict(X_test)
        deriv_y_pred = np.diff(y_pred, axis=0)
        sc = MinMaxScaler(feature_range=(0,1))
        deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)
        print(deriv_y_pred_scaled[-1])
        if float(deriv_y_pred_scaled[-1]) >= 0.6:
            ut.sound()
            ut.sound()
            ut.sound()
            ut.printandlog(cons.nombrelog,'Encontrado '+symbol+'. Pendiente: '+str(deriv_y_pred_scaled[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))

        symbol='FILUSDT'
        print('chequeo '+symbol)
        X_train,y_train,X_test,y_test,campos=preparardata(symbol,timeframe)
        y_pred = modelFILUSDT.predict(X_test)
        deriv_y_pred = np.diff(y_pred, axis=0)
        sc = MinMaxScaler(feature_range=(0,1))
        deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)
        print(deriv_y_pred_scaled[-1])
        if float(deriv_y_pred_scaled[-1]) >= 0.6:
            ut.sound()
            ut.sound()
            ut.sound()
            ut.printandlog(cons.nombrelog,'Encontrado '+symbol+'. Pendiente: '+str(deriv_y_pred_scaled[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))

        symbol='MATICUSDT'
        print('chequeo '+symbol)
        X_train,y_train,X_test,y_test,campos=preparardata(symbol,timeframe)
        y_pred = modelMATICUSDT.predict(X_test)
        deriv_y_pred = np.diff(y_pred, axis=0)
        sc = MinMaxScaler(feature_range=(0,1))
        deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)
        print(deriv_y_pred_scaled[-1])
        if float(deriv_y_pred_scaled[-1]) >= 0.6:
            ut.sound()
            ut.sound()
            ut.sound()
            ut.printandlog(cons.nombrelog,'Encontrado '+symbol+'. Pendiente: '+str(deriv_y_pred_scaled[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))

        symbol='ALPHAUSDT'
        print('chequeo '+symbol)
        X_train,y_train,X_test,y_test,campos=preparardata(symbol,timeframe)
        y_pred = modelALPHAUSDT.predict(X_test)
        deriv_y_pred = np.diff(y_pred, axis=0)
        sc = MinMaxScaler(feature_range=(0,1))
        deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)
        print(deriv_y_pred_scaled[-1])
        if float(deriv_y_pred_scaled[-1]) >= 0.6:
            ut.sound()
            ut.sound()
            ut.sound()
            ut.printandlog(cons.nombrelog,'Encontrado '+symbol+'. Pendiente: '+str(deriv_y_pred_scaled[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))

        symbol='HBARUSDT'
        print('chequeo '+symbol)
        X_train,y_train,X_test,y_test,campos=preparardata(symbol,timeframe)
        y_pred = modelHBARUSDT.predict(X_test)
        deriv_y_pred = np.diff(y_pred, axis=0)
        sc = MinMaxScaler(feature_range=(0,1))
        deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)
        print(deriv_y_pred_scaled[-1])
        if float(deriv_y_pred_scaled[-1]) >= 0.6:
            ut.sound()
            ut.sound()
            ut.sound()
            ut.printandlog(cons.nombrelog,'Encontrado '+symbol+'. Pendiente: '+str(deriv_y_pred_scaled[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))

        symbol='LINAUSDT'
        print('chequeo '+symbol)
        X_train,y_train,X_test,y_test,campos=preparardata(symbol,timeframe)
        y_pred = modelLINAUSDT.predict(X_test)
        deriv_y_pred = np.diff(y_pred, axis=0)
        sc = MinMaxScaler(feature_range=(0,1))
        deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)
        print(deriv_y_pred_scaled[-1])
        if float(deriv_y_pred_scaled[-1]) >= 0.6:
            ut.sound()
            ut.sound()
            ut.sound()
            ut.printandlog(cons.nombrelog,'Encontrado '+symbol+'. Pendiente: '+str(deriv_y_pred_scaled[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))

        symbol='DYDXUSDT'
        print('chequeo '+symbol)
        X_train,y_train,X_test,y_test,campos=preparardata(symbol,timeframe)
        y_pred = modelDYDXUSDT.predict(X_test)
        deriv_y_pred = np.diff(y_pred, axis=0)
        sc = MinMaxScaler(feature_range=(0,1))
        deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)
        print(deriv_y_pred_scaled[-1])
        if float(deriv_y_pred_scaled[-1]) >= 0.6:
            ut.sound()
            ut.sound()
            ut.sound()
            ut.printandlog(cons.nombrelog,'Encontrado '+symbol+'. Pendiente: '+str(deriv_y_pred_scaled[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))

        symbol='CTSIUSDT'
        print('chequeo '+symbol)
        X_train,y_train,X_test,y_test,campos=preparardata(symbol,timeframe)
        y_pred = modelCTSIUSDT.predict(X_test)
        deriv_y_pred = np.diff(y_pred, axis=0)
        sc = MinMaxScaler(feature_range=(0,1))
        deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)
        print(deriv_y_pred_scaled[-1])
        if float(deriv_y_pred_scaled[-1]) >= 0.6:
            ut.sound()
            ut.sound()
            ut.sound()
            ut.printandlog(cons.nombrelog,'Encontrado '+symbol+'. Pendiente: '+str(deriv_y_pred_scaled[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))

        symbol='OPUSDT'
        print('chequeo '+symbol)
        X_train,y_train,X_test,y_test,campos=preparardata(symbol,timeframe)
        y_pred = modelOPUSDT.predict(X_test)
        deriv_y_pred = np.diff(y_pred, axis=0)
        sc = MinMaxScaler(feature_range=(0,1))
        deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)
        print(deriv_y_pred_scaled[-1])
        if float(deriv_y_pred_scaled[-1]) >= 0.6:
            ut.sound()
            ut.sound()
            ut.sound()
            ut.printandlog(cons.nombrelog,'Encontrado '+symbol+'. Pendiente: '+str(deriv_y_pred_scaled[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))

        symbol='INJUSDT'
        print('chequeo '+symbol)
        X_train,y_train,X_test,y_test,campos=preparardata(symbol,timeframe)
        y_pred = modelINJUSDT.predict(X_test)
        deriv_y_pred = np.diff(y_pred, axis=0)
        sc = MinMaxScaler(feature_range=(0,1))
        deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)
        print(deriv_y_pred_scaled[-1])
        if float(deriv_y_pred_scaled[-1]) >= 0.6:
            ut.sound()
            ut.sound()
            ut.sound()
            ut.printandlog(cons.nombrelog,'Encontrado '+symbol+'. Pendiente: '+str(deriv_y_pred_scaled[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))

        symbol='ICPUSDT'
        print('chequeo '+symbol)
        X_train,y_train,X_test,y_test,campos=preparardata(symbol,timeframe)
        y_pred = modelICPUSDT.predict(X_test)
        deriv_y_pred = np.diff(y_pred, axis=0)
        sc = MinMaxScaler(feature_range=(0,1))
        deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)
        print(deriv_y_pred_scaled[-1])
        if float(deriv_y_pred_scaled[-1]) >= 0.6:
            ut.sound()
            ut.sound()
            ut.sound()
            ut.printandlog(cons.nombrelog,'Encontrado '+symbol+'. Pendiente: '+str(deriv_y_pred_scaled[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))

        symbol='APTUSDT'
        print('chequeo '+symbol)
        X_train,y_train,X_test,y_test,campos=preparardata(symbol,timeframe)
        y_pred = modelAPTUSDT.predict(X_test)
        deriv_y_pred = np.diff(y_pred, axis=0)
        sc = MinMaxScaler(feature_range=(0,1))
        deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)
        print(deriv_y_pred_scaled[-1])
        if float(deriv_y_pred_scaled[-1]) >= 0.6:
            ut.sound()
            ut.sound()
            ut.sound()
            ut.printandlog(cons.nombrelog,'Encontrado '+symbol+'. Pendiente: '+str(deriv_y_pred_scaled[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))

        symbol='RNDRUSDT'
        print('chequeo '+symbol)
        X_train,y_train,X_test,y_test,campos=preparardata(symbol,timeframe)
        y_pred = modelRNDRUSDT.predict(X_test)
        deriv_y_pred = np.diff(y_pred, axis=0)
        sc = MinMaxScaler(feature_range=(0,1))
        deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)
        print(deriv_y_pred_scaled[-1])
        if float(deriv_y_pred_scaled[-1]) >= 0.6:
            ut.sound()
            ut.sound()
            ut.sound()
            ut.printandlog(cons.nombrelog,'Encontrado '+symbol+'. Pendiente: '+str(deriv_y_pred_scaled[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))

        symbol='CFXUSDT'
        print('chequeo '+symbol)
        X_train,y_train,X_test,y_test,campos=preparardata(symbol,timeframe)
        y_pred = modelCFXUSDT.predict(X_test)
        deriv_y_pred = np.diff(y_pred, axis=0)
        sc = MinMaxScaler(feature_range=(0,1))
        deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)
        print(deriv_y_pred_scaled[-1])
        if float(deriv_y_pred_scaled[-1]) >= 0.6:
            ut.sound()
            ut.sound()
            ut.sound()
            ut.printandlog(cons.nombrelog,'Encontrado '+symbol+'. Pendiente: '+str(deriv_y_pred_scaled[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))

        symbol='IDUSDT'
        print('chequeo '+symbol)
        X_train,y_train,X_test,y_test,campos=preparardata(symbol,timeframe)
        y_pred = modelIDUSDT.predict(X_test)
        deriv_y_pred = np.diff(y_pred, axis=0)
        sc = MinMaxScaler(feature_range=(0,1))
        deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)
        print(deriv_y_pred_scaled[-1])
        if float(deriv_y_pred_scaled[-1]) >= 0.6:
            ut.sound()
            ut.sound()
            ut.sound()
            ut.printandlog(cons.nombrelog,'Encontrado '+symbol+'. Pendiente: '+str(deriv_y_pred_scaled[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))

        symbol='ARBUSDT'
        print('chequeo '+symbol)
        X_train,y_train,X_test,y_test,campos=preparardata(symbol,timeframe)
        y_pred = modelARBUSDT.predict(X_test)
        deriv_y_pred = np.diff(y_pred, axis=0)
        sc = MinMaxScaler(feature_range=(0,1))
        deriv_y_pred_scaled = sc.fit_transform(deriv_y_pred)
        print(deriv_y_pred_scaled[-1])
        if float(deriv_y_pred_scaled[-1]) >= 0.6:
            ut.sound()
            ut.sound()
            ut.sound()
            ut.printandlog(cons.nombrelog,'Encontrado '+symbol+'. Pendiente: '+str(deriv_y_pred_scaled[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))
      
        print("duermo 15 min")    
        sleep(900)

if __name__ == '__main__':
    main()
