import modulos as md
import os
import sys

symbol='BTCUSDT'
timeframe = '1m'
anuncioaltavariacionbtc=False

while True:
    try:
        df = md.obtiene_historial(symbol, timeframe)
        df = df.tail(30)
        preciomenor=df.Close.min()
        preciomayor=df.Close.max()
        timestampmaximo=max(df[df['Close']==max( df['Close'])]['Open Time'])
        timestampminimo=max(df[df['Close']==min( df['Close'])]['Open Time'])
        if timestampmaximo>=timestampminimo:    
            variacion = md.truncate(((preciomayor/preciomenor)-1)*100,2)
        else:    
            variacion = md.truncate(-((preciomenor/preciomayor)-1)*-100,2)
        print(variacion)
        if variacion>=1.5 and anuncioaltavariacionbtc==False:
            print("\nALTA VARIACION DE BTC!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
            anuncioaltavariacionbtc=True
        if variacion<1.5 and anuncioaltavariacionbtc==True:
            print("\nBAJA VARIACION DE BTC!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
            anuncioaltavariacionbtc=False
    except KeyboardInterrupt:
        print("\nSalida solicitada.")
        sys.exit() 
    except Exception as falla:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - par: "+symbol+"\n")
        pass
     