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
import ccxt
import pandas_ta as ta

period='1h' # indicators work period

chatid="@gofrecrypto" #canal
idgrupo = "-704084758" #grupo de amigos
token = "2108740619:AAHcUBakZLdoHYnvUvkBp6oq7SoS63erb2g"

botlaburo = TelegramBot(token, chatid)
botamigos = TelegramBot(token, idgrupo)  

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
                        preciomenor=float(min(suddendf['low']))
                        preciomayor=float(max(suddendf['high']))
                        precioactual = float(client.get_symbol_ticker(symbol=par)["price"])

                        #VWAP and EMA9 cross signals
                        if ta.xsignals(suddendf.ta.ema(9),tr.np_vwap(par),tr.np_vwap(par),above=True)['TS_Entries'].iloc[-1]!=0:
                            botlaburo.send_text(par+" - SCALPING - VWAP and EMA9 signals: LONG!!!")
                        if ta.xsignals(suddendf.ta.ema(9),tr.np_vwap(par),tr.np_vwap(par),above=False)['TS_Entries'].iloc[-1]!=0:
                            botlaburo.send_text(par+" - SCALPING - VWAP and EMA9 signals: SHORT!!!") 

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

####################################################TRADING horas

                        df=tr.historicdf(par,timeframe=period, limit=300) ## Datos históricos para alarmas relacionadas con indicadores.

                        #MACD crosses signals + RSI          
                        if ta.xsignals(ta.macd(df['close'])['MACD_12_26_9'], ta.macd(df['close'])['MACDs_12_26_9'], ta.macd(df['close'])['MACDs_12_26_9'],above=True)['TS_Entries'].iloc[-1]!=0:
                            if (tr.truncate(df.ta.rsi().iloc[-1],2))<=34:
                                botlaburo.send_text(par+" - TRADING - MACD crosses signals + RSI: LONG!!!")
                        if ta.xsignals(ta.macd(df['close'])['MACD_12_26_9'], ta.macd(df['close'])['MACDs_12_26_9'], ta.macd(df['close'])['MACDs_12_26_9'],above=False)['TS_Entries'].iloc[-1]!=0:
                            if (tr.truncate(df.ta.rsi().iloc[-1],2))>=60:
                                botlaburo.send_text(par+" - TRADING - MACD crosses signals + RSI: SHORT!!!")

                        #VWAP and EMA9 cross signals
                        if ta.xsignals(df.ta.ema(9),tr.np_vwap(par),tr.np_vwap(par),above=True)['TS_Entries'].iloc[-1]!=0:
                            botlaburo.send_text(par+" - TRADING - VWAP and EMA9 signals: LONG!!!")
                        if ta.xsignals(df.ta.ema(9),tr.np_vwap(par),tr.np_vwap(par),above=False)['TS_Entries'].iloc[-1]!=0:
                            botlaburo.send_text(par+" - TRADING - VWAP and EMA9 signals: SHORT!!!")  

###############################################################
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

