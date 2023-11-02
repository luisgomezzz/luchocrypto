import modulos as md
import numpy as np
import constantes as cons
import os
import sys
lista_filtrada = []

#lista=md.lista_de_monedas()
#lista=md.filtradodemonedas ()
#lista=['SPELLUSDT', 'AXSUSDT', 'ETHUSDT', 'BNBUSDT', 'OGNUSDT', 'CYBERUSDT', '1000PEPEUSDT', 'COMPUSDT', 'ADAUSDT', 'BCHUSDT', 'RUNEUSDT', 'MATICUSDT', 'BLZUSDT', 'HBARUSDT', 'TRBUSDT', 'WLDUSDT', 'MTLUSDT', 'BTCUSDT', 'XRPUSDT', 'OPUSDT', 'PERPUSDT', 'ARBUSDT', 'STMXUSDT', 'CFXUSDT', 'SOLUSDT', 'DOGEUSDT', 'APEUSDT', 'UNFIUSDT', 'LTCUSDT', 'STORJUSDT', 'CRVUSDT']
lista=['STMXUSDT']

if len(lista)>1:
    imprimo=False
    debug=False
else:
    imprimo= True
    debug=True
for symbol in lista:    
    try:
        #data,porcentajeentrada = md.estrategia_santa(symbol,tp_flag = True)
        #data,porcentajeentrada = md.estrategia_trampa(symbol,tp_flag = True)
        data = md.estrategia_haz(symbol, debug=debug)
        #data,porcentajeentrada = md.estrategia_oro('XAU',tp_flag = True)
        #######################################################################
        resultado = md.backtesting(data, plot_flag = imprimo)
        #resultado = md.backtestingsanta(data, plot_flag = imprimo, debug = True)
        ########################################################################
        #if resultado['Return [%]'] < 0: # para santa3 mazmorra
        #if data.disparo.iloc[-1]!=0: # imprime las monedas que estan en posible haz martillo
        #        print(symbol)
        if resultado['Return [%]'] > 0:
            #if ((resultado['Profit Factor'] > 2 or np.isnan(resultado['Profit Factor'])) and (resultado['Return [%]']/resultado['# Trades']) >=0.33):            
                lista_filtrada.append(symbol)
        print(f"{symbol} - Return [%]: {md.truncate(resultado['Return [%]'],2)}% - # Trades: {resultado['# Trades']} - Profit Factor: {resultado['Profit Factor']} - Win Rate [%]: {resultado['Win Rate [%]']}")
    except Exception as falla:
        _, _, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+"\n")
        pass
for symbol in lista_filtrada:
    md.printandlog(cons.nombrelog,symbol,pal=1)
#md.dibuja_patrones_triangulos (data,998)    