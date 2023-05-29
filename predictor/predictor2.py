import pandas_ta as ta
from keras.layers import Dense, LSTM
import util as ut
from time import sleep
import datetime as dt
from tensorflow import keras
import os
import json
from binance.exceptions import BinanceAPIException
import sys
import inquirer
import pandas as pd
import numpy as np
from keras.models import Sequential
from sklearn.preprocessing import MinMaxScaler
import constantes as cons

ut.printandlog(cons.nombrelog,"PREDICTOR2")

umbralbajo=0.2
umbralalto=0.8

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
    data['timestamp']=data['Open Time']
    data.set_index('timestamp', inplace=True)

    data.dropna(inplace=True)
    data.drop(['Open Time','Close Time','Quote Asset Volume', 'TB Base Volume', 'TB Quote Volume','Number of Trades',
            'Ignore'], axis=1, inplace=True)
    stock_data = data
    pd.set_option('display.max_columns', None)

    #################################################################################################################
    X_feat = stock_data.iloc[:,0:3]
    #X_ft = StandardScaler().fit_transform(X_feat.values)

    X_ft = MinMaxScaler(feature_range=(0, 1)).fit_transform(X_feat.values)
    X_ft = pd.DataFrame(columns=X_feat.columns,data=X_ft,index=X_feat.index)

    def ltsm_split (data,n_steps):
        X, y = [], []
        for i in range(len(data)-n_steps+1):
            X.append(data[i:i + n_steps, :-1])
            y.append(data[i + n_steps-1, -1])
        return np.array(X),np.array(y)

    n_steps=1
    X1, y1 = ltsm_split(X_ft.values, n_steps=n_steps)

    train_split =0.8
    split_idx = int(np.ceil(len(X1)*train_split))

    X_train , X_test = X1[:split_idx], X1[split_idx:]
    y_train , y_test = y1[:split_idx], y1[split_idx:]
    #################################################################################################################   
    return X_train,y_train,X_test,y_test,data

def entrena_modelo(symbol):
    X_train,y_train,X_test,y_test,data=obtiene_historial(symbol)
    print('entrena '+symbol)
    lstm=Sequential()
    lstm.add(LSTM(32,input_shape=(X_train.shape[1],X_train.shape[2]),activation='relu',return_sequences=True))
    lstm.add(Dense(1))
    lstm.compile(loss='mean_squared_error',optimizer='adam')
    lstm.fit(X_train,y_train,epochs=20,batch_size=4,verbose=2,shuffle=False)
    lstm.save('predictor/modelos/lstm'+symbol+'.h5')

def filtrado_de_monedas (): 
    print("filtrado_de_monedas...")   
    lista_de_monedas_filtradas = []
    lista_de_monedas = ut.lista_de_monedas ()
    for par in lista_de_monedas:
        try:  
            volumeOf24h=ut.volumeOf24h(par)
            capitalizacion=ut.capitalizacion(par)
            if volumeOf24h >= cons.minvolumen24h and capitalizacion >= cons.mincapitalizacion:
                lista_de_monedas_filtradas.append(par)
        except Exception as ex:
            pass        
        except KeyboardInterrupt as ky:
            print("\nSalida solicitada. ")
            sys.exit()   
    print("Fin de filtrado_de_monedas.")   
    return lista_de_monedas_filtradas    

# programa principal
def main():
    #Lee archivo de mmonedas filtradas
    listamonedas=[]
    with open(cons.pathroot+"lista_monedas_filtradas.txt", 'r') as fp:
        for line in fp:
            x = line[:-1]
            listamonedas.append(x)
    
    try:
        if modo_ejecucion in [0,1,2]: # solo opciones válidas

            if modo_ejecucion in [1,2] or len(listamonedas)==0: 
                listamonedas=filtrado_de_monedas()
                for symbol in listamonedas:
                    entrena_modelo(symbol)
                ## Escribe el archivo de monedas filtradas
                with open(cons.pathroot+"lista_monedas_filtradas.txt", 'w') as fp:
                    for item in listamonedas:
                        fp.write("%s\n" % item)
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
                        
                        X_train,y_train,X_test,y_test,data=obtiene_historial(symbol)
                        
                        if len(data)>=800:# chequea que haya suficiente historial para que la prediccion sea coherente.                            

                            lstm = keras.models.load_model('predictor/modelos/lstm'+symbol+'.h5')

                            y_pred = lstm.predict(X_test)
                            # Calcular las derivadas
                            deriv_y_pred = np.diff(y_pred, axis=0)
                            deriv_y_pred2 = np.diff(deriv_y_pred, axis=0)
                            # Ajustar la forma de deriv_y_pred
                            deriv_y_pred = deriv_y_pred.reshape(-1, 1)
                            deriv_y_pred2 = deriv_y_pred2.reshape(-1, 1)
                            # Escalar las derivadas
                            scaler1 = MinMaxScaler(feature_range=(0, 1))
                            deriv_y_pred_scaled = scaler1.fit_transform(deriv_y_pred)
                            #scaler2 = MinMaxScaler(feature_range=(0, 1))
                            #deriv_y_pred_scaled2 = scaler2.fit_transform(deriv_y_pred2)

                            print(f"derivada 1ra: {deriv_y_pred_scaled[-1]}")
                            # CREA POSICION
                            side=''
                            if symbol not in posiciones:
                                data['atr']=ta.atr(data.High, data.Low, data.Close)
                                atr=data.atr.iloc[-1]
                                ###BUY###
                                if  deriv_y_pred_scaled[-1] >= umbralalto and y_test[-1] > 0.5:
                                    side='BUY'
                                    atr=atr*1
                                else:
                                    ###SELL###
                                    if deriv_y_pred_scaled[-1] <= umbralbajo and y_test[-1] < 0.5:
                                        side='SELL'
                                        atr=atr*-1
                                if side !='' and len(ut.get_posiciones_abiertas()) < cantidad_posiciones and ut.get_positionamt(symbol)==0.0:    
                                    posiciones[symbol]=side
                                    with open(cons.pathroot+"posiciones.json","w") as j:
                                        json.dump(posiciones,j, indent=4)
                                    ut.printandlog(cons.nombrelog,'Entra en Trade '+symbol+'. Side: '+str(side)+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))
                                    ut.sound()
                                    ut.sound() 
                                    posicionpredictor(symbol,side,porcentajeentrada=100) 
                                    # STOP LOSS Y TAKE PROFIT 
                                    entry_price = ut.getentryprice(symbol)
                                    if entry_price!=0.0:
                                        profit_price = entry_price + 1*atr
                                        stop_price = entry_price - 1.5*atr                                        
                                        ut.creostoploss (symbol,side,stop_price)                                       
                                        ut.creotakeprofit(symbol,preciolimit=profit_price,posicionporc=100,lado=posiciones[symbol])  

                            # CERRAR POSICION
                            else: 
                                if ut.get_positionamt(symbol)==0.0: 
                                    # Se cerró la posición por limit o manual y se elimina del diccionario y archivo. 
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
