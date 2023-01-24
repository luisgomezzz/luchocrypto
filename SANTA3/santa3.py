#****************************************************************************************
# version 3.0
#****************************************************************************************
import sys, os
import util as ut
import datetime as dt
from datetime import datetime
import threading
from playsound import playsound
import constantes as cons
from binance.exceptions import BinanceAPIException
import indicadores as ind
from binance.client import AsyncClient
from binance.streams import BinanceSocketManager
import asyncio
import websockets
import json

def posicionsanta(par,lado,porcentajeentrada):   
    serror = True
    micapital = ut.balancetotal()
    size = float(micapital*porcentajeentrada/100)
    mensaje=''
    try:      
        if ut.creoposicion (par,size,lado)==True:
           mensaje=mensaje+"\nEntryPrice: "+str(ut.truncate(ut.getentryprice(par),6))
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
    mazmorra=[''] #Monedas que no quiero operar
    for par in lista_de_monedas:
        try:  
            volumeOf24h=ut.volumeOf24h(par)
            capitalizacion=ut.capitalizacion(par)
            if par not in mazmorra:                
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
    procentajeperdida=ut.leeconfiguracion("procentajeperdida")
    incrementocompensacionporc=ut.leeconfiguracion('incrementocompensacionporc')
    cantidadcompensaciones=ut.leeconfiguracion('cantidadcompensaciones')
    if cons.exchange_name == 'kucoinfutures':
        multiplier=float(cons.clientmarket.get_contract_detail(par)['multiplier'])
    else:
        multiplier=1
    ut.printandlog(cons.nombrelog,"Porcentaje de entrada: "+str(porcentajeentrada))
    ut.printandlog(cons.nombrelog,"Porcentaje de pérdida: "+str(procentajeperdida))
    ut.printandlog(cons.nombrelog,"Incremento porcentual entre compensaciones: "+str(incrementocompensacionporc))
    ut.printandlog(cons.nombrelog,"Cantidad de compensaciones: "+str(cantidadcompensaciones))
    posicioncreada,mensajeposicioncompleta=posicionsanta(par,lado,porcentajeentrada)
    if posicioncreada==True:  
        entryprice = ut.getentryprice(par)
        tamanio=ut.get_positionamt(par)
        #stop de precaución por si el precio varía rapidamente.
        if lado=='SELL':
            preciostopprecaicion=entryprice*(1+((cantidadcompensaciones+2)*distanciaentrecompensaciones/100))
        else:
            preciostopprecaicion=entryprice*(1-((cantidadcompensaciones+2)*distanciaentrecompensaciones/100))
        ut.creostoploss (par,lado,preciostopprecaicion)        
        ut.printandlog(cons.nombrelog,mensajeposicioncompleta+"\nQuantity: "+str(tamanio))
        ut.printandlog(cons.nombrelog,"distancia entre compensaciones: "+str(distanciaentrecompensaciones))
        #agrego el par al file
        with open(os.path.join(cons.pathroot, cons.operandofile), 'a') as filehandle:            
            filehandle.writelines("%s\n" % place for place in [par])
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
            hayguita,preciolimit,cantidadformateada,compensacionid = ut.compensaciones(par,cons.client,lado,cantidad,distanciaporc)
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
            distanciaporc = (distanciaporc-distanciaentrecompensaciones)+(distanciaentrecompensaciones/3)
            if lado =='SELL':
                preciolimit = ut.getentryprice(par)*(1+(distanciaporc/100))   
            else:
                preciolimit = ut.getentryprice(par)*(1-(distanciaporc/100))
            limitprice=ut.RoundToTickUp(par,preciolimit)
            ut.printandlog(cons.nombrelog,"Punto de atque sugerido. Cantidad: "+str(cantidad)+". Precio: "+str(limitprice))
            hayguita,preciolimit,cantidadformateada,compensacionid = ut.compensaciones(par,cons.client,lado,cantidad,distanciaporc)    
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
    return posicioncreada        

# MANEJO DE TPs
def creaactualizatps (par,lado,limitorders=[]):
    print("creaactualizatps-limitorders: "+str(limitorders))
    limitordersnuevos=[]
    tp = 1
    dict = {     #porcentaje de variacion - porcentaje a desocupar   
         1.15 : 50
        #,1.30 : 20
        #,1.50 : 15
        #,2.00 : 15
    }
    profitnormalporc = 1 
    profitaltoporc = 2 # para tener el tp mas cerca en caso de estar pesado
    balancetotal=ut.balancetotal() 
    tamanioactualusdt=abs(ut.get_positionamtusdt(par))
    procentajeperdida = ut.leeconfiguracion("procentajeperdida")
    try:        
        if tamanioactualusdt <= (balancetotal*procentajeperdida/100)*1.8:
            divisor = profitnormalporc
        else:
            divisor=profitaltoporc
        #crea los TPs
        for porcvariacion, porcdesocupar in dict.items():
            print("tp "+str(tp))
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
        print("limitorders: "+str(limitorders))
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
    thread_trading = threading.Thread(target=callback_updatingv2,args=(par,lado), daemon=True)
    thread_trading.start()
    return posicioncreada   

