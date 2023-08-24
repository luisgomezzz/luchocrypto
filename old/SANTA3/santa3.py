#****************************************************************************************
# version 3.0
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
import tkinter as tk
from tkinter import messagebox

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
            # por ahora dejo de funcionar la obtencion de la capitalizacion porque binance cambió ciertas funciones
            #capitalizacion=ut.capitalizacion(par)
            if volumeOf24h >= cons.minvolumen24h:# and capitalizacion >= cons.mincapitalizacion:
                dict_monedas_filtradas_aux[par]={"volumeOf24h":volumeOf24h,"capitalizacion":0}
        except Exception as ex:
            pass        
        except KeyboardInterrupt as ky:
            print("\nSalida solicitada. ")
            sys.exit()   
    dict_filtrada = {}
    import warnings
    sys.path.insert(0, 'C:/LUCHO/personal/repopersonal/luchocrypto/FENIX')
    import modulos as md  
    warnings.filterwarnings("ignore")
    for symbol in dict_monedas_filtradas_aux:    
        try:
            data,_ = md.estrategia_santa(symbol,tp_flag = True)
            resultado = md.backtestingsanta(data, plot_flag = False)
            if resultado['Return [%]'] >= -2:
                    dict_filtrada[symbol]={"volumeOf24h":dict_monedas_filtradas_aux[symbol]['volumeOf24h'],"capitalizacion":0}
            else:
                # Agregar a mazmorra. Ahora filtra esta moneda y safamos pero en el futuro no detectará estas variaciones que llegan 
                # al stop porque solo se toman 1000 frames.
                # Basicamente lo que se hace es alertar de monedas con demasiada variación ya que luego de un tiempo no es posible detectar
                # el historial ya que se toman solo 1000 frames y es aconsajable agregar a la mazmorra o estudiar si vale la pena agragarla.
                print(f"\nAnalizar si se agrega a mazmorra : {symbol}")
        except Exception as ex:
            pass        
        except KeyboardInterrupt as ky:
            print("\nSalida solicitada. ")
            sys.exit() 
    global dict_monedas_filtradas_nueva
    dict_monedas_filtradas_nueva = dict_filtrada
    return dict_filtrada

def loopfiltradodemonedas ():
    while True:
        filtradodemonedas ()

