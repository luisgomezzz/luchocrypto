import util as ut
import numpy as np
from backtesting import Backtest, Strategy
import constantes as cons
cons.clear()

np.seterr(divide='ignore')

monedas = [
'XRPUSDT',
'EOSUSDT',
'LTCUSDT',
'LINKUSDT',
'ADAUSDT',
'BNBUSDT',
'DOGEUSDT',
'KAVAUSDT',
'SOLUSDT',
'STORJUSDT',
'AVAXUSDT',
'FTMUSDT',
'TOMOUSDT',
'FILUSDT',
'MATICUSDT',
'ALPHAUSDT',
'SANDUSDT',
'LINAUSDT',
'MTLUSDT',
'MASKUSDT',
'DYDXUSDT',
'APEUSDT',
'OPUSDT',
'INJUSDT',
'LDOUSDT',
'APTUSDT',
'RNDRUSDT',
'CFXUSDT',
'STXUSDT',
'ARBUSDT',
'EDUUSDT',
'SUIUSDT',
'RADUSDT'
]

for symbol in monedas:
    data = ut.estrategia(symbol)
    if ut.backtesting_validation(data,print_output=False):
        print("#########################################")
        print(symbol)
        ut.backtesting_validation(data,print_output=True)
