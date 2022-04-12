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
import talib

temporalidad='3m'
client = Client(ut.binance_api, ut.binance_secret)         

def main() -> None:

    mazmorra=['NADA '] #Monedas que no quiero operar en orden de castigo
    ventana = 240 #Ventana de búsqueda en minutos.   
    exchange=ut.binanceexchange(ut.binance_api,ut.binance_secret) #login
    lista_de_monedas = client.futures_exchange_info()['symbols'] #obtiene lista de monedas
    saldo_inicial=float(exchange.fetch_balance()['info']['totalWalletBalance'])
    posicioncreada = False
    ratio=0.75 #relación riesgo/beneficio 
    minvolumen24h=float(100000000)

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
                 
                        ###CODIGO
                        ut.timeindex(df) #Formatea el campo time para luego calcular las señales
                        df.ta.study() # Runs and appends all indicators to the current DataFrame by default

                        crosshigh=(ta.xsignals(df.ta.cci(40),100,100,above=True)).iloc[-1]
                        crosslow=(ta.xsignals(df.ta.cci(40),-100,-100,above=True)).iloc[-1]
                        if  (crosshigh[0]==1 and crosshigh[1]==1 and crosshigh[2]==1 and crosshigh[3]==0) or (crosslow[0]==1 and crosslow[1]==1 and crosslow[2]==1 and crosslow[3]==0):                             

                            high_9 = df.high.rolling(9).max()
                            low_9 = df.low.rolling(9).min()
                            df['tenkan_sen_line'] = (high_9 + low_9) /2
                            # Calculate Kijun-sen
                            high_26 = df.high.rolling(26).max()
                            low_26 = df.low.rolling(26).min()
                            df['kijun_sen_line'] = (high_26 + low_26) / 2
                            # Calculate Senkou Span A
                            df['senkou_spna_A'] = ((df.tenkan_sen_line + df.kijun_sen_line) / 2).shift(26)
                            # Calculate Senkou Span B
                            high_52 = df.high.rolling(52).max()
                            low_52 = df.high.rolling(52).min()
                            df['senkou_spna_B'] = ((high_52 + low_52) / 2).shift(26)
                            # Calculate Chikou Span B
                            df['chikou_span'] = df.close.shift(-26)
                            df['SAR'] = talib.SAR(df.high, df.low, acceleration=0.02, maximum=0.2)
                            df['signal'] = 0
                            df.loc[(df.close > df.senkou_spna_A) & (df.close > df.senkou_spna_B) & (df.close > df.SAR), 'signal'] = 1
                            df.loc[(df.close < df.senkou_spna_A) & (df.close < df.senkou_spna_B) & (df.close < df.SAR), 'signal'] = -1
                            
                            currentprice = float(client.get_symbol_ticker(symbol=par)["price"])
                            if df['signal'].iloc[-1]==1 and (df['signal'].iloc[-2]==0 or df['signal'].iloc[-2]==-1) and currentprice>df.ta.ema(50).iloc[-1] and currentprice>df.ta.ema(200).iloc[-1] and float(client.futures_ticker(symbol=par)['quoteVolume'])>minvolumen24h:
                                print("- "+par+" ESTRATEGIA psar BUY\n")
                                ut.posicionfuerte(par,'BUY',client)                                
                                posicioncreada=True
                                ut.sound()
                        else: 
                            if (crosshigh[0]==0 and crosshigh[1]==-1 and crosshigh[2]==0 and crosshigh[3]==1) or (crosslow[0]==0 and crosslow[1]==-1 and crosslow[2]==0 and crosslow[3]==1):
                                                                      
                                high_9 = df.high.rolling(9).max()
                                low_9 = df.low.rolling(9).min()
                                df['tenkan_sen_line'] = (high_9 + low_9) /2
                                # Calculate Kijun-sen
                                high_26 = df.high.rolling(26).max()
                                low_26 = df.low.rolling(26).min()
                                df['kijun_sen_line'] = (high_26 + low_26) / 2
                                # Calculate Senkou Span A
                                df['senkou_spna_A'] = ((df.tenkan_sen_line + df.kijun_sen_line) / 2).shift(26)
                                # Calculate Senkou Span B
                                high_52 = df.high.rolling(52).max()
                                low_52 = df.high.rolling(52).min()
                                df['senkou_spna_B'] = ((high_52 + low_52) / 2).shift(26)
                                # Calculate Chikou Span B
                                df['chikou_span'] = df.close.shift(-26)
                                df['SAR'] = talib.SAR(df.high, df.low, acceleration=0.02, maximum=0.2)
                                df['signal'] = 0
                                df.loc[(df.close > df.senkou_spna_A) & (df.close > df.senkou_spna_B) & (df.close > df.SAR), 'signal'] = 1
                                df.loc[(df.close < df.senkou_spna_A) & (df.close < df.senkou_spna_B) & (df.close < df.SAR), 'signal'] = -1
                                
                                currentprice = float(client.get_symbol_ticker(symbol=par)["price"])
                                if df['signal'].iloc[-1]==-1 and (df['signal'].iloc[-2]==0 or df['signal'].iloc[-2]==1) and currentprice<df.ta.ema(50).iloc[-1] and currentprice<df.ta.ema(200).iloc[-1] and float(client.futures_ticker(symbol=par)['quoteVolume'])>minvolumen24h:
                                    print("- "+par+" ESTRATEGIA psar SELL\n")
                                    ut.posicionfuerte(par,'SELL',client)
                                    posicioncreada=True
                                    ut.sound()

                        if posicioncreada==True:
                            while float(exchange.fetch_balance()['info']['totalPositionInitialMargin'])!=0.0:
                                sleep(1)

                            posicioncreada=False
                            client.futures_cancel_all_open_orders(symbol=par) 
                            
                            print("\rGANANCIA ACUMULADA: ",ut.truncate(((float(exchange.fetch_balance()['info']['totalWalletBalance'])/saldo_inicial)-1)*100,3),"%\033[K", ut.truncate(float(exchange.fetch_balance()['info']['totalWalletBalance'])-saldo_inicial,2),"USDT")
                            print("BALANCE TOTAL USDT: ",float(exchange.fetch_balance()['info']['totalWalletBalance']))
                            print("BALANCE TOTAL BNB: ",float((exchange.fetch_balance()['BNB']['total'])*float(client.get_symbol_ticker(symbol='BNBUSDT')["price"])))       

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

