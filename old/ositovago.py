from binance.client import Client
from binance.exceptions import BinanceAPIException
import sys, os
import pandas as pd
pd.core.common.is_list_like = pd.api.types.is_list_like
import yfinance as yahoo_finance
yahoo_finance.pdr_override()
sys.path.insert(1,'./')
import utilidades as ut
import datetime as dt
from datetime import datetime, timedelta
import numpy as np
import pandas_ta as pta

client = Client(ut.binance_api, ut.binance_secret)   
botlaburo = ut.creobot('laburo')      

def main() -> None:

    ##PARAMETROS##########################################################################################
    mazmorra=['1000SHIBUSDT','1000XECUSDT','BTCUSDT_220624'] #Monedas que no quiero operar en orden de castigo
    ventana = 240 #Ventana de búsqueda en minutos.   
    exchange=ut.binanceexchange(ut.binance_api,ut.binance_secret) #login
    lista_de_monedas = client.futures_exchange_info()['symbols'] #obtiene lista de monedas
    saldo_inicial=ut.balancetotal(exchange,client)
    posicioncreada = False
    minvolumen24h=float(100000000)
    vueltas=0
    minutes_diff=0
    lista_monedas_filtradas=[]
    mensaje=''
    balanceobjetivo = 24.00+24.88
    temporalidad='3m'   
    ratio = 1/2.0 #Risk/Reward Ratio
    mensajeposicioncompleta=''
    porcentajelejosdeema5=0.80
        
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

                        df=ut.calculardf (par,temporalidad,ventana)  
                        long,short,gray,value=ut.osovago(df)
                        df2=ut.adx(df)
                        #SEÑAL BUY
                        if  ((df.ta.ema(5).iloc[-1] > df.ta.ema(20).iloc[-1] > df.ta.ema(200).iloc[-1])  
                            and long == True   
                            and gray == True
                            and df2['adx'].iloc[-1]>25
                            and df2['plus_di'].iloc[-1]>30
                            and df2['plus_di'].iloc[-1]>df2['minus_di'].iloc[-1]
                            and ut.currentprice(client,par) <= df.ta.ema(5).iloc[-1]*(1+porcentajelejosdeema5/100)
                            ):    
                            ############################
                            ########POSICION BUY########
                            ############################                            
                            lado='BUY'
                            print("\n*********************************************************************************************")
                            mensaje="Trade - "+par+" - "+lado
                            mensaje=mensaje+"\nInicio: "+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))
                            print(mensaje)                            
                            stopprice = df.ta.ema(20).iloc[-1] 
                            posicioncreada,mensajeposicioncompleta=ut.posicioncompleta(par,lado,client,ratio,stopprice)
                            print(mensajeposicioncompleta)
                            mensaje=mensaje+mensajeposicioncompleta 
                            balancegame=ut.balancetotal(exchange,client)
                        #SEÑAL SELL
                        elif ((df.ta.ema(5).iloc[-1] < df.ta.ema(20).iloc[-1] < df.ta.ema(200).iloc[-1])
                            and short == True   
                            and gray == True
                            and df2['adx'].iloc[-1]>25
                            and df2['minus_di'].iloc[-1]>30
                            and df2['plus_di'].iloc[-1]<df2['minus_di'].iloc[-1]
                            and ut.currentprice(client,par) >= df.ta.ema(5).iloc[-1]*(1-porcentajelejosdeema5/100)
                            ):           
                            ############################
                            ####### POSICION SELL ######
                            ############################
                            lado='SELL'
                            print("\n*********************************************************************************************")
                            mensaje="Trade - "+par+" - "+lado
                            mensaje=mensaje+"\nInicio: "+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))
                            print(mensaje)
                            stopprice = df.ta.ema(20).iloc[-1]                                                                
                            posicioncreada,mensajeposicioncompleta=ut.posicioncompleta(par,lado,client,ratio,stopprice) 
                            print(mensajeposicioncompleta)
                            mensaje=mensaje+mensajeposicioncompleta
                            balancegame=ut.balancetotal(exchange,client)
                    
                        if posicioncreada==True:
                            
                            ut.sound()
                            entryprice = ut.getentryprice(exchange,par)

                            if lado=='BUY':
                                ###############################################################################
                                while ut.posicionesabiertas(exchange)==True:
                                    ut.waiting(30)
                                    df=ut.calculardf (par,temporalidad,ventana)    
                                    df.ta.squeeze(bb_length=20, bb_std=2.0, kc_length=20, kc_scalar=1.5, lazybear=True, use_tr=True, append=True)
                                    #df2=ut.adx(df)
                                    if (
                                        df['SQZ_20_2.0_20_1.5_LB'].iloc[-2] > df['SQZ_20_2.0_20_1.5_LB'].iloc[-1] 
                                        #df2['minus_di'].iloc[-1] > df2['minus_di'].iloc[-2]
                                        and ut.posicionesabiertas(exchange)==True
                                        and ut.currentprice(client,par) > entryprice #cierro por squeeze solo cuando estoy en ganancias, si estoy en perdida que cierre por stop
                                        ):
                                        ut.binancecierrotodo(client,par,exchange,'SELL')                                
                            else:                                
                                while ut.posicionesabiertas(exchange)==True:
                                    ut.waiting(30)
                                    df=ut.calculardf (par,temporalidad,ventana)    
                                    df.ta.squeeze(bb_length=20, bb_std=2.0, kc_length=20, kc_scalar=1.5, lazybear=True, use_tr=True, append=True)
                                    #df2=ut.adx(df)
                                    if (
                                        df['SQZ_20_2.0_20_1.5_LB'].iloc[-2] < df['SQZ_20_2.0_20_1.5_LB'].iloc[-1]
                                        #df2['plus_di'].iloc[-1] > df2['plus_di'].iloc[-2]
                                        and ut.posicionesabiertas(exchange)==True
                                        and ut.currentprice(client,par) < entryprice #cierro por squeeze solo cuando estoy en ganancias, si estoy en perdida que cierre por stop
                                        ):
                                        ut.binancecierrotodo(client,par,exchange,'BUY')
                                ###############################################################################

                            ut.closeallopenorders(client,par)
                            posicioncreada=False                                                                
                            print("\nResumen: ")
                            balancetotal=ut.balancetotal(exchange,client)
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
                            f = open("log_ositovago.txt", "a")
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

