import sys
import pandas as pd
pd.core.common.is_list_like = pd.api.types.is_list_like
sys.path.insert(1,'./')
import numpy as np
  
def atr(df):
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    atr = true_range.rolling(14).sum()/14
    return atr

def atrslf(df):
    #ATR Stop Loss Finder
    rma = df.ta.rma(close=atr(df), length=14)
    m = 0.85
    x = rma * m + df.high
    x2 = df.low - rma * m
    return x,x2


