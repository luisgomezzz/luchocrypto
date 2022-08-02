#****************************************************************************************
# version 2.0
#
#****************************************************************************************

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
import pandas_ta as pta
from time import sleep

##CONFIG########################
client = ut.client
exchange = ut.exchange
botlaburo = ut.creobot('laburo')      
nombrelog = "log_santa2.txt"
################################

def main() -> None:

    ##PARAMETROS##########################################################################################
    mazmorra=['1000SHIBUSDT','1000XECUSDT','BTCUSDT_220624','ETHUSDT_220624','ETHUSDT_220930','BTCUSDT_220930'] #Monedas que no quiero operar 
    ventana = 40 #Ventana de búsqueda en minutos.   
    lista_de_monedas = client.futures_exchange_info()['symbols'] #obtiene lista de monedas
    posicioncreada = False
    minvolumen24h=float(100000000)
    vueltas=0
    minutes_diff=0
    lista_monedas_filtradas=[]
    mensaje=''
    temporalidad='1m'   
    ratio = 1/(0.5) #Risk/Reward Ratio
    mensajeposicioncompleta=''    
    apalancamiento = 10 #siempre en 10 segun la estrategia de santi
    margen = 'CROSSED'
    porcentaje = 5 #porcentaje de variacion para entrar 
    porcentajeentrada = 10 #porcentaje de la cuenta para crear la posición (10)
        
    ##############START
    ut.clear() #limpia terminal
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

            for par in lista_monedas_filtradas:
                if par not in mazmorra:
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
                                                            
                            sys.stdout.write("\rBuscando. Ctrl+c para salir. Par: "+par+" - Tiempo de vuelta: "+str(ut.truncate(minutes_diff,2))+" min - Monedas analizadas: "+ str(len(lista_monedas_filtradas))+"\033[K")
                            sys.stdout.flush()
                            
                            ###############

                            trades = ut.binancetrades(par,ventana)
                            preciomenor = float(min(trades, key=lambda x:x['p'])['p'])
                            precioactual = float(client.get_symbol_ticker(symbol=par)["price"])  
                            preciomayor = float(max(trades, key=lambda x:x['p'])['p'])   

                            ################

                            if  ((precioactual - preciomenor)*(100/preciomenor))>=porcentaje and (precioactual>=preciomayor):
                                ############################
                                ####### POSICION SELL ######
                                ############################
                                
                                df=ut.calculardf (par,temporalidad,ventana)
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
                                mensaje=mensaje+"\nSubió un "+str(round(((precioactual - preciomenor)*(100/preciomenor)),2))+" %"
                                mensaje=mensaje+"\nInicio: "+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))
                                print(mensaje)                                
                                stopprice = precioactual*(1+50/100)
                                posicioncreada,mensajeposicioncompleta=ut.posicioncompleta(par,lado,ratio,df,porcentajeentrada,stopprice) 
                                print(mensajeposicioncompleta)
                            else:
                                if ((preciomenor - precioactual)*(100/preciomenor))>=porcentaje and (precioactual<=preciomenor):
                                    ############################
                                    ####### POSICION BUY ######
                                    ############################
                                    
                                    df=ut.calculardf (par,temporalidad,ventana)
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
                                    mensaje=mensaje+"\nBajó un "+str(round(((precioactual - preciomenor)*(100/preciomenor)),2))+" %"
                                    mensaje=mensaje+"\nInicio: "+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))
                                    print(mensaje)                                
                                    stopprice = precioactual*(1-50/100)
                                    posicioncreada,mensajeposicioncompleta=ut.posicioncompleta(par,lado,ratio,df,porcentajeentrada,stopprice) 
                                    print(mensajeposicioncompleta)

                            if posicioncreada==True:                            
                                ut.sound()
                                hayguita = True
                                i = 1
                                distanciaporc = 1
                                montoinicialposicion = ut.get_positionamt(par)
                                apretoporc = 0 # por ahora solo se arman algunas compensaciones con el mismo tamaño que la posición inicial.
                                    
                                #CREA COMPENSACIONES
                                while hayguita==True and i<2:
                                    hayguita = ut.compensaciones(par,client,lado,montoinicialposicion,distanciaporc,apretoporc)                       
                                    i=i+1
                                    distanciaporc=distanciaporc+1

                                posicioncreada=False    
                                mazmorra.append(par)                                                            
                                
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

