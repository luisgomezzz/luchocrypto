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

botlaburo = tr.creobot('laburo')
botamigos = tr.creobot('amigos') 
temporalidad = '1m'

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
                        volumen24h = client.futures_ticker(symbol=par)['quoteVolume']
                    except:
                        volumen24h = 0

                    try:

                        sys.stdout.write("\rSearching. Ctrl+c to exit. Pair: "+par+"\033[K")
                        sys.stdout.flush()

                        if temporalidad == '1m':
                        
                            suddendf=tr.binancehistoricdf(par,timeframe=temporalidad,limit=ventana) # Buscar valores mínimos y máximos N (ventana) minutos para atrás.
                            tr.timeindex(suddendf) #Formatea el campo time para luego calcular las señales
                            suddendf.ta.strategy()# Runs and appends all indicators to the current DataFrame by default

                            #MACD crosses signals 
                            crossmacd=(ta.xsignals(suddendf.ta.macd()['MACD_12_26_9'], suddendf.ta.macd()['MACDs_12_26_9'], suddendf.ta.macd()['MACDs_12_26_9'],above=True)).iloc[-1]    
                            if  crossmacd[0]==1 and crossmacd[1]==1 and crossmacd[2]==1 and crossmacd[3]==0 \
                                and suddendf.ta.ema(9).iloc[-1]>suddendf.ta.vwap().iloc[-1] \
                                and abs(suddendf.ta.macd()['MACDh_12_26_9'].iloc[-1]*100/suddendf.ta.macd()['MACD_12_26_9'].iloc[-1])>=30:
                                    #BUY!!!
                                    print("1")
                                    bt.binancetrader(par,'BUY',botlaburo)
                            if  crossmacd[0]==0 and crossmacd[1]==-1 and crossmacd[2]==0 and crossmacd[3]==1 \
                                and suddendf.ta.ema(9).iloc[-1]<suddendf.ta.vwap().iloc[-1] \
                                and abs(suddendf.ta.macd()['MACDh_12_26_9'].iloc[-1]*100/suddendf.ta.macd()['MACD_12_26_9'].iloc[-1])>=30:
                                    #SELL!!!
                                    print("2")
                                    bt.binancetrader(par,'SELL',botlaburo)
                            #EMA9 crossing VWAP
                            #crossvwap=(ta.xsignals(suddendf.ta.ema(9),suddendf.ta.vwap(),suddendf.ta.vwap(),above=True)).iloc[-1]
                            #if  crossvwap[0]==1 and crossvwap[1]==1 and crossvwap[2]==1 and crossvwap[3]==0 \
                            #    and suddendf.ta.macd()['MACD_12_26_9'].iloc[-1]>suddendf.ta.macd()['MACDs_12_26_9'].iloc[-1] \
                            #    and abs(suddendf.ta.macd()['MACDh_12_26_9'].iloc[-1]*100/suddendf.ta.macd()['MACD_12_26_9'].iloc[-1])>=30:
                            #        #BUY!!!
                            #        print("3")
                            #        bt.binancetrader(par,'BUY',botlaburo)
                            #if  crossvwap[0]==0 and crossvwap[1]==-1 and crossvwap[2]==0 and crossvwap[3]==1 \
                            #    and suddendf.ta.macd()['MACD_12_26_9'].iloc[-1]<suddendf.ta.macd()['MACDs_12_26_9'].iloc[-1] \
                            #    and abs(suddendf.ta.macd()['MACDh_12_26_9'].iloc[-1]*100/suddendf.ta.macd()['MACD_12_26_9'].iloc[-1])>=30:
                            #        #SELL!!!
                            #        print("4")
                            #        bt.binancetrader(par,'SELL',botlaburo)
                            
                            '''
                            # MOVIMIENTOS BRUSCOS
                            preciomenor=float(min(suddendf['low']))
                            preciomayor=float(max(suddendf['high']))
                            precioactual = float(client.get_symbol_ticker(symbol=par)["price"])

                            if ((precioactual - preciomenor)*(100/preciomenor))>=porcentaje and (precioactual>=preciomayor):
                                mensaje=par+" up "+str(round(((precioactual - preciomenor)*(100/preciomenor)),2))+"% - "+str(ventana)+" minutes. Price: "+str(precioactual)
                                dibu, lista = tr.dibujo(par,0)
                                botamigos.send_text(mensaje+"\nSupports and Resistances: "+str(lista))                            
                                botamigos.send_plot(dibu)
                                #para mi
                                botlaburo.send_text(mensaje+"\nSupports and Resistances: "+str(lista))
                                botlaburo.send_plot(dibu)
                            if ((preciomenor - precioactual)*(100/preciomenor))>=porcentaje and (precioactual<=preciomenor):
                                mensaje=par+" down "+str(round(((preciomenor - precioactual)*(100/preciomenor)),2))+"% - "+str(ventana)+" minutes. Price: "+str(precioactual)
                                dibu, lista = tr.dibujo(par,0)
                                botamigos.send_text(mensaje+"\nSupports and Resistances: "+str(lista))                            
                                botamigos.send_plot(dibu)
                                #para mi
                                botlaburo.send_text(mensaje+"\nSupports and Resistances: "+str(lista))
                                botlaburo.send_plot(dibu) 
                            '''

                        #Hay posicion abierta?
                        if float(exchange.fetch_balance()['info']['totalPositionInitialMargin'])!=0.0:   
                            # si la distancia entre macd y señal es menor al 18% cierro
                            if abs(suddendf.ta.macd()['MACDh_12_26_9'].iloc[-1]*100/suddendf.ta.macd()['MACD_12_26_9'].iloc[-1])<=20:
                                print("Cierro por Histogram pequeño")
                                if tr.binancetamanioposicion(exchange,par)>0.0:
                                    tr.binancecierrotodo(client,par,exchange,'SELL') 
                                else:
                                    tr.binancecierrotodo(client,par,exchange,'BUY')
                                client.futures_cancel_all_open_orders(symbol=par) 

                    except KeyboardInterrupt:
                        print("\rSalida solicitada.\033[K")
                        sys.exit()
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

