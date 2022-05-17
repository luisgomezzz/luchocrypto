from binance.client import Client
from binance.exceptions import BinanceAPIException
import sys, os
import pandas as pd
pd.core.common.is_list_like = pd.api.types.is_list_like
import yfinance as yahoo_finance
yahoo_finance.pdr_override()
sys.path.insert(1,'./')
import utilidades as ut
import pandas_ta as pdta
import datetime as dt
from datetime import datetime

temporalidad='3m'
client = Client(ut.binance_api, ut.binance_secret)   
botlaburo = ut.creobot('laburo')      

def main() -> None:

    ratio=1.5 #relación riesgo/beneficio 
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
    balanceobjetivo = 24.00

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
                        sys.stdout.write("\rSearching. Ctrl+c to exit. Pair: "+par+" - Tiempo de vuelta: "+str(ut.truncate(minutes_diff,2))+" min\033[K"+" - Monedas analizadas: "+ str(len(lista_monedas_filtradas)))
                        sys.stdout.flush()

                        df=ut.calculardf (par,temporalidad,ventana)    

                        #Para analizar posible estrategia Oliver
                        if  (
                            (df['low'].iloc[-2] > (df.ta.ema(5).iloc[-2])*(1+(0.16/100))) 
                            and (df.ta.ema(5).iloc[-2] > df.ta.ema(20).iloc[-2] > df.ta.ema(200).iloc[-2])                            
                            #and (df.ta.macd()["MACD_12_26_9"].iloc[-2]>df.ta.macd()["MACDs_12_26_9"].iloc[-2])
                            and df['low'].iloc[-1] <= (df.ta.ema(5).iloc[-1]) 
                            and df['high'].iloc[-2]-df['low'].iloc[-2]>df['high'].iloc[-1]-df['low'].iloc[-1]
                            ):

                            ut.sound()
                            print("\nVer Oliver - "+par+" - "+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))
                            balancegame=ut.balancetotal(exchange,client)
                            print("\n*********************************************************************************************")
                            mensaje="Trade - "+par+" - SELL"
                            mensaje=mensaje+"\nInicio: "+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))
                            print(mensaje)
                            posicioncreada=ut.posicionfuerte(par,'SELL',client)                                
                        
                        if posicioncreada==True:
                            
                            ut.sound()

                            while ut.posicionesabiertas(exchange)==True:
                                #sleep(1)
                                ut.waiting()
                                #se espera a que cierre por alcanzar profit o stop

                            posicioncreada=False

                            ut.closeallopenorders(client,par)
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

