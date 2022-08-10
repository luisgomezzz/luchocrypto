#****************************************************************************************
# version 2.0
#
#****************************************************************************************

from time import sleep
from binance.exceptions import BinanceAPIException
import sys, os
import pandas as pd
pd.core.common.is_list_like = pd.api.types.is_list_like
import yfinance as yahoo_finance
yahoo_finance.pdr_override()
sys.path.insert(1,'./')
import utilidades as ut
import datetime as dt
from datetime import datetime
import threading
from time import sleep
##CONFIG########################
client = ut.client
exchange = ut.exchange
nombrelog = "log_santa2.txt"
################################
temporalidad = '1m'
operando=[] #lista de monedas que se están operando
apalancamiento = 10 #siempre en 10 segun la estrategia de santi
procentajeperdida = 10 #porcentaje de mi capital total maximo a perder

def updating(par,lado):

    print("updating... "+par+"-"+lado)
    tamanioposicion = ut.get_positionamt(par)    

    while tamanioposicion!=0: 
        #actualizar takeprofit
        if tamanioposicion!=ut.get_positionamt(par):
            if lado=='BUY':
                profitprice = ut.getentryprice(par)*(1+1.1/100)
                
            else:
                profitprice = ut.getentryprice(par)*(1-1.1/100)
                
            ut.binancetakeprofit(par,lado,profitprice)
            tamanioposicion = ut.get_positionamt(par)            
    
    print("Final del trade "+par+" en "+lado)

def trading(par,lado):
    #Actualiza el profit
    updating(par,lado)
    #cierra todas las 'ordenes
    ut.closeallopenorders(par)
    #ya no lo estoy operando
    operando.remove(par)

