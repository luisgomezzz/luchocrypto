import plotly.graph_objects as go
import util as ut
import numpy as np
import pandas_ta as pta
from plotly.subplots import make_subplots
import pandas as pd

# Get user input
symbol = "BTCUSDT"
marketTF = "1d"
rsiMom = 70
useRsi      = False

# Get daily data
df = ut.calculardf(symbol, marketTF)
# Get weekly data
df_weekly = ut.calculardf(symbol, "1w")
# Calculate EMA for weekly data
ema_weekly = df_weekly['close'].ewm(span=20, adjust=False).mean()
# Resample EMA to daily data
ema_weekly = ema_weekly.reindex(df.index, method='nearest')
df['emaweek']=ema_weekly
df['emaweek']=df['emaweek'].shift(9)
df['color_emaweek']=np.where(df.close>df.emaweek, 'green', 'red')
# Get ATR value
df['atrValue'] = pta.atr(df['high'], df['low'], df['close'], length=5)
# Check if price is above or below EMA filter
df['regimeFilter'] = df.close > (df.emaweek + (df.atrValue * 0.25))
# Calculate RSI
df['rsiValue'] = pta.rsi(df['close'], length=7)
# Get bullish momentum filter
df['bullish'] = df['regimeFilter'] & (df.rsiValue.any() > rsiMom or not useRsi)
# Define bearish caution filter
df['caution'] = df['bullish'] & ((df['high'].rolling(window=7).max() - df['low']) > (df['atrValue'] * 1.5))
# Set momentum color
df['bgCol'] = 'red'
df['bgCol'] = np.where(df['bullish'].shift(-1)==True,'green',df['bgCol'])
df['bgCol'] = np.where(df['caution'].shift(-1)==True,'orange',df['bgCol'])
# Set trailing stop loss
df['trailStop']= np.nan
position_size=0
df['buy_sell'] = np.nan


#########################################################

for i, row in df.iterrows():
    #Handle strategy entry
    if row.bullish and position_size==0 and not row.caution:
        row.buy_sell = 'buy'
        position_size=100
        row.trailStop == np.nan 
    #Handle trailing stop           
    if position_size > 0:
        temp_trailStop = pd.Series([row.low]).rolling(window=7).max() - np.where(not row.caution, row.atrValue * 0.2 , row.atrValue)
        if (temp_trailStop > row.trailStop).any() or row.trailStop == np.nan:
            row.trailStop = temp_trailStop
    # Handle strategy exit
    if (((row.close < row.trailStop) or (row.close < row.emaweek))) and position_size>0:
        row.buy_sell = 'sell'
        position_size=0

print(df.tail(60))
fig = make_subplots(specs=[[{"secondary_y": True}]])
# velas
fig.add_trace(
            go.Candlestick(
            x=df['timestamp'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close']
        ),
               secondary_y=True
)
# volume
fig.add_trace(go.Bar(
    x=df.index,
    y=df['volume'],
    showlegend=False,
    marker={
        "color": "rgba(128,128,128,0.5)",
    }
),
secondary_y=False)
# ema weekly
fig.add_trace(
            go.Scatter(
            x=df['timestamp'],
            y=df['emaweek'],
            mode='markers+lines',
            marker={'color': df['color_emaweek']}, 
            line={'color': 'gray'},
            name='EMA(20) weekly'
        ),
               secondary_y=True
)
# momentum
fig.add_trace(
            go.Scatter(
            x=df['timestamp'],
            y=df['emaweek'],
            mode='markers+lines',
            marker={'color': df['bgCol']}, 
            line={'color': 'gray'},
            name='Momentum Strength'
        ),
               secondary_y=False
)

fig.update_layout(title=f"{symbol}", height=800)
fig.update_yaxes(title="Price $", secondary_y=True, showgrid=True)
fig.update_yaxes(title="Volume $", secondary_y=False, showgrid=False)
fig.show()
