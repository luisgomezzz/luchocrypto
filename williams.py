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

botlaburo = ut.creobot('laburo')
temporalidad='5m'
client = Client(ut.binance_api, ut.binance_secret)         

def main() -> None:

    posicioncreada = False    
    mazmorra=['NADA '] #Monedas que no quiero operar en orden de castigo
    ventana = 240 #Ventana de búsqueda en minutos.   
    exchange=ut.binanceexchange(ut.binance_api,ut.binance_secret) #login
    lista_de_monedas = client.futures_exchange_info()['symbols'] #obtiene lista de monedas
    posicion=[0,'NADA']

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
                        df=ut.binancehistoricdf(par,timeframe=temporalidad,limit=ventana) # para fractales.
                 
                        if ut.will_frac(df)[0].iloc[-1]==True:
                            posicion=[-1,'BEARS']
                        else:
                            if ut.will_frac(df)[1].iloc[-1]==True:
                                posicion=[-1,'BULLS']
                            else:
                                if ut.will_frac(df)[0].iloc[-2]==True:
                                    posicion=[-2,'BEARS']
                                else:
                                    if ut.will_frac(df)[1].iloc[-2]==True:
                                        posicion=[-2,'BULLS']
                                    else:
                                        if ut.will_frac(df)[0].iloc[-3]==True:
                                            posicion=[-3,'BEARS']
                                        else:
                                            if ut.will_frac(df)[1].iloc[-3]==True:
                                                posicion=[-3,'BULLS']
                                            else:
                                                if ut.will_frac(df)[0].iloc[-4]==True:
                                                    posicion=[-4,'BEARS']
                                                else:
                                                    if ut.will_frac(df)[1].iloc[-4]==True:
                                                        posicion=[-4,'BULLS']       


                        if posicion[0]!=0:
                            df2=ut.binancehistoricdf(par,timeframe=temporalidad,limit=ventana) # Buscar valores mínimos y máximos N (ventana) minutos para atrás.
                            ut.timeindex(df2) #Formatea el campo time para luego calcular las señales
                            df2.ta.study() # Runs and appends all indicators to the current DataFrame by default

                            ema20=df2.ta.ema(20).iloc[posicion[0]]
                            ema50=df2.ta.ema(50).iloc[posicion[0]]
                            
                            if posicion[1]=='BULLS':
                                factral = df2.low.iloc[posicion[0]]
                                lado='BUY'
                                if ema20<ema50:
                                    stopprice=ema20
                                else:
                                    stopprice=ema50
                            else:
                                factral = df2.high.iloc[posicion[0]]
                                lado='SELL'
                                if ema20<ema50:
                                    stopprice=ema50
                                else:
                                    stopprice=ema20

                            if ema20<ema50:
                                if ema20<factral<ema50:
                                    print('-1-'+par+'-'+posicion[1])
                                    ut.posicionfuerte(par,lado,client,stopprice)
                                    ut.sound()
                                    sys.exit()
                            else:
                                if ema20>factral>ema50:
                                    print('-2-'+par+'-'+posicion[1])
                                    ut.posicionfuerte(par,lado,client,stopprice)
                                    ut.sound()
                                    sys.exit()

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

