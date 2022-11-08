#****************************************************************************************
# version 1.0
#
#****************************************************************************************

from this import d
from binance.exceptions import BinanceAPIException
import sys, os
sys.path.insert(1,'./')
import utilidades as ut
##CONFIG
client = ut.client
exchange = ut.exchange
## PARAMETROS FUNDAMENTALES 
temporalidad = '5m'
apalancamiento = 15 #siempre en 10 segun la estrategia de santi
procentajeperdida = 10 #porcentaje de mi capital total maximo a perder
porcentajeentrada = 10 #porcentaje de la cuenta para crear la posición (10)
ventana = 2 #Ventana de búsqueda en minutos.   
## VARIABLES GLOBALES 
incrementocompensacionporc = 30 #porcentaje de incremento del tamaño de la compensacion con respecto a su anterior

###################################################################################################################
###################################################################################################################
###################################################################################################################

def main() -> None:

    lista_de_monedas = ['ETHUSDT']
    posicioncreada = False
    mensaje=''
    mensajeposicioncompleta=''        
    margen = 'CROSSED'
    distanciatoppar = 1 # distancia entre compensaciones cuando el par está en el top
    cantidadcompensaciones = 8 #compensaciones
    limite=1460
    ##############START    
    
    ut.clear() #limpia terminal

    try:

        while True:
            
            for par in lista_de_monedas:

                try:

                    try:
                        
                        df=ut.calculardf (par,temporalidad,ventana)
                        precioactual=ut.currentprice(par)

                        sys.stdout.write("\rAnalizando... "+par+"\033[K")
                        sys.stdout.flush()                            

                        if  (df.open.iloc[-2] > df.close.iloc[-2] #vela anterior roja
                            and df.open.iloc[-2] > limite and df.close.iloc[-2] < limite # vela anterior cruzando el limite
                            and precioactual < df.open.iloc[-1] < limite #vela acutal cruzando 
                            ):
                            ############################
                            ####### POSICION SELL ######
                            ############################
                            ut.sound()
                            sys.exit()
                            '''
                            print("\rDefiniendo apalancamiento...")
                            client.futures_change_leverage(symbol=par, leverage=apalancamiento)
                            try: 
                                print("\rDefiniendo Cross/Isolated...")
                                client.futures_change_margin_type(symbol=par, marginType=margen)
                            except BinanceAPIException as a:
                                if a.message!="No need to change margin type.":
                                    print("Except 7",a.status_code,a.message)
                                else:
                                    print("Done!")   
                                pass

                            lado='SELL'
                            print("\n*********************************************************************************************")
                            mensaje="Trade - "+par+" - "+lado
                            mensaje=mensaje+"\nSubió un "+str(ut.truncate(variacion,3))+" %"
                            mensaje=mensaje+"\nInicio: "+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))
                            print(mensaje)

                            paso = distanciatoppar

                            distanciaporc=(cantidadcompensaciones+2)*paso                               
                            posicioncreada,mensajeposicioncompleta=ut.posicioncompletasanta(par,lado,porcentajeentrada,distanciaporc) 
                            print(mensajeposicioncompleta)
                            mensaje=mensaje+mensajeposicioncompleta   
                                                 
                          
                        else:
                            if  variacion >= porcentaje and precioactual <= preciomenor:
                                ############################
                                ####### POSICION BUY ######
                                ############################
                                ut.sound()
                                print("\rDefiniendo apalancamiento...")
                                client.futures_change_leverage(symbol=par, leverage=apalancamiento)
                                try: 
                                    print("\rDefiniendo Cross/Isolated...")
                                    client.futures_change_margin_type(symbol=par, marginType=margen)
                                except BinanceAPIException as a:
                                    if a.message!="No need to change margin type.":
                                        print("Except 7",a.status_code,a.message)
                                    else:
                                        print("Done!")   
                                    pass

                                lado='BUY'
                                print("\n*********************************************************************************************")
                                mensaje="Trade - "+par+" - "+lado
                                mensaje=mensaje+"\nBajó un "+str(ut.truncate(variacion,3))+" %"
                                mensaje=mensaje+"\nInicio: "+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))
                                print(mensaje)    
                                if par in toppar:
                                    paso = distanciatoppar
                                else:
                                    paso = distancianotoppar
                                distanciaporc=(cantidadcompensaciones+2)*paso
                                posicioncreada,mensajeposicioncompleta=ut.posicioncompletasanta(par,lado,porcentajeentrada,distanciaporc) 
                                print(mensajeposicioncompleta)
                                mensaje=mensaje+mensajeposicioncompleta
                        '''
                        if posicioncreada==True:                                     

                            hayguita = True
                            i = 1
                            distanciaporc = 0.0
                            tamanio = ut.get_positionamt(par)
                            tamaniototal = tamanio
                            precioporcantidad = tamanio*ut.getentryprice(par)
                            #CREA COMPENSACIONES
                            '''
                            while hayguita==True and i<=cantidadcompensaciones:
                                tamanio=tamanio*(1+incrementocompensacionporc/100)                                    
                                distanciaporc=distanciaporc+paso                                    
                                hayguita,preciolimit,tamanioformateado = ut.compensaciones(par,client,lado,tamanio,distanciaporc) 
                                precioporcantidad = precioporcantidad+(tamanioformateado*preciolimit)
                                tamaniototal = tamaniototal+tamanioformateado
                                i=i+1            

                            # PUNTO DE ATAQUE
                            # si ya creó todas las compensaciones se crea la de ataque a una distancia del 1% de la última
                            if i==cantidadcompensaciones+1:
                                tamanio=tamaniototal*3
                                hayguita,preciolimit,tamanioformateado = ut.compensaciones(par,client,lado,tamanio,distanciaporc+1)    
                                if hayguita==False:
                                    print("\nNo se pudo crear la compensación de ataque...\n")
                                else:
                                    print("\nCompensación de ataque creada...\n")
                                    precioporcantidad = precioporcantidad+(tamanioformateado*preciolimit)
                                    tamaniototal = tamaniototal+tamanioformateado
                                    if lado=='BUY':
                                        stopprice=preciolimit*(1-1/100)
                                    else:
                                        stopprice=preciolimit*(1+1/100)
                                    #se crea el stop price nuevo a una distancia del 1% de la compensacion de ataque
                                    ut.binancestoploss (par,lado,stopprice) 

                            precioposicionfinal=precioporcantidad/tamaniototal
                            
                            print("precioporcantidad: "+str(precioporcantidad))
                            print("tamaniototal: "+str(tamaniototal))
                            print("precioposicionfinal: "+str(precioposicionfinal))
                            print("precio en que debería ir stop: "+str(ut.preciostopsanta(procentajeperdida,tamaniototal,precioposicionfinal)))

                            hilo = threading.Thread(target=trading, args=(par,lado))
                            hilo.start()

                            posicioncreada=False   
                            maximavariacion = 0.0    
                            
                            print("\n*********************************************************************************************")
                            #escribo file
                            f = open(nombrelog, "a")
                            f.write(mensaje)
                            f.write("\n*********************************************************************************************\n")
                            f.close()
                            '''
                        ut.waiting(1)
                    except KeyboardInterrupt:
                        print("\nSalida solicitada. ")
                        sys.exit()
                    except BinanceAPIException as e:
                        if e.message!="Invalid symbol.":
                            print("\nError3 - Par:",par,"-",e.status_code,e.message)                            
                        pass
                    except Exception as falla:
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                        print("\nError4: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - par: "+par)
                        pass

                except KeyboardInterrupt:
                    print("\nSalida solicitada.")
                    sys.exit()            
                except BinanceAPIException as a:
                    if a.message!="Invalid symbol.":
                        print("Error5 - Par:",par,"-",a.status_code,a.message)
                    pass

    except BinanceAPIException as a:
       print("Error6 - Par:",par,"-",a.status_code,a.message)
       pass

if __name__ == '__main__':
    main()