def malladecompensaciones(par,lado,entryprice,tamanio,distanciaentrecompensaciones,cantidadcompensaciones):
    procentajeperdida=ut.leeconfiguracion("procentajeperdida")
    ut.printandlog(cons.nombrelog,"Porcentaje de pérdida: "+str(procentajeperdida)) 
    incrementocompensacionporc=ut.leeconfiguracion('incrementocompensacionporc')
    ut.printandlog(cons.nombrelog,"Incremento porcentual entre compensaciones: "+str(incrementocompensacionporc))
    if cons.exchange_name == 'kucoinfutures':
        multiplier=float(cons.clientmarket.get_contract_detail(par)['multiplier'])
    else:
        multiplier=1     
    balancetotal = ut.balancetotal()
    perdida = (balancetotal*procentajeperdida/100)*-1
    hayguita = True
    distanciaporc = 0.0
    cantidadtotal = 0.0
    cantidadtotalusdt = 0.0  
    precioinicial = entryprice
    cantidad = abs(tamanio)
    cantidadusdt = cantidad*entryprice*multiplier
    cantidadtotal = cantidadtotal+cantidad
    cantidadtotalusdt = cantidadtotalusdt+cantidadusdt
    cantidadtotalconataque = cantidadtotal+(cantidadtotal*3)
    if lado == 'BUY':
        preciodeataque = precioinicial*(1-distanciaentrecompensaciones/2/100)
    else:
        preciodeataque = precioinicial*(1+distanciaentrecompensaciones/2/100)                                
    cantidadtotalconataqueusdt = cantidadtotalusdt+(cantidadtotal*3*preciodeataque*multiplier)
    preciodondequedariaposicionalfinal = cantidadtotalconataqueusdt/cantidadtotalconataque    
    preciostopsanta= preciostopsantasugerido(lado,cantidadtotalconataqueusdt,preciodondequedariaposicionalfinal,perdida)/multiplier
    i=0
    #CREA COMPENSACIONES         
    while (cantidadtotalconataqueusdt <= balancetotal*cons.apalancamientoreal # pregunta si supera mi capital
        and (
        (lado=='BUY' and preciodeataque > preciostopsanta)
        or 
        (lado=='SELL' and preciodeataque < preciostopsanta)
        ) 
        and i<=cantidadcompensaciones
        and ut.getentryprice(par)!=0
        ):
        i=i+1
        if i==1:
            cantidad = cantidad
        else:                
            cantidad = cantidad*(1+incrementocompensacionporc/100)
        distanciaporc = distanciaporc+distanciaentrecompensaciones              
        hayguita,preciolimit,cantidadformateada,compensacionid = ut.creacompensacion(par,cons.client,lado,cantidad,distanciaporc)
        if hayguita == True:
            cantidadtotal = cantidadtotal+cantidadformateada
            cantidadtotalusdt = cantidadtotalusdt+(cantidadformateada*preciolimit*multiplier)
            cantidadtotalconataque = cantidadtotal+(cantidadtotal*3)
            if lado == 'BUY':                                      
                preciodeataque = preciolimit*(1-distanciaentrecompensaciones/2/100)                                            
            else:
                preciodeataque = preciolimit*(1+distanciaentrecompensaciones/2/100)
            cantidadtotalconataqueusdt = cantidadtotalusdt+(cantidadtotal*3*preciodeataque*multiplier)                
            preciodondequedariaposicionalfinal = cantidadtotalconataqueusdt/cantidadtotalconataque ##
        ut.printandlog(cons.nombrelog,"Compensación "+str(i)+". Amount: "+str(cantidadformateada)+" - Price: "+str(preciolimit)+" - Volume: "+str(cantidadformateada*preciolimit)+" - Total Volume: "+str(cantidadtotalusdt))
        preciostopsanta= preciostopsantasugerido(lado,cantidadtotalconataqueusdt,preciodondequedariaposicionalfinal,perdida)/multiplier        
    # CANCELA ÚLTIMA COMPENSACIÓN
    try:
        ut.printandlog(cons.nombrelog,"Cancela última compensación ("+str(i)+")")
        cons.exchange.cancel_order(compensacionid, par)  
        ut.printandlog(cons.nombrelog,"Cancelada. ")
        cantidadtotal = cantidadtotal-cantidadformateada      
        cantidadtotalusdt = cantidadtotalusdt-(cantidadformateada*preciolimit)   
    except Exception as ex:
        print("Error cancela última compensación: "+str(ex)+"\n")
        pass                                                    
    # PUNTO DE ATAQUE  
    if cons.flagpuntodeataque ==1 and ut.getentryprice(par)!=0:
        cantidad = cantidadtotal*3  #cantidad nueva para mandar a crear              
        cantidadtotalconataque = cantidadtotal+cantidad
        distanciaporc = (distanciaporc-distanciaentrecompensaciones)+(distanciaentrecompensaciones)
        if lado =='SELL':
            preciolimit = ut.getentryprice(par)*(1+(distanciaporc/100))   
        else:
            preciolimit = ut.getentryprice(par)*(1-(distanciaporc/100))
        limitprice=ut.RoundToTickUp(par,preciolimit)
        ut.printandlog(cons.nombrelog,"Punto de atque sugerido. Cantidad: "+str(cantidad)+". Precio: "+str(limitprice))
        hayguita,preciolimit,cantidadformateada,compensacionid = ut.creacompensacion(par,cons.client,lado,cantidad,distanciaporc)    
        if hayguita == False:
            print("No se pudo crear la compensación de ataque.")
            cantidadtotalconataqueusdt = cantidadtotalusdt #seria la cantidad total sin ataque
            preciodondequedariaposicionalfinal = cantidadtotalusdt/cantidadtotal # totales sin ataque
        else:
            ut.printandlog(cons.nombrelog,"Ataque creado. "+"Cantidadformateada: "+str(cantidadformateada)+". preciolimit: "+str(preciolimit))     
            cantidadtotalconataqueusdt = cantidadtotalusdt+(cantidadformateada*preciolimit)                                    
            preciodondequedariaposicionalfinal = cantidadtotalconataqueusdt/cantidadtotalconataque
    else:
        cantidadtotalconataqueusdt = cantidadtotalusdt #seria la cantidad total sin ataque
        preciodondequedariaposicionalfinal = cantidadtotalusdt/cantidadtotal # totales sin ataque        
    # STOP LOSS
    preciostopsanta= preciostopsantasugerido(lado,cantidadtotalconataqueusdt,preciodondequedariaposicionalfinal,perdida)/multiplier
    ut.printandlog(cons.nombrelog,"Precio Stop sugerido: "+str(preciostopsanta))
    ut.creostoploss (par,lado,preciostopsanta,cantidadtotal)         
    ut.printandlog(cons.nombrelog,"\n*********************************************************************************************")         

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
            preciostopprecaicion=entryprice*(1+((cantidadcompensaciones+3)*distanciaentrecompensaciones/100))
        else:
            preciostopprecaicion=entryprice*(1-((cantidadcompensaciones+3)*distanciaentrecompensaciones/100))
        ut.creostoploss (par,lado,preciostopprecaicion)        
        ut.printandlog(cons.nombrelog,mensajeposicioncompleta+"\nQuantity: "+str(tamanio))
        ut.printandlog(cons.nombrelog,"distancia entre compensaciones: "+str(distanciaentrecompensaciones))
        #agrego el par al file
        with open(os.path.join(cons.pathroot, cons.operandofile), 'a') as filehandle:            
            filehandle.writelines("%s\n" % place for place in [par])
        malladecompensaciones(par,lado,entryprice,tamanio,distanciaentrecompensaciones,cantidadcompensaciones)            
    return posicioncreada        

