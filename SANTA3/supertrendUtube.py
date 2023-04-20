#****************************************************************************************
# version 1
#****************************************************************************************
import sys, os
import util as ut
import datetime as dt
from datetime import datetime
import threading
import constantes as cons
from binance.exceptions import BinanceAPIException
import indicadores as ind
from binance.client import AsyncClient
from binance.streams import BinanceSocketManager
import asyncio
import websockets
import json
import pandas_ta as pta
import numpy as np
import pandas as pd

class Archivooperando:    
    def leer(self):
        with open(os.path.join(cons.pathroot,cons.operandofile), 'r') as filehandle:
            operando = [current_place.rstrip() for current_place in filehandle.readlines()]
            return operando
    def borrarsymbol(self,symbol):
        #leo
        with open(os.path.join(cons.pathroot,cons.operandofile), 'r') as filehandle:
            operando = [current_place.rstrip() for current_place in filehandle.readlines()]
        # remove the item for all its occurrences
        c = operando.count(symbol)
        for i in range(c):
            operando.remove(symbol)
        #borro todo
        open(os.path.join(cons.pathroot,cons.operandofile), "w").close()
        ##agrego
        with open(os.path.join(cons.pathroot,cons.operandofile), 'a') as filehandle:
            filehandle.writelines("%s\n" % place for place in operando)
    def agregarsymbol(self,symbol):
        with open(os.path.join(cons.pathroot, cons.operandofile), 'a') as filehandle:            
            filehandle.writelines("%s\n" % place for place in [symbol])

archivooperando = Archivooperando()

def posicionsanta(par,lado,porcentajeentrada):   
    serror = True
    micapital = ut.balancetotal()
    size = float(micapital*porcentajeentrada/100)
    mensaje=''
    try:      
        if ut.creoposicion (par,size,lado)==True:
           mensaje=mensaje+"EntryPrice: "+str(ut.truncate(ut.getentryprice(par),6))
        else:
           mensaje="No se pudo crear la posición. "
           print(mensaje)
           serror=False
    except BinanceAPIException as a:
        print(a.message,"No se pudo crear la posición.")
        serror=False
        pass     
    except Exception as falla:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - par: "+par+"\n")
        serror=False
        pass
    return serror, mensaje 

def preciostopsantasugerido(lado,cantidadtotalconataqueusdt,preciodondequedariaposicionalfinal,perdida):  
    if lado == 'SELL':
        cantidadtotalconataqueusdt=cantidadtotalconataqueusdt*-1
    if preciodondequedariaposicionalfinal !=0.0:
        perdida=abs(perdida)*-1
        cantidadtotalconataqueusdt = cantidadtotalconataqueusdt
        try:
            preciostop = ((perdida/cantidadtotalconataqueusdt)+1)*preciodondequedariaposicionalfinal
        except Exception as ex:
            preciostop = 0
            pass
    else:
        preciostop = 0
    return preciostop   

def filtradodemonedas ():    
    dict_monedas_filtradas_aux = {}
    lista_de_monedas = ut.lista_de_monedas ()
    for par in lista_de_monedas:
        try:  
            volumeOf24h=ut.volumeOf24h(par)
            capitalizacion=ut.capitalizacion(par)
            if volumeOf24h >= cons.minvolumen24h and capitalizacion >= cons.mincapitalizacion:
                dict_monedas_filtradas_aux[par]={"volumeOf24h":volumeOf24h,"capitalizacion":capitalizacion}
        except Exception as ex:
            pass        
        except KeyboardInterrupt as ky:
            print("\nSalida solicitada. ")
            sys.exit()   
    global dict_monedas_filtradas_nueva
    dict_monedas_filtradas_nueva = dict_monedas_filtradas_aux
    return dict_monedas_filtradas_aux

def loopfiltradodemonedas ():
    while True:
        filtradodemonedas ()

