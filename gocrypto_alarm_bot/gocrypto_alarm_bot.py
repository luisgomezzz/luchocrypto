import os
from binance.client import Client
from datetime import datetime
from datetime import timedelta
import sys
from binance.exceptions import BinanceAPIException
import requests

#!/usr/bin/env python3
import requests
import json
#bot: gocrypto_alarm_bot

chatid="@gofrecrypto" #canal
idgrupo = "-704084758" #grupo de amigos
token = "2108740619:AAHcUBakZLdoHYnvUvkBp6oq7SoS63erb2g"
url = "https://api.telegram.org/bot"+token+"/sendMessage"

def main() -> None:    

    def mandomensaje (mensaje,id):
        params = {
            'chat_id':id,
            'text':mensaje
        }
        r=requests.post(url,params=params)

        data = json.loads(r.text)
        print(data['ok'])
        print (r.text)

    #procentajes de subida al cual se activa la alarma
    porcentajedia = 5

    #mazmorra - monedas que no quiero operar en orden de castigo
    #mazmorra=['GTCUSDT','TLMUSDT','KEEPUSDT','SFPUSDT','ALICEUSDT','SANDUSDT','STORJUSDT','RUNEUSDT','FTMUSDT','HBARUSDT','CVCUSDT','LRCUSDT','LINAUSDT','CELRUSDT','SKLUSDT','CTKUSDT','SNXUSDT','SRMUSDT','1INCHUSDT','ANKRUSDT'] 
    mazmorra=['NADA '] 

    #alarma
    duration = 1000  # milliseconds
    freq = 440  # Hz
   
    ventana = 40 #Ventana de búsqueda en minutos.   

    #login
    binance_api="N7yU75L3CNJg2RW0TcJBAW2cUjhPGvyuSFUgnRHvMSMMiS8WpZ8Yd8yn70evqKl0"
    binance_secret="2HfMkleskGwTb6KQn0AKUQfjBDd5dArBW3Ykd2uTeOiv9VZ6qSU2L1yWM1ZlQ5RH"
    client = Client(binance_api, binance_secret)

    #*****************************************************PROGRAMA PRINCIPAL *************************************************************
    #os.system("clear")

    exchange_info = client.futures_exchange_info()
    mandomensaje ("Starting... ",chatid)
    try:

        while 1==1:#dt.datetime.today().hour >=10 and dt.datetime.today().hour <=16: #horario en donde las oportunidades no son tan volátiles. Además no jugar sábados y domingos.

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

                        precioanterior = float(min(trades, key=lambda x:x['p'])['p'])
                        precioactual = float(client.get_symbol_ticker(symbol=par)["price"])  
                        preciomayor = float(max(trades, key=lambda x:x['p'])['p'])        

                        if ((precioactual - precioanterior)*(100/precioanterior))>=porcentaje and (precioactual>=preciomayor) and float(volumen24h)>=float(1):
                            print("\rOportunidad "+par+" Subió un",round(((precioactual - precioanterior)*(100/precioanterior)),2),"%\033[K")
                            os.system('play -nq -t alsa synth %s sin %s' % (duration/1000, freq))
                            #input("Press Enter to continue...")     
                            mensaje=par+" up "+str(round(((precioactual - precioanterior)*(100/precioanterior)),2))+"%"
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

