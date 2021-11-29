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
                client.futures_cancel_all_open_orders(symbol=par) 

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
                            if ta.xsignals(suddendf.ta.macd()['MACD_12_26_9'], suddendf.ta.macd()['MACDs_12_26_9'], suddendf.ta.macd()['MACDs_12_26_9'],above=True)['TS_Trades'].iloc[-1]==1 \
                                and suddendf.ta.ema(9).iloc[-1]>suddendf.ta.vwap().iloc[-1] \
                                and suddendf.ta.rsi().iloc[-1]<=40:
                                    #botlaburo.send_text(par+" "+temporalidad+" - MACD crosses: BUY!!!")
                                    print("1")
                                    bt.binancetrader(par,'BUY',botlaburo)
                            if ta.xsignals(suddendf.ta.macd()['MACD_12_26_9'], suddendf.ta.macd()['MACDs_12_26_9'], suddendf.ta.macd()['MACDs_12_26_9'],above=True)['TS_Trades'].iloc[-1]==-1 \
                                and suddendf.ta.ema(9).iloc[-1]<suddendf.ta.vwap().iloc[-1] \
                                and suddendf.ta.rsi().iloc[-1]>=60:
                                    #botlaburo.send_text(par+" "+temporalidad+" - MACD crosses: SELL!!!")
                                    print("2")
                                    bt.binancetrader(par,'SELL',botlaburo)
                            #EMA9 crossing VWAP
                            if ta.xsignals(suddendf.ta.ema(9),suddendf.ta.vwap(),suddendf.ta.vwap(),above=True)['TS_Trades'].iloc[-1]==1 and suddendf.ta.macd()['MACD_12_26_9'].iloc[-1]>suddendf.ta.macd()['MACDs_12_26_9'].iloc[-1] \
                                and suddendf.ta.rsi().iloc[-1]<50 \
                                and suddendf.ta.macd()['MACD_12_26_9'].iloc[-1]>suddendf.ta.macd()['MACDs_12_26_9'].iloc[-1]:
                                #botlaburo.send_text(par+" "+temporalidad+" - EMA9 crossing VWAP: BUY!!!")
                                print("3")
                                bt.binancetrader(par,'BUY',botlaburo)
                            if ta.xsignals(suddendf.ta.ema(9),suddendf.ta.vwap(),suddendf.ta.vwap(),above=True)['TS_Trades'].iloc[-1]==-1 and suddendf.ta.macd()['MACD_12_26_9'].iloc[-1]<suddendf.ta.macd()['MACDs_12_26_9'].iloc[-1] \
                                and suddendf.ta.rsi().iloc[-1]>50 \
                                and suddendf.ta.macd()['MACD_12_26_9'].iloc[-1]<suddendf.ta.macd()['MACDs_12_26_9'].iloc[-1]:
                                #botlaburo.send_text(par+" "+temporalidad+" - EMA9 crossing VWAP: SELL!!!")  
                                print("4")
                                bt.binancetrader(par,'SELL',botlaburo)

                            # MOVIMIENTOS BRUSCOS
                            '''
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
                            
                        if temporalidad =='1h':

                            df=tr.binancehistoricdf(par,timeframe=temporalidad, limit=300) #Datos históricos para alarmas relacionadas con indicadores.
                            tr.timeindex(df) #Formatea el campo time para luego calcular las señales
                            df.ta.strategy() #Runs and appends all indicators to the current DataFrame by default

                            #MACD crosses signals         
                            if ta.xsignals(df.ta.macd()['MACD_12_26_9'], df.ta.macd()['MACDs_12_26_9'], df.ta.macd()['MACDs_12_26_9'],above=True)['TS_Trades'].iloc[-1]==1 \
                                and df.ta.ema(9).iloc[-1]>df.ta.vwap().iloc[-1]:
                                    #botlaburo.send_text(par+" "+temporalidad+" - MACD crosses: BUY!!!")
                                    bt.binancetrader(par,'BUY',botlaburo)
                            if ta.xsignals(df.ta.macd()['MACD_12_26_9'], df.ta.macd()['MACDs_12_26_9'], df.ta.macd()['MACDs_12_26_9'],above=True)['TS_Trades'].iloc[-1]==-1 \
                                and df.ta.ema(9).iloc[-1]<df.ta.vwap().iloc[-1]:
                                    #botlaburo.send_text(par+" "+temporalidad+" - MACD crosses: SELL!!!")
                                    bt.binancetrader(par,'SELL',botlaburo)
                            #EMA9 crossing VWAP
                            if ta.xsignals(df.ta.ema(9),df.ta.vwap(),df.ta.vwap(),above=True)['TS_Trades'].iloc[-1]==1 and df.ta.macd()['MACD_12_26_9'].iloc[-1]>df.ta.macd()['MACDs_12_26_9'].iloc[-1]:
                                #botlaburo.send_text(par+" "+temporalidad+" - EMA9 crossing VWAP: BUY!!!")
                                bt.binancetrader(par,'BUY',botlaburo)
                            if ta.xsignals(df.ta.ema(9),df.ta.vwap(),df.ta.vwap(),above=True)['TS_Trades'].iloc[-1]==-1 and df.ta.macd()['MACD_12_26_9'].iloc[-1]<df.ta.macd()['MACDs_12_26_9'].iloc[-1]:
                                #botlaburo.send_text(par+" "+temporalidad+" - EMA9 crossing VWAP: SELL!!!")  
                                bt.binancetrader(par,'SELL',botlaburo)

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

