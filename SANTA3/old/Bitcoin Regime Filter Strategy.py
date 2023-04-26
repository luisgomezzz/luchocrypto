import plotly.graph_objects as go
import util as ut
import numpy as np
import pandas_ta as pta
from plotly.subplots import make_subplots
import pandas as pd

# Get user input
symbol = "DOGEUSDT"
marketTF = "1d"
rsiMom = 70
useRsi = False
res = "1w"

def f_sec(df, timeframe):
    # convertir la columna timestamp a un objeto datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    # calcular la diferencia de tiempo entre filas adyacentes
    time_diff = df['timestamp'].diff()
    # determinar si la barra actual ha terminado
    if time_diff.iloc[-1] == pd.Timedelta(timeframe):
        # la barra actual ha terminado
        return 0
    else:
        # la barra actual aún no ha terminado
        return 1

# Get daily data
df = ut.calculardf(symbol, marketTF)
# Get weekly data
df_weekly = ut.calculardf(symbol, res)
# Calculate EMA for weekly data
ema_weekly = pta.ema(df_weekly['close'],20)
if f_sec(df, res) == 1:
    ema_weekly.iloc[-1] = ema_weekly.iloc[-2]
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
df['bgCol'] = np.where(df['bullish'].shift(-1),'green',df['bgCol'])
df['bgCol'] = np.where(df['caution'].shift(-1),'orange',df['bgCol'])
# Set trailing stop loss
df['trailStop']= np.nan
position_size=0
df['buy_sell'] = np.nan


#########################################################
df['temp_trailStop']=np.nan

for i, row in df.iterrows():
    df.loc[:, 'temp_trailStop'] = df['low'].rolling(7).max() - (df.atrValue[i] * 0.2 if pd.Series(df.caution).shift(-1)[i] else df.atrValue[i])
    #Handle strategy entry
    if df.bullish[i] and position_size==0 and not df.caution[i]:
        df.loc[i, 'buy_sell'] = 'buy'
        position_size=100
        df.loc[i, 'trailStop'] = np.nan
    # Handle trailing stop
    elif position_size > 0:
        if (pd.Series(df.temp_trailStop[i] > df.trailStop[i]).any() or pd.isna(df.trailStop[i])):
            df.loc[i, 'trailStop'] = df.temp_trailStop[i]
    
    # Handle strategy exit
    if (((df.close[i] < df.trailStop[i]) or (df.close[i] < df.emaweek[i]))) and position_size>0:
        df.loc[i, 'buy_sell'] = 'sell'
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
# trail stop
fig.add_trace(
            go.Scatter(
            x=df['timestamp'],
            y=df['trailStop'],
            mode='markers+lines',
            marker={'color': 'blue'}, 
            line={'color': 'gray'},
            name='trailing stop'
        ),
               secondary_y=True
)

fig.add_trace(
            go.Scatter(x=df['timestamp'],
               y=df['close'],
               text=df['buy_sell'],
               textposition='top right',
               textfont=dict(color='black',size=16),
               mode='text',
               name='buy_sell')
,secondary_y=True
)
fig.update_layout(title=f"{symbol}", height=800)
fig.update_yaxes(title="Price $", secondary_y=True, showgrid=True)
fig.update_yaxes(title="Volume $", secondary_y=False, showgrid=False)
fig.show()



