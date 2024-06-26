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
from datetime import datetime, timedelta
import numpy as np
import pandas_ta as pta

client = Client(ut.binance_api, ut.binance_secret)   
botlaburo = ut.creobot('laburo')      

def limpiezaenlamira(client,dicciobuy,dicciosell):
    # Limpieza. Si se cumplió la condición en alguna moneda mientras 
    # se estaba tradeando entonces se borra porque se ingresaría tarde.    
    for par in list(dicciobuy):
        precioactual= ut.currentprice(client,par)
        if precioactual > dicciobuy[par][0]:
            dicciobuy.pop(par, None)  

    for par in list(dicciosell):
        precioactual= ut.currentprice(client,par)
        if precioactual < dicciosell[par][0]:
            dicciosell.pop(par, None)    


def enlamira(client,lista_monedas_filtradas,porcentajevariacion,temporalidad,minutes_diff,dicciobuy,dicciosell):
    ventana=480
    dicciobuy.clear()
    dicciosell.clear()
    for par in lista_monedas_filtradas:
        sys.stdout.write("\rBuscando HISTORIAL de señales para tener en la mira: "+str(par)+"\033[K")
        sys.stdout.flush()
        df=ut.calculardf (par,temporalidad,ventana)
        df['ema5']=df.ta.ema(5)
        df['ema5up']=df['ema5']*(1+(porcentajevariacion/100))
        df['ema5down']=df['ema5']*(1-(porcentajevariacion/100))
        df['ema20']=df.ta.ema(20)
        df['ema200']=df.ta.ema(200)
        # create a new column and use np.select to assign values to it using our lists as arguments
        df['matchup'] = np.where((df.low.shift(periods=1) > df.ema5up.shift(periods=1))
                        & (df.ema5.shift(periods=1) > df.ema20.shift(periods=1))
                        & (df.ema20.shift(periods=1) > df.ema200.shift(periods=1))
                        & (df.low <= df.ema5)
                        & ((df.high.shift(periods=1)-df.low.shift(periods=1))>(df.high-df.low))
                        & (df.high.shift(periods=1) > ut.currentprice(client,par))
                        , True,False)

        df['matchdown'] = np.where((df.high.shift(periods=1) < df.ema5down.shift(periods=1))
                        & (df.ema5.shift(periods=1) < df.ema20.shift(periods=1))
                        & (df.ema20.shift(periods=1) < df.ema200.shift(periods=1))
                        & (df.high >= df.ema5)
                        & ((df.high.shift(periods=1)-df.low.shift(periods=1))>(df.high-df.low))
                        & (df.low.shift(periods=1) < ut.currentprice(client,par))
                        , True,False)        
###me quedo con las ultimas señales de buy y sell
        for i in df.index: 
            if df.matchup[i]==True:
                dicciobuy[par]=[df.high.shift(periods=1)[i],df.low.shift(periods=1)[i],str(i-timedelta(hours=3)),df.volume.shift(periods=1)[i]]
        for i in df.index: 
            if df.matchdown[i]==True:
                dicciosell[par]=[df.low.shift(periods=1)[i],df.high.shift(periods=1)[i],str(i-timedelta(hours=3)),df.volume.shift(periods=1)[i]]            


