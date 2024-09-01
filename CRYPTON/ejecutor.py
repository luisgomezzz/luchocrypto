################################
## EJECUCIONES A VELA CERRADA ##
################################

import estrategias as est
import sys
import util
from datetime import datetime
from time import sleep

lista = ['ETHUSDT', 'BCHUSDT', 'XRPUSDT', 'LTCUSDT', 'ETCUSDT', 'LINKUSDT', 'ADAUSDT', 'BNBUSDT', 'DOGEUSDT', 'DOTUSDT', 
         'SOLUSDT', 'AVAXUSDT', 'NEARUSDT', 'FILUSDT', 'MATICUSDT', 'OPUSDT', 'FETUSDT', 'AGIXUSDT', 'ARBUSDT',  
         'SLPUSDT', 'MEMEUSDT',  '1000SATSUSDT', 'PIXELUSDT'
         #,'BNBUSDT' #no alcanza para crear la posicion
         #,'BTCUSDT' #no alcanza para crear la posicion
         ]

timeframe = '1h'
limit = 1000
sma_length = 50
sma_macd_length = 80
balance_tradear = 240

print(f"timeframe: {timeframe} - limit: {limit} - sma_length: {sma_length} - sma_macd_length: {sma_macd_length}")
while True:
    for symbol in lista:
        try:
            posiciones_abiertas = util.get_posiciones_abiertas()
            fecha_hora_actual = datetime.now()
            mensaje = f"Fecha: {fecha_hora_actual} - Symbol: {symbol} - posiciones_abiertas: {posiciones_abiertas}                                       "
            sys.stdout.write("\r"+mensaje)
            sys.stdout.flush()
            data = est.estrategia_divergencias (symbol,timeframe,limit,sma_length,sma_macd_length)            
            if data.trade[-2] == -1: #BUY                
                if symbol in posiciones_abiertas:
                    if posiciones_abiertas[symbol] == 'SELL':
                        # cierra posicion
                        util.sound(duration = 1000, freq = 400)
                        print(f"fecha: {fecha_hora_actual} - Cerrar SELL Symbol: {symbol}")
                        util.closeposition(symbol,'SELL')
                        util.closeallopenorders (symbol)
                else:
                    # crea posicion
                    util.sound(duration = 1000, freq = 400)
                    print(f"fecha: {fecha_hora_actual} - Entrada en BUY Symbol: {symbol} - precio: {data.Close[-2]} - SL: {data.stop_loss[-2]}")                    
                    if util.crea_posicion(symbol,'BUY',balance_tradear,data.porcentajeentrada[-2]):
                        util.crea_stoploss (symbol,'BUY',data.stop_loss[-2])
            elif data.trade[-2] == -2: #SELL                
                if symbol in posiciones_abiertas:
                    if posiciones_abiertas[symbol] == 'BUY':
                        # cierra posicion
                        util.sound(duration = 1000, freq = 400)
                        print(f"fecha: {fecha_hora_actual} - Cerrar BUY Symbol: {symbol}")
                        util.closeposition(symbol,'BUY')
                        util.closeallopenorders (symbol)
                else:
                    # crea posicion
                    util.sound(duration = 1000, freq = 400)
                    print(f"fecha: {fecha_hora_actual} - Entrada en SELL Symbol: {symbol} - precio: {data.Close[-2]} - SL: {data.stop_loss[-2]}")
                    if util.crea_posicion(symbol,'SELL',balance_tradear,data.porcentajeentrada[-2]):
                        util.crea_stoploss (symbol,'SELL',data.stop_loss[-2])
        except Exception as e:
            print(f"Error en {symbol}: {e}")
        except KeyboardInterrupt as ky:
            print("\nSalida solicitada. ")
            sys.exit() 
    sleep(1200) # espero 1200 segundos
