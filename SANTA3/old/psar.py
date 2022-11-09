#****************************************************************************************
# Psar version 2.0
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
nombrelog = "log_psar.txt"

def main() -> None:

    ##PARAMETROS##########################################################################################
    mazmorra=['1000SHIBUSDT','1000XECUSDT','BTCUSDT_220624','ETHUSDT_220624'] #Monedas que no quiero operar en orden de castigo
    ventana = 240 #Ventana de búsqueda en minutos.   
    lista_de_monedas = client.futures_exchange_info()['symbols'] #obtiene lista de monedas
    saldo_inicial = ut.balancetotal()
    posicioncreada = False
    minvolumen24h=float(100000000)
    vueltas=0
    minutes_diff=0
    lista_monedas_filtradas=[]
    mensaje=''
    balanceobjetivo = 24.00+24.88
    temporalidad='3m'   
    ratio = 1/1.5 #Risk/Reward Ratio
    mensajeposicioncompleta=''
    porcentajelejosdeema5=1.00
        
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

                        crosshigh=(pta.xsignals(df.ta.cci(40),100,100,above=True)).iloc[-1]
                        crosslow=(pta.xsignals(df.ta.cci(40),-100,-100,above=True)).iloc[-1]
                        
                        if  (((crosshigh[0]==1 and crosshigh[1]==1 and crosshigh[2]==1 and crosshigh[3]==0) 
                            or (crosslow[0]==1 and crosslow[1]==1 and crosslow[2]==1 and crosslow[3]==0))
                            and 50 > df.ta.stochrsi()['STOCHRSIk_14_14_3_3'].iloc[-1] > df.ta.stochrsi()['STOCHRSId_14_14_3_3'].iloc[-1]
                            ):

                            ut.komucloud (df)                            
                            df2=ut.adx(df)
                            currentprice = ut.currentprice(par)                            

                            if (df['signal'].iloc[-1]==1 
                                and (df['signal'].iloc[-2]==0 or df['signal'].iloc[-2]==-1)
                                and currentprice > df.ta.ema(50).iloc[-1] > df.ta.ema(200).iloc[-1]
                                and currentprice <= df.ta.ema(5).iloc[-1]*(1+porcentajelejosdeema5/100)
                                and df2['adx'].iloc[-1]>23
                                #and df2['plus_di'].iloc[-1]>23
                                and df2['plus_di'].iloc[-1]>df2['minus_di'].iloc[-1]
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
                                posicioncreada,mensajeposicioncompleta=ut.posicioncompleta(par,lado,ratio,stopprice)
                                print(mensajeposicioncompleta)
                                mensaje=mensaje+mensajeposicioncompleta 
                                balancegame=ut.balancetotal()
                        else: 
                            if (((crosshigh[0]==0 and crosshigh[1]==-1 and crosshigh[2]==0 and crosshigh[3]==1) 
                                or (crosslow[0]==0 and crosslow[1]==-1 and crosslow[2]==0 and crosslow[3]==1)
                                and 50 < df.ta.stochrsi()['STOCHRSIk_14_14_3_3'].iloc[-1] < df.ta.stochrsi()['STOCHRSId_14_14_3_3'].iloc[-1]
                                )):
                                                                      
                                ut.komucloud (df)                  
                                df2=ut.adx(df)              
                                currentprice = ut.currentprice(par)

                                if (df['signal'].iloc[-1]==-1 
                                    and (df['signal'].iloc[-2]==0 or df['signal'].iloc[-2]==1)
                                    and currentprice < df.ta.ema(50).iloc[-1] < df.ta.ema(200).iloc[-1] 
                                    and currentprice >= df.ta.ema(5).iloc[-1]*(1-porcentajelejosdeema5/100)
                                    and df2['adx'].iloc[-1]>23
                                    #and df2['minus_di'].iloc[-1]>23
                                    and df2['plus_di'].iloc[-1]<df2['minus_di'].iloc[-1]
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
                                    posicioncreada,mensajeposicioncompleta=ut.posicioncompleta(par,lado,ratio,stopprice) 
                                    print(mensajeposicioncompleta)
                                    mensaje=mensaje+mensajeposicioncompleta
                                    balancegame=ut.balancetotal()

                        if posicioncreada==True:
                            ut.sound()
                            while float(exchange.fetch_balance()['info']['totalPositionInitialMargin'])!=0.0:
                                ut.waiting(1)
                                
                                df=ut.calculardf (par,temporalidad,ventana)
                                df2=ut.adx(df)

                                if lado=='BUY':
                                    if crosshigh[0]==1 and crosshigh[1]==1 and crosshigh[2]==1 and crosshigh[3]==0:
                                        if  (df.ta.cci(40).iloc[-1] <=95 
                                            or df.ta.stochrsi()['STOCHRSIk_14_14_3_3'].iloc[-1]<df.ta.stochrsi()['STOCHRSId_14_14_3_3'].iloc[-1]
                                            or df2['adx'].iloc[-1] < 23
                                            ):    
                                            ut.binancecierrotodo(par,'SELL')
                                    else:
                                        if  (df.ta.cci(40).iloc[-1] <=-105 
                                            or df.ta.stochrsi()['STOCHRSIk_14_14_3_3'].iloc[-1]<df.ta.stochrsi()['STOCHRSId_14_14_3_3'].iloc[-1]
                                            or df2['adx'].iloc[-1] < 23
                                            ):    
                                            ut.binancecierrotodo(par,'SELL')
                                else:
                                    if crosshigh[0]==0 and crosshigh[1]==-1 and crosshigh[2]==0 and crosshigh[3]==1:
                                        if  (df.ta.cci(40).iloc[-1] >=105 
                                            or df.ta.stochrsi()['STOCHRSIk_14_14_3_3'].iloc[-1]>df.ta.stochrsi()['STOCHRSId_14_14_3_3'].iloc[-1]
                                            or df2['adx'].iloc[-1] < 23
                                            ):
                                            ut.binancecierrotodo(par,'BUY')
                                    else:
                                        if  (df.ta.cci(40).iloc[-1] >=-95 
                                            or df.ta.stochrsi()['STOCHRSIk_14_14_3_3'].iloc[-1]>df.ta.stochrsi()['STOCHRSId_14_14_3_3'].iloc[-1]
                                            or df2['adx'].iloc[-1] < 23
                                            ):
                                            ut.binancecierrotodo(par,'BUY')                                

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

