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
import indicadores as ind


##CONFIG########################
client = ut.client
exchange = ut.exchange
botlaburo = ut.creobot('laburo')      
nombrelog = "log_santa2.txt"

def main() -> None:

    ##PARAMETROS##########################################################################################
    mazmorra=['1000SHIBUSDT','1000XECUSDT','BTCUSDT_220624','ETHUSDT_220624','ETHUSDT_220930'] #Monedas que no quiero operar 
    ventana = 40 #Ventana de búsqueda en minutos.   
    lista_de_monedas = client.futures_exchange_info()['symbols'] #obtiene lista de monedas
    saldo_inicial = ut.balancetotal()
    posicioncreada = False
    minvolumen24h=float(100000000)
    vueltas=0
    minutes_diff=0
    lista_monedas_filtradas=[]
    mensaje=''
    balanceobjetivo = 24.00+24.88
    temporalidad='1m'   
    ratio = 1/(1.0) #Risk/Reward Ratio
    mensajeposicioncompleta=''
    porcentajelejosdeema5=1.00
    porcentaje = 5
    apalancamiento = 10 #siempre en 10 segun la estrategia de santi
    margen = 'CROSSED'
        
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
                        precioanterior = float(min(trades, key=lambda x:x['p'])['p'])
                        precioactual = float(client.get_symbol_ticker(symbol=par)["price"])  
                        preciomayor = float(max(trades, key=lambda x:x['p'])['p'])

                        ################

                        if  ((precioactual - precioanterior)*(100/precioanterior))>=porcentaje and (precioactual>=preciomayor):
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
                            mensaje=mensaje+"\nSubió un "+str(round(((precioactual - precioanterior)*(100/precioanterior)),2))+" %"
                            mensaje=mensaje+"\nInicio: "+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))
                            print(mensaje)                                
                            stopprice = precioactual*(1+2/100)
                            #posicioncreada,mensajeposicioncompleta=ut.posicioncompleta(par,lado,ratio,df,stopprice) 
                            print(mensajeposicioncompleta)
                            mensaje=mensaje+mensajeposicioncompleta
                            balancegame=ut.balancetotal()                                
                        
                        if posicioncreada==True:
                            ut.sound()
                            hayguita = True
                            i = 1
                            while ut.posicionesabiertas() == True:
                                ut.waiting(1)
                                #CREA COMPENSACIONES
                                if hayguita==True:
                                    hayguita=ut.compensaciones(par,client,i)                       
                                    i=i+1

                            ut.closeallopenorders(par)
                            posicioncreada=False                                                                
                            print("\nResumen: ")
                            balancetotal=ut.balancetotal()
                            if balancetotal>balancegame:
                                mensaje="WIN :) "+mensaje
                            else:
                                if balancetotal<balancegame:
                                    mensaje="LOSE :( "+mensaje
                                else:
                                    mensaje="NADA :| "+mensaje
                            try:
                                mensaje=mensaje+"\nCierre: "+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))
                                mensaje=mensaje+"\n24h Volumen: "+str(ut.truncate(float(client.futures_ticker(symbol=par)['quoteVolume'])/1000000,1))+"M"
                                mensaje=mensaje+"\nGanancia sesión: "+str(ut.truncate(((balancetotal/saldo_inicial)-1)*100,3))+"% "+str(ut.truncate(balancetotal-saldo_inicial,2))+" USDT"
                                mensaje=mensaje+"\nBal TOTAL: "+str(ut.truncate(balancetotal,3))+" USDT - (BNB: " +str(ut.truncate(float((exchange.fetch_balance()['BNB']['total'])*float(client.get_symbol_ticker(symbol='BNBUSDT')["price"])),3))+" USDT)"
                                mensaje=mensaje+"\nObjetivo a: "+str(ut.truncate(balanceobjetivo-balancetotal,3))+" USDT"
                                botlaburo.send_text(mensaje)
                            except Exception as a:
                                print("Error2: "+str(a))
                                pass

                            print(mensaje)
                            print("\n*********************************************************************************************")

                            #escribo file
                            f = open(nombrelog, "a")
                            f.write(mensaje)
                            f.write("\n*********************************************************************************************\n")
                            f.close()

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

