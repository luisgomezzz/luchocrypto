from time import sleep
from binance.client import Client
from binance.exceptions import BinanceAPIException
import sys
import pandas as pd
pd.core.common.is_list_like = pd.api.types.is_list_like
import yfinance as yahoo_finance
yahoo_finance.pdr_override()
sys.path.insert(1,'./')
import utilidades as ut
import pandas_ta as pdta
import datetime as dt
from datetime import datetime

temporalidad='3m'
client = Client(ut.binance_api, ut.binance_secret)   
botlaburo = ut.creobot('laburo')      

def main() -> None:

    ratio=1.5 #relación riesgo/beneficio 
    mazmorra=['NADA '] #Monedas que no quiero operar en orden de castigo
    ventana = 240 #Ventana de búsqueda en minutos.   
    exchange=ut.binanceexchange(ut.binance_api,ut.binance_secret) #login
    lista_de_monedas = client.futures_exchange_info()['symbols'] #obtiene lista de monedas
    saldo_inicial=float(exchange.fetch_balance()['info']['totalWalletBalance'])+float((exchange.fetch_balance()['BNB']['total'])*float(client.get_symbol_ticker(symbol='BNBUSDT')["price"]))
    posicioncreada = False
    minvolumen24h=float(100000000)
    primerpar=str('')
    minutes_diff=0
    lista_monedas_filtradas=[]
    mensaje=''
    balanceobjetivo = 24.00

    ut.clear() #limpia terminal

    for s in lista_de_monedas:
        try:  
            par = s['symbol']
            sys.stdout.write("\rFiltrando monedas: "+par+"\033[K")
            sys.stdout.flush()
            if float(client.futures_ticker(symbol=par)['quoteVolume'])>minvolumen24h and 'USDT' in par:
                lista_monedas_filtradas.append(par)
        except:
            pass

    try:

        while True:

          for par in lista_monedas_filtradas:

            if par not in mazmorra:

                if primerpar=='':
                    primerpar=par
                    datetime_start = datetime.today()
                else:
                    if primerpar==par:
                        datetime_end = datetime.today()
                        minutes_diff = (datetime_end - datetime_start).total_seconds() / 60.0
                        primerpar=''

                try:
                    try:
                        sys.stdout.write("\rSearching. Ctrl+c to exit. Pair: "+par+" - Tiempo de vuelta: "+str(ut.truncate(minutes_diff,2))+" min\033[K")
                        sys.stdout.flush()
                        
                        df=ut.calculardf (par,temporalidad,ventana)
                        dfmacd=ut.calculardf (par,'1d',ventana)
                        
                        if  ((df['low'].iloc[-1] > (df.ta.ema(5).iloc[-1])*(1+0.16/100)) and (df.ta.ema(5).iloc[-1] > df.ta.ema(20).iloc[-1] > df.ta.ema(200).iloc[-1])
                            and (df.ta.macd()["MACD_12_26_9"].iloc[-1]>df.ta.macd()["MACDs_12_26_9"].iloc[-1])):
                                
                            print("\n*********************************************************************************************")
                            mensaje="Trade - "+par+" - BUY"
                            mensaje=mensaje+"\nVer Oliver: "+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))
                            print(mensaje)
                            ut.sound()

                    except KeyboardInterrupt:
                        print("Salida solicitada. ")
                        sys.exit()
                    except BinanceAPIException as e:
                        if e.message!="Invalid symbol.":
                            print("Error3 - Par:",par,"-",e.status_code,e.message)                            
                        pass
                    except Exception as falla:
                        if str(falla)!="binance does not have market symbol "+par:
                            print("Error4: "+str(falla))
                        pass

                except KeyboardInterrupt:
                    print("Salida solicitada.")
                    sys.exit()            
                except BinanceAPIException as a:
                    if a.message!="Invalid symbol.":
                        print("Error5 - Par:",par,"-",a.status_code,a.message)
                    pass
       
    except BinanceAPIException as a:
       print("Error6 - Par:",par,"-",a.status_code,a.message)
       pass

if __name__ == '__main__':
    main()

