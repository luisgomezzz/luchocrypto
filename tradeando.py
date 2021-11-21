from datetime import datetime
from datetime import timedelta
import math
import yfinance
import matplotlib.dates as mpl_dates
import pandas as pd
import numpy as np
pd.core.common.is_list_like = pd.api.types.is_list_like
import pandas_datareader.data as web
import time
import yfinance as yahoo_finance
yahoo_finance.pdr_override()
from mplfinance.original_flavor import candlestick2_ohlc
from argparse import ArgumentParser
import matplotlib.pyplot as plt
import ccxt
import talib.abstract as tl
import pandas_ta as ta
from os import system, name
import ccxt
import os

def historicdf(par):
    ## Datos para indicadores que precisan muchos días hacia atrás para su análisis.
    exchange=ccxt.binance()
    barsindicators = exchange.fetch_ohlcv(par,timeframe='1d',limit=300)
    dfindicators = pd.DataFrame(barsindicators,columns=['time','open','high','low','close','volume'])
    return dfindicators

def sound():
    duration = 1000  # milliseconds
    freq = 440  # Hz

    # for windows
    if name == 'nt':
        _ = system('cls')
    # for mac and linux(here, os.name is 'posix')
    else:
        _ = os.system('play -nq -t alsa synth %s sin %s' % (duration/1000, freq))

def clear():  
    # for windows
    if name == 'nt':
        _ = system('cls')
    # for mac and linux(here, os.name is 'posix')
    else:
        _ = system('clear')

def truncate(number, digits) -> float:
    stepper = 10.0 ** digits
    return math.trunc(stepper * number) / stepper

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
        df['time'] = pd.to_datetime(df.index)
        df['time'] = df['time'].apply(mpl_dates.date2num)
        df = df.loc[:,['time', 'open', 'high', 'low', 'close']]

        def isSupport(df,i):
            support = df['low'][i] < df['low'][i-1]  and df['low'][i] < df['low'][i+1] and df['low'][i+1] < df['low'][i+2] and df['low'][i-1] < df['low'][i-2]
            return support
        def isResistance(df,i):
            resistance = df['high'][i] > df['high'][i-1]  and df['high'][i] > df['high'][i+1] and df['high'][i+1] > df['high'][i+2] and df['high'][i-1] > df['high'][i-2]
            return resistance

        s =  np.mean(df['high'] - df['low'])

        def isFarFromLevel(l):
            return np.sum([abs(l-x) < s  for x in levels]) == 0

        levels = []
        for i in range(2,df.shape[0]-2):
            if isSupport(df,i):
                l = df['low'][i]
                if isFarFromLevel(l):
                    levels.append((i,l))
            elif isResistance(df,i):
                l = df['high'][i]
                if isFarFromLevel(l):
                    levels.append((i,l))
            
        output= str([x[1] for x in levels])
    except:
        output= str('-1')
        pass

    return output            

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

def dibujo(par) -> plt:
    name = par

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


    print("aca1")

    connected = False
    while not connected:
        try:
            exchange=ccxt.binance()
            barsindicators = exchange.fetch_ohlcv(par,timeframe='1d',limit=300)
            ticker_df = pd.DataFrame(barsindicators,columns=['time','open','high','low','close','volume'])
            ticker_df = ticker_df.reset_index()

            #ticker_df = web.get_data_yahoo(tickers, period = args.period, interval = args.interval)
            #ticker_df = ticker_df.reset_index()
            connected = True
        except Exception as e:
            print("type error: " + str(e))
            time.sleep(5)
            pass

    print("aca2")
    for ticker in tickers:
        print ("\n\n" + ticker)
        try:
            print("aca3")
            x_max = 0
            fig, ax = plt.subplots()
            print("aca4")
            if(len(tickers)!=1):
                print("aca5")
                dfRes = createZigZagPoints(ticker_df.Close[ticker]).dropna()
                candlestick2_ohlc(ax,ticker_df['open'][ticker],ticker_df['high'][ticker],ticker_df['low'][ticker],ticker_df['close'][ticker],width=0.6, colorup='g', colordown='r')
            else:
                print("aca6")
                dfRes = createZigZagPoints(ticker_df.Close).dropna()
                print("aca7")
                candlestick2_ohlc(ax,ticker_df['open'],ticker_df['high'],ticker_df['low'],ticker_df['close'],width=0.6, colorup='g', colordown='r')
            
            
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
            #botlaburo.send_plot(plt)
            #botamigos.send_plot(plt)	
            if (x_max>args.min):
                plt.title(ticker)
                #plt.show()
            return plt
            #plt.clf()
            #plt.cla()
            #plt.close()
        except Exception as e: print(e)      