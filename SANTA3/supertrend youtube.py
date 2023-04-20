#https://www.youtube.com/watch?v=ekz6ugJE1h0&ab_channel=AnalyzingAlpha
import pandas_ta as pta
import util as ut
import numpy as np
import pandas as pd

symbol='ETCUSDT'
timeframe ='1m'
df=ut.calculardf(symbol,timeframe)

atrPeriod = 10
factor = 3
adxlen = 7
dilen = 7

def tr(df):
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)    
    return true_range

def dirmov(df,len):
    up = df['high'] - df['high'].shift(1)
    down=df['down'] = -1 * df['low'].diff()
    df['plusDM']=np.where((np.isnan(up)),np.NaN,(np.where(((up > down) & (up > 0)),up,0)))
    df['minusDM']=np.where((np.isnan(down)),np.NaN,(np.where(((down > up) & (down > 0)),down,0)))
    truerange = pta.rma(tr(df), length=len)
    plus = (100* pta.rma(df.plusDM, len) / truerange)
    minus = (100 * pta.rma(df.minusDM, len) / truerange)
    return plus, minus

def adx(df,dilen, adxlen):
    [plus, minus] = dirmov(df,dilen)
    sum = plus + minus
    adx = 100 * pta.rma(abs(plus - minus) / (np.where(sum == 0,1,sum)), adxlen)
    return adx

def lucho_rsi(x, y):
    delta = x.diff()
    u = delta.where(delta > 0, 0)
    d = abs(delta.where(delta < 0, 0))
    rs = pta.rma(u, y) / pta.rma(d, y)
    res = 100 - 100 / (1 + rs)
    return res

df['sig'] = adx(df,dilen, adxlen)
position_size= 0
df['direccion'] = pta.supertrend(df['high'], df['low'], df['close'], atrPeriod=atrPeriod, factor=factor)['SUPERTd_7_3.0']*-1
df['resta'] = df['direccion'] - df['direccion'].shift(1)
df['resta'].fillna(0)
df['rsi21']=lucho_rsi(df.close, 21)
df['rsi3']=lucho_rsi(df.close, 3)
df['rsi28']=lucho_rsi(df.close, 28)
df['entry'] = np.nan
df['entry'] = np.where((df.resta < 0) & (df.rsi21 < 66) & (df.rsi3 > 80) & (df.rsi28 > 49) & (df.sig > 20), "BUY", np.where((df.resta > 0) & (df.rsi21 > 34) & (df.rsi3 < 20) & (df.rsi28 < 51) & (df.sig > 20),"SELL",np.nan))

print(df.tail(60))
