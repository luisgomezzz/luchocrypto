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

period='1h' # indicators work period
suddendfperiod = '1m'

botlaburo = tr.creobot('laburo')
botamigos = tr.creobot('amigos') 

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

    #*****************************************************PROGRAMA PRINCIPAL *************************************************************
    tr.clear()

    lista_de_monedas = client.futures_exchange_info()['symbols']
    
    botlaburo.send_text("Starting...")
   
    try:

        while True:

          for s in lista_de_monedas:

            par = s['symbol']

            #par = 'DASHUSDT'            #por si solo quiero ver señales en un par

            if par not in mazmorra:

                try:
                    try:
                        volumen24h = client.futures_ticker(symbol=par)['quoteVolume']
                    except:
                        volumen24h = 0

                    try:

                        sys.stdout.write("\rSearching. Ctrl+c to exit. Pair: "+par+"\033[K")
                        sys.stdout.flush()

####################################################SCALPING miuntos
                        
                        suddendf=tr.historicdf(par,timeframe='1m',limit=ventana) # Buscar valores mínimos y máximos N (ventana) minutos para atrás.
                        tr.timeindex(suddendf) #Formatea el campo time para luego calcular las señales
                        preciomenor=float(min(suddendf['low']))
                        preciomayor=float(max(suddendf['high']))
                        precioactual = float(client.get_symbol_ticker(symbol=par)["price"])
                        suddendf.ta.strategy()# Runs and appends all indicators to the current DataFrame by default

                        #VWAP and EMA9 cross signals
                        if ta.xsignals(suddendf.ta.ema(9),suddendf.ta.vwap(),suddendf.ta.vwap(),above=True)['TS_Trades'].iloc[-1]==1 and suddendf.ta.ema(9).iloc[-1]>suddendf.ta.vwap().iloc[-1]:
                            botlaburo.send_text(par+" "+suddendfperiod+" - EMA9 crossing VWAP: LONG!!!")
                        if ta.xsignals(suddendf.ta.ema(9),suddendf.ta.vwap(),suddendf.ta.vwap(),above=True)['TS_Trades'].iloc[-1]==-1 and suddendf.ta.ema(9).iloc[-1]<suddendf.ta.vwap().iloc[-1]:
                            botlaburo.send_text(par+" "+suddendfperiod+" - EMA9 crossing VWAP: SHORT!!!") 

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

####################################################TRADING HORAS NUEVO#########################################################

                        df=tr.historicdf(par,timeframe=period, limit=300) #Datos históricos para alarmas relacionadas con indicadores.
                        tr.timeindex(df) #Formatea el campo time para luego calcular las señales
                        df.ta.strategy() #Runs and appends all indicators to the current DataFrame by default

                        #MACD crosses signals         
                        if ta.xsignals(df.ta.macd()['MACD_12_26_9'], df.ta.macd()['MACDs_12_26_9'], df.ta.macd()['MACDs_12_26_9'],above=True)['TS_Trades'].iloc[-1]==1 \
                            and df.ta.ema(9).iloc[-1]>df.ta.vwap().iloc[-1]:
                                #botlaburo.send_text(par+" "+period+" - MACD crosses: LONG!!!")
                                bt.binancetrader(par,'LONG',botlaburo)
                        if ta.xsignals(df.ta.macd()['MACD_12_26_9'], df.ta.macd()['MACDs_12_26_9'], df.ta.macd()['MACDs_12_26_9'],above=True)['TS_Trades'].iloc[-1]==-1 \
                            and df.ta.ema(9).iloc[-1]<df.ta.vwap().iloc[-1]:
                                #botlaburo.send_text(par+" "+period+" - MACD crosses: SHORT!!!")
                                bt.binancetrader(par,'SHORT',botlaburo)
                        #EMA9 crossing VWAP
                        if ta.xsignals(df.ta.ema(9),df.ta.vwap(),df.ta.vwap(),above=True)['TS_Trades'].iloc[-1]==1 and df.ta.macd()['MACD_12_26_9'].iloc[-1]>df.ta.macd()['MACDs_12_26_9'].iloc[-1]:
                            #botlaburo.send_text(par+" "+period+" - EMA9 crossing VWAP: LONG!!!")
                            bt.binancetrader(par,'LONG',botlaburo)
                        if ta.xsignals(df.ta.ema(9),df.ta.vwap(),df.ta.vwap(),above=True)['TS_Trades'].iloc[-1]==-1 and df.ta.macd()['MACD_12_26_9'].iloc[-1]<df.ta.macd()['MACDs_12_26_9'].iloc[-1]:
                            #botlaburo.send_text(par+" "+period+" - EMA9 crossing VWAP: SHORT!!!")  
                            bt.binancetrader(par,'SHORT',botlaburo)

##########################################################################################################################

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
