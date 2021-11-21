from binance.client import Client
from binance.exceptions import BinanceAPIException
import sys
import pandas as pd
pd.core.common.is_list_like = pd.api.types.is_list_like
import yfinance as yahoo_finance
yahoo_finance.pdr_override()
from bob_telegram_tools.bot import TelegramBot
sys.path.insert(1,'./')
import tradeando as tr
import ccxt
import pandas_ta as ta

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
                        volumen24h=client.futures_ticker(symbol=par)['quoteVolume']
                    except:
                        volumen24h=0

                    try:
                        ## Datos para dentro de los últimos minutos para la alarma de movimientos bruscos.
                        exchange=ccxt.binance()
                        bars = exchange.fetch_ohlcv(par,timeframe='1m',limit=ventana)
                        df = pd.DataFrame(bars,columns=['time','open','high','low','close','volume'])
                        preciomenor=float(min(df['low']))
                        preciomayor=float(max(df['high']))
                        precioactual = float(client.get_symbol_ticker(symbol=par)["price"])

                        ## Datos históricos para alarmas relacionadas con indicadores.
                        historicdf=tr.historicdf(par)

                        #ALARMA DE MOVIEMIENTOS BRUSCOS
                        if ((precioactual - preciomenor)*(100/preciomenor))>=porcentaje and (precioactual>=preciomayor) and float(volumen24h)>=float(1):
                            mensaje=par+" up "+str(round(((precioactual - preciomenor)*(100/preciomenor)),2))+"% - "+str(ventana)+" minutes. RSI: "+str(tr.truncate(historicdf.ta.rsi().iloc[-1],2))+". Price: "+str(precioactual)
                            botamigos.send_text(mensaje)                            
                            botamigos.send_plot(tr.dibujo(par))
                            #####################################para mi
                            botlaburo.send_text(mensaje)
                            botlaburo.send_plot(tr.dibujo(par))
                            botlaburo.send_text(tr.supportresistance(par))
                        if ((preciomenor - precioactual)*(100/preciomenor))>=porcentaje and (precioactual<=preciomenor) and float(volumen24h)>=float(1):
                            mensaje=par+" down "+str(round(((preciomenor - precioactual)*(100/preciomenor)),2))+"% - "+str(ventana)+" minutes. RSI: "+str(tr.truncate(historicdf.ta.rsi().iloc[-1],2))+". Price: "+str(precioactual)
                            botamigos.send_text(mensaje)                            
                            botamigos.send_plot(tr.dibujo(par))
                            #####################################para mi
                            botlaburo.send_text(mensaje)
                            botlaburo.send_plot(tr.dibujo(par))
                            botlaburo.send_text(tr.supportresistance(par))                        
                        sys.stdout.write("\rBuscando oportunidad. Ctrl+c para salir. Par: "+par+"\033[K")
                        sys.stdout.flush()

                        #ALARMA DE SOBRECOMPRA O SOBREVENTA

                        #if (tr.truncate(historicdf.ta.rsi().iloc[-1],2))<30:
                        #    botlaburo.send_text(par+" Sobreventa")
                        #else:
                        #    if (tr.truncate(historicdf.ta.rsi().iloc[-1],2))>70:
                        #        botlaburo.send_text(par+" Sobrecompra")

                        #ALARMAS DE CRUCES
                        #cruces de RSI
                        if ta.xsignals(historicdf.ta.rsi(), 30, 70, above=True)['TS_Entries'].iloc[-1]!=0:
                            botlaburo.send_text(par+" RSI crosses above 30 and then below 70. ENTRY")

                        if ta.xsignals(historicdf.ta.rsi(), 30, 70, above=True)['TS_Exits'].iloc[-1]!=0:
                            botlaburo.send_text(par+" RSI crosses above 30 and then below 70. EXIT")
                           
                        if ta.xsignals(historicdf.ta.rsi(), 30, 70, above=False)['TS_Entries'].iloc[-1]!=0:
                            botlaburo.send_text(par+" RSI crosses below 30 and then above 70. ENTRY")

                        if ta.xsignals(historicdf.ta.rsi(), 30, 70, above=False)['TS_Exits'].iloc[-1]!=0:
                            botlaburo.send_text(par+" RSI crosses below 30 and then above 70. EXIT")

                        #cruces entre 2 SMAs
                        
                        #if ta.xsignals(historicdf.ta.sma(21), historicdf.ta.sma(50), historicdf.ta.sma(50),above=True)['TS_Entries'].iloc[-1]!=0:
                        #    botlaburo.send_text(par+" The first SMA crosses above the second SMA and then below.")
                        #    print(ta.xsignals(historicdf.ta.sma(21), historicdf.ta.sma(50), historicdf.ta.sma(50),above=True)['TS_Entries'].iloc[-1])
                        #if ta.xsignals(historicdf.ta.sma(21), historicdf.ta.sma(50), historicdf.ta.sma(50),above=False)['TS_Entries'].iloc[-1]!=0:
                        #    botlaburo.send_text(par+" The first SMA crosses below the second SMA and then above.")                            
                        #    print(ta.xsignals(historicdf.ta.sma(21), historicdf.ta.sma(50), historicdf.ta.sma(50),above=False)['TS_Entries'].iloc[-1])

                    except KeyboardInterrupt:
                        print("\rSalida solicitada.\033[K")
                        sys.exit()
                    except Exception as falla:
                        sys.stdout.write("\rFALLA:"+str(falla)+"\033[K")
                        sys.stdout.flush()
                        pass
                    
                except KeyboardInterrupt:
                   print("\rSalida solicitada.\033[K")
                   sys.exit()            
                except BinanceAPIException as a:
                   if a.message!="Invalid symbol.":
                      print("\rExcept 1 - Par:",par,"- Error:",a.status_code,a.message,"\033[K")
                   pass
       
    except BinanceAPIException as a:
       print("\rExcept 2 - Par:",par,"- Error:",a.status_code,a.message,"\033[K")
       pass

if __name__ == '__main__':
    main()