def main() -> None:

    ##PARAMETROS##########################################################################################
    mazmorra=['1000SHIBUSDT','DODOUSDT','BELUSDT','ARPAUSDT'] #Monedas que no quiero operar en orden de castigo
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
    porcentajevariacion = 0.30
    balanceobjetivo = 24.00
    dicciobuy = {'NADA': [0.0,0.0,str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')),0.0]} #high, low, time, volume
    dicciosell = {'NADA': [0.0,0.0,str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')),0.0]} #low, high, time, volume
    dicciobuy.clear()
    dicciosell.clear()
    temporalidad='3m'   
    ratio = 1/1.0 #Risk/Reward Ratio
    mensajeposicioncompleta=''
        
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

    #se obtiene el historial de todas las monedas
    enlamira(client,lista_monedas_filtradas,porcentajevariacion,temporalidad,minutes_diff,dicciobuy,dicciosell) 
    #prints

    sys.stdout.write("\rMonedas analizadas: "+ str(len(lista_monedas_filtradas))+"\033[K")
    sys.stdout.flush()
    print("\nEn la mira BUY: "+str(dicciobuy))   
    print("\nEn la mira SELL: "+str(dicciosell)+"\n")

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

                        #SEÑAL BUY
                        if  (
                            (df['low'].iloc[-2] > (df.ta.ema(5).iloc[-2])*(1+(porcentajevariacion/100))) 
                            and (df.ta.ema(5).iloc[-2] > df.ta.ema(20).iloc[-2] > df.ta.ema(200).iloc[-2])                            
                            and df['low'].iloc[-1] <= (df.ta.ema(5).iloc[-1]) 
                            and df['high'].iloc[-2]-df['low'].iloc[-2]>df['high'].iloc[-1]-df['low'].iloc[-1]
                            ):
                            
                            #se detectó la señal y se guarda el valor pico para crear posicion cuando sea superado.
                            dicciobuy[par] = [df['high'].iloc[-2],df['low'].iloc[-2],str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')),df['volume'].iloc[-2]]
                            sys.stdout.write("\rActualización en la mira BUY: "+str(dicciobuy)+"\033[K")
                            sys.stdout.flush()
                            print('\n')

                        else:
                            #SEÑAL SELL
                            if  (
                                (df['high'].iloc[-2] < (df.ta.ema(5).iloc[-2])*(1-(porcentajevariacion/100))) 
                                and (df.ta.ema(5).iloc[-2] < df.ta.ema(20).iloc[-2] < df.ta.ema(200).iloc[-2])                            
                                and df['high'].iloc[-1] >= (df.ta.ema(5).iloc[-1]) 
                                and df['high'].iloc[-2]-df['low'].iloc[-2]>df['high'].iloc[-1]-df['low'].iloc[-1]
                                ):
                            
                                #se detectó la señal y se guarda el low para crear posicion cuando sea superado.
                                dicciosell[par] = [df['low'].iloc[-2],df['high'].iloc[-2],str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')),df['volume'].iloc[-2]]
                                sys.stdout.write("\rActualización en la mira SELL: "+str(dicciosell)+"\033[K")
                                sys.stdout.flush()
                                print('\n')

                        if par in dicciobuy or par in dicciosell:
                            precioactual= ut.currentprice(client,par)
                            ema5=df.ta.ema(5).iloc[-1]
                            ema20=df.ta.ema(20).iloc[-1]
                            ema200=df.ta.ema(200).iloc[-1]
                            sti = pta.supertrend(df['high'], df['low'], df['close'], 7, 3)

                        if par in dicciobuy:
                            if (#si ya hubo señal se ve si se dan las condiciones para que crear la posicion
                                precioactual > (dicciobuy[par][0])
                                and ema5>ema20>ema200 
                                and df.ta.cci(20).iloc[-1] > 100
                                and (df.ta.macd()["MACD_12_26_9"].iloc[-1]>df.ta.macd()["MACDs_12_26_9"].iloc[-1])
                                and sti['SUPERT_7_3.0'].iloc[-1]>sti['SUPERT_7_3.0'].iloc[-2] > ema200
                                and sti['SUPERTd_7_3.0'].iloc[-1] == 1
                                ):
                                ############################
                                ########POSICION BUY########
                                ############################                            

                                lado='BUY'
                                print("\n*********************************************************************************************")
                                mensaje="Trade - "+par+" - "+lado
                                mensaje=mensaje+"\nSeñal "+str(dicciobuy[par])
                                mensaje=mensaje+"\nInicio: "+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))
                                print(mensaje)
                                
                                stopprice = sti['SUPERT_7_3.0'].iloc[-1]         
                                posicioncreada,mensajeposicioncompleta=ut.posicioncompleta(par,lado,client,ratio,stopprice)
                                print(mensajeposicioncompleta)
                                mensaje=mensaje+mensajeposicioncompleta 
                                balancegame=ut.balancetotal(exchange,client)
                        else:
                            if par in dicciosell:
                                if (#si ya hubo señal se ve si se dan las condiciones para que crear la posicion
                                    precioactual < (dicciosell[par][0])
                                    and ema5<ema20<ema200 
                                    and df.ta.cci(20).iloc[-1] < -100
                                    and (df.ta.macd()["MACD_12_26_9"].iloc[-1]<df.ta.macd()["MACDs_12_26_9"].iloc[-1])
                                    and sti['SUPERT_7_3.0'].iloc[-1]<sti['SUPERT_7_3.0'].iloc[-2] < ema200
                                    and sti['SUPERTd_7_3.0'].iloc[-1] == -1
                                    ):
                                    ############################
                                    ####### POSICION SELL ######
                                    ############################

                                    lado='SELL'
                                    print("\n*********************************************************************************************")
                                    mensaje="Trade - "+par+" - "+lado
                                    mensaje=mensaje+"\nSeñal "+str(dicciosell[par])
                                    mensaje=mensaje+"\nInicio: "+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))
                                    print(mensaje)

                                    stopprice = sti['SUPERT_7_3.0'].iloc[-1]                                                                       
                                    posicioncreada,mensajeposicioncompleta=ut.posicioncompleta(par,lado,client,ratio,stopprice) 
                                    print(mensajeposicioncompleta)
                                    mensaje=mensaje+mensajeposicioncompleta
                                    balancegame=ut.balancetotal(exchange,client)
                    
                        if posicioncreada==True:
                            
                            ut.sound()

                            if lado=='BUY':
                                ###############################################################################
                                while ut.posicionesabiertas(exchange)==True:
                                    ut.waiting()
                                    df=ut.calculardf (par,temporalidad,ventana)
                                    sti = pta.supertrend(df['high'], df['low'], df['close'], 7, 3)
                                    if (
                                        sti['SUPERTd_7_3.0'].iloc[-1] == -1 
                                        #or ut.currentprice(client,par) <= df.ta.ema(13).iloc[-1]                                        
                                        #or df.ta.cci(20).iloc[-1] < 100
                                        ):
                                        ut.binancecierrotodo(client,par,exchange,'SELL')
                                ###############################################################################
                            else:
                                ###############################################################################
                                while ut.posicionesabiertas(exchange)==True:
                                    ut.waiting()
                                    df=ut.calculardf (par,temporalidad,ventana)
                                    sti = pta.supertrend(df['high'], df['low'], df['close'], 7, 3)
                                    if (sti['SUPERTd_7_3.0'].iloc[-1] == 1                                        
                                        #or ut.currentprice(client,par) >= df.ta.ema(13).iloc[-1]
                                        #or df.ta.cci(20).iloc[-1] > -100  
                                        ):
                                        ut.binancecierrotodo(client,par,exchange,'BUY')
                                ###############################################################################

                            ut.closeallopenorders(client,par)
                            posicioncreada=False                                                                
                            print("\nResumen: ")
                            balancetotal=ut.balancetotal(exchange,client)
                            if balancetotal>balancegame:
                                mensaje="\nWIN :) "+mensaje
                            else:
                                if balancetotal<balancegame:
                                    mensaje="\nLOSE :( "+mensaje
                                else:
                                    mensaje="\nNADA :| "+mensaje
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
                            f = open("log_oliver.txt", "a")
                            f.write(mensaje)
                            f.write("\n*********************************************************************************************\n")
                            f.close()

                            #Reinicio
                            print("\nREINICIO...\n")
                            enlamira(client,lista_monedas_filtradas,porcentajevariacion,temporalidad,minutes_diff,dicciobuy,dicciosell)

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

