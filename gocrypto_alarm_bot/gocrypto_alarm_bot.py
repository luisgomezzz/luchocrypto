from binance.client import Client
from datetime import datetime
from datetime import timedelta
import sys
from binance.exceptions import BinanceAPIException
import requests
import math
import yfinance
from mplfinance.original_flavor import candlestick_ohlc
import matplotlib.dates as mpl_dates
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
#!/usr/bin/env python3
import requests
import json
#bot: gocrypto_alarm_bot
import talib
import numpy as np
#dibujar
pd.core.common.is_list_like = pd.api.types.is_list_like
import pandas_datareader.data as web
import time
import yfinance as yahoo_finance
yahoo_finance.pdr_override()
from mplfinance.original_flavor import candlestick2_ohlc
from argparse import ArgumentParser
from bob_telegram_tools.bot import TelegramBot
import matplotlib.pyplot as plt

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

botlaburo = TelegramBot(token, chatid)
botamigos = TelegramBot(token, idgrupo)

def createZigZagPoints(dfSeries, minSegSize=0.1, sizeInDevs=0.5):

	minRetrace = minSegSize
	
	curVal = dfSeries[0]
	curPos = dfSeries.index[0]
	curDir = 1
	dfRes = pd.DataFrame(index=dfSeries.index, columns=["Dir", "Value"])
	for ln in dfSeries.index:
		if((dfSeries[ln] - curVal)*curDir >= 0):
			curVal = dfSeries[ln]
			curPos = ln
		else:	   
			retracePrc = abs((dfSeries[ln]-curVal)/curVal*100)
			if(retracePrc >= minRetrace):
				dfRes.loc[curPos, 'Value'] = curVal
				dfRes.loc[curPos, 'Dir'] = curDir
				curVal = dfSeries[ln]
				curPos = ln
				curDir = -1*curDir
	dfRes[['Value']] = dfRes[['Value']].astype(float)
	return(dfRes)

def dibujo(par):
    name = par.replace("USDT", "-USD")

    parser = ArgumentParser(description='Algorithmic Support and Resistance')
    parser.add_argument('-t', '--tickers', default='SPY500', type=str, required=False, help='Used to look up a specific tickers. Commma seperated. Example: MSFT,AAPL,AMZN default: List of S&P 500 companies')
    parser.add_argument('-p', '--period', default='1d', type=str, required=False, help='Period to look back. valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max. default: 1d')
    parser.add_argument('-i', '--interval', default='1m', type=str, required=False, help='Interval of each bar. valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo. default: 1m')
    parser.add_argument('-d', '--dif', default='0.05', type=float, required=False, help='Max %% difference between two points to group them together. Default: 0.05')
    parser.add_argument('--time', default='150', type=int, required=False, help='Max time measured in number of bars between two points to be grouped together. Default: 150')
    parser.add_argument('-n', '--number', default='3', type=int, required=False, help='Min number of points in price range to draw a support/resistance line. Default: 3')
    parser.add_argument('-m', '--min', default='150', type=int, required=False, help='Min number of bars from the start the support/resistance line has to be at to display chart. Default: 150')
    args = parser.parse_args()

    #S&P 500 Tickers
    if (args.tickers=="SPY500"):
        tickers = [name]
    else:
        tickers = args.tickers.split(",")

    connected = False
    while not connected:
        try:
            ticker_df = web.get_data_yahoo(tickers, period = args.period, interval = args.interval)
            ticker_df = ticker_df.reset_index()
            connected = True
        except Exception as e:
            print("type error: " + str(e))
            time.sleep(5)
            pass

    for ticker in tickers:
        print ("\n\n" + ticker)
        try:
            x_max = 0
            fig, ax = plt.subplots()
            if(len(tickers)!=1):
                dfRes = createZigZagPoints(ticker_df.Close[ticker]).dropna()
                candlestick2_ohlc(ax,ticker_df['Open'][ticker],ticker_df['High'][ticker],ticker_df['Low'][ticker],ticker_df['Close'][ticker],width=0.6, colorup='g', colordown='r')
            else:
                dfRes = createZigZagPoints(ticker_df.Close).dropna()
                candlestick2_ohlc(ax,ticker_df['Open'],ticker_df['High'],ticker_df['Low'],ticker_df['Close'],width=0.6, colorup='g', colordown='r')
            
            plt.plot(dfRes['Value'])
            removed_indexes = []
            for index, row in dfRes.iterrows():
                if (not(index in removed_indexes)):
                    dropindexes = []
                    dropindexes.append(index)
                    counter = 0
                    values = []
                    values.append(row.Value)
                    startx = index
                    endx = index
                    dir = row.Dir
                    for index2, row2 in dfRes.iterrows():
                        if (not(index2 in removed_indexes)):
                            if (index!=index2 and abs(index2-index)<args.time and row2.Dir==dir):
                                if (abs((row.Value/row2.Value)-1)<(args.dif/100)):
                                        dropindexes.append(index2)
                                        values.append(row2.Value)
                                        if (index2<startx):
                                            startx = index2
                                        elif (index2>endx):
                                            endx = index2
                                        counter=counter+1
                    if (counter>args.number):
                        sum = 0
                        print ("Support at ", end='')
                        for i in range(len(values)-1):
                            print("{:0.2f} and ".format(values[i]), end='')
                        print("{:0.2f} \n".format(values[len(values)-1]), end='')
                        removed_indexes.extend(dropindexes)
                        for value in values:
                            sum = sum + value
                        if (endx>x_max):
                            x_max=endx
                        plt.hlines(y=sum/len(values), xmin=startx, xmax=endx, linewidth=1, color='r')
            botlaburo.send_plot(plt)
            botamigos.send_plot(plt)	
            if (x_max>args.min):
                plt.title(ticker)
                #plt.show()
            plt.clf()
            plt.cla()
            plt.close()
        except Exception as e: print(e)    

