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
import asyncio
import websockets
import json
import pandas_ta as pta

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

def formacioninicial(par,lado,porcentajeentrada):        
    ut.printandlog(cons.nombrelog,"Porcentaje de entrada: "+str(porcentajeentrada))    
    posicioncreada,mensajeposicioncompleta=posicionsanta(par,lado,porcentajeentrada)
    if posicioncreada==True:  
        entryprice = ut.getentryprice(par)
        tamanio = ut.get_positionamt(par)
        #stop de precaución por si el precio varía rapidamente.
        if lado=='SELL':
            preciostopprecaicion=entryprice*(1+(10/100))
        else:
            preciostopprecaicion=entryprice*(1-(10/100))
        ut.creostoploss (par,lado,preciostopprecaicion)        
        ut.printandlog(cons.nombrelog,mensajeposicioncompleta+"\nQuantity: "+str(tamanio))
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

def trading(par,lado,porcentajeentrada):
    mensajelog="Trade - "+par+" - "+lado+" - Hora:"+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))
    mensajelog=mensajelog+"\nBalance: "+str(ut.truncate(ut.balancetotal(),2))
    ut.printandlog(cons.nombrelog,mensajelog)    
    posicioncreada=formacioninicial(par,lado,porcentajeentrada) 
    thread_trading = threading.Thread(target=updating,args=(par,lado), daemon=True)
    thread_trading.start()
    return posicioncreada   

def updating(symbol,side):
    try:
        print("\nUPDATING COMIENZA..."+symbol)
        atrPeriod = 14
        atrMultiplier = 1.0
        swingLookback = 30

        trailPrice = 0.0
        next_trailPrice = 0.0
        while ut.get_positionamt(symbol) !=0.0:
            df=ut.calculardf(symbol,cons.temporalidad)
            atrValue    = pta.atr(df.high, df.low, df.close, length=atrPeriod) * atrMultiplier
            swingLow    = pta.lowest(df.low, swingLookback)
            swingHigh   = pta.highest(df.high, swingLookback)
            if side=='BUY':
                next_trailPrice = swingLow - atrValue
            else: 
                next_trailPrice = swingHigh + atrValue
            if side=='BUY':
                if next_trailPrice > trailPrice or trailPrice ==0.0 :
                    trailPrice = next_trailPrice
            else:
                if next_trailPrice < trailPrice or trailPrice ==0.0 :
                    trailPrice = next_trailPrice
            print("trailPrice: "+str(trailPrice))
            ##ir actualizando el stop con el trailprice
            ut.sleep(30)

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

def validaciones(symbol,side,df)->float:
    # validaciones
    # -que haya ruptura de BB
    salida = False
    if side=='BUY':
        if (
            df.close.iloc[-2] > df.upper.iloc[-2]
            ):
            salida = True
        else:
            print(f"\n{symbol} {side} - BB no cumplida. Hora: "+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))    
            salida = False
    else:
        if  (
            df.close.iloc[-2] < df.lower.iloc[-2]
            ):
            salida = True
        else:
            salida = False
            print(f"\n{symbol} {side} - BB no cumplida. Hora: "+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))
    return salida

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
                                
                                # lee las configuraciones
                                variaciontrigger=ut.leeconfiguracion("variaciontrigger")
                                ventana=ut.leeconfiguracion('ventana')
                                porcentajeentrada = ut.leeconfiguracion('porcentajeentrada')
                                sideflag=ut.leeconfiguracion('sideflag')

                                # reinicia el mensaje de la máxima variación de precio al pasar una hora
                                if maximavariacionhoracomienzo != float(dt.datetime.today().hour):
                                    maximavariacion=0.0
                                    maximavariacionhoracomienzo = float(dt.datetime.today().hour)

                                # calcula la variacion de precio
                                df=ut.calculardf (par,cons.temporalidad,ventana)
                                df = df[:-1]
                                preciomenor=df.close.min()
                                preciomayor=df.close.max()     
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
                                
                                # Avisa si BTC se mueve con fuerza
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

                                if  variacionmecha >= variaciontrigger:
                                    df=ut.calculardf (par,cons.temporalidad,ventana)
                                    df=ind.get_bollinger_bands(df)
                                    if flechamecha==" ↑" and (sideflag ==0 or sideflag ==2):
                                        lado='BUY'
                                        if validaciones(par,lado,df)==True:
                                            ###################
                                            ###### BUY ######
                                            ###################
                                            ut.sound()
                                            ut.sound()  
                                            print("*********************************************************************************************")
                                            ut.printandlog(cons.nombrelog,"\nPar: "+par+" - Variación mecha: "+str(ut.truncate(variacionmecha,2)))                                                    
                                            trading(par,lado,porcentajeentrada)

                                    else:
                                        if flechamecha==" ↓" and (sideflag ==0 or sideflag ==1):
                                            lado='SELL'
                                            if validaciones(par,lado,df)==True:
                                                ###################
                                                ###### SELL #######
                                                ###################
                                                ut.sound()
                                                ut.sound()
                                                print("*********************************************************************************************")
                                                ut.printandlog(cons.nombrelog,"\nPar: "+par+" - Variación mecha: "+str(ut.truncate(variacionmecha,2)))                                                    
                                                trading(par,lado,porcentajeentrada) 
                                
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