def formacioninicial(par,lado,porcentajeentrada,distanciaentrecompensaciones):        
    cantidadcompensaciones=ut.leeconfiguracion('cantidadcompensaciones')
    ut.printandlog(cons.nombrelog,"Porcentaje de entrada: "+str(porcentajeentrada))    
    ut.printandlog(cons.nombrelog,"Cantidad de compensaciones: "+str(cantidadcompensaciones))
    posicioncreada,mensajeposicioncompleta=posicionsanta(par,lado,porcentajeentrada)
    if posicioncreada==True:  
        entryprice = ut.getentryprice(par)
        tamanio=ut.get_positionamt(par)
        #stop de precaución por si el precio varía rapidamente.
        if lado=='SELL':
            preciostopprecaicion=entryprice*(1+10/100)
        else:
            preciostopprecaicion=entryprice*(1-10/100)
        ut.creostoploss (par,lado,preciostopprecaicion)        
        ut.printandlog(cons.nombrelog,mensajeposicioncompleta+"\nQuantity: "+str(tamanio))
        ut.printandlog(cons.nombrelog,"distancia entre compensaciones: "+str(distanciaentrecompensaciones))
        #agrego el par al file
        with open(os.path.join(cons.pathroot, cons.operandofile), 'a') as filehandle:            
            filehandle.writelines("%s\n" % place for place in [par])      
    return posicioncreada        

# MANEJO DE TPs
def creaactualizatps (par,lado,limitorders=[]):
    limitordersnuevos=[]
    tp = 1
    porcentajeadesocupar=ut.leeconfiguracion("porcentajeadesocupar")
    dict = {     #porcentaje de variacion - porcentaje a desocupar   
         10 : porcentajeadesocupar
    }
    profitnormalporc = 1 
    profitaltoporc = 2 # para tener el tp mas cerca en caso de estar pesado
    balancetotal=ut.balancetotal() 
    tamanioactualusdt=abs(ut.get_positionamtusdt(par))
    try:        
        if tamanioactualusdt <= balancetotal*cons.apalancamientoreal*7/100:
            divisor = profitnormalporc
        else:
            divisor=profitaltoporc
        #crea los TPs
        for porcvariacion, porcdesocupar in dict.items():
            print("\ntp "+str(tp))
            if lado=='BUY':
                preciolimit = ut.getentryprice(par)*(1+((porcvariacion/divisor)/100))                
            else:
                preciolimit = ut.getentryprice(par)*(1-((porcvariacion/divisor)/100))
            creado,orderid=ut.creotakeprofit(par,preciolimit,porcdesocupar,lado)
            if creado==True:
                limitordersnuevos.append(orderid)
            tp=tp+1
            if preciolimit == 0:
                break
        #cancela los TPs viejos
        for id in limitorders:
            print("Cancela "+str(id))
            try:
                cons.exchange.cancel_order(id, par)   
            except Exception as ex:
                print("Error3 creaactualizatps: "+str(ex)+"\n")
                pass  
        limitorders=limitordersnuevos
    except BinanceAPIException as bin:
        print("Error1 creaactualizatps: ",bin.status_code,bin.message+"\n")   
        pass          
    except Exception as ex:
        print("Error2 creaactualizatps: "+str(ex)+"\n")
        pass    
    return limitorders

def trading(par,lado,porcentajeentrada,distanciaentrecompensaciones):
    mensajelog="Trade - "+par+" - "+lado+" - Hora:"+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))
    mensajelog=mensajelog+"\nBalance: "+str(ut.truncate(ut.balancetotal(),2))
    ut.printandlog(cons.nombrelog,mensajelog)    
    posicioncreada=formacioninicial(par,lado,porcentajeentrada,distanciaentrecompensaciones) 
    thread_trading = threading.Thread(target=updating,args=(par,lado), daemon=True)
    thread_trading.start()
    return posicioncreada   

