import sys
import pandas as pd
pd.core.common.is_list_like = pd.api.types.is_list_like
sys.path.insert(1,'./')
import numpy as np
import pandas_ta as pta
pd.options.mode.chained_assignment = None

def tr(df):
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)    
    return true_range

def atr(df,length):
    true_range = tr(df)
    atr = true_range.rolling(length).sum()/length
    return atr

def atrslf(df,length):
    #ATR Stop Loss Finder
    rma = df.ta.rma(close=atr(df,length), length=14)
    m = 0.85
    x = rma * m + df.high
    x2 = df.low - rma * m
    return x.iloc[-1],x2.iloc[-1]

def trendtraderstrategy (df):
    Multiplier = 3
    Length = 21    
    df['avgTR'] = pta.wma(atr(df,1), Length)
    df=df.tail(Length)
    df['highestC']   = df.close.max()
    df['lowestC']    = df.close.min()
    df=df.tail(Length)
    df['hiLimit'] = 0.0
    df['loLimit'] = 0.0
    df['ret'] = 0.0
    df.insert(loc=0, column='row_num', value=np.arange(len(df)))

    for index, row in df.iterrows():
        df.hiLimit[index] = df.highestC[df.row_num[index]-1] - (df.avgTR[df.row_num[index]-1] * Multiplier)
        df.loLimit[index] = df.lowestC[df.row_num[index]-1] + (df.avgTR[df.row_num[index]-1] * Multiplier)

    for index, row in df.iterrows():
        df.ret[index] = np.where((row.close > row.hiLimit) & (row.close > row.loLimit), row.hiLimit, 
            np.where((row.close < row.hiLimit) & (row.close < row.loLimit),row.loLimit,
            np.where(df.ret[df.row_num[index]-1]!=0,df.ret[df.row_num[index]-1],row.close)))

    return df.ret.iloc[-1]

def get_sma(prices, rate):
    return prices.rolling(rate).mean()

def get_bollinger_bands(df, rate=20):
    df.index = np.arange(df.shape[0])
    prices=df.close
    sma = get_sma(prices, rate)
    std = prices.rolling(rate).std()
    bollinger_up = sma + std * 2 # Calculate top band
    bollinger_down = sma - std * 2 # Calculate bottom band
    return bollinger_up, bollinger_down

def wwma(values, n):
    """
     J. Welles Wilder's EMA 
    """
    return values.ewm(alpha=1/n, adjust=False).mean()

def indatr(df, n=14):
    data = df.copy()
    high = data.high
    low = data.low
    close = data.close
    data['tr0'] = abs(high - low)
    data['tr1'] = abs(high - close.shift())
    data['tr2'] = abs(low - close.shift())
    tr = data[['tr0', 'tr1', 'tr2']].max(axis=1)
    atr = wwma(tr, n)
    return atr    

def fli(df):
    flidf=df.copy()
    BBperiod      = 21
    BBdeviations  = 1
    ATRperiod     = 5
    
    flidf['BBUpper']=pta.sma(flidf.close,BBperiod)+flidf.close.rolling(BBperiod).std()*BBdeviations
    flidf['BBLower']=pta.sma(flidf.close,BBperiod)-flidf.close.rolling(BBperiod).std()*BBdeviations    
    flidf['BBSignal'] = np.where(flidf.close>flidf.BBUpper,1,np.where(flidf.close<flidf.BBLower,-1,0))
    flidf['lowatr']=flidf.low-indatr(flidf,ATRperiod)
    flidf['highatr']=flidf.high+indatr(flidf,ATRperiod)
    
    flidf['TrendLine'] = 0.0
    flidf['iTrend'] = 0
    flidf['buy'] = 0
    flidf['sell'] = 0

    for index, row in flidf.iterrows():
        flidf.TrendLine = np.where(flidf.BBSignal==1,np.where(flidf.lowatr<flidf.TrendLine.shift(1),flidf.TrendLine.shift(1),flidf.lowatr),flidf.TrendLine)
        flidf.TrendLine = np.where(flidf.BBSignal==-1,np.where(flidf.highatr>flidf.TrendLine.shift(1),flidf.TrendLine.shift(1),flidf.highatr),flidf.TrendLine)
        flidf.TrendLine = np.where(flidf.BBSignal==0,flidf.TrendLine.shift(1),flidf.TrendLine)            
    
    for index, row in flidf.iterrows():
        flidf.iTrend = flidf.iTrend.shift(1)
        flidf.iTrend = np.where(flidf.TrendLine>flidf.TrendLine.shift(1),1,np.where(flidf.TrendLine<flidf.TrendLine.shift(1),-1,flidf.iTrend.shift(1)))
    
    flidf.buy = np.where((flidf.iTrend.shift(1)==-1) & (flidf.iTrend==1),1,np.NaN)
    flidf.sell  = np.where((flidf.iTrend.shift(1)==1) & (flidf.iTrend==-1),1,np.NaN)
    flidf['dibujo'] = np.where(flidf.buy == 1 & (flidf.sell.shift(1) != 1),'Bomba',np.where(flidf.sell == 1 & (flidf.buy.shift(1) != 1),'Martillo',np.NaN))

    dffinal=flidf[['TrendLine','dibujo']].copy() 

    return dffinal

def swingHighLow(df):
    df2=df.copy()
    df2['swinglow'] = (df.low < df.low.shift(1)) & (df.low < df.low.shift(2)) & (df.low < df.low.shift(3)) & (df.low < df.low.shift(4)) & (df.low < df.low.shift(5)) & (df.low < df.low.shift(6)) & (df.low < df.low.shift(7)) & (df.low < df.low.shift(8)) & (df.low < df.low.shift(9))
    df2['swinghigh'] = (df.high > df.high.shift(1)) & (df.high > df.high.shift(2)) & (df.high > df.high.shift(3)) & (df.high > df.high.shift(4)) & (df.high > df.high.shift(5)) & (df.high > df.high.shift(6)) & (df.high > df.high.shift(7)) & (df.high > df.high.shift(8)) & (df.high > df.high.shift(9))
    df2.insert(loc=0, column='row_num', value=np.arange(len(df2)))
    swinglow=df2.loc[(df2['swinglow'] == True)].iloc[-1].close
    swinghigh=df2.loc[(df2['swinghigh'] == True)].iloc[-1].close

    return swinglow, swinghigh


