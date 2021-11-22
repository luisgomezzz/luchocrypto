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
    porcentajedia = 5

    #mazmorra - monedas que no quiero operar en orden de castigo
    #mazmorra=['GTCUSDT','TLMUSDT','KEEPUSDT','SFPUSDT','ALICEUSDT','SANDUSDT','STORJUSDT','RUNEUSDT','FTMUSDT','HBARUSDT','CVCUSDT','LRCUSDT','LINAUSDT','CELRUSDT','SKLUSDT','CTKUSDT','SNXUSDT','SRMUSDT','1INCHUSDT','ANKRUSDT'] 
    mazmorra=['NADA '] 

    #alarma
    #duration = 1000  # milliseconds
    #freq = 440  # Hz
   
    ventana = 60 #Ventana de búsqueda en minutos.   

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

          porcentaje=porcentajedia
             
          for s in lista_de_monedas:

            par = s['symbol']            

            if par not in mazmorra:

                try:
                    try:
                        volumen24h = client.futures_ticker(symbol=par)['quoteVolume']
                    except:
                        volumen24h = 0

                    try:
                        ####SCALPING
                        ################ SUDDEN ALERTS (minutes) ############################################
                        suddendf=tr.historicdf(par,timeframe='1m',limit=ventana) # Buscar valores mínimos y máximos N (ventana) minutos para atrás.
                        preciomenor=float(min(suddendf['low']))
                        preciomayor=float(max(suddendf['high']))
                        precioactual = float(client.get_symbol_ticker(symbol=par)["price"])
                        
                        if ((precioactual - preciomenor)*(100/preciomenor))>=porcentaje and (precioactual>=preciomayor) and (tr.truncate(suddendf.ta.rsi().iloc[-1],2))>=70 and float(volumen24h)>=float(1):
                            mensaje=par+" up "+str(round(((precioactual - preciomenor)*(100/preciomenor)),2))+"% - "+str(ventana)+" minutes. RSI: "+str(tr.truncate(suddendf.ta.rsi().iloc[-1],2))+". Price: "+str(precioactual)
                            dibu, lista = tr.dibujo(par,0)
                            botamigos.send_text(mensaje+"\nSupports and Resistances: "+str(lista))                            
                            botamigos.send_plot(dibu)
                            #para mi
                            botlaburo.send_text(mensaje+"\nSupports and Resistances: "+str(lista))
                            botlaburo.send_plot(dibu)
                        if ((preciomenor - precioactual)*(100/preciomenor))>=porcentaje and (precioactual<=preciomenor) and (tr.truncate(suddendf.ta.rsi().iloc[-1],2))<=30 and float(volumen24h)>=float(1):
                            mensaje=par+" down "+str(round(((preciomenor - precioactual)*(100/preciomenor)),2))+"% - "+str(ventana)+" minutes. RSI: "+str(tr.truncate(suddendf.ta.rsi().iloc[-1],2))+". Price: "+str(precioactual)
                            dibu, lista = tr.dibujo(par,0)
                            botamigos.send_text(mensaje+"\nSupports and Resistances: "+str(lista))                            
                            botamigos.send_plot(dibu)
                            #para mi
                            botlaburo.send_text(mensaje+"\nSupports and Resistances: "+str(lista))
                            botlaburo.send_plot(dibu)
                        sys.stdout.write("\rSearching. Ctrl+c to exit. Pair: "+par+"\033[K")
                        sys.stdout.flush()

                        ####TRADING
                        ########################### ALERTS (on period period) #############################
                        df=tr.historicdf(par,timeframe=period, limit=300) ## Datos históricos para alarmas relacionadas con indicadores.

                        #RSI crosses
                        #if ta.xsignals(df.ta.rsi(), 30, 70, above=True)['TS_Exits'].iloc[-1]!=0:
                        #    botlaburo.send_text(par+" RSI crosses below 70. EXIT "+period)
                           
                        #if ta.xsignals(df.ta.rsi(), 30, 70, above=False)['TS_Exits'].iloc[-1]!=0:
                        #    botlaburo.send_text(par+" RSI crosses above 70. EXIT "+period)

                        #MACD crosses            
                        if ta.xsignals(ta.macd(df['close'])['MACD_12_26_9'], ta.macd(df['close'])['MACDs_12_26_9'], ta.macd(df['close'])['MACDs_12_26_9'],above=True)['TS_Entries'].iloc[-1]!=0:
                            #botlaburo.send_text(par+" The MACD line crosses above. "+period)
                            if (tr.truncate(df.ta.rsi().iloc[-1],2))<=30:
                                botlaburo.send_text(par+" LONG!!!")
                        if ta.xsignals(ta.macd(df['close'])['MACD_12_26_9'], ta.macd(df['close'])['MACDs_12_26_9'], ta.macd(df['close'])['MACDs_12_26_9'],above=False)['TS_Entries'].iloc[-1]!=0:
                            #botlaburo.send_text(par+" The MACD line crosses below. "+period)                            
                            if (tr.truncate(df.ta.rsi().iloc[-1],2))>=70:
                                botlaburo.send_text(par+" SHORT!!!")

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

