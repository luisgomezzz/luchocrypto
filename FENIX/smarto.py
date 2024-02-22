import modulos as md
import numpy as np
import os
import sys
import constantes as cons
import warnings
from time import sleep

def warn(*args, **kwargs):
    pass
warnings.warn = warn
np.seterr(divide='ignore')
lista_filtrada = []

while True:
    print(f"Filtrando monedas...")
    lista=md.filtradodemonedas ()
    #lista = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'LINKUSDT', 'BNBUSDT', 'SOLUSDT', 'ARBUSDT', 'SUIUSDT', 'ORDIUSDT', '1000SATSUSDT', 'MANTAUSDT', 'ALTUSDT', 'JUPUSDT']
    #lista = ['XRPUSDT']

    timeframe = '1h'

    if len(lista) > 1:
        imprimo = False
        debug = False
    else:
        imprimo = True
        debug = True
    print(lista)
    porcentajes_sumados = 0
    win_rate_buenos = 0
    win_rate_malos = 0
    trades = 0
    balance = 100
    tp_multiplicador = 18
    poisiciones_abiertas = md.get_posiciones_abiertas()
    for symbol in lista:    
        try:
            if symbol not in poisiciones_abiertas:
                crear_orden = False
                data = md.estrategia_smart(symbol, debug = False, refinado = False, fuente = 0, timeframe = timeframe, largo = 1)
                resultado = md.backtesting_smart(data, plot_flag=imprimo, symbol=symbol)
                if resultado['Win Rate [%]'] >= 50:
                    lista_filtrada.append(symbol)
                print(f"{symbol} - Return [%]: {md.truncate(resultado['Return [%]'],2)}% - # Trades: {resultado['# Trades']} - Profit Factor: {resultado['Profit Factor']} - Win Rate [%]: {resultado['Win Rate [%]']}")
                porcentajes_sumados=porcentajes_sumados+resultado['Return [%]']
                trades = trades + resultado['# Trades']
                if not np.isnan(resultado['Win Rate [%]']):
                    if resultado['Win Rate [%]'] >= 50:
                        win_rate_buenos = win_rate_buenos+1
                    else:
                        win_rate_malos = win_rate_malos+1
                ## para smart        
                if (### LONG
                    data.trend.iloc[-2]=='Alcista' and
                    data.Close.iloc[-1] < (data.decisional_alcista_high.iloc[-2] + (data.atr.iloc[-1]*6))):
                    print(f"posible entrada long symbol: {symbol}")   
                    crear_orden=True
                    size = balance * data.porcentajeentrada_alcista.iloc[-2]/100
                    precio = md.RoundToTickUp(symbol,data.decisional_alcista_high.iloc[-2] + data.offset.iloc[-2])
                    sl= md.RoundToTickUp(symbol,data.decisional_alcista_low.iloc[-2] - data.offset.iloc[-2])
                    tp = md.RoundToTickUp(symbol,data.decisional_alcista_high.iloc[-2] + data.atr.iloc[-2]*tp_multiplicador)
                    tamanio = md.truncate((size/precio),md.get_quantityprecision(symbol))   
                    side = 'BUY'
                elif (### SHORT
                        data.trend.iloc[-2]=='Bajista' and
                        data.Close.iloc[-1] > (data.decisional_bajista_low.iloc[-2] - (data.atr.iloc[-1]*6))):
                        print(f"posible entrada short symbol: {symbol}")
                        crear_orden=True
                        size = balance * data.porcentajeentrada_bajista.iloc[-2]/100
                        precio = md.RoundToTickUp(symbol,data.decisional_bajista_low.iloc[-2] - data.offset.iloc[-2])
                        sl= md.RoundToTickUp(symbol,data.decisional_bajista_high.iloc[-2] + data.offset.iloc[-2])
                        tp = md.RoundToTickUp(symbol,data.decisional_bajista_low.iloc[-2] - data.atr.iloc[-2]*tp_multiplicador)
                        tamanio = md.truncate((size/precio),md.get_quantityprecision(symbol))
                        side = 'SELL'
                ### creacion de ordenes
                #crear_orden=False
                if crear_orden==True:
                    md.closeallopenorders (symbol)
                    cons.client.futures_create_order(symbol=symbol,
                        side=side,
                        type='LIMIT',
                        quantity=tamanio,
                        timeInForce='GTC',
                        price=precio
                    )
                    # Crear la orden Stop-Loss
                    orden_stop_loss = cons.client.futures_create_order(
                        symbol=symbol,
                        side=np.where(side == 'BUY','SELL','BUY'),
                        type='STOP_MARKET',
                        quantity=tamanio,
                        stopPrice=sl,
                        closePosition=True
                    )
                    ## Crear la orden take profit
                    #orden_take_profit = cons.client.futures_create_order(
                    #    symbol=symbol,
                    #    side=np.where(side == 'BUY','SELL','BUY'),
                    #    type='TAKE_PROFIT_MARKET',
                    #    quantity=tamanio,
                    #    stopPrice=tp,
                    #    closePosition=True
                    #)
        except Exception as falla:
            _, _, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print("Error: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname))
            pass
    print("duermo 30 minutos...")
    sleep(1800)
    for symbol in lista_filtrada:
        md.printandlog(cons.nombrelog,symbol,pal=1)
    print(f"Timeframe {timeframe} - porcentajes_sumados {md.truncate(porcentajes_sumados,2)} - trades {trades} - win_rate_buenos {win_rate_buenos} - win_rate_malos {win_rate_malos} - Ganancia por trade: {md.truncate((porcentajes_sumados/trades if trades !=0 else porcentajes_sumados),2)}%")
