from time import sleep
from binance.client import Client
from binance.exceptions import BinanceAPIException
import sys
import pandas as pd
from pandas.io.formats.format import DataFrameFormatter
pd.core.common.is_list_like = pd.api.types.is_list_like
import yfinance as yahoo_finance
yahoo_finance.pdr_override()
from bob_telegram_tools.bot import TelegramBot
sys.path.insert(1,'./')
import tradeando as tr
import pandas_ta as ta
import binancetrader as bt
import time
import datetime as dt

botlaburo = tr.creobot('laburo')
botamigos = tr.creobot('amigos') 

temporalidad='1m'

def main() -> None:

    #procentajes de subida al cual se activa la alarma
    porcentaje = 5

    #mazmorra - monedas que no quiero operar en orden de castigo
    #mazmorra=['GTCUSDT','TLMUSDT','KEEPUSDT','SFPUSDT','ALICEUSDT','SANDUSDT','STORJUSDT','RUNEUSDT','FTMUSDT','HBARUSDT','CVCUSDT','LRCUSDT','LINAUSDT','CELRUSDT','SKLUSDT','CTKUSDT','SNXUSDT','SRMUSDT','1INCHUSDT','ANKRUSDT'] 
    mazmorra=['NADA '] 

    #alarma
    #duration = 1000  # milliseconds
    #freq = 440  # Hz
   
    ventana = 240 #Ventana de búsqueda en minutos.   

    #login
    binance_api="N7yU75L3CNJg2RW0TcJBAW2cUjhPGvyuSFUgnRHvMSMMiS8WpZ8Yd8yn70evqKl0"
    binance_secret="2HfMkleskGwTb6KQn0AKUQfjBDd5dArBW3Ykd2uTeOiv9VZ6qSU2L1yWM1ZlQ5RH"
    client = Client(binance_api, binance_secret)
    exchange=tr.binanceexchange(binance_api,binance_secret)

    #*****************************************************PROGRAMA PRINCIPAL *************************************************************
    tr.clear()

    lista_de_monedas = client.futures_exchange_info()['symbols']
    botlaburo.send_text("Starting...")
    maxdist=0
    flagestrategy = 0
    try:

        while True:

          for s in lista_de_monedas:
            try:  
                position = exchange.fetch_balance()['info']['positions']
                par=[p for p in position if p['notional'] != '0'][0]['symbol']
            except:
                par = s['symbol']      

            #par = 'DASHUSDT' #por si solo quiero ver señales en un par

            if par not in mazmorra:

                try:

                    try:

                        sys.stdout.write("\rSearching. Ctrl+c to exit. Pair: "+par+"\033[K")
                        sys.stdout.flush()

                        if flagestrategy ==0 or flagestrategy ==1: #no hay posicion abierta o la estrategia es MACD
                        
                            suddendf=tr.binancehistoricdf(par,timeframe=temporalidad,limit=ventana) # Buscar valores mínimos y máximos N (ventana) minutos para atrás.
                            tr.timeindex(suddendf) #Formatea el campo time para luego calcular las señales
                            suddendf.ta.strategy() # Runs and appends all indicators to the current DataFrame by default
                            print ("\033[A                                                                       \033[A")

                            #MACD crosses signals 
                            crossmacd=(ta.xsignals(suddendf.ta.macd()['MACD_12_26_9'], suddendf.ta.macd()['MACDs_12_26_9'], suddendf.ta.macd()['MACDs_12_26_9'],above=True)).iloc[-1]    
                            if  crossmacd[0]==1 and crossmacd[1]==1 and crossmacd[2]==1 and crossmacd[3]==0 \
                                and abs(suddendf.ta.macd()['MACDh_12_26_9'].iloc[-1]*100/suddendf.ta.macd()['MACD_12_26_9'].iloc[-1])>=90:
                                    print(par+" ESTRATEGIA MACD BUY\n"+str(crossmacd))
                                    print(str(tr.truncate(abs(suddendf.ta.macd()['MACDh_12_26_9'].iloc[-1]*100/suddendf.ta.macd()['MACD_12_26_9'].iloc[-1]),2))+"%")
                                    bt.binancetrader(par,'BUY',botlaburo)
                                    flagestrategy=1
                                    botlaburo.send_text(par+" ESTRATEGIA MACD BUY")
                            if  crossmacd[0]==0 and crossmacd[1]==-1 and crossmacd[2]==0 and crossmacd[3]==1 \
                                and abs(suddendf.ta.macd()['MACDh_12_26_9'].iloc[-1]*100/suddendf.ta.macd()['MACD_12_26_9'].iloc[-1])>=90:
                                    print(par+" ESTRATEGIA MACD SELL\n"+str(crossmacd))
                                    print(str(tr.truncate(abs(suddendf.ta.macd()['MACDh_12_26_9'].iloc[-1]*100/suddendf.ta.macd()['MACD_12_26_9'].iloc[-1]),2))+"%")
                                    bt.binancetrader(par,'SELL',botlaburo)
                                    flagestrategy=1
                                    botlaburo.send_text(par+" ESTRATEGIA MACD SELL")
                        
                        if (flagestrategy ==0 or flagestrategy ==2) and (dt.datetime.today().hour >=21 or dt.datetime.today().hour <=6): #no hay posicion abierta o la estrategia es VWAP
                        
                            #EMA9 crossing VWAP
                            crossvwap=(ta.xsignals(suddendf.ta.ema(9),suddendf.ta.vwap(),suddendf.ta.vwap(),above=True)).iloc[-1]
                            if  crossvwap[0]==1 and crossvwap[1]==1 and crossvwap[2]==1 and crossvwap[3]==0:
                                    print(" ESTRATEGIA VWAP BUY\n")
                                    bt.binancetrader(par,'BUY',botlaburo)
                                    flagestrategy=2
                                    botlaburo.send_text(par+" ESTRATEGIA VWAP BUY ")
                            if  crossvwap[0]==0 and crossvwap[1]==-1 and crossvwap[2]==0 and crossvwap[3]==1:
                                    print("ESTRATEGIA VWAP SELL\n")
                                    bt.binancetrader(par,'SELL',botlaburo)      
                                    flagestrategy=2
                                    botlaburo.send_text(par+" ESTRATEGIA VWAP SELL ")
                                    
                        #Hay posicion abierta?
                        if float(exchange.fetch_balance()['info']['totalPositionInitialMargin'])!=0.0:   
                            time.sleep(30)                              
                            if float(exchange.fetch_balance()['info']['totalPositionInitialMargin'])!=0.0:
                                if flagestrategy==1:
                                    suddendf.ta.strategy()
                                    #si la distancia es igual o va creciendo continuo, si no, cierro
                                    if  maxdist <= abs(suddendf.ta.macd()['MACDh_12_26_9'].iloc[-1]):
                                        maxdist  = abs(suddendf.ta.macd()['MACDh_12_26_9'].iloc[-1])    
                        
                                    else:
                                        print("Cierro por Histogram bajando....")
                                        if tr.binancetamanioposicion(exchange,par)>0.0:
                                            tr.binancecierrotodo(client,par,exchange,'SELL') 
                                        else:
                                            tr.binancecierrotodo(client,par,exchange,'BUY')
                                        client.futures_cancel_all_open_orders(symbol=par) 
                                        maxdist=0
                                        flagestrategy=0

                                if flagestrategy==2:
                                    currentpnl = tr.truncate(float(exchange.fetch_balance()['info']['totalCrossUnPnl']),2)
                                    if  maxdist <= currentpnl:
                                        maxdist = currentpnl

                                    else:
                                        print("Cierro porque empieza a bajar el PNL....")
                                        if tr.binancetamanioposicion(exchange,par)>0.0:
                                            tr.binancecierrotodo(client,par,exchange,'SELL') 
                                        else:
                                            tr.binancecierrotodo(client,par,exchange,'BUY')
                                        client.futures_cancel_all_open_orders(symbol=par) 
                                        maxdist=0
                                        flagestrategy=0
                            else:
                                maxdist=0            
                                flagestrategy=0                            
                        else:
                            maxdist=0            
                            flagestrategy=0

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

