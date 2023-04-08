import plotly.graph_objects as go
import util as ut
import pandas as pd
import numpy as np

# Get user input
symbol = "BTCUSDT"
marketTF = "1d"

# Get daily data
df = ut.calculardf(symbol, marketTF)

# Get weekly data
df_weekly = ut.calculardf(symbol, "1w")

# Calculate EMA for weekly data
ema_weekly = df_weekly['close'].ewm(span=20, adjust=False).mean()

# Resample EMA to daily data
ema_weekly = ema_weekly.reindex(df.index, method='nearest')
df['emaweek']=ema_weekly
df['color_emaweek']=np.where(df.close>df.emaweek, 'green', 'red')
print(df)
# Plot candlestick chart with EMA overlay
fig = go.Figure(
    data=[
        go.Candlestick(
            x=df['timestamp'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close']
        ),
        go.Scatter(
            x=df['timestamp'],
            y=df['emaweek'],
            mode='markers+lines',
            marker={'color': df['color_emaweek']}, 
            line={'color': 'gray'},
            name='EMA(20)'
        )
    ]
)

fig.show()
