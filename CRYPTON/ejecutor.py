import estrategias as est
import sys
import util

lista = ['BTCUSDT', 'ETHUSDT', 'BCHUSDT', 'XRPUSDT', 'LTCUSDT', 'ETCUSDT', 'LINKUSDT', 'ADAUSDT', 'BNBUSDT', 'DOGEUSDT', 'DOTUSDT', 
         'SOLUSDT', 'AVAXUSDT', 'NEARUSDT', 'FILUSDT', 'MATICUSDT', 'OPUSDT', 'FETUSDT', 'AGIXUSDT', 'ARBUSDT',  
         'SLPUSDT', 'MEMEUSDT',  '1000SATSUSDT', 'PIXELUSDT']

timeframe = '1h'
limit = 1000
sma_length = 50
sma_macd_length = 80

print(f"timeframe: {timeframe} - limit: {limit} - sma_length: {sma_length} - sma_macd_length: {sma_macd_length}")
while True:
    for symbol in lista:
        try:
            mensaje = f"Symbol: {symbol}    "
            sys.stdout.write("\r"+mensaje)
            sys.stdout.flush()
            data = est.estrategia_divergencias (symbol,timeframe,limit,sma_length,sma_macd_length)
            if data.trade[-1] == -1:
                print(f"Entrada en long Symbol: {symbol} SL: {data.stop_loss[-1]}")
                util.sound(duration = 1000, freq = 400)
            if data.trade[-1] == -2:    
                print(f"Entrada en short Symbol: {symbol} SL: {data.stop_loss[-1]}")
                util.sound(duration = 1000, freq = 400)
        except Exception as e:
            print(f"Error en {symbol}: {e}")

