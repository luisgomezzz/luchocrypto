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
import constantes as cons
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler
ut.printandlog(cons.nombrelog,"PREDICTOR2")

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

def entrena_modelo(symbol):
    X_train,y_train,X_test,y_test,data=ut.obtiene_historial(symbol)
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

def calcular_porcentaje_tiempo(df, temporalidad):
    # Calcula el porcentaje de tiempo transcurrido desde la última fila hasta el momento.
    # se usa para entrar temprano en el trade.
    tiempo_vela = pd.Timedelta(minutes=temporalidad)
    tiempo_transcurrido = dt.datetime.today() - (df.index[-1] - dt.timedelta(hours=3))  
    porcentaje_tiempo = (tiempo_transcurrido.total_seconds() / tiempo_vela.total_seconds()) * 100
    return porcentaje_tiempo

# programa principal
def main():
    vueltas=0
    minutes_diff=0 
    balancetotal=ut.balancetotal()
    reservas = 2965
    ##############START        
    print("Saldo: "+str(ut.truncate(balancetotal,2)))
    print(f"PNL acumulado: {str(ut.truncate(balancetotal-reservas,2))}")

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
                        # para calcular tiempo de vuelta completa                
                        if vueltas == 0:
                            datetime_start = datetime.today()
                            vueltas = 1
                        else:
                            if vueltas == len(listamonedas):
                                datetime_end = datetime.today()
                                minutes_diff = (datetime_end - datetime_start).total_seconds() / 60.0
                                vueltas = 0
                            else:
                                vueltas = vueltas+1                        
                        
                        data = ut.estrategia(symbol)
                        
                        if len(data)>=200:# chequea que haya suficiente historial para que la prediccion sea coherente. 
                            
                            # CREA POSICION
                            side=''
                            if symbol not in posiciones:
                                tiempo_transcurrido = calcular_porcentaje_tiempo(data, temporalidad=30) < 25
                                ###BUY###
                                if  tiempo_transcurrido and data.signal[-1] ==1:
                                    side='BUY'
                                else:
                                    ###SELL###
                                    if tiempo_transcurrido and data.signal[-1] ==-1:
                                        side='SELL'
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
                                        profit_price = data.take_profit[-1]
                                        stop_price = data.stop_loss[-1]
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

                        sys.stdout.write(f"\r{symbol} - T. vuelta: {ut.truncate(minutes_diff,2)} \033[K")
                        sys.stdout.flush()  

    except Exception as falla:
        _, _, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+"\n")
        pass  

if __name__ == '__main__':
    main()
