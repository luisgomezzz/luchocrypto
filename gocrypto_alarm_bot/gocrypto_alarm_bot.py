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
                        
                        exchange=ccxt.binance()
                        bars = exchange.fetch_ohlcv(par,timeframe='1m',limit=ventana)
                        df = pd.DataFrame(bars,columns=['time','open','high','low','close','volume'])
                        preciomenor=float(min(df['low']))
                        preciomayor=float(max(df['high']))
                        precioactual = float(client.get_symbol_ticker(symbol=par)["price"])

                        if ((precioactual - preciomenor)*(100/preciomenor))>=porcentaje and (precioactual>=preciomayor) and float(volumen24h)>=float(1):
                            #os.system('play -nq -t alsa synth %s sin %s' % (duration/1000, freq))
                            #input("Press Enter to continue...")
                            mensaje=par+" up "+str(round(((precioactual - preciomenor)*(100/preciomenor)),2))+"% - "+str(ventana)+" minutes. RSI: "+str(tr.truncate(tr.rsi14(par),2))+". Price: "+str(precioactual)
                            botlaburo.send_text(mensaje)
                            botamigos.send_text(mensaje)                            
                            botlaburo.send_plot(tr.dibujo(par))
                            botamigos.send_plot(tr.dibujo(par))
                            botlaburo.send_text(tr.supportresistance(par))
                        if ((preciomenor - precioactual)*(100/preciomenor))>=porcentaje and (precioactual<=preciomenor) and float(volumen24h)>=float(1):
                            #os.system('play -nq -t alsa synth %s sin %s' % (duration/1000, freq))
                            #input("Press Enter to continue...")     
                            mensaje=par+" down "+str(round(((preciomenor - precioactual)*(100/preciomenor)),2))+"% - "+str(ventana)+" minutes. RSI: "+str(tr.truncate(tr.rsi14(par),2))+". Price: "+str(precioactual)
                            botlaburo.send_text(mensaje)
                            botamigos.send_text(mensaje)
                            botlaburo.send_plot(tr.dibujo(par))
                            botamigos.send_plot(tr.dibujo(par))
                            botlaburo.send_text(tr.supportresistance(par))
                        
                        if tr.estrategia3emas (par) == True:
                            botlaburo.send_text("estrategia 3 gemas")

                        sys.stdout.write("\rBuscando oportunidad. Ctrl+c para salir. Par: "+par+"\033[K")
                        sys.stdout.flush()
                        
                    except KeyboardInterrupt:
                        print("\rSalida solicitada.\033[K")
                        sys.exit()
                    except:
                        sys.stdout.write("\rFalla típica de conexión catcheada...:D\033[K")
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

