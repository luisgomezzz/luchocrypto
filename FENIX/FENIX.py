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

md.printandlog(cons.nombrelog,"FENIX")

def actualiza_trailing_stop(symbol):
    trailing_stop_price = 0.0
    ultimo_trailing_stop_price = trailing_stop_price
    while True:
        positionamt = md.get_positionamt(symbol)
        if positionamt == 0:
            print(f"actualiza_trailing_stop {symbol} - Ya se cerró la posicion. ")
            break
        else:
            data = md.obtiene_historial(symbol)
            atr = md.set_atr_periods(data)
            if positionamt>0: #Es un long
                trailing_stop_price = max(trailing_stop_price or -np.inf, data.Close[-1] - atr[-1] * md.n_atr)
                side='BUY'
            else: # Es un short
                trailing_stop_price = min(trailing_stop_price or np.inf, data.Close[-1] + atr[-1] * md.n_atr)
                side='SELL'
            if trailing_stop_price != ultimo_trailing_stop_price or ultimo_trailing_stop_price ==0.0:
                print(f"Actualizo Trailing stop {symbol} - {side}.")
                md.crea_stoploss (symbol,side,trailing_stop_price)
                ultimo_trailing_stop_price = trailing_stop_price
        sleep(900) # duerme 15 minutos (revisaria 2 veces por vela de 30 minutos)

# programa principal
def main():
    vueltas=0
    minutes_diff=0 
    balancetotal=md.balancetotal()
    reservas = 2965
    ##############START        
    print("Saldo: "+str(md.truncate(balancetotal,2)))
    print(f"PNL acumulado: {str(md.truncate(balancetotal-reservas,2))}")

    #Lee archivo de mmonedas filtradas
    listamonedas=[]
    with open(cons.pathroot+"lista_monedas_filtradas.txt", 'r') as fp:
        for line in fp:
            x = line[:-1]
            listamonedas.append(x)
    
    try:

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
                
                try:
                    data = md.obtiene_historial(symbol)
                    data = md.estrategia_bb(data)
                    
                    # CREA POSICION
                    side=''
                    if symbol not in posiciones:                        
                        ###BUY###
                        if  data.signal[-1] ==1:
                            side='BUY'
                        else:
                            ###SELL###
                            if data.signal[-1] ==-1:
                                side='SELL'
                        if side !='' and len(md.get_posiciones_abiertas()) < cantidad_posiciones and md.get_positionamt(symbol)==0.0:    
                            posiciones[symbol]=side
                            with open(cons.pathroot+"posiciones.json","w") as j:
                                json.dump(posiciones,j, indent=4)
                            md.printandlog(cons.nombrelog,'Entra en Trade '+symbol+'. Side: '+str(side)+' - hora: '+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))
                            md.sound()
                            md.sound() 
                            md.crea_posicion(symbol,side,porcentajeentrada=100) 
                            # STOP LOSS Y TAKE PROFIT 
                            entry_price = md.getentryprice(symbol)
                            if entry_price!=0.0:                                
                                stop_price = data.stop_loss[-1]
                                md.crea_stoploss (symbol,side,stop_price)
                                #profit_price = data.take_profit[-1]
                                #md.crea_takeprofit(symbol,preciolimit=profit_price,posicionporc=100,lado=posiciones[symbol])  
                                hilo = threading.Thread(target=actualiza_trailing_stop, args=(symbol,))
                                hilo.start()  

                    # CERRAR POSICION
                    else: 
                        
                        if md.get_positionamt(symbol)==0.0: 
                            # Se cerró la posición por limit o manual y se elimina del diccionario y archivo. 
                            # TAMBIEN SE CIERRAN LAS ORDENES QUE PUEDEN HABER QUEDADO ABIERTAS.
                            posiciones.pop(symbol)
                            with open(cons.pathroot+"posiciones.json","w") as j:
                                json.dump(posiciones,j, indent=4)
                            md.closeallopenorders(symbol)
                
                except:
                    pass        

                sys.stdout.write(f"\r{symbol} - T. vuelta: {md.truncate(minutes_diff,2)} \033[K")
                sys.stdout.flush()  

            sleep(10)

    except Exception as falla:
        _, _, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+"\n")
        pass  
    except KeyboardInterrupt:
        print("\nSalida solicitada. ")
        sys.exit()    

if __name__ == '__main__':
    main()