def updating(symbol,side):
    try:
        
        while(ut.get_positionamt(symbol)!=0):
            df=ut.calculardf(symbol,cons.temporalidad)
            df['sig'] = adx(df,dilen, adxlen)
            df['direccion'] = pta.supertrend(df['high'], df['low'], df['close'], atrPeriod=atrPeriod, factor=factor)['SUPERTd_7_3.0']*-1
            df['resta'] = df['direccion'] - df['direccion'].shift(1)
            df['resta'].fillna(0)
            df['rsi21']=lucho_rsi(df.close, 21)
            df['rsi3']=lucho_rsi(df.close, 3)
            df['rsi28']=lucho_rsi(df.close, 28)
            df['entry'] = np.nan
            df['entry'] = np.where((df.resta.shift(1) < 0) & (df.rsi21.shift(1) < 66) & (df.rsi3.shift(1) > 80) & (df.rsi28.shift(1) > 49) & (df.sig.shift(1) > 20), "BUY", np.where((df.resta.shift(1) > 0) & (df.rsi21.shift(1) > 34) & (df.rsi3.shift(1) < 20) & (df.rsi28.shift(1) < 51) & (df.sig.shift(1) > 20),"SELL",np.nan))
            if side =='BUY':
                if df.entry.iloc[-1] =='SELL':
                    ut.closeposition(symbol,side)
                    print(f"Posición {symbol} cerrada. ")
                else:
                    ut.sleep(10)
            else:
                if df.entry.iloc[-1] =='BUY':
                    ut.closeposition(symbol,side)
                    print(f"Posición {symbol} cerrada. ")
                else:
                    ut.sleep(10)
        
        #cierra todo porque se terminó el trade
        ut.closeallopenorders(symbol)    
        #se quita la moneda del arhivo ya que no se está operando
        #leo
        with open(os.path.join(cons.pathroot,cons.operandofile), 'r') as filehandle:
            operando = [current_place.rstrip() for current_place in filehandle.readlines()]
        # remove the item for all its occurrences
        c = operando.count(symbol)
        for i in range(c):
            operando.remove(symbol)
        #borro todo
        open(os.path.join(cons.pathroot,cons.operandofile), "w").close()
        ##agrego
        with open(os.path.join(cons.pathroot,cons.operandofile), 'a') as filehandle:
            filehandle.writelines("%s\n" % place for place in operando)       
        ut.sound("computer-processing.mp3")
        balancetotal=ut.balancetotal()
        reservas=ut.leeconfiguracion("reservas")
        print(f"\nTrading-Final del trade {symbol} en {side} - Saldo: {str(ut.truncate(balancetotal,2))} - PNL acumulado: {str(ut.truncate(balancetotal-reservas,2))}")
    except Exception as falla:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - par: "+symbol+"\n")
        pass

async def stopvelavela(par,lado,preciostopenganancias):
    try:
        print(f"\nSTOP VELA A VELA {par} ACTIVADO....\n")
        orderidanterior = 0
        url = cons.url_stream
        first_pair = f'{par.lower()}@kline_{cons.temporalidad}' 
        async with websockets.connect(url+first_pair) as sock:
            while True:
                data = json.loads(await sock.recv()) #ESPERO RECIBIR
                vela_cerrada = data['k']['x']
                if vela_cerrada==True:
                    if ut.get_positionamt(par)!=0.0:
                        preciostopvelavela=ut.get_preciostopvelavela (par,lado,cons.temporalidad)
                        if lado=='SELL':
                            if preciostopvelavela!=0.0 and preciostopvelavela<preciostopenganancias:
                                print("\nCrea stopvelavela nuevo. "+par)
                                creado,orderid=ut.creostoploss (par,lado,preciostopvelavela)
                                preciostopenganancias=preciostopvelavela
                                if creado==True:
                                    if orderidanterior==0:
                                        orderidanterior=orderid
                                    else:
                                        try:
                                            cons.exchange.cancel_order(orderidanterior, par)
                                            orderidanterior=orderid
                                            print("\nStopvelavela anterior cancelado. "+par)
                                        except:
                                            orderidanterior=orderid
                                            pass
                        else:
                            if preciostopvelavela!=0.0 and preciostopvelavela>preciostopenganancias:
                                print("\ncrea stopvelavela. "+par)
                                creado,orderid=ut.creostoploss (par,lado,preciostopvelavela)
                                preciostopenganancias=preciostopvelavela
                                if creado==True:
                                    if orderidanterior==0:
                                        orderidanterior=orderid
                                    else:
                                        try:
                                            cons.exchange.cancel_order(orderidanterior, par)
                                            orderidanterior=orderid
                                            print("\nStopvelavela anterior cancelado. "+par)
                                        except:
                                            orderidanterior=orderid
                                            pass
                    else:                        
                        break

            ut.closeallopenorders(par)
            #sock.close()
            print(f"\nSTOP VELA A VELA {par} TERMINADO....\n")
            if '1' not in archivooperando.leer():
                archivooperando.agregarsymbol('1')
    except Exception as falla:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - par: "+par+"\n")
        pass

def callback_stopvelavela(par,lado,preciostopenganancias):
    try:      
        archivooperando.borrarsymbol('1')         
        loop = asyncio.new_event_loop() 
        asyncio.set_event_loop(loop)
        loop.run_until_complete(stopvelavela(par,lado,preciostopenganancias))
    except Exception as falla:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - par: "+par+"\n")
        pass      

