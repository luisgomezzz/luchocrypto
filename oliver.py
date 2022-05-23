from time import sleep
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
from datetime import datetime

client = Client(ut.binance_api, ut.binance_secret)   
botlaburo = ut.creobot('laburo')      

def main() -> None:

    ##PARAMETROS##########################################################################################
    mazmorra=['1000SHIBUSDT'] #Monedas que no quiero operar en orden de castigo
    ventana = 240 #Ventana de búsqueda en minutos.   
    exchange=ut.binanceexchange(ut.binance_api,ut.binance_secret) #login
    lista_de_monedas = client.futures_exchange_info()['symbols'] #obtiene lista de monedas
    saldo_inicial=ut.balancetotal(exchange,client)
    posicioncreada = False
    minvolumen24h=float(100000000)
    primerpar=str('')
    minutes_diff=0
    lista_monedas_filtradas=[]
    mensaje=''
    porcentajevariacion = 0.30
    balanceobjetivo = 24.00
    dicciobuy = {'NADA': [0.0,0.0,str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))]}
    dicciosell = {'NADA': [0.0,0.0,str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))]}
    ratio = 2 #relación riesgo/beneficio 
    temporalidad='3m'
    ##DATOS GUARDADOS##########################################################################################
    #dicciobuy = {'RSRUSDT': [0.00619, 0.0059, '23/May/2022 14:38:39']}
    ###########################################################################################################


    ut.clear() #limpia terminal
    dicciobuy.pop('NADA', None)
    dicciosell.pop('NADA', None)

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

                if primerpar=='':
                    primerpar=par
                    datetime_start = datetime.today()
                else:
                    if primerpar==par:
                        datetime_end = datetime.today()
                        minutes_diff = (datetime_end - datetime_start).total_seconds() / 60.0
                        primerpar=''

                try:
                    try:
                        sys.stdout.write("\rBuscando. Ctrl+c para salir. Par: "+par+" - Tiempo de vuelta: "+str(ut.truncate(minutes_diff,2))+" min - Monedas analizadas: "+ str(len(lista_monedas_filtradas))+" - En la mira: "+str(dicciobuy)+"\033[K")
                        sys.stdout.flush()

                        df=ut.calculardf (par,temporalidad,ventana)    

                        #SEÑAL BUY
                        if  (
                            (df['low'].iloc[-2] > (df.ta.ema(5).iloc[-2])*(1+(porcentajevariacion/100))) 
                            and (df.ta.ema(5).iloc[-2] > df.ta.ema(20).iloc[-2] > df.ta.ema(200).iloc[-2])                            
                            and df['low'].iloc[-1] <= (df.ta.ema(5).iloc[-1]) 
                            and df['high'].iloc[-2]-df['low'].iloc[-2]>df['high'].iloc[-1]-df['low'].iloc[-1]
                            ):
                            
                            #se detectó la señal y se guarda el valor pico y low para crear posicion y stop respectivamente.
                            dicciobuy[par] = [df['high'].iloc[-2],df['low'].iloc[-2],str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))]
                        else:
                            #SEÑAL SELL
                            if  (
                                (df['high'].iloc[-2] < (df.ta.ema(5).iloc[-2])*(1-(porcentajevariacion/100))) 
                                and (df.ta.ema(5).iloc[-2] < df.ta.ema(20).iloc[-2] < df.ta.ema(200).iloc[-2])                            
                                and df['high'].iloc[-1] >= (df.ta.ema(5).iloc[-1]) 
                                and df['high'].iloc[-2]-df['low'].iloc[-2]>df['high'].iloc[-1]-df['low'].iloc[-1]
                                ):
                            
                                #se detectó la señal y se guarda el valor pico y low para crear stop y posicion respectivamente.
                                dicciosell[par] = [df['low'].iloc[-2],df['high'].iloc[-2],str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))]

                        if len(dicciobuy)>0:
                            for par2 in dicciobuy:
                                sys.stdout.write("\rApuntando. Ctrl+c para salir. Par: "+par2+" - En la mira: "+str(dicciobuy)+"\033[K")
                                sys.stdout.flush()

                                df=ut.calculardf (par2,temporalidad,ventana)

                                #si ya hubo señal se ve si es momento de crear la posición
                                precioactual= ut.currentprice(client,par2)
                                ema5=df.ta.ema(5).iloc[-1]
                                ema20=df.ta.ema(20).iloc[-1]
                                ema200=df.ta.ema(200).iloc[-1]
                                
                                if precioactual > dicciobuy[par2][0] and ema5>ema20>ema200:
                                    #si el precio actual supera el pico de la señal crear posición buy
                                    lado='BUY'
                                    print("\n*********************************************************************************************")
                                    mensaje="Trade - "+par2+" - "+lado
                                    mensaje=mensaje+"\nInicio: "+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))
                                    print(mensaje)

                                    stopprice = dicciobuy[par2][1]
                                    profitprice = ((precioactual-stopprice)/ratio)+precioactual

                                    posicioncreada=ut.posicioncompleta(par2,lado,client,stopprice,profitprice) 

                                    balancegame=ut.balancetotal(exchange,client)
                        
                                if posicioncreada==True:
                                    
                                    ut.sound()

                                    ###############################################################################
                                    while ut.posicionesabiertas(exchange)==True:
                                        #sleep(0.5)
                                        ut.waiting()
                                        df=ut.calculardf (par2,temporalidad,ventana)
                                        if (df.ta.ema(5).iloc[-1] < df.ta.ema(20).iloc[-1]) or df.ta.cci(40).iloc[-1] < 0:
                                            ut.binancecierrotodo(client,par2,exchange,'SELL')
                                    ###############################################################################

                                    ut.closeallopenorders(client,par2)
                                    posicioncreada=False
                                    dicciobuy.pop(par2, None)                            
                                    balancetotal=ut.balancetotal(exchange,client)

                                    print("\nResumen: ")
                                    if balancetotal>balancegame:
                                        mensaje="\nWIN :) "+mensaje
                                    else:
                                        if balancetotal<balancegame:
                                            mensaje="\nLOSE :( "+mensaje
                                        else:
                                            mensaje="\nNADA :| "+mensaje
                                    try:
                                        mensaje=mensaje+"\nCierre: "+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))
                                        mensaje=mensaje+"\n24h Volumen: "+str(ut.truncate(float(client.futures_ticker(symbol=par2)['quoteVolume'])/1000000,1))+"M"
                                        mensaje=mensaje+"\nGanancia sesión: "+str(ut.truncate(((balancetotal/saldo_inicial)-1)*100,3))+"% "+str(ut.truncate(balancetotal-saldo_inicial,2))+" USDT"
                                        mensaje=mensaje+"\nBal TOTAL: "+str(ut.truncate(balancetotal,3))+" USDT - (BNB: " +str(ut.truncate(float((exchange.fetch_balance()['BNB']['total'])*float(client.get_symbol_ticker(symbol='BNBUSDT')["price"])),3))+" USDT)"
                                        mensaje=mensaje+"\nObjetivo a: "+str(ut.truncate(balanceobjetivo-balancetotal,3))+" USDT"
                                        botlaburo.send_text(mensaje)
                                    except Exception as a:
                                        print("Error2: "+str(a))
                                        pass

                                    print(mensaje)
                                    print("\n*********************************************************************************************")
                                    #sys.exit()
