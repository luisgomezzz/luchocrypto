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

listamonedas = ['BTCUSDT' , 'ETHUSDT' , 'XRPUSDT' , 'LTCUSDT' , 'LINKUSDT', 'ADAUSDT' , 'BNBUSDT' , 'ATOMUSDT'
, 'DOGEUSDT', 'RLCUSDT' , 'DOTUSDT' , 'SOLUSDT' , 'AVAXUSDT', 'FTMUSDT' , 'TOMOUSDT', 'FILUSDT' , 'MATICUSDT'
, 'ALPHAUSDT', 'HBARUSDT', 'LINAUSDT', 'DYDXUSDT', 'CTSIUSDT', 'OPUSDT' , 'INJUSDT' , 'ICPUSDT' , 'APTUSDT' 
, 'RNDRUSDT', 'CFXUSDT' , 'IDUSDT' , 'ARBUSDT' , 'EDUUSDT']

script = ''
script = script+"\nsymbol='XXXXUSDT'"
script = script+"\nX_train,y_train,X_test,y_test,cantidadcamposentrenar=preparardata(symbol,timeframe)"
script = script+"\nnp.random.seed(10)"
script = script+"\nlstm_input = Input(shape=(backcandles, cantidadcamposentrenar), name='lstm_input')"
script = script+"\nlstm_layer1 = LSTM(150, return_sequences=True, name='lstm_layer1')(lstm_input)"
script = script+"\nlstm_layer2 = LSTM(150, name='lstm_layer2')(lstm_layer1)"
script = script+"\ndense_layer = Dense(1, name='dense_layer')(lstm_layer2)"
script = script+"\noutput_layer = Activation('linear', name='output')(dense_layer)"
script = script+"\nmodelXXXXUSDT = Model(inputs=lstm_input, outputs=output_layer)"
script = script+"\nadam = optimizers.Adam()"
script = script+"\nmodelXXXXUSDT.compile(optimizer=adam, loss='mse')"
script = script+"\nprint('entrena '+symbol)"
script = script+"\nmodelXXXXUSDT.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split=0.1)"


script2 =''
script2 = script2+"\nsymbol='XXXXUSDT'"
script2 = script2+"\nprint('chequeo '+symbol)"
script2 = script2+"\nX_train,y_train,X_test,y_test,campos=preparardata(symbol,timeframe)"
script2 = script2+"\ny_pred = modelXXXXUSDT.predict(X_test)"
script2 = script2+"\nderiv_y_pred = np.diff(y_pred, axis=0)"
script2 = script2+"\nsc = MinMaxScaler(feature_range=(0,1))"
script2 = script2+"\nderiv_y_pred_scaled = sc.fit_transform(deriv_y_pred)"
script2 = script2+"\nprint(deriv_y_pred_scaled[-1])"
script2 = script2+"\nif float(deriv_y_pred_scaled[-1]) >= 0.6:"
script2 = script2+"\n    ut.sound()"
script2 = script2+"\n    ut.sound()"
script2 = script2+"\n    ut.sound()"
script2 = script2+"\n    ut.printandlog(cons.nombrelog,'Encontrado '+symbol+'. Pendiente: '+str(deriv_y_pred_scaled[-1])+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))"




for i in listamonedas:
    #scriptmodificado=script.replace('XXXXUSDT',i)
    #print(scriptmodificado)
    script2modificado=script2.replace('XXXXUSDT',i)
    print(script2modificado)


