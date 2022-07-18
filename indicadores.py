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