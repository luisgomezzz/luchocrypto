import modulos as md
import datetime as dt
import os
import json
import sys
import constantes as cons
from datetime import datetime
from time import sleep

md.printandlog(cons.nombrelog,"FENIX")

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
                
                data = md.obtiene_historial(symbol)
                data = md.estrategia(data)
                
                if True:
                    
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
                                profit_price = data.take_profit[-1]
                                stop_price = data.stop_loss[-1]
                                md.crea_stoploss (symbol,side,stop_price)                                       
                                md.crea_takeprofit(symbol,preciolimit=profit_price,posicionporc=100,lado=posiciones[symbol])  

                    # CERRAR POSICION
                    else: 
                        
                        if md.get_positionamt(symbol)==0.0: 
                            # Se cerró la posición por limit o manual y se elimina del diccionario y archivo. 
                            # TAMBIEN SE CIERRAN LAS ORDENES QUE PUEDEN HABER QUEDADO ABIERTAS.
                            posiciones.pop(symbol)
                            with open(cons.pathroot+"posiciones.json","w") as j:
                                json.dump(posiciones,j, indent=4)
                            md.closeallopenorders(symbol)

                sys.stdout.write(f"\r{symbol} - T. vuelta: {md.truncate(minutes_diff,2)} \033[K")
                sys.stdout.flush()  
            
            sleep(10)

    except Exception as falla:
        _, _, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+"\n")
        pass  

if __name__ == '__main__':
    main()