def main() -> None:

    ##PARAMETROS##########################################################################################
    mazmorra=['1000SHIBUSDT','1000XECUSDT','BTCUSDT_220624','ETHUSDT_220624','ETHUSDT_220930','BTCUSDT_220930','BTCDOMUSDT'
    ,'ATOMUSDT'] #Monedas que no quiero operar 
    toppar=['ADAUSDT','BNBUSDT','BTCUSDT','AXSUSDT','DOGEUSDT','ETHUSDT','MATICUSDT','TRXUSDT'] #monedas top
    ventana = 40 #Ventana de búsqueda en minutos.   
    lista_de_monedas = client.futures_exchange_info()['symbols'] #obtiene lista de monedas
    posicioncreada = False
    minvolumen24h=float(50000000.00)
    vueltas=0
    minutes_diff=0
    lista_monedas_filtradas=[]
    mensaje=''
    balanceobjetivo = 24.00+24.88+71.53+71.62
    mensajeposicioncompleta=''        
    margen = 'CROSSED'
    porcentajeentrada = 10 #porcentaje de la cuenta para crear la posición (10)
    tradessimultaneos = 2 #Número máximo de operaciones en simultaneo
    distanciatoppar = 1 # distancia entre compensaciones cuando el par está en el top
    distancianotoppar = 1.7 # distancia entre compensaciones cuando el par no está en el top
    cantidadcompensaciones = 8 #compensaciones
    porcentajevariacionnormal=5.0
    porcentajevariacionriesgo=7.0
    maximavariacion=0.0
    ##############START    
    
    ut.clear() #limpia terminal
    print("Objetivo a: "+str(ut.truncate(balanceobjetivo-ut.balancetotal(),2)))
    for s in lista_de_monedas:
        try:  
            par = s['symbol']
            sys.stdout.write("\rFiltrando monedas: "+par+"\033[K")
            sys.stdout.flush()
            if float(client.futures_ticker(symbol=par)['quoteVolume'])>minvolumen24h and 'USDT' in par and par not in mazmorra:
                lista_monedas_filtradas.append(par)
        except Exception as ex:
            pass        
        except KeyboardInterrupt as ky:
            print("\nSalida solicitada. ")
            sys.exit()

    try:

        while True:
            #en operaciones riesgosas las variaciones deben ser mayores
            if dt.datetime.today().hour == 21:
                porcentaje = porcentajevariacionriesgo
            else:
                porcentaje = porcentajevariacionnormal
            
            for par in lista_monedas_filtradas:

                # para calcular tiempo de vuelta completa                
                if vueltas==0:
                    datetime_start = datetime.today()
                else:
                    if vueltas == len(lista_monedas_filtradas):
                        datetime_end = datetime.today()
                        minutes_diff = (datetime_end - datetime_start).total_seconds() / 60.0
                        vueltas==0
                try:
                    try:
                        if par not in operando:     

                            df=ut.calculardf (par,temporalidad,ventana)
                            df = df[:-1]
                            preciomenor=df.close.min()
                            preciomayor=df.close.max()
                            precioactual=ut.currentprice(par)

                            if (precioactual - preciomenor)*(100/preciomenor)>0:
                                variacion = (precioactual - preciomenor)*(100/preciomenor)
                            else:
                                variacion = (preciomenor - precioactual)*(100/preciomenor)
                            
                            if variacion > maximavariacion:
                                maximavariacion = variacion
                                maximavariacionpar = par
                            
                            sys.stdout.write("\rBuscando. Ctrl+c para salir. Par: "+par+" - Variación: "+str(ut.truncate(variacion,2))+"% - Tiempo de vuelta: "+str(ut.truncate(minutes_diff,2))+" min - Monedas analizadas: "+ str(len(lista_monedas_filtradas))+" - máxima variación "+maximavariacionpar+" "+str(ut.truncate(maximavariacion,2))+"%\033[K")
                            sys.stdout.flush()
                            ################

                            if  ((precioactual - preciomenor)*(100/preciomenor)) >= porcentaje and precioactual >= preciomayor:
                                vol=float(client.futures_ticker(symbol=par)['quoteVolume'])
                                print("SELL-cumple1 vol: "+str(vol))
                                if (vol >= float(100000000.00)
                                or (vol <  float(100000000.00) and ((precioactual - preciomenor)*(100/preciomenor)) >= porcentajevariacionriesgo)
                                    ):
                                    ############################
                                    ####### POSICION SELL ######
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

                                    lado='SELL'
                                    print("\n*********************************************************************************************")
                                    mensaje="Trade - "+par+" - "+lado
                                    mensaje=mensaje+"\nSubió un "+str(ut.truncate(variacion,3))+" %"
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
                              
                            else:
                                if  ((preciomenor - precioactual)*(100/preciomenor)) >= porcentaje and precioactual <= preciomenor:
                                    vol=float(client.futures_ticker(symbol=par)['quoteVolume'])
                                    print("BUY-cumple1 vol: "+str(vol))
                                    if (vol >= float(100000000)
                                    or (vol <  float(100000000) and ((preciomenor - precioactual)*(100/preciomenor)) >= porcentajevariacionriesgo)
                                        ):
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

                            if posicioncreada==True:     
                                                       
                                operando.append(par)
                                hayguita = True
                                i = 1
                                distanciaporc = 0.0
                                tamanio = ut.get_positionamt(par)
                                tamaniototal = 0.0

                                #CREA COMPENSACIONES
                                while hayguita==True and i<=cantidadcompensaciones:
                                    tamanio=tamanio*(1+30/100)
                                    tamaniototal=tamaniototal+tamanio
                                    distanciaporc=distanciaporc+paso                                    
                                    hayguita = ut.compensaciones(par,client,lado,tamanio,distanciaporc)                       
                                    i=i+1            

                                # PUNTO DE ATAQUE
                                ut.compensaciones(par,client,lado,tamaniototal*3,distanciaporc+1)    

                                hilo = threading.Thread(target=trading, args=(par,lado))
                                hilo.start()

                                posicioncreada=False       
                                
                                print("\n*********************************************************************************************")
                                #escribo file
                                f = open(nombrelog, "a")
                                f.write(mensaje)
                                f.write("\n*********************************************************************************************\n")
                                f.close()

                                if len(operando)>=tradessimultaneos:
                                    print("\nSe alcanzó el número máximo de trades simultaneos.")
                                while len(operando)>=tradessimultaneos:                                    
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
            
                vueltas=vueltas+1

    except BinanceAPIException as a:
       print("Error6 - Par:",par,"-",a.status_code,a.message)
       pass

if __name__ == '__main__':
    main()

