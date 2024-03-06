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
    lista = md.filtradodemonedas ()
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
    balance = int(md.balancetotal())
    tp_multiplicador = 18
    lejania = 6
    # posiciones abiertas    
    posiciones_abiertas = md.get_posiciones_abiertas()

    # obtiene una lista de las ordenes actuales
    open_orders = cons.client.futures_get_open_orders() 
    lista_ordenes_acutales =[]
    for dato in open_orders:    
        if dato['symbol'] not in lista_ordenes_acutales:
            lista_ordenes_acutales.append(dato['symbol'])

    # cierra las ordenes que no estén en trades abiertos
    for i in lista_ordenes_acutales:
        if i not in posiciones_abiertas:
            md.closeallopenorders (i)

    # si hay una posición abierta y no está en la lista de monedas filtradas porque ya no comple las condiciones 
    # entonces la agrego ya que debo crear el tp.
    for i in posiciones_abiertas.keys():
        if i not in lista:
            lista.append(i)

    for symbol in lista:    
        try:
            data = md.estrategia_smart(symbol, debug = False, refinado = False, fuente = 0, timeframe = timeframe, largo = 1)
            if symbol not in posiciones_abiertas:
                crear_orden = False                
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
                    data.Close.iloc[-1] < (data.decisional_alcista_high.iloc[-2] + (data.atr.iloc[-1]*lejania))):
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
                        data.Close.iloc[-1] > (data.decisional_bajista_low.iloc[-2] - (data.atr.iloc[-1]*lejania))):
                        print(f"posible entrada short symbol: {symbol}")
                        crear_orden=True
                        size = balance * data.porcentajeentrada_bajista.iloc[-2]/100
                        precio = md.RoundToTickUp(symbol,data.decisional_bajista_low.iloc[-2] - data.offset.iloc[-2])
                        sl= md.RoundToTickUp(symbol,data.decisional_bajista_high.iloc[-2] + data.offset.iloc[-2])
                        tp = md.RoundToTickUp(symbol,data.decisional_bajista_low.iloc[-2] - data.atr.iloc[-2]*tp_multiplicador)
                        tamanio = md.truncate((size/precio),md.get_quantityprecision(symbol))
                        side = 'SELL'
                ### creacion de ordenes
                if crear_orden==True:                    
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
            else:
                # crea TP para las órdenes abiertas si no lo poseen
                tps_creados = 0
                open_limits = cons.client.futures_get_open_orders(symbol=symbol)     
                for orden in open_limits:
                    if orden['type'] == 'TAKE_PROFIT_MARKET':
                        tps_creados = tps_creados + 1
                if tps_creados == 0:
                    lado = posiciones_abiertas[symbol]
                    if lado == 'BUY':
                        tp = data['Close'].rolling(40).max().iloc[-1]
                    else:
                        tp = data['Close'].rolling(40).min().iloc[-1]
                    print(f"creo tp para {symbol}")
                    orden_take_profit = cons.client.futures_create_order(
                                                                        symbol=symbol,
                                                                        side=np.where(lado == 'BUY','SELL','BUY'),
                                                                        type='TAKE_PROFIT_MARKET',
                                                                        stopPrice=tp,
                                                                        closePosition=True
                                                                        )
        except Exception as falla:
            _, _, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print("Error: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname))
            pass
    for symbol in lista_filtrada:
        md.printandlog(cons.nombrelog,symbol,pal=1)
    print(f"Timeframe {timeframe} - porcentajes_sumados {md.truncate(porcentajes_sumados,2)} - trades {trades} - win_rate_buenos {win_rate_buenos} - win_rate_malos {win_rate_malos} - Ganancia por trade: {md.truncate((porcentajes_sumados/trades if trades !=0 else porcentajes_sumados),2)}%")
    print("duermo 30 minutos...")
    sleep(1800)