# MANEJO DE TPs
def creaactualizatps (par,lado,limitorders=[]):
    limitordersnuevos=[]
    tp = 1
    porcentajeadesocupar=ut.leeconfiguracion("porcentajeadesocupar")
    dict = {     #porcentaje de variacion - porcentaje a desocupar   
         1.15 : porcentajeadesocupar
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
    thread_trading = threading.Thread(target=callback_updating,args=(par,lado), daemon=True)
    thread_trading.start()
    return posicioncreada   

async def updating(symbol,side):
    try:
        print("\nupdating-CREA TPs..."+symbol)
        compensacioncount = 0
        stopengananciascreado = False
        positionamtbk=ut.get_positionamt(symbol)
        limitorders=creaactualizatps (symbol,side)        
        client = await AsyncClient.create(cons.api_key, cons.api_secret)
        bm = BinanceSocketManager(client)
        # start any sockets here, i.e a trade socket
        ts = bm.futures_user_socket()#-за фючърсният срийм или за спот стрийма
        # then start receiving messages
        if abs(ut.get_positionamt(symbol)) >= abs(positionamtbk): #Si en el transcurso de la creación de las compensaciones no se cerró la posición y no tocó un TP .
            async with ts as tscm:
                while True:
                    res = await tscm.recv() #espera a recibir un mensaje
                    if res['e']=='ACCOUNT_UPDATE' and res['a']['m']== "ORDER" :
                        especifico=next((item for item in res['a']['P'] if item["ps"] == 'BOTH' and item["s"] == symbol), None)
                        if especifico:
                            pnl=float(especifico['up'])
                            if pnl > 0.0 and stopengananciascreado == False:# stop en ganancias porque tocó un TP                                
                                    print("\nupdating-CREA STOP EN GANANCIAS PORQUE TOCÓ UN TP..."+symbol)
                                    stopenganancias=float(especifico['ep'])
                                    ut.creostoploss (symbol,side,stopenganancias) 
                                    stopengananciascreado = True
                                    ut.sound("cash-register-purchase.mp3")  
                                    #cierro todas las compensaciones ya que no sirven más. Dejo los STOP LOSS por las dudas
                                    info = cons.client.futures_get_open_orders(symbol=symbol)
                                    for i in range(len(info)):
                                        if info[i]['type']=='LIMIT':
                                            orid=(info[i]['orderId'])
                                            cons.exchange.cancel_order(orid, symbol)                                    
                                    if float(ut.get_positionamt(symbol))!=0.0:
                                        if compensacioncount>=1:
                                            #stop vela vela
                                            thread_stopvelavela = threading.Thread(target=callback_stopvelavela,args=(symbol,side,stopenganancias), daemon=True)
                                            thread_stopvelavela.start() 
                                        else:
                                            print(f"\n{symbol} - {side} - Se cierra la posición porque el tamaño es muy chico.")
                                            ut.closeposition(symbol,side)
                                            if '1' not in archivooperando.leer():
                                                archivooperando.agregarsymbol('1')
                            else:
                                if pnl < 0.0 and stopengananciascreado == False:# take profit que persigue al precio cuando toma compensaciones                                 
                                    print("\nupdating-ACTUALIZAR TPs PORQUE TOCÓ UNA COMPENSACIÓN..."+symbol)
                                    compensacioncount=compensacioncount+1
                                    limitorders=creaactualizatps (symbol,side,limitorders)
                                    if compensacioncount<=1:
                                        ut.sound()
                                    else:
                                        ut.sound("call-to-attention.mp3")
                                else:
                                    if pnl == 0.0:
                                       break
            await client.close_connection()
        else:
            print(f"\nSe cierra la posición porque tocó un TP al mismo momento en que se creaba o se cerró la posición mientras se creaban las compensaciones. ")
            ut.closeposition(symbol,side)
        print(f"Posición {symbol} cerrada. ")
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

def callback_updating(symbol,side):
    try:               
        loop = asyncio.new_event_loop() 
        asyncio.set_event_loop(loop)
        loop.run_until_complete(updating(symbol,side))
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
    try:
        salida = False
        LL=ind.PPSR(symbol)
        R4=LL['R4']
        S4=LL['S4']
        S5=LL['S5']
        R5=LL['R5']
        # variacion porcentual aproximada soportada por la estrategia antes de caer en stop loss...
        distanciasoportada=(ut.leeconfiguracion('cantidadcompensaciones')*distanciaentrecompensaciones)+distanciaentrecompensaciones

        data2 = ut.calculardf (symbol,'15m',1000)
        data2['ema50']=data2.ta.ema(50)
        ema50_15m = data2.ema50
        ema50_15m = ema50_15m.reindex(df.index, method='nearest')
        df['ema50_15m']=ema50_15m
        if side=='SELL':
                if precioactual < R4: #and df.close.iloc[-1] < df.ema50_15m.iloc[-1]: # si el precio anda entre los muros
                    salida = True
                else:
                    print(f"\n{symbol} {side} - No se cumple condición. El precio actual no es menor que R4 o ema no cumplida.\n")
                    salida = False
        else:
                if precioactual > S4: #and df.close.iloc[-1] > df.ema50_15m.iloc[-1]:# si el precio anda entre los muros
                    salida = True
                else:
                    print(f"\n{symbol} {side} - No se cumple condición. El precio actual no es mayor que S4 o ema no cumplida.\n")
                    salida = False
        if salida==True:
            ut.printandlog(cons.nombrelog,f"\n{symbol} {side} - Distancia soportada: {ut.truncate(distanciasoportada,2)}%")
        return salida
    except Exception as falla:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - par: "+symbol+"\n")
        pass    

def interfaz_usuario():
    def guardar_configuracion():
        nueva_configuracion = {
            "ventana": ventana_var.get(),
            "porcentajeentrada": porcentaje_entrada_var.get(),
            "procentajeperdida": porcentaje_perdida_var.get(),
            "incrementocompensacionporc": incremento_compensacion_var.get(),
            "cantidadcompensaciones": cantidad_compensaciones_var.get(),
            "variaciontrigger": variacion_trigger_var.get(),
            "maximavariaciondiaria": max_variacion_diaria_var.get(),
            "tradessimultaneos": trades_simultaneos_var.get(),
            "distanciaentrecompensacionesalta": distancia_comp_alta_var.get(),
            "distanciaentrecompensacionesbaja": distancia_comp_baja_var.get(),
            "reservas": reservas_var.get(),
            "sideflag": side_flag_var.get(),
            "sonidos": sonidos_var.get(),
            "restriccionhoraria": restriccion_horaria_var.get(),
            "porcentajeadesocupar": porcentaje_desocupar_var.get()
        }
        with open(os.path.join(cons.pathroot, "configuration.json"), "w") as json_file:
            json.dump(nueva_configuracion, json_file, indent=4)
        messagebox.showinfo("Éxito", "Configuración guardada exitosamente")
    
    # Crear la ventana principal
    root = tk.Tk()
    root.title("Santa3")
    # Variables de control
    ventana_var = tk.IntVar()
    porcentaje_entrada_var = tk.IntVar()
    porcentaje_perdida_var = tk.IntVar()
    incremento_compensacion_var = tk.IntVar()
    cantidad_compensaciones_var = tk.IntVar()
    variacion_trigger_var = tk.IntVar()
    max_variacion_diaria_var = tk.IntVar()
    trades_simultaneos_var = tk.IntVar()
    distancia_comp_alta_var = tk.DoubleVar()
    distancia_comp_baja_var = tk.DoubleVar()
    reservas_var = tk.IntVar()
    side_flag_var = tk.IntVar()
    sonidos_var = tk.IntVar()
    restriccion_horaria_var = tk.IntVar()
    porcentaje_desocupar_var = tk.IntVar()
    # Cargar valores iniciales desde el archivo JSON
    with open(os.path.join(cons.pathroot, "configuration.json"), "r") as json_file:
        configuracion = json.load(json_file)
        ventana_var.set(configuracion["ventana"])
        porcentaje_entrada_var.set(configuracion["porcentajeentrada"])
        porcentaje_perdida_var.set(configuracion["procentajeperdida"])
        incremento_compensacion_var.set(configuracion["incrementocompensacionporc"])
        cantidad_compensaciones_var.set(configuracion["cantidadcompensaciones"])
        variacion_trigger_var.set(configuracion["variaciontrigger"])
        max_variacion_diaria_var.set(configuracion["maximavariaciondiaria"])
        trades_simultaneos_var.set(configuracion["tradessimultaneos"])
        distancia_comp_alta_var.set(configuracion["distanciaentrecompensacionesalta"])
        distancia_comp_baja_var.set(configuracion["distanciaentrecompensacionesbaja"])
        reservas_var.set(configuracion["reservas"])
        side_flag_var.set(configuracion["sideflag"])
        sonidos_var.set(configuracion["sonidos"])
        restriccion_horaria_var.set(configuracion["restriccionhoraria"])
        porcentaje_desocupar_var.set(configuracion["porcentajeadesocupar"])
    # Crear etiquetas y campos de entrada
    tk.Label(root, text="Ventana:").grid(row=0, column=0)
    tk.Entry(root, textvariable=ventana_var).grid(row=0, column=1)
    tk.Label(root, text="Porcentaje de Entrada:").grid(row=1, column=0)
    tk.Entry(root, textvariable=porcentaje_entrada_var).grid(row=1, column=1)
    tk.Label(root, text="Porcentaje de Pérdida:").grid(row=2, column=0)
    tk.Entry(root, textvariable=porcentaje_perdida_var).grid(row=2, column=1)
    tk.Label(root, text="Incremento Compensación (%):").grid(row=3, column=0)
    tk.Entry(root, textvariable=incremento_compensacion_var).grid(row=3, column=1)
    tk.Label(root, text="Cantidad de Compensaciones:").grid(row=4, column=0)
    tk.Entry(root, textvariable=cantidad_compensaciones_var).grid(row=4, column=1)
    tk.Label(root, text="Variación Trigger:").grid(row=5, column=0)
    tk.Entry(root, textvariable=variacion_trigger_var).grid(row=5, column=1)
    tk.Label(root, text="Máxima Variación Diaria:").grid(row=6, column=0)
    tk.Entry(root, textvariable=max_variacion_diaria_var).grid(row=6, column=1)
    tk.Label(root, text="Trades Simultáneos:").grid(row=7, column=0)
    tk.Entry(root, textvariable=trades_simultaneos_var).grid(row=7, column=1)
    tk.Label(root, text="Distancia Compensaciones Alta:").grid(row=8, column=0)
    tk.Entry(root, textvariable=distancia_comp_alta_var).grid(row=8, column=1)
    tk.Label(root, text="Distancia Compensaciones Baja:").grid(row=9, column=0)
    tk.Entry(root, textvariable=distancia_comp_baja_var).grid(row=9, column=1)
    tk.Label(root, text="Reservas:").grid(row=10, column=0)
    tk.Entry(root, textvariable=reservas_var).grid(row=10, column=1)
    tk.Label(root, text="Side Flag:").grid(row=11, column=0)
    tk.Entry(root, textvariable=side_flag_var).grid(row=11, column=1)
    tk.Label(root, text="Sonidos:").grid(row=12, column=0)
    tk.Entry(root, textvariable=sonidos_var).grid(row=12, column=1)
    tk.Label(root, text="Restricción Horaria:").grid(row=13, column=0)
    tk.Entry(root, textvariable=restriccion_horaria_var).grid(row=13, column=1)
    tk.Label(root, text="Porcentaje a Desocupar:").grid(row=14, column=0)
    tk.Entry(root, textvariable=porcentaje_desocupar_var).grid(row=14, column=1)
    # Botón para guardar la configuración
    tk.Button(root, text="Guardar Configuración", command=guardar_configuracion).grid(row=15, columnspan=2)    
    root.mainloop()

def main() -> None:
    ##PARAMETROS##########################################################################################
    gui_thread = threading.Thread(target=interfaz_usuario)
    gui_thread.start()
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
                                variaciontrigger=ut.leeconfiguracion("variaciontrigger")
                                ventana=ut.leeconfiguracion('ventana')
                                porcentajeentrada = ut.leeconfiguracion('porcentajeentrada')

                                tradingflag = False                                
                                df=ut.calculardf (par,cons.temporalidad,ventana)
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
                                if precioactual>=preciomayor*(1-0.5/100): # solo toma reentradas. El 0.5 es amortiguacion ya que a lo mejor bajó un poco.
                                    flechamecha = " ↑"
                                    variacionmecha = ((precioactual/preciomenor)-1)*100
                                else:
                                    if precioactual<preciomenor*(1+0.5/100): # solo toma reentradas. El 0.5 es amortiguacion ya que a lo mejor subió un poco.
                                        flechamecha = " ↓"
                                        variacionmecha = ((precioactual/preciomayor)-1)*-100       
                                    else:
                                        flechamecha = " "
                                        variacionmecha = 0

                                sideflag=ut.leeconfiguracion('sideflag')

                                #df=ind.get_bollinger_bands(df)

                                # #######################################################################################################
                                ######################################TRADE MECHA
                                # #######################################################################################################

                                if  variacionmecha >= variaciontrigger and btcvariacion<1.5 and tradingflag==False and (17 >= dt.datetime.today().hour >= 7 or ut.leeconfiguracion('restriccionhoraria')==0):                                    
                                    ########### Para chequear que tenga soportes/resitencias si el precio se va en contra.
                                    if flechamecha==" ↑" and (sideflag ==0 or sideflag ==1):
                                        lado='SELL'
                                        if validaciones(par,lado,precioactual,distanciaentrecompensaciones,df)==True:
                                            ###################
                                            ###### SHORT ######
                                            ###################
                                            ut.sound()
                                            ut.sound()  
                                            print("*********************************************************************************************")
                                            ut.printandlog(cons.nombrelog,"\nPar: "+par+" - Variación mecha: "+str(ut.truncate(variacionmecha,2)))                                                    
                                            trading(par,lado,porcentajeentrada,distanciaentrecompensaciones)
                                            tradingflag=True

                                    else:
                                        if flechamecha==" ↓" and (sideflag ==0 or sideflag ==2):
                                            lado='BUY'
                                            if validaciones(par,lado,precioactual,distanciaentrecompensaciones,df)==True:
                                                ###################
                                                ###### LONG #######
                                                ###################
                                                ut.sound()
                                                ut.sound()
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

