import pandas as pd
pd.core.common.is_list_like = pd.api.types.is_list_like
import pandas_datareader.data as web
import matplotlib.pyplot as plt
import time
import yfinance as yahoo_finance
yahoo_finance.pdr_override()
from mplfinance.original_flavor import candlestick2_ohlc
from argparse import ArgumentParser
from bob_telegram_tools.bot import TelegramBot
import matplotlib.pyplot as plt

token = '2108740619:AAHcUBakZLdoHYnvUvkBp6oq7SoS63erb2g'
user_id = '@gofrecrypto'
bot = TelegramBot(token, user_id)

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
	tickers = ['ONGC-USD']
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
		#bot.send_plot(plt)	
		if (x_max>args.min):
			plt.title(ticker)
			plt.show()
		plt.clf()
		plt.cla()
		plt.close()
	except Exception as e: print(e)