async def updatingv2(symbol,side):
    try:
        compensacioncount = 0
        stopengananciascreado = False
        print("\nupdatingv2-CREA TPs..."+symbol)
        limitorders=creaactualizatps (symbol,side)        
        client = await AsyncClient.create(cons.api_key, cons.api_secret)
        bm = BinanceSocketManager(client)
        # start any sockets here, i.e a trade socket
        ts = bm.futures_user_socket()#-за фючърсният срийм или за спот стрийма
        # then start receiving messages
        async with ts as tscm:
            while True:
                res = await tscm.recv() #espera a recibir un mensaje
                if res['e']=='ACCOUNT_UPDATE' and res['a']['m']== "ORDER" :
                    especifico=next((item for item in res['a']['P'] if item["ps"] == 'BOTH' and item["s"] == symbol), None)
                    if especifico:
                        pnl=float(especifico['up'])
                        print(f"\nSymbol: {especifico['s']} - entryPrice: {especifico['ep']} - amount: {especifico['pa']} - PNL: {pnl}\n")
                        if pnl > 0.0 and stopengananciascreado == False:# stop en ganancias porque tocó un TP                                
                                print("\nUpdatingv2-CREA STOP EN GANANCIAS PORQUE TOCÓ UN TP..."+symbol)
                                stopenganancias=float(especifico['ep'])
                                ut.creostoploss (symbol,side,stopenganancias) 
                                stopengananciascreado = True
                                playsound(cons.pathsound+"cash-register-purchase.mp3")                                
                                thread_stopvelavela = threading.Thread(target=callback_stopvelavela,args=(symbol,side,stopenganancias), daemon=True)
                                thread_stopvelavela.start() 
                        if pnl < 0.0 and stopengananciascreado == False:# take profit que persigue al precio cuando toma compensaciones                                 
                            print("\nUpdatingv2-ACTUALIZAR TPs PORQUE TOCÓ UNA COMPENSACIÓN..."+symbol)
                            compensacioncount=compensacioncount+1
                            limitorders=creaactualizatps (symbol,side,limitorders)
                            if compensacioncount<=1:
                                ut.sound(duration = 250,freq = 659)
                            else:
                                playsound(cons.pathsound+"call-to-attention.mp3")                                
                        if pnl == 0.0:
                            print(f"\nPosición {symbol} cerrada.\n")
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
                            playsound(cons.pathsound+"computer-processing.mp3")
                            print(f"\nTrading-Final del trade {symbol} en {side} - Saldo: {str(ut.truncate(ut.balancetotal(),2))}- Objetivo a: {str(ut.truncate(cons.balanceobjetivo-ut.balancetotal(),2))}\n")
                            break
        await client.close_connection()
    except Exception as falla:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - par: "+symbol+"\n")
        pass

def callback_updatingv2(symbol,side):
    try:               
        loop = asyncio.new_event_loop() 
        asyncio.set_event_loop(loop)
        loop.run_until_complete(updatingv2(symbol,side))
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
                                            print("Stopvelavela anterior cancelado. "+par)
                                        except:
                                            orderidanterior=orderid
                                            pass
                    else:                        
                        break

            ut.closeallopenorders(par)
            #sock.close()
            print(f"\nSTOP VELA A VELA {par} TERMINADO....\n")
    except Exception as falla:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - par: "+par+"\n")
        pass

def callback_stopvelavela(par,lado,preciostopenganancias):
    try:               
        loop = asyncio.new_event_loop() 
        asyncio.set_event_loop(loop)
        loop.run_until_complete(stopvelavela(par,lado,preciostopenganancias))
    except Exception as falla:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\nError: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - par: "+par+"\n")
        pass      

