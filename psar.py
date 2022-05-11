from time import sleep
from binance.client import Client
from binance.exceptions import BinanceAPIException
import sys
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
    mazmorra=['NADA '] #Monedas que no quiero operar en orden de castigo
    ventana = 240 #Ventana de búsqueda en minutos.   
    exchange=ut.binanceexchange(ut.binance_api,ut.binance_secret) #login
    lista_de_monedas = client.futures_exchange_info()['symbols'] #obtiene lista de monedas
    saldo_inicial=float(exchange.fetch_balance()['info']['totalWalletBalance'])
    posicioncreada = False
    minvolumen24h=float(100000000)
    primerpar=str('')
    minutes_diff=0
    lista_monedas_filtradas=[]
    mensaje=''

    ut.clear() #limpia terminal

    for s in lista_de_monedas:
        try:  
            par = s['symbol']
            sys.stdout.write("\rFiltrando monedas: "+par+"\033[K")
            sys.stdout.flush()
            if float(client.futures_ticker(symbol=par)['quoteVolume'])>minvolumen24h and 'USDT' in par:
                lista_monedas_filtradas.append(par)
        except:
            pass

    try:

        while True:

          for par in lista_monedas_filtradas:

            if par not in mazmorra:

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
                        sys.stdout.write("\rSearching. Ctrl+c to exit. Pair: "+par+" - Tiempo de vuelta: "+str(ut.truncate(minutes_diff,2))+" min\033[K")
                        sys.stdout.flush()
                        
                        df=ut.calculardf (par,temporalidad,ventana)
                        crosshigh=(pdta.xsignals(df.ta.cci(40),100,100,above=True)).iloc[-1]
                        crosslow=(pdta.xsignals(df.ta.cci(40),-100,-100,above=True)).iloc[-1]

                        #CRUCE ARRIBA
                        if float(client.get_symbol_ticker(symbol=par)["price"]) > df.ta.ema(50).iloc[-1] > df.ta.ema(200).iloc[-1]:
                            if  (((crosshigh[0]==1 and crosshigh[1]==1 and crosshigh[2]==1 and crosshigh[3]==0) 
                                or (crosslow[0]==1 and crosslow[1]==1 and crosslow[2]==1 and crosslow[3]==0))
                                and 50>df.ta.stochrsi()['STOCHRSIk_14_14_3_3'].iloc[-1]>df.ta.stochrsi()['STOCHRSId_14_14_3_3'].iloc[-1]
                                ):

                                ut.komucloud (df)
                                
                                if df['signal'].iloc[-1]==1 and (df['signal'].iloc[-2]==0 or df['signal'].iloc[-2]==-1):
                                    posicioncreada=ut.posicionfuerte(par,'BUY',client)                                
                                    if posicioncreada==True:
                                        lado='BUY'
                                        ut.sound()
                                        mensaje=par+" - "+lado+" - Hora comienzo: "+str(dt.datetime.today())
                                        print(mensaje)
                        else: 
                            #CRUCE ABAJO
                            if float(client.get_symbol_ticker(symbol=par)["price"]) < df.ta.ema(50).iloc[-1] < df.ta.ema(200).iloc[-1]:
                                if (((crosshigh[0]==0 and crosshigh[1]==-1 and crosshigh[2]==0 and crosshigh[3]==1) 
                                    or (crosslow[0]==0 and crosslow[1]==-1 and crosslow[2]==0 and crosslow[3]==1))
                                    and 50<df.ta.stochrsi()['STOCHRSIk_14_14_3_3'].iloc[-1]<df.ta.stochrsi()['STOCHRSId_14_14_3_3'].iloc[-1]
                                    ):
                                                                        
                                    ut.komucloud (df)
                                    
                                    if df['signal'].iloc[-1]==-1 and (df['signal'].iloc[-2]==0 or df['signal'].iloc[-2]==1):                                    
                                        posicioncreada=ut.posicionfuerte(par,'SELL',client)
                                        if posicioncreada==True:
                                            lado='SELL'
                                            ut.sound()
                                            mensaje=par+" - "+lado+" - Hora comienzo: "+str(dt.datetime.today())
                                            print(mensaje)

                        if posicioncreada==True:
                            while float(exchange.fetch_balance()['info']['totalPositionInitialMargin'])!=0.0:
                                sleep(1)
                                ut.waiting()
                                df=ut.calculardf (par,temporalidad,ventana)

                                if lado=='BUY':
                                    if crosshigh[0]==1 and crosshigh[1]==1 and crosshigh[2]==1 and crosshigh[3]==0:
                                        if df.ta.cci(40).iloc[-1] <=80 or df.ta.stochrsi()['STOCHRSIk_14_14_3_3'].iloc[-1]<df.ta.stochrsi()['STOCHRSId_14_14_3_3'].iloc[-1]:    
                                            ut.binancecierrotodo(client,par,exchange,'SELL')
                                    else:
                                        if df.ta.cci(40).iloc[-1] <=-120 or df.ta.stochrsi()['STOCHRSIk_14_14_3_3'].iloc[-1]<df.ta.stochrsi()['STOCHRSId_14_14_3_3'].iloc[-1]:    
                                            ut.binancecierrotodo(client,par,exchange,'SELL')
                                else:
                                    if crosshigh[0]==0 and crosshigh[1]==-1 and crosshigh[2]==0 and crosshigh[3]==1:
                                        if df.ta.cci(40).iloc[-1] >=120 or df.ta.stochrsi()['STOCHRSIk_14_14_3_3'].iloc[-1]>df.ta.stochrsi()['STOCHRSId_14_14_3_3'].iloc[-1]:    
                                            ut.binancecierrotodo(client,par,exchange,'BUY')
                                    else:
                                        if df.ta.cci(40).iloc[-1] >=-80 or df.ta.stochrsi()['STOCHRSIk_14_14_3_3'].iloc[-1]>df.ta.stochrsi()['STOCHRSId_14_14_3_3'].iloc[-1]:    
                                            ut.binancecierrotodo(client,par,exchange,'BUY')

                            posicioncreada=False

                            ut.closeallopenorders(client,par)

                            try:
                                mensaje=mensaje+"\nHora cierre: "+str(dt.datetime.today())
                                mensaje=mensaje+"\nGanancia acumulada: "+str(ut.truncate(((float(exchange.fetch_balance()['info']['totalWalletBalance'])/saldo_inicial)-1)*100,3))+"% "+str(ut.truncate(float(exchange.fetch_balance()['info']['totalWalletBalance'])-saldo_inicial,2))+" USDT"
                                mensaje=mensaje+"\nBalance USDT: "+str(ut.truncate(float(exchange.fetch_balance()['info']['totalWalletBalance']),3))+" USDT"
                                mensaje=mensaje+"\nBalance BNB: "+str(ut.truncate(float((exchange.fetch_balance()['BNB']['total'])*float(client.get_symbol_ticker(symbol='BNBUSDT')["price"])),3))+" USDT"
                                mensaje=mensaje+"\nVolumen: "+str(ut.truncate(float(client.futures_ticker(symbol=par)['quoteVolume'])/1000000,2))+"M"
                                botlaburo.send_text(mensaje)
                            except Exception as a:
                                print("Error2: "+str(a))
                                pass

                            print(mensaje)
                            #sys.exit()

                    except KeyboardInterrupt:
                        print("Salida solicitada. ")
                        sys.exit()
                    except BinanceAPIException as e:
                        if e.message!="Invalid symbol.":
                            print("Error3 - Par:",par,"-",e.status_code,e.message)                            
                        pass
                    except Exception as falla:
                        if str(falla)!="binance does not have market symbol "+par:
                            print("Error4: "+str(falla))
                        pass

                except KeyboardInterrupt:
                    print("Salida solicitada.")
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