def validaciones(symbol,side,precioactual,distanciaentrecompensaciones,df)->float:
    # validaciones
    # que haya al menos 2 resitencias/soportes en la dirección opuesta.
    # que el stop esté cerca de una resistencia/compensación. O en caso de que entryprice esté más allá de los límites, tenga una-
    # resitencia/compensación a menos del porcentaje de variación que soporta la estrategia.
    salida = False
    LL=ind.PPSR(symbol)
    R4=LL['R4']
    S4=LL['S4']
    S5=LL['S5']
    R5=LL['R5']
    # variacion porcentual aproximada soportada por la estrategia antes de caer en stop loss...
    distanciasoportada=(ut.leeconfiguracion('cantidadcompensaciones')*distanciaentrecompensaciones)+distanciaentrecompensaciones
    if side=='BUY':
        proximomuro=R5
        preciosoporta=precioactual*(1-(distanciasoportada/100))
    else:
        proximomuro=S5
        preciosoporta=precioactual*(1+(distanciasoportada/100))
    for rs, precio in LL.items():
        if side =='BUY':
            if preciosoporta<precio:
                if precio<proximomuro:
                    proximomuro=precio
        else:
            if preciosoporta>precio:
                if precio>proximomuro:
                    proximomuro=precio
    # Variacion es la variacion entre el precio stop y el muro más cercano en dirección hacia la posición.
    if side=='SELL':
        variacion =((preciosoporta/proximomuro)-1)*100
    else:
        variacion =((proximomuro/preciosoporta)-1)*100
    if side=='SELL':
        if precioactual<S5: # si el precio anda por abajo de todos los muros
            if abs(variacion)<distanciasoportada:
                if (
                    df.close.iloc[-3] > df.upper.iloc[-3]
                    and
                    df.close.iloc[-2] < df.upper.iloc[-2]
                    ):
                    salida = True
                else:
                    print(f"\n{symbol} {side} - Incumplida. Precio debajo de todos los muros. BB no cumplida. Hora: "+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))    
                    salida = False
            else:
                print(f"\n{symbol} {side} - Incumplida. Precio debajo de todos los muros. No hay muro cercano para contener una variación en contra. Distancia al más cercano: {ut.truncate(variacion,2)}% - Distancia soportada: {ut.truncate(distanciasoportada,2)}%\n")
                salida = False
        else:        
            if precioactual<R4: # si el precio anda entre los muros
                if abs(variacion)<distanciasoportada:
                    if (
                        df.close.iloc[-3] > df.upper.iloc[-3]
                        and
                        df.close.iloc[-2] < df.upper.iloc[-2]
                        ):
                        salida = True
                    else:
                        print(f"\n{symbol} {side} - Incumplida. Precio entre muros. BB no cumplida. Hora: "+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))
                        salida = False
                else:
                    print(f"\n{symbol} {side} - Incumplida. Precio entre muros. No hay muro cercano para contener una variación en contra. Distancia al más cercano: {ut.truncate(variacion,2)}% - Distancia soportada: {ut.truncate(distanciasoportada,2)}%\n")
                    salida = False
            else:
                print(f"\n{symbol} {side} - No se cumple condición. El precio actual no es menor que R4.\n")
                salida = False
    else:
        if precioactual>R5: # si el precio anda por arriba de todos los muros
            if abs(variacion)<distanciasoportada:
                if  (
                    df.close.iloc[-3] < df.lower.iloc[-3]
                    and
                    df.close.iloc[-2] > df.lower.iloc[-2] 
                    ):
                    salida = True
                else:
                    salida = False
                    print(f"\n{symbol} {side} - Incumplida. Precio arriba de todos los muros. BB no cumplida. Hora: "+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))
            else:
                print(f"\n{symbol} {side} - Incumplida. Precio arriba de todos los muros. No hay muro cercano para contener una variación en contra. Distancia al más cercano: {ut.truncate(variacion,2)}% - Distancia soportada: {ut.truncate(distanciasoportada,2)}%\n")
                salida = False                
        else:
            if precioactual>S4:# si el precio anda entre los muros
                if abs(variacion)<distanciasoportada:
                    if  (
                        df.close.iloc[-3] < df.lower.iloc[-3]
                        and
                        df.close.iloc[-2] > df.lower.iloc[-2] 
                        ):
                        salida = True
                    else:
                        salida = False
                        print(f"\n{symbol} {side} - Incumplida. Precio entre muros. BB no cumplida. Hora: "+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))
                else:
                    print(f"\n{symbol} {side} - Incumplida. Precio entre muros. No hay muro cercano para contener una variación en contra. Distancia al más cercano: {ut.truncate(variacion,2)}% - Distancia soportada: {ut.truncate(distanciasoportada,2)}%\n")
                    salida = False                    
            else:
                print(f"\n{symbol} {side} - No se cumple condición. El precio actual no es mayor que S4.\n")
                salida = False
    if salida==True:
        ut.printandlog(cons.nombrelog,f"\n{symbol} {side} - Variación último soporte: {ut.truncate(variacion,2)}% - Distancia soportada: {ut.truncate(distanciasoportada,2)}%")
    return salida