def main() -> None:
    ##PARAMETROS##########################################################################################
    print("Buscando equipos liquidando...")
    dictequipoliquidando=ut.equipoliquidando()
    vueltas=0
    minutes_diff=0    
    maximavariacion=0.0
    maximavariacionhora=''
    maximavariacionhoracomienzo = float(dt.datetime.today().hour)
    btcvariacion = 0
    btcflecha = ''    
    ##############START        
    print("Saldo: "+str(ut.truncate(ut.balancetotal(),2)))
    print("Objetivo a: "+str(ut.truncate(cons.balanceobjetivo-ut.balancetotal(),2)))
    ut.printandlog(cons.nombrelog,"Equipos liquidando: "+str(dictequipoliquidando))
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
            if dt.datetime.today().hour !=18: #se detecta q a esa hora (utc-3) existen variaciones altas.

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
                                maximavariaciondiaria=ut.leeconfiguracion("maximavariaciondiaria")
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
                                    if btcvariacion>=2 and anuncioaltavariacionbtc==False:
                                        playsound(cons.pathsound+"call-to-attention.mp3")
                                        print("\nALTA VARIACION DE BTC!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
                                        anuncioaltavariacionbtc=True
                                    if btcvariacion<2 and anuncioaltavariacionbtc==True:
                                        playsound(cons.pathsound+"call-to-attention.mp3")
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

                                # #######################################################################################################
                                ######################################TRADE MECHA
                                # #######################################################################################################

                                if  variacionmecha >= variaciontrigger and tradingflag==False:                                    
                                    ###########para la variaciÓn diaria (aunque tomo 12 hs para atrás)
                                    df2=ut.calculardf (par,'1h',12)
                                    df2preciomenor=df2.low.min()
                                    df2preciomayor=df2.high.max()
                                    variaciondiaria = ut.truncate((((df2preciomayor/df2preciomenor)-1)*100),2) # se toma como si siempre fuese una subida ya que sería el caso más alto.
                                    print("\nVariación diaria "+par+": "+str(variaciondiaria)+"\n")
                                    ###########
                                    if variaciondiaria <= maximavariaciondiaria:
                                        ########### Para chequear que tenga soportes/resitencias si el precio se va en contra.
                                        LL=ind.PPSR(par)
                                        R3=LL['R3']
                                        S3=LL['S3']
                                        if (flechamecha==" ↑" and precioactual<R3):
                                            ###################
                                            ###### SHORT ######
                                            ###################
                                            if  (par not in dictequipoliquidando 
                                                or (par in dictequipoliquidando and precioactual < dictequipoliquidando[par][0]*(1-10/100))
                                                ): # precio actual alejado un 10% del máximo                                                
                                                ut.sound(duration = 200,freq = 800)
                                                ut.sound(duration = 200,freq = 800)   
                                                ut.printandlog(cons.nombrelog,"\nPar: "+par+" - Variación mecha: "+str(ut.truncate(variacionmecha,2))+"% - Variación diaria: "+str(variaciondiaria)+"%")
                                                lado='SELL'
                                                trading(par,lado,porcentajeentrada,distanciaentrecompensaciones)
                                                tradingflag=True
                                        else:
                                            if (flechamecha==" ↓" and precioactual>S3):
                                                ###################
                                                ###### LONG #######
                                                ###################
                                                ut.sound(duration = 200,freq = 800)
                                                ut.sound(duration = 200,freq = 800)
                                                ut.printandlog(cons.nombrelog,"\nPar: "+par+" - Variación mecha: "+str(ut.truncate(variacionmecha,2))+"% - Variación diaria: "+str(variaciondiaria)+"%")
                                                lado='BUY'
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
                                    lanzadorscript = lanzadorscript+"\nloop.run_until_complete(san.updatingv2(par,lado))"
                                    ut.printandlog(cons.lanzadorfile,lanzadorscript,pal=1,mode='w')
                                    f = open(os.path.join(cons.pathroot, cons.lanzadorfile), 'w',encoding="utf-8")
                                    f.write(lanzadorscript)
                                    f.close()                                                                                    

                                # #######################################################################################################
                                ######################################EQUIPOS LIQUIDANDO
                                # #######################################################################################################

                                if par in dictequipoliquidando and tradingflag==False:
                                     if (dictequipoliquidando[par][0]*(1+(0.3/100)) >= precioactual >= dictequipoliquidando[par][0]): #el precio es mayor al maximo detectado o menor o igual al 0.3% de dicho maximo 
                                        ###########para la variacion diaria (aunque tomo 12 hs para atrás ;)
                                        df2=ut.calculardf (par,'1h',12)
                                        df2preciomenor = df2.low.min()
                                        df2preciomayor = df2.high.max()
                                        variaciondiaria = ut.truncate((((df2preciomayor/df2preciomenor)-1)*100),2) # se toma como si siempre fuese una subida ya que sería el caso más alto.
                                        print("\nvariaciondiaria "+par+": "+str(variaciondiaria)+"\n")
                                        ###########para calcular que tenga soportes/resitencias si el precio se va en contra.
                                        LL=ind.PPSR(par)
                                        R4=LL['R4']
                                        #####################################                                    
                                        if variaciondiaria <= maximavariaciondiaria and precioactual > R4:
                                            ut.sound(duration = 200,freq = 800)
                                            ut.sound(duration = 200,freq = 800)
                                            ut.printandlog(cons.nombrelog,"\nOportunidad Equipo liquidando - Par: "+par+" - Variación: "+str(ut.truncate(variacion,2))+"% - Variación diaria: "+str(variaciondiaria)+"%")
                                            lado='BUY'
                                            trading(par,lado,porcentajeentrada,distanciaentrecompensaciones)                                        
                                            print("\nTake profit sugerido a:"+str(dictequipoliquidando[par][1])+"\n")
                                            playsound(cons.pathsound+"liquidating.mp3")   
                                            tradingflag=True                                                                         

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
            else:
                sys.stdout.write("\rFuera de horario...\033[K")
                ut.waiting(60)
                sys.stdout.flush()    

    except BinanceAPIException as a:
       print("Error6 - Par:",par,"-",a.status_code,a.message)
       pass

if __name__ == '__main__':
    main()

