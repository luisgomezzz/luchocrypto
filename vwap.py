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
import pandas_ta as ta
import datetime as dt

botlaburo = ut.creobot('laburo')
botamigos = ut.creobot('amigos') 
apalancamiento = 50
margen = 'CROSSED'
temporalidad='1m'
client = Client(ut.binance_api, ut.binance_secret)

def posicionfuerte(pair,side,bot):

    porcentajeentrada=2200
    exchange=ut.binanceexchange(ut.binance_api,ut.binance_secret)
    micapital = float(exchange.fetch_balance()['info']['totalWalletBalance'])
    size = (micapital*porcentajeentrada/100)/(float(client.get_symbol_ticker(symbol=pair)["price"]))
    try:
        if float(exchange.fetch_balance()['info']['totalPositionInitialMargin'])==0.0: #si no hay posiciones abiertas creo la alertada.
            if ut.binancecreoposicion (pair,client,size,side)==True:

                currentprice = float(client.get_symbol_ticker(symbol=pair)["price"]) 

                if side =='BUY':
                    stopprice = currentprice-(currentprice*0.2/100)
                else:
                    stopprice = currentprice+(currentprice*0.2/100)

                ut.binancestoploss (pair,client,side,stopprice)

                if ut.binancetakeprofit(pair,client,side,porc=0.20)==True:
                    bot.send_text(pair+" - TAKE_PROFIT_MARKET created "+ side)
    except:
        pass           

def main() -> None:

    posicioncreada = False    
    mazmorra=['NADA '] #Monedas que no quiero operar en orden de castigo
    ventana = 240 #Ventana de búsqueda en minutos.   
    exchange=ut.binanceexchange(ut.binance_api,ut.binance_secret) #login
    lista_de_monedas = client.futures_exchange_info()['symbols'] #obtiene lista de monedas

    botlaburo.send_text("Starting...") #mensaje de arranque telegram
    ut.clear() #limpia terminal

    try:
        while True:
          for s in lista_de_monedas:
            try:  
                position = exchange.fetch_balance()['info']['positions']
                par=[p for p in position if p['notional'] != '0'][0]['symbol']
            except:
                par = s['symbol']      

            if par not in mazmorra:
                try:
                    try:
                        sys.stdout.write("\rSearching. Ctrl+c to exit. Pair: "+par+"\033[K")
                        sys.stdout.flush()
                        df=ut.binancehistoricdf(par,timeframe=temporalidad,limit=ventana) # Buscar valores mínimos y máximos N (ventana) minutos para atrás.
                        ut.timeindex(df) #Formatea el campo time para luego calcular las señales
                        df.ta.study() # Runs and appends all indicators to the current DataFrame by default
                        print ("\033[A                                                                       \033[A")
                        
                        #EMA9 crossing VWAP
                        crossvwap=(ta.xsignals(df.ta.ema(9),df.ta.vwap(),df.ta.vwap(),above=True)).iloc[-1]
                        if  crossvwap[0]==1 and crossvwap[1]==1 and crossvwap[2]==1 and crossvwap[3]==0 : #and (dt.datetime.today().hour ==21):
                                
                                try:
                                    volumen24h=client.futures_ticker(symbol=par)['quoteVolume']
                                except:
                                    volumen24h=0

                                if float(volumen24h)>=float(100000000):    
                                    print(par+" ESTRATEGIA VWAP BUY\n")
                                    client.futures_change_leverage(symbol=par, leverage=apalancamiento)

                                    try: 
                                        print("\rDefiniendo Cross/Isolated...")
                                        client.futures_change_margin_type(symbol=par, marginType=margen)
                                    except BinanceAPIException as a:
                                        if a.message!="No need to change margin type.":
                                            print("Except 7",a.status_code,a.message)
                                        else:
                                            print("Done!")   
                                        pass  

                                    posicionfuerte(par,'BUY',botlaburo)
                                    ut.sound()
                                    #botlaburo.send_text(par+" ESTRATEGIA VWAP BUY ")
                                    posicioncreada = True
                        else: 
                            if  crossvwap[0]==0 and crossvwap[1]==-1 and crossvwap[2]==0 and crossvwap[3]==1:# and (dt.datetime.today().hour ==21):
                                
                                try:
                                    volumen24h=client.futures_ticker(symbol=par)['quoteVolume']
                                except:
                                    volumen24h=0

                                if float(volumen24h)>=float(100000000):    
                                    print(par+" ESTRATEGIA VWAP SELL\n")
                                    client.futures_change_leverage(symbol=par, leverage=apalancamiento)
                                    try: 
                                        print("\rDefiniendo Cross/Isolated...")
                                        client.futures_change_margin_type(symbol=par, marginType=margen)
                                    except BinanceAPIException as a:
                                        if a.message!="No need to change margin type.":
                                            print("Except 7",a.status_code,a.message)
                                        else:
                                            print("Done!")   
                                        pass  

                                    posicionfuerte(par,'SELL',botlaburo)      
                                    ut.sound()
                                    #botlaburo.send_text(par+" ESTRATEGIA VWAP SELL ")
                                    posicioncreada = True
                                    
                        if posicioncreada == True:
                            while float(exchange.fetch_balance()['info']['totalPositionInitialMargin'])!=0.0:
                                sleep(1)

                            client.futures_cancel_all_open_orders(symbol=par)
                            posicioncreada == False
                            #sys.exit()

                    except KeyboardInterrupt:
                        print("\rSalida solicitada.\033[K")
                        sys.exit()
                    except BinanceAPIException as e:
                        if e.message!="Invalid symbol.":
                            print("\rExcept 1 - Par:",par,"- Error:",e.status_code,e.message,"\033[K")
                            print("\n")
                        pass
                    except Exception as falla:
                        sys.stdout.write("\rError1: "+str(falla)+"\033[K")
                        sys.stdout.flush()
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

