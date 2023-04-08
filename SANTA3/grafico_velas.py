import plotly.graph_objects as go
import util as ut
import numpy as np
import pandas_ta as pta
from plotly.subplots import make_subplots

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
df['bullish'] = df.regimeFilter.any() and (df.rsiValue.any() > rsiMom or not useRsi)
# Define bearish caution filter
df['caution'] = df['bullish'] & ((df['high'].rolling(window=7).max() - df['low']) > (df['atrValue'] * 1.5))
# Set momentum color
df['bgCol'] = 'red'
if df.bullish.iloc[-2]:
    df['bgCol'] = 'green'
if df.caution.iloc[-2]:
    df['bgCol'] = 'orange'
print(df)

fig = make_subplots(specs=[[{"secondary_y": True}]])

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

# include a go.Bar trace for volumes
fig.add_trace(go.Bar(
    x=df.index,
    y=df['volume'],
    showlegend=False,
    marker={
        "color": "rgba(128,128,128,0.5)",
    }
),
secondary_y=False)

fig.add_trace(
            go.Scatter(
            x=df['timestamp'],
            y=df['emaweek'],
            mode='markers+lines',
            marker={'color': df['color_emaweek']}, 
            line={'color': 'gray'},
            name='EMA(20)'
        ),
               secondary_y=True
)

fig.layout.yaxis2.showgrid=False
fig.update_layout(title="ETH/USDC pool after Uniswap v3 deployment", height=800)
fig.update_yaxes(title="Price $", secondary_y=True, showgrid=True)
fig.update_yaxes(title="Volume $", secondary_y=False, showgrid=False)
fig.show()
