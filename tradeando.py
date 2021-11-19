from datetime import datetime
from datetime import timedelta
import math
from pkg_resources import ensure_directory
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
        df['Date'] = pd.to_datetime(df.index)
        df['Date'] = df['Date'].apply(mpl_dates.date2num)
        df = df.loc[:,['Date', 'Open', 'High', 'Low', 'Close']]

        def isSupport(df,i):
            support = df['Low'][i] < df['Low'][i-1]  and df['Low'][i] < df['Low'][i+1] and df['Low'][i+1] < df['Low'][i+2] and df['Low'][i-1] < df['Low'][i-2]
            return support
        def isResistance(df,i):
            resistance = df['High'][i] > df['High'][i-1]  and df['High'][i] > df['High'][i+1] and df['High'][i+1] > df['High'][i+2] and df['High'][i-1] > df['High'][i-2]
            return resistance

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

def rsi14 (par) -> float:
    exchange=ccxt.binance()
    bars = exchange.fetch_ohlcv(par,timeframe='1m',limit=20160)
    df = pd.DataFrame(bars,columns=['time','open','high','low','close','volume'])
    return float(df.ta.rsi().iloc[-1])

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

def ema(par, period, posi =-1, field='close' ):   
    #posi: -1 indicates last position
    exchange=ccxt.binance()
    bars = exchange.fetch_ohlcv(par,timeframe='1m',limit=300)
    df = pd.DataFrame(bars,columns=['time','open','high','low','close','volume'])
    return tl.EMA(df, timeperiod=period, price=field).iloc[posi]    

def ema3(par, posi =-1, short=50, medium=100, large=150, field='close' ):   
    #posi: -1 indicates last position
    exchange=ccxt.binance()
    bars = exchange.fetch_ohlcv(par,timeframe='1m',limit=300)
    df = pd.DataFrame(bars,columns=['time','open','high','low','close','volume'])
    return [tl.EMA(df, timeperiod=short, price=field).iloc[posi],tl.EMA(df, timeperiod=medium, price=field).iloc[posi],tl.EMA(df, timeperiod=large, price=field).iloc[posi]]
           
def estrategia3emas (par):
    output=False
    now=ema3(par,-1)
    minago=ema3(par,-30)

    myradiansshort = math.atan2(minago[0]-now[0],30)
    mydegreesshort = math.degrees(myradiansshort)

    myradiansmedium = math.atan2(minago[1]-now[1],30)
    mydegreesmedium = math.degrees(myradiansmedium)

    myradianslarge = math.atan2(minago[2]-now[2],30)
    mydegreeslarge = math.degrees(myradianslarge)

    #si el angulo esta entre 60 y 30 y entre ellos no difiere en mas de 10 grados
    if 60 <= mydegreesshort <= 30:
        if abs(mydegreesshort - mydegreesmedium) < 10:
            if abs(mydegreesmedium - mydegreeslarge) < 10:
                output=True
            else:
                output=False
    
    return output
