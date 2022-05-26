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
import numpy as np

client = Client(ut.binance_api, ut.binance_secret)   
botlaburo = ut.creobot('laburo')      

def enlamira(lista_monedas_filtradas,porcentajevariacion,temporalidad,dicciobuy,dicciosell):
    ventana=480
    for par in lista_monedas_filtradas:
        sys.stdout.write("\rBuscando señales para tener en la mira: "+str(par)+"\033[K")
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
                        , True,False)
        for i in df.index: 
            if df.matchup[i]==True:
                dicciobuy[par]=[df.high.shift(periods=1)[i],df.low.shift(periods=1)[i],str(i)]
        # Limpieza. Si se cumplió la condición en alguna moneda mientras 
        # se estaba tradeando entonces se borra porque se ingresaría tarde.
        for par in list(dicciobuy):
            precioactual= ut.currentprice(client,par)
            if precioactual > dicciobuy[par][0]:
                dicciobuy.pop(par, None)       
                        
    sys.stdout.write("\rEn la mira BUY \033[K")
    sys.stdout.flush()
    print(dicciobuy)

def main() -> None:

    ##PARAMETROS##########################################################################################
    mazmorra=['1000SHIBUSDT','DODOUSDT'] #Monedas que no quiero operar en orden de castigo
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
    dicciobuy.clear()
    dicciosell.clear()
    ratio = 0.5 #Risk/Reward Ratio
    temporalidad='3m'   
    
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
    enlamira(lista_monedas_filtradas,porcentajevariacion,temporalidad,dicciobuy,dicciosell)

    try:

        while True:

            for par in lista_monedas_filtradas:
                # para calcular tiempo de vuelta completa
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
                        if par not in dicciobuy: #voy moneda por moneda buscando mientras no esté en el dicciobuy ya que si está la analiza dentro del próximo bucle

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
                                dicciobuy[par] = [df['high'].iloc[-2],df['low'].iloc[-2],str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))]
                                print("\nNueva deteccion BUY ")
                                print(dicciobuy)

                            else:
                                #SEÑAL SELL
                                if  (
                                    (df['high'].iloc[-2] < (df.ta.ema(5).iloc[-2])*(1-(porcentajevariacion/100))) 
                                    and (df.ta.ema(5).iloc[-2] < df.ta.ema(20).iloc[-2] < df.ta.ema(200).iloc[-2])                            
                                    and df['high'].iloc[-1] >= (df.ta.ema(5).iloc[-1]) 
                                    and df['high'].iloc[-2]-df['low'].iloc[-2]>df['high'].iloc[-1]-df['low'].iloc[-1]
                                    ):
                                
                                    #se detectó la señal y se guarda el low para crear posicion cuando sea superado.
                                    dicciosell[par] = [df['low'].iloc[-2],df['high'].iloc[-2],str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))]
                                    print("\nNueva deteccion sell ")
                                    print(dicciosell)

                            if len(dicciobuy)>0: #entro si hay señales de BUY guardadas para analizar si es momento de entrar
                                for par2 in list(dicciobuy):
                                    
                                    sys.stdout.write("\rEn la mira Buy. Ctrl+c para salir. Par: "+par2+"\033[K")
                                    sys.stdout.flush()
                                    
                                    df=ut.calculardf (par2,temporalidad,ventana)
                                    
                                    precioactual= ut.currentprice(client,par2)
                                    ema5=df.ta.ema(5).iloc[-1]
                                    ema20=df.ta.ema(20).iloc[-1]
                                    ema200=df.ta.ema(200).iloc[-1]
                                    ema13=df.ta.ema(13).iloc[-1]
                                    
                                    if (#si ya hubo señal se ve si se dan las condiciones para que crear la posicion
                                        precioactual > (dicciobuy[par2][0])*(1+(porcentajevariacion*2/100))
                                        and ema5>ema20>ema200 
                                        and df.ta.cci(20).iloc[-1] > 100
                                        ):
                                        
                                        lado='BUY'
                                        print("\n*********************************************************************************************")
                                        mensaje="Trade - "+par2+" - "+lado
                                        mensaje=mensaje+"\nInicio: "+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))
                                        print(mensaje)

                                        stopprice = ema13

                                        profitprice = ((precioactual-stopprice)/ratio)+precioactual

                                        posicioncreada=ut.posicioncompleta(par2,lado,client,stopprice,profitprice) 

                                        balancegame=ut.balancetotal(exchange,client)
                            
                                    if posicioncreada==True:
                                        
                                        ut.sound()

                                        ###############################################################################
                                        while ut.posicionesabiertas(exchange)==True:
                                            ut.waiting()
                                            df=ut.calculardf (par2,temporalidad,ventana)
                                            if df.ta.cci(20).iloc[-1] < 100 or ut.currentprice(client,par2) <= df.ta.ema(13).iloc[-1]:
                                                ut.binancecierrotodo(client,par2,exchange,'SELL')
                                        ###############################################################################

                                        ut.closeallopenorders(client,par2)
                                        posicioncreada=False                                    
                                        
                                        # Limpieza. Si se cumplieron las condiciones en alguna moneda mientras 
                                        # se estaba tradeando se borra porque se ingresaría tarde.
                                        for par3 in list(dicciobuy):
                                            precioactual= ut.currentprice(client,par3)
                                            if precioactual > dicciobuy[par3][0]:
                                                dicciobuy.pop(par3, None)   

                                        #se analiza nuevamente el par por si aun es valido y se inserta nuevamente en el df
                                        enlamira([par2],porcentajevariacion,temporalidad,dicciobuy,dicciosell) 

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