def supportresistance(par):
    plt.rcParams['figure.figsize'] = [12, 7]
    plt.rc('font', size=14)
    now = datetime.now() # current date and time
    hoy = now.strftime("%Y-%m-%d")
    haceNdias=(now-timedelta(days=300)).strftime("%Y-%m-%d")

    output=str('-1')
    name = par.replace("USDT", "-USD")
    print("Searching pair in yfinance as", name) 


    try:
        ticker = yfinance.Ticker(name)
        df = ticker.history(interval="1d",start=haceNdias, end=hoy)
        df['Date'] = pd.to_datetime(df.index)
        df['Date'] = df['Date'].apply(mpl_dates.date2num)
        df = df.loc[:,['Date', 'Open', 'High', 'Low', 'Close']]

        def isSupport(df,i):
            support = df['Low'][i] < df['Low'][i-1]  and df['Low'][i] < df['Low'][i+1] and df['Low'][i+1] < df['Low'][i+2] and df['Low'][i-1] < df['Low'][i-2]
            return support
        def isResistance(df,i):
            resistance = df['High'][i] > df['High'][i-1]  and df['High'][i] > df['High'][i+1] and df['High'][i+1] > df['High'][i+2] and df['High'][i-1] > df['High'][i-2]
            return resistance

        def plot_all():
            fig, ax = plt.subplots()
            candlestick_ohlc(ax,df.values,width=0.6,colorup='green', colordown='red', alpha=0.8)
            date_format = mpl_dates.DateFormatter('%d %b %Y')
            ax.xaxis.set_major_formatter(date_format)
            fig.autofmt_xdate()
            fig.tight_layout()
            for level in levels:
                plt.hlines(level[1],xmin=df['Date'][level[0]], xmax=max(df['Date']),colors='blue')
            fig.show()    

        s =  np.mean(df['High'] - df['Low'])

        def isFarFromLevel(l):
            return np.sum([abs(l-x) < s  for x in levels]) == 0

        levels = []
        for i in range(2,df.shape[0]-2):
            if isSupport(df,i):
                l = df['Low'][i]
                if isFarFromLevel(l):
                    levels.append((i,l))
            elif isResistance(df,i):
                l = df['High'][i]
                if isFarFromLevel(l):
                    levels.append((i,l))
            
        output= str([x[1] for x in levels])
    except:
        output= str('-1')
        pass

    return output        

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
    
    botlaburo.send_text("Starting...")
   
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
                            print("paso1")     
                            mensaje=par+" up "+str(round(((precioactual - preciomenor)*(100/preciomenor)),2))+"% - "+str(ventana)+" minutes. RSI: "+str(truncate(rsi14(client,par),2))+". Price: "+str(precioactual)
                            botlaburo.send_text(mensaje)
                            botamigos.send_text(mensaje)
                            dibujo(par)
                            botlaburo.send_text(supportresistance(par))
                        if ((preciomenor - precioactual)*(100/preciomenor))>=porcentaje and (precioactual<=preciomenor) and float(volumen24h)>=float(1):
                            #os.system('play -nq -t alsa synth %s sin %s' % (duration/1000, freq))
                            #input("Press Enter to continue...")     
                            print("paso2")
                            mensaje=par+" down "+str(round(((preciomenor - precioactual)*(100/preciomenor)),2))+"% - "+str(ventana)+" minutes. RSI: "+str(truncate(rsi14(client,par),2))+". Price: "+str(precioactual)
                            botlaburo.send_text(mensaje)
                            botamigos.send_text(mensaje)
                            dibujo(par)
                            botlaburo.send_text(supportresistance(par))

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

