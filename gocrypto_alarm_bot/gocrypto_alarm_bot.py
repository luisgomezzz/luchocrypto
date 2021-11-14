from binance.client import Client
from datetime import datetime
from datetime import timedelta
import sys
from binance.exceptions import BinanceAPIException
import requests
import math

#!/usr/bin/env python3
import requests
import json
#bot: gocrypto_alarm_bot

import talib
import numpy as np

def truncate(number, digits) -> float:
    stepper = 10.0 ** digits
    return math.trunc(stepper * number) / stepper

def rsi14 (client,par) -> float:
    now = datetime.now() # current date and time
    hoy = now.strftime("%d %b %Y")

    haceNdias=(now-timedelta(days=300)).strftime("%d %b %Y")

    candles = client.get_historical_klines(par,Client.KLINE_INTERVAL_1DAY,haceNdias,hoy)

    all4th = [el[4] for el in candles]

    np_float_data = np.array([float(x) for x in all4th])
    np_out=talib.RSI(np_float_data)

    return float(np_out[-1])

chatid="@gofrecrypto" #canal
idgrupo = "-704084758" #grupo de amigos
token = "2108740619:AAHcUBakZLdoHYnvUvkBp6oq7SoS63erb2g"
url = "https://api.telegram.org/bot"+token+"/sendMessage"

def mandomensaje (mensaje,id):
    params = {
        'chat_id':id,
        'text':mensaje
    }
    r=requests.post(url,params=params)
    data = json.loads(r.text)
    print(data['ok'])
    print (r.text)

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
    #os.system("clear")

    exchange_info = client.futures_exchange_info()
    mandomensaje ("Starting... ",chatid)
    try:

        while True:

          porcentaje=porcentajedia
             
          for s in exchange_info['symbols']:

            par = s['symbol']            

            if par not in mazmorra:

                comienzo = datetime.now() - timedelta(minutes=ventana)
                comienzoms = int(comienzo.timestamp() * 1000)

                finalms = int(datetime.now().timestamp() * 1000)

                try:
                    try:
                        volumen24h=client.futures_ticker(symbol=par)['quoteVolume']
                    except:
                        volumen24h=0

                    try:   

                        trades = client.get_aggregate_trades(symbol=par, startTime=comienzoms,endTime=finalms)

                        preciomenor = float(min(trades, key=lambda x:x['p'])['p'])
                        precioactual = float(client.get_symbol_ticker(symbol=par)["price"])  
                        preciomayor = float(max(trades, key=lambda x:x['p'])['p'])        

                        if ((precioactual - preciomenor)*(100/preciomenor))>=porcentaje and (precioactual>=preciomayor) and float(volumen24h)>=float(1):
                            #os.system('play -nq -t alsa synth %s sin %s' % (duration/1000, freq))
                            #input("Press Enter to continue...")     
                            print("paso")
                            mensaje=par+" up "+str(round(((precioactual - preciomenor)*(100/preciomenor)),2))+"% - "+str(ventana)+" minutes. RSI14: "+str(truncate(rsi14(client,par),2))
                            print (mensaje)
                            mandomensaje (mensaje,idgrupo)
                            mandomensaje (mensaje,chatid)                             

                        if ((preciomenor - precioactual)*(100/preciomenor))>=porcentaje and (precioactual<=preciomenor) and float(volumen24h)>=float(1):
                            #os.system('play -nq -t alsa synth %s sin %s' % (duration/1000, freq))
                            #input("Press Enter to continue...")     
                            print("paso")
                            mensaje=par+" down "+str(round(((preciomenor - precioactual)*(100/preciomenor)),2))+"% - "+str(ventana)+" minutes. RSI14: "+str(truncate(rsi14(client,par),2))
                            print (mensaje)
                            mandomensaje (mensaje,idgrupo)
                            mandomensaje (mensaje,chatid) 
                        
                        sys.stdout.write("\rBuscando oportunidad. Ctrl+c para salir. Par: "+par+"\033[K")
                        sys.stdout.flush()
                        
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