######################################################################################################################################################3
                        if len(dicciosell)>0:
                            for par2 in dicciosell:
                                sys.stdout.write("\rApuntando. Ctrl+c para salir. Par: "+par2+" - En la mira: "+str(dicciosell)+"\033[K")
                                sys.stdout.flush()

                                df=ut.calculardf (par2,temporalidad,ventana)

                                #si ya hubo señal se ve si es momento de crear la posición
                                precioactual= ut.currentprice(client,par2)
                                ema5=df.ta.ema(5).iloc[-1]
                                ema20=df.ta.ema(20).iloc[-1]
                                ema200=df.ta.ema(200).iloc[-1]
                                
                                if precioactual < dicciosell[par2][0] and ema5<ema20<ema200:
                                    #si el precio actual menor el low de la señal crear posición sell
                                    lado='SELL'
                                    print("\n*********************************************************************************************")
                                    mensaje="Trade - "+par2+" - "+lado
                                    mensaje=mensaje+"\nInicio: "+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))
                                    print(mensaje)

                                    stopprice = dicciosell[par2][1]
                                    profitprice = ((precioactual-stopprice)/ratio)+precioactual

                                    posicioncreada=ut.posicioncompleta(par2,lado,client,stopprice,profitprice) 

                                    balancegame=ut.balancetotal(exchange,client)
                        
                                if posicioncreada==True:
                                    
                                    ut.sound()

                                    ###############################################################################
                                    while ut.posicionesabiertas(exchange)==True:
                                        #sleep(0.5)
                                        ut.waiting()
                                        df=ut.calculardf (par2,temporalidad,ventana)
                                        if (df.ta.ema(5).iloc[-1] > df.ta.ema(20).iloc[-1]) or df.ta.cci(40).iloc[-1] > 0:
                                            ut.binancecierrotodo(client,par2,exchange,'BUY')
                                    ###############################################################################

                                    ut.closeallopenorders(client,par2)
                                    posicioncreada=False
                                    dicciosell.pop(par2, None)                            
                                    balancetotal=ut.balancetotal(exchange,client)

                                    print("\nResumen: ")
                                    if balancetotal>balancegame:
                                        mensaje="\nWIN :) "+mensaje
                                    else:
                                        if balancetotal<balancegame:
                                            mensaje="\nLOSE :( "+mensaje
                                        else:
                                            mensaje="\nNADA :| "+mensaje
                                    try:
                                        mensaje=mensaje+"\nCierre: "+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))
                                        mensaje=mensaje+"\n24h Volumen: "+str(ut.truncate(float(client.futures_ticker(symbol=par2)['quoteVolume'])/1000000,1))+"M"
                                        mensaje=mensaje+"\nGanancia sesión: "+str(ut.truncate(((balancetotal/saldo_inicial)-1)*100,3))+"% "+str(ut.truncate(balancetotal-saldo_inicial,2))+" USDT"
                                        mensaje=mensaje+"\nBal TOTAL: "+str(ut.truncate(balancetotal,3))+" USDT - (BNB: " +str(ut.truncate(float((exchange.fetch_balance()['BNB']['total'])*float(client.get_symbol_ticker(symbol='BNBUSDT')["price"])),3))+" USDT)"
                                        mensaje=mensaje+"\nObjetivo a: "+str(ut.truncate(balanceobjetivo-balancetotal,3))+" USDT"
                                        botlaburo.send_text(mensaje)
                                    except Exception as a:
                                        print("Error2: "+str(a))
                                        pass

                                    print(mensaje)
                                    print("\n*********************************************************************************************")
                                    #sys.exit()                                    

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

