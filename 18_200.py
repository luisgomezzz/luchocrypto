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

temporalidad='3m'
client = Client(ut.binance_api, ut.binance_secret)         

def main() -> None:

    mazmorra=['NADA '] #Monedas que no quiero operar en orden de castigo
    ventana = 240 #Ventana de búsqueda en minutos.   
    exchange=ut.binanceexchange(ut.binance_api,ut.binance_secret) #login
    lista_de_monedas = client.futures_exchange_info()['symbols'] #obtiene lista de monedas
    saldo_inicial=float(exchange.fetch_balance()['info']['totalWalletBalance'])
    posicioncreada = bool
    minvolumen24h=float(100000000)

    ut.clear() #limpia terminal

    try:
        while True:
          for s in lista_de_monedas:
            try:  
                position = exchange.fetch_balance()['info']['positions']
                par=[p for p in position if p['notional'] != '0'][0]['symbol']
            except:
                par = s['symbol']      

            if par not in mazmorra:
                try:
                    try:
                        sys.stdout.write("\rSearching. Ctrl+c to exit. Pair: "+par+"\033[K")
                        sys.stdout.flush()
                        
                        df=ut.calculardf (par,temporalidad,ventana)

                        crosshigh=(pdta.xsignals(df.ta.ema(18),df.ta.ema(200),df.ta.ema(200),above=True)).iloc[-1]
                        if  (crosshigh[0]==1 and crosshigh[1]==1 and crosshigh[2]==1 and crosshigh[3]==0 and 40<df.ta.rsi(14).iloc[-1]<60):

                            ut.komucloud (df)
                            
                            currentprice = float(client.get_symbol_ticker(symbol=par)["price"])
                            if (float(client.futures_ticker(symbol=par)['quoteVolume'])>minvolumen24h):

                                print("\rHORA: ",dt.datetime.today())
                                print("- "+par+" ESTRATEGIA cruce 18 200 BUY\n")                                
                                ut.posicionfuerte(par,'BUY',client)                                
                                posicioncreada=True
                                lado='BUY'
                                ut.sound()
                        else: 
                            if (crosshigh[0]==0 and crosshigh[1]==-1 and crosshigh[2]==0 and crosshigh[3]==1):
                                                                      
                                ut.komucloud (df)
                                
                                currentprice = float(client.get_symbol_ticker(symbol=par)["price"])
                                if (float(client.futures_ticker(symbol=par)['quoteVolume'])>minvolumen24h):

                                    print("\rHORA: ",dt.datetime.today())
                                    print("- "+par+" ESTRATEGIA cruce 18 200 SELL\n")                                    
                                    ut.posicionfuerte(par,'SELL',client)
                                    posicioncreada=True
                                    lado='SELL'
                                    ut.sound()

                        if posicioncreada==True:
                            while float(exchange.fetch_balance()['info']['totalPositionInitialMargin'])!=0.0:
                                sleep(1)
                                
                            posicioncreada=False

                            ut.closeallopenorders(client,par)
                            print("\rHORA: ",dt.datetime.today())
                            print("GANANCIA ACUMULADA: ",ut.truncate(((float(exchange.fetch_balance()['info']['totalWalletBalance'])/saldo_inicial)-1)*100,3),"%\033[K", ut.truncate(float(exchange.fetch_balance()['info']['totalWalletBalance'])-saldo_inicial,2),"USDT")
                            print("BALANCE TOTAL USDT: ",ut.truncate(float(exchange.fetch_balance()['info']['totalWalletBalance']),3),"USDT")
                            print("BALANCE TOTAL BNB: ",ut.truncate(float((exchange.fetch_balance()['BNB']['total'])*float(client.get_symbol_ticker(symbol='BNBUSDT')["price"])),3),"USDT")       

                            #sys.exit()

                    except KeyboardInterrupt:
                        print("\rSalida solicitada.\033[K")
                        sys.exit()
                    except BinanceAPIException as e:
                        if e.message!="Invalid symbol.":
                            print("\rExcept 1 - Par:",par,"- Error:",e.status_code,e.message,"\033[K")
                            print("\n")
                        pass
                    except Exception as falla:
                        sys.stdout.write("\rError1: "+str(falla)+"\033[K")
                        sys.stdout.flush()
                        pass
                    
                except KeyboardInterrupt:
                   print("\rSalida solicitada.\033[K")
                   sys.exit()            
                except BinanceAPIException as a:
                   if a.message!="Invalid symbol.":
                      print("\rExcept 1 - Par:",par,"- Error:",a.status_code,a.message,"\033[K")
                      print("\n")
                   pass
       
    except BinanceAPIException as a:
       print("\rExcept 2 - Par:",par,"- Error:",a.status_code,a.message,"\033[K")
       pass

if __name__ == '__main__':
    main()