atrPeriod = 10
factor = 3
adxlen = 7
dilen = 7

def tr(df):
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)    
    return true_range

def dirmov(df,len):
    up = df['high'] - df['high'].shift(1)
    down=df['down'] = -1 * df['low'].diff()
    df['plusDM']=np.where((np.isnan(up)),np.NaN,(np.where(((up > down) & (up > 0)),up,0)))
    df['minusDM']=np.where((np.isnan(down)),np.NaN,(np.where(((down > up) & (down > 0)),down,0)))
    truerange = pta.rma(tr(df), length=len)
    plus = (100* pta.rma(df.plusDM, len) / truerange)
    minus = (100 * pta.rma(df.minusDM, len) / truerange)
    return plus, minus

def adx(df,dilen, adxlen):
    [plus, minus] = dirmov(df,dilen)
    sum = plus + minus
    adx = 100 * pta.rma(abs(plus - minus) / (np.where(sum == 0,1,sum)), adxlen)
    return adx

def lucho_rsi(x, y):
    delta = x.diff()
    u = delta.where(delta > 0, 0)
    d = abs(delta.where(delta < 0, 0))
    rs = pta.rma(u, y) / pta.rma(d, y)
    res = 100 - 100 / (1 + rs)
    return res

def main() -> None:
    ##PARAMETROS##########################################################################################
    vueltas=0
    minutes_diff=0    
    maximavariacion=0.0
    maximavariacionhora=''
    maximavariacionhoracomienzo = float(dt.datetime.today().hour)
    btcvariacion = 0
    btcflecha = ''    
    balancetotal=ut.balancetotal()
    reservas = ut.leeconfiguracion("reservas")
    ##############START        
    print("Saldo: "+str(ut.truncate(balancetotal,2)))
    print(f"PNL acumulado: {str(ut.truncate(balancetotal-reservas,2))}")
    print("Filtrando monedas...")
    filtradodemonedas()
    dict_monedas_filtradas = dict_monedas_filtradas_nueva
    ut.printandlog(cons.dict_monedas_filtradas_file,str(dict_monedas_filtradas),pal=1,mode='w')
    anuncioaltavariacionbtc=False
    try:

        #lanza filtrado de monedas paralelo
        hilofiltramoneda = threading.Thread(target=loopfiltradodemonedas)
        hilofiltramoneda.daemon = True
        hilofiltramoneda.start()        

        while True:
                
                lista_aux = list(dict_monedas_filtradas.keys())
                lista_nueva_aux = list(dict_monedas_filtradas_nueva.keys())
                res = [x for x in lista_aux + lista_nueva_aux if x not in lista_aux or x not in lista_nueva_aux]
                
                if res:
                    print("\nCambios en monedas filtradas: ")     
                    print(res)
                    dict_monedas_filtradas = dict_monedas_filtradas_nueva
                    ut.printandlog(cons.dict_monedas_filtradas_file,str(dict_monedas_filtradas),pal=1,mode='w')
                
                for par in dict_monedas_filtradas:
                    tradessimultaneos=ut.leeconfiguracion('tradessimultaneos')
                    #leo file
                    with open(os.path.join(cons.pathroot,cons.operandofile), 'r') as filehandle:
                        operando = [current_place.rstrip() for current_place in filehandle.readlines()]
                    if len(operando)>=tradessimultaneos:
                        print("\nSe alcanzó el número máximo de trades simultaneos.")
                    while len(operando)>=tradessimultaneos:           
                        with open(os.path.join(cons.pathroot,cons.operandofile), 'r') as filehandle:
                            operando = [current_place.rstrip() for current_place in filehandle.readlines()]                         
                        ut.waiting(1)

                    # para calcular tiempo de vuelta completa                
                    if vueltas == 0:
                        datetime_start = datetime.today()
                        vueltas = 1
                    else:
                        if vueltas == len(dict_monedas_filtradas):
                            datetime_end = datetime.today()
                            minutes_diff = (datetime_end - datetime_start).total_seconds() / 60.0
                            vueltas = 0
                        else:
                            vueltas = vueltas+1
                    
                    try:

                        try:
                            
                            if par not in operando:    
                                # #######################################################################################################
                                #################################CÁLCULOS
                                # ####################################################################################################### 
                                porcentajeentrada = ut.leeconfiguracion('porcentajeentrada')

                                tradingflag = False                                
                                df=ut.calculardf (par,cons.temporalidad)
                                df = df[:-1]
                                preciomenor=df.close.min()
                                preciomayor=df.close.max()                                

                                # reinicia la máxima variación al pasar una hora
                                if maximavariacionhoracomienzo != float(dt.datetime.today().hour):
                                    maximavariacion=0.0
                                    maximavariacionhoracomienzo = float(dt.datetime.today().hour)

                                timestampmaximo=max(df[df['close']==max( df['close'])]['time'])
                                timestampminimo=max(df[df['close']==min( df['close'])]['time'])

                                if timestampmaximo>=timestampminimo:
                                    flecha = " ↑"
                                    variacion = ((preciomayor/preciomenor)-1)*100
                                else:
                                    flecha = " ↓"
                                    variacion = ((preciomenor/preciomayor)-1)*-100

                                if variacion > maximavariacion:
                                    maximavariacion = variacion
                                    maximavariacionpar = par
                                    maximavariacionhora = str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))
                                    maximavariacionflecha = flecha
                                
                                if par[0:7] =='BTCUSDT' or par[0:7] =='XBTUSDT':
                                    btcvariacion = variacion
                                    btcflecha = flecha                                    
                                    if btcvariacion>=1.5 and anuncioaltavariacionbtc==False:
                                        ut.sound("High_volatility_of_bitcoin.mp3")
                                        print("\nALTA VARIACION DE BTC!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
                                        anuncioaltavariacionbtc=True
                                    if btcvariacion<1.5 and anuncioaltavariacionbtc==True:
                                        ut.sound("High_volatility_of_bitcoin.mp3")
                                        print("\nBAJA VARIACION DE BTC!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
                                        anuncioaltavariacionbtc=False

                                capitalizaciondelsymbol=dict_monedas_filtradas[par]["capitalizacion"]
                                if capitalizaciondelsymbol>=1000000000:
                                    distanciaentrecompensaciones = ut.leeconfiguracion('distanciaentrecompensacionesbaja')
                                else:
                                    distanciaentrecompensaciones = ut.leeconfiguracion('distanciaentrecompensacionesalta')                                 

                                precioactual=ut.currentprice(par)
                                if precioactual>=preciomayor*(1-0.5/100):
                                    flechamecha = " ↑"
                                    variacionmecha = ((precioactual/preciomenor)-1)*100
                                else:
                                    if precioactual<preciomenor*(1+0.5/100):
                                        flechamecha = " ↓"
                                        variacionmecha = ((precioactual/preciomayor)-1)*-100       
                                    else:
                                        flechamecha = " "
                                        variacionmecha = 0

                                df['sig'] = adx(df,dilen, adxlen)
                                df['direccion'] = pta.supertrend(df['high'], df['low'], df['close'], atrPeriod=atrPeriod, factor=factor)['SUPERTd_7_3.0']*-1
                                df['resta'] = df['direccion'] - df['direccion'].shift(1)
                                df['resta'].fillna(0)
                                df['rsi21']=lucho_rsi(df.close, 21)
                                df['rsi3']=lucho_rsi(df.close, 3)
                                df['rsi28']=lucho_rsi(df.close, 28)
                                df['entry'] = np.nan
                                df['entry'] = np.where((df.resta.shift(1) < 0) & (df.rsi21.shift(1) < 66) & (df.rsi3.shift(1) > 80) & (df.rsi28.shift(1) > 49) & (df.sig.shift(1) > 20), "BUY", np.where((df.resta.shift(1) > 0) & (df.rsi21.shift(1) > 34) & (df.rsi3.shift(1) < 20) & (df.rsi28.shift(1) < 51) & (df.sig.shift(1) > 20),"SELL",np.nan))


                                # #######################################################################################################
                                ######################################TRADE 
                                # #######################################################################################################

                                if  df.entry.iloc[-1]=='SELL':
                                    ###################
                                    ###### SHORT ######
                                    ###################
                                    ut.sound()
                                    ut.sound()  
                                    lado='SELL'
                                    print("*********************************************************************************************")
                                    ut.printandlog(cons.nombrelog,"\nPar: "+par+" - Variación mecha: "+str(ut.truncate(variacionmecha,2)))                                                    
                                    trading(par,lado,porcentajeentrada,distanciaentrecompensaciones)
                                    tradingflag=True

                                else:
                                    if df.entry.iloc[-1]=='BUY':
                                        ###################
                                        ###### LONG #######
                                        ###################
                                        ut.sound()
                                        ut.sound()
                                        lado='BUY'
                                        print("*********************************************************************************************")
                                        ut.printandlog(cons.nombrelog,"\nPar: "+par+" - Variación mecha: "+str(ut.truncate(variacionmecha,2)))                                                    
                                        trading(par,lado,porcentajeentrada,distanciaentrecompensaciones) 
                                        tradingflag=True  

                                    #crea archivo lanzador por si quiero ejecutarlo manualmente
                                    lanzadorscript = "import sys"
                                    lanzadorscript = lanzadorscript+"\nsys.path.insert(1,'./')"
                                    lanzadorscript = lanzadorscript+"\nimport santa3 as san"
                                    lanzadorscript = lanzadorscript+"\nimport asyncio"
                                    lanzadorscript = lanzadorscript+"\npar='"+par+"'"
                                    lanzadorscript = lanzadorscript+"\ndistanciaentrecompensaciones = "+str(distanciaentrecompensaciones)
                                    lanzadorscript = lanzadorscript+"\nporcentajeentrada = "+str(porcentajeentrada)
                                    if flecha == " ↑":
                                        lanzadorscript = lanzadorscript+"\nlado='SELL'"
                                    else:
                                        lanzadorscript = lanzadorscript+"\nlado='BUY'"
                                    lanzadorscript = lanzadorscript+"\nloop = asyncio.new_event_loop()"
                                    lanzadorscript = lanzadorscript+"\nasyncio.set_event_loop(loop)"
                                    lanzadorscript = lanzadorscript+"\n#san.trading(par,lado,porcentajeentrada,distanciaentrecompensaciones)"
                                    lanzadorscript = lanzadorscript+"\nloop.run_until_complete(san.updating(par,lado))"
                                    ut.printandlog(cons.lanzadorfile,lanzadorscript,pal=1,mode='w')
                                    f = open(os.path.join(cons.pathroot, cons.lanzadorfile), 'w',encoding="utf-8")
                                    f.write(lanzadorscript)
                                    f.close()                                                                                    
                                
                                sys.stdout.write("\r"+par+" -"+flecha+str(ut.truncate(variacion,2))+"% - T. vuelta: "+str(ut.truncate(minutes_diff,2))+" min - Monedas filtradas: "+ str(len(dict_monedas_filtradas))+" - máxima variación "+maximavariacionpar+maximavariacionflecha+str(ut.truncate(maximavariacion,2))+"% Hora: "+maximavariacionhora+" - BITCOIN:"+btcflecha+str(ut.truncate(btcvariacion,2))+"%"+"\033[K")
                                sys.stdout.flush()  

                        except KeyboardInterrupt:
                            print("\nSalida solicitada. ")
                            sys.exit()
                        except BinanceAPIException as e:
                            if e.message!="Invalid symbol.":
                                print("\nError3 - Par:",par,"-",e.status_code,e.message)                            
                            pass
                        except Exception as falla:
                            exc_type, exc_obj, exc_tb = sys.exc_info()
                            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                            print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - par: "+par+"\n")
                            pass

                    except KeyboardInterrupt:
                        print("\nSalida solicitada.")
                        sys.exit()            
                    except BinanceAPIException as a:
                        if a.message!="Invalid symbol.":
                            print("Error5 - Par:",par,"-",a.status_code,a.message)
                        pass

    except BinanceAPIException as a:
       print("Error6 - Par:",par,"-",a.status_code,a.message)
       pass

if __name__ == '__main__':
    main()

