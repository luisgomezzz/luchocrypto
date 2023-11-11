import modulos as md
import datetime as dt
import os
import json
import sys
import constantes as cons
from datetime import datetime
from time import sleep
import threading
import numpy as np
import inquirer
import ccxt
from datetime import datetime

RED   = "\033[1;31m"  
BLUE  = "\033[1;34m"
CYAN  = "\033[1;36m"
GREEN = "\033[0;32m"
RESET = "\033[0;0m"
BOLD    = "\033[;1m"
REVERSE = "\033[;7m"
YELLOW = "\33[33m"
#EXCHANGE SELECT
questions = [
inquirer.List('Estrategia',
                message="Seleccionar estrategia: ",
                choices=['estrategia_smart','estrategia_haz'],
            ),
]
answers = inquirer.prompt(questions)
estrategia_name=answers['Estrategia']
if estrategia_name=='estrategia_haz':
    sys.stdout.write(RED)            
if estrategia_name=='estrategia_smart':
    sys.stdout.write(YELLOW)    

md.printandlog(cons.nombrelog, estrategia_name)   

def dataframe_estrategia(symbol,estrategia_name):
    balance = md.balancetotal()
    timeframe = '1h'
    if estrategia_name=='estrategia_haz':
        data = md.estrategia_haz(symbol,alerta=False)
    if estrategia_name=='estrategia_smart':
        data = md.estrategia_smart(symbol, debug = False, refinado = False, file_source = False, timeframe = timeframe, balance = balance)
    return data

posiciones={}
lista_monedas_filtradas = estrategia_name+"_symbols.txt"

def actualiza_trailing_stop(symbol):
    trailing_stop_price = 0.0
    ultimo_trailing_stop_price = trailing_stop_price
    global posiciones
    trailing_stop_id_anterior = 0
    while True:
        positionamt = md.get_positionamt(symbol)
        if positionamt == 0.0:
            print(f"\nActualiza_trailing_stop {symbol} - Ya se cerró la posicion. ")
            # Se cerró la posición por limit o manual y se elimina del diccionario y archivo. 
            # TAMBIEN SE CIERRAN LAS ORDENES QUE PUEDEN HABER QUEDADO ABIERTAS.
            posiciones.pop(symbol)
            with open(cons.pathroot+"posiciones.json","w") as j:
                json.dump(posiciones,j, indent=4)
            md.closeallopenorders(symbol)            
            break
        else:
            data = dataframe_estrategia(symbol,estrategia_name)
            atr = md.set_atr_periods(data)
            if positionamt>0: #Es un long
                trailing_stop_price = max(trailing_stop_price or -np.inf, data.Close[-1] - atr[-1] * data.n_atr[-1])
                side='BUY'
            else: # Es un short
                trailing_stop_price = min(trailing_stop_price or np.inf, data.Close[-1] + atr[-1] * data.n_atr[-1])
                side='SELL'
            if data.cierra[-1]==True:
                md.closeposition(symbol,side)
            else:
                if trailing_stop_price != ultimo_trailing_stop_price or ultimo_trailing_stop_price ==0.0:
                    print(f"\nActualizo Trailing stop {symbol} - {side}.")
                    creado,trailing_stop_id=md.crea_stoploss (symbol,side,trailing_stop_price)
                    ultimo_trailing_stop_price = trailing_stop_price
                    if creado==True:
                        if trailing_stop_id_anterior==0:
                            trailing_stop_id_anterior=trailing_stop_id
                        else:
                            try:
                                cons.exchange.cancel_order(trailing_stop_id_anterior, symbol)
                                trailing_stop_id_anterior=trailing_stop_id
                                print("\nTrailing_stop_id anterior cancelado. "+symbol)
                            except:
                                trailing_stop_id_anterior=trailing_stop_id
                                pass

# programa principal
def main():
    vueltas=0
    minutes_diff=0 
    balancetotal=md.balancetotal()
    reservas = 3065
    global posiciones
    ##############START        
    print("Saldo: "+str(md.truncate(balancetotal,2)))
    print(f"PNL acumulado: {str(md.truncate(balancetotal-reservas,2))}")
    exchange = ccxt.binance()
    try:

        while True:

            # Obtiene la hora del servidor de Binance
            server_time = exchange.fetch_time()
            # Convierte la marca de tiempo a formato de fecha y hora
            hora_utc = datetime.utcfromtimestamp(server_time / 1000.0).strftime('%H')

            # Lee archivo de configuracion
            with open(cons.pathroot+"configuracion.json","r") as j:
                dic_configuracion=json.load(j) 
            cantidad_posiciones = dic_configuracion['cantidad_posiciones']
            restriccionhoraria = dic_configuracion['restriccionhoraria']
            # Lee archivo de posiciones
            with open(cons.pathroot+"posiciones.json","r") as j:
                posiciones=json.load(j)    

            #Lee archivo de mmonedas filtradas
            listamonedas=[]            
            f = open(os.path.join(cons.pathroot, lista_monedas_filtradas), 'a',encoding="utf-8")
            f.close()      
            with open(cons.pathroot+lista_monedas_filtradas, 'r') as fp:
                for line in fp:
                    x = line[:-1]
                    listamonedas.append(x)

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
                
                if md.salida_solicitada_flag:
                    print("\nSalida solicitada. ")
                    sys.exit()

                try:

                    data = dataframe_estrategia(symbol,estrategia_name)
                    
                    # CREA POSICION
                    side=''
                    if symbol not in posiciones:                        
                        ###BUY###
                        if  data.signal[-1] ==1 or data.signal[-2] ==1:
                            side='BUY'
                        else:
                            ###SELL###
                            if data.signal[-1] ==-1 or data.signal[-2] ==-1:
                                side='SELL'
                        if (side !='' 
                            and len(md.get_posiciones_abiertas()) < cantidad_posiciones 
                            and md.get_positionamt(symbol) == 0.0
                            and (16 >= hora_utc >= 0 or restriccionhoraria == 0) # killzones de asia, london y NY
                            ):
                            print(f"Symbol: {symbol} - Hora: {dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')} - Side: {side} - TP: {data.take_profit[-1]} - SL: {data.stop_loss[-1]} - porc_ent: {data.porcentajeentrada[-1]}")   
                            md.sound()
                            md.sound() 
                            porcentajeentrada = data.porcentajeentrada[-1]
                            md.crea_posicion(symbol,side,porcentajeentrada) 
                            # STOP LOSS Y TAKE PROFIT 
                            entry_price = md.getentryprice(symbol)
                            if entry_price!=0.0:                                
                                posiciones[symbol]=side
                                with open(cons.pathroot+"posiciones.json","w") as j:
                                    json.dump(posiciones,j, indent=4)
                                md.printandlog(cons.nombrelog,'Entra en Trade '+symbol+'. Side: '+str(side)+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))
                                stop_price = data.stop_loss[-1]
                                md.crea_stoploss (symbol,side,stop_price)
                                profit_price = data.take_profit[-1]
                                if not np.isnan(data.take_profit[-1]):
                                    md.crea_takeprofit(symbol,preciolimit=profit_price,posicionporc=100,lado=posiciones[symbol])  
                                #hilo = threading.Thread(target=actualiza_trailing_stop, args=(symbol,))
                                #hilo.start()  

                except:
                    pass        

                sys.stdout.write(f"\r{symbol} - T. vuelta: {md.truncate(minutes_diff,2)} \033[K")
                sys.stdout.flush()  

    except Exception as falla:
        _, _, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+"\n")
        pass  
    except KeyboardInterrupt:
        md.salida_solicitada()

if __name__ == '__main__':
    main()
