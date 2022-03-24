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
import pandas_ta as ta
import binancetrader as bt

botlaburo = ut.creobot('laburo')
botamigos = ut.creobot('amigos') 
apalancamiento = 50
margen = 'CROSSED'
temporalidad='1m'

def main() -> None:

    #mazmorra - monedas que no quiero operar en orden de castigo
    #mazmorra=['GTCUSDT','TLMUSDT','KEEPUSDT','SFPUSDT','ALICEUSDT','SANDUSDT','STORJUSDT','RUNEUSDT','FTMUSDT','HBARUSDT','CVCUSDT','LRCUSDT','LINAUSDT','CELRUSDT','SKLUSDT','CTKUSDT','SNXUSDT','SRMUSDT','1INCHUSDT','ANKRUSDT'] 
    mazmorra=['NADA '] 

    ventana = 240 #Ventana de búsqueda en minutos.   

    #login
    binance_api="N7yU75L3CNJg2RW0TcJBAW2cUjhPGvyuSFUgnRHvMSMMiS8WpZ8Yd8yn70evqKl0"
    binance_secret="2HfMkleskGwTb6KQn0AKUQfjBDd5dArBW3Ykd2uTeOiv9VZ6qSU2L1yWM1ZlQ5RH"
    client = Client(binance_api, binance_secret)
    exchange=ut.binanceexchange(binance_api,binance_secret)

    #*****************************************************PROGRAMA PRINCIPAL *************************************************************
    ut.clear()

    lista_de_monedas = client.futures_exchange_info()['symbols']
    botlaburo.send_text("Starting...")

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

                        suddendf=ut.binancehistoricdf(par,timeframe=temporalidad,limit=ventana) # Buscar valores mínimos y máximos N (ventana) minutos para atrás.
                        ut.timeindex(suddendf) #Formatea el campo time para luego calcular las señales
                        suddendf.ta.strategy() # Runs and appends all indicators to the current DataFrame by default
                        print ("\033[A                                                                       \033[A")
                        
                        #EMA9 crossing VWAP
                        crossvwap=(ta.xsignals(suddendf.ta.ema(9),suddendf.ta.vwap(),suddendf.ta.vwap(),above=True)).iloc[-1]
                        if  crossvwap[0]==1 and crossvwap[1]==1 and crossvwap[2]==1 and crossvwap[3]==0:
                                ut.sound()
                                print(" ESTRATEGIA VWAP BUY\n")
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

                                bt.binancetrader(par,'BUY',botlaburo)
                                botlaburo.send_text(par+" ESTRATEGIA VWAP BUY ")
                        if  crossvwap[0]==0 and crossvwap[1]==-1 and crossvwap[2]==0 and crossvwap[3]==1:
                                ut.sound()
                                print("ESTRATEGIA VWAP SELL\n")
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

                                bt.binancetrader(par,'SELL',botlaburo)      
                                botlaburo.send_text(par+" ESTRATEGIA VWAP SELL ")
                                    
                        #Hay posicion abierta?
                        if float(exchange.fetch_balance()['info']['totalPositionInitialMargin'])!=0.0: 
                            sys.exit()                                                     

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
                        print("\n")
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

