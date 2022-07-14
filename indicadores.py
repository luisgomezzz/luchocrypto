import sys
import pandas as pd
pd.core.common.is_list_like = pd.api.types.is_list_like
sys.path.insert(1,'./')
import numpy as np
import pandas_ta as pta

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

def atrslf(df):
    #ATR Stop Loss Finder
    rma = df.ta.rma(close=atr(df), length=14)
    m = 0.85
    x = rma * m + df.high
    x2 = df.low - rma * m
    return x,x2

def trendtraderstrategy (df):
    Multiplier = 3
    Length = 21    
    df2=df.tail(Length)

    df['avgTR'] = pta.wma(atr(df,1), Length)
    df['highestC']   = df2.close.max()
    df['lowestC']    = df2.close.min()

    df['hiLimit'] = df.highestC.shift(1) - (df.avgTR.shift(1) * Multiplier)
    df['loLimit'] = df.lowestC.shift(1) + (df.avgTR.shift(1) * Multiplier)

    df['ret'] = 0.0
    df['ret'] = np.where((df.close > df.hiLimit) & (df.close > df.loLimit), df.hiLimit, 
    np.where((df.close < df.hiLimit) & (df.close < df.loLimit),df.loLimit,
    np.where(~df.ret.shift(1).isna(),df.ret.shift(1),df.close)))

    return df.ret

