#****************************************************************************************
# version 2.0
#
#****************************************************************************************

from this import d
from binance.exceptions import BinanceAPIException
import sys, os
sys.path.insert(1,'./')
import utilidades as ut
import datetime as dt
from datetime import datetime
import threading
import math
##CONFIG
client = ut.client
exchange = ut.exchange
nombrelog = "log_santa2.txt"
operandofile = 'operando.txt'
## PARAMETROS FUNDAMENTALES 
temporalidad = '1m'
apalancamiento = 10 #siempre en 10 segun la estrategia de santi
procentajeperdida = 10 #porcentaje de mi capital total maximo a perder
porcentajeentrada = 10 #porcentaje de la cuenta para crear la posición (10)
ventana = 30 #Ventana de búsqueda en minutos.   
porcentajevariacionnormal = 5
porcentajevariacionriesgo = 7
## VARIABLES GLOBALES 
operando=[] #lista de monedas que se están operando
incrementocompensacionporc = 30 #porcentaje de incremento del tamaño de la compensacion con respecto a su anterior
balanceobjetivo = 24.00+24.88+71.53+71.62+106.01+105.3+400 #los 400 son los del prestamo del dpto

###################################################################################################################
###################################################################################################################
###################################################################################################################

# MANEJO DE TPs
def creaactualizatps (par,lado,limitorders=[],divisor=1):
    print("creaactualizatps-limitorders: "+str(limitorders))
    limitordersnuevos=[]
    tp = 1
    dict = {
        ###original        
        # por ahora solo uno para probar el stop vela a vela
        1.1 : 50
        #1.1 : 30
        #1.15: 20,
        #1.3 : 20,
        #1.5 : 15,
        #2   : 15
    }
    try:
        #crea los TPs
        for porc, tamanio in dict.items():
            print("tp "+str(tp))
            if lado=='BUY':
                preciolimit = ut.getentryprice(par)*(1+((porc/divisor)/100))                
            else:
                preciolimit = ut.getentryprice(par)*(1-((porc/divisor)/100))
            creado,order=ut.binancecrearlimite(par,preciolimit,tamanio,lado)
            if creado==True:
                limitordersnuevos.append(order['orderId'])
            tp=tp+1
        #cancela los TPs viejos
        for id in limitorders:
            print("Cancela "+str(id))
            try:
                exchange.cancel_order(id, par)   
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

def updating(par,lado):
    
    profitnormalporc = 1
    profitmedioporc = 2
    profitaltoporc = 3
    tamanioposicionguardado = ut.get_positionamt(par)
    tamanioactual = tamanioposicionguardado
    balancetotal=ut.balancetotal()    
    limitorders = []
    divisor=1
    #crea TPs
    print("\nupdating-CREA TPs...")
    limitorders=creaactualizatps (par,lado,limitorders,divisor)
    stopenganancias = 0.0

    #actualiza tps y stops
    while tamanioactual!=0.0: 

        if tamanioposicionguardado!=tamanioactual:

            ut.sound(duration = 250,freq = 659)

            if ut.pnl(par) > 0.0:
                try:
                    # stop en ganancias cuando tocó un TP
                    print("\nupdating-ACTUALIZAR STOP EN GANANCIAS PORQUE TOCÓ UN TP...")
                    precioactual=ut.currentprice(par)
                    precioposicion=ut.getentryprice(par)
                    if lado=='BUY':
                        stopenganancias=precioposicion+((precioactual-precioposicion)/2)
                    else:
                        stopenganancias=precioposicion-((precioposicion-precioactual)/2)
                    ut.binancestoploss (par,lado,stopenganancias) 
                except Exception as ex:
                    pass
            else:
                # take profit que persigue al precio cuando toma compensaciones 
                print("\nupdating-ACTUALIZAR TPs PORQUE TOCÓ UNA COMPENSACIÓN...")
                tamanioactualusdt=ut.get_positionamtusdt(par) 

                if tamanioactualusdt <= (balancetotal*procentajeperdida/100)*3:
                    divisor = profitnormalporc
                else:
                    if tamanioactualusdt >= (balancetotal*procentajeperdida/100)*4:
                        divisor=profitaltoporc
                    else:
                        divisor=profitmedioporc   
                                    
                limitorders=creaactualizatps (par,lado,limitorders,divisor)
            
            tamanioposicionguardado = tamanioactual            
    
        else:
            if ut.pnl(par) > 0.0 and stopenganancias != 0.0:
                stopvelavela=ut.stopvelavela (par,lado,temporalidad)
                if lado=='SELL':
                    if stopvelavela!=0.0 and stopvelavela<stopenganancias:
                        ut.binancestoploss (par,lado,stopvelavela)
                        stopenganancias=stopvelavela
                else:
                    if stopvelavela!=0.0 and stopvelavela>stopenganancias:
                        ut.binancestoploss (par,lado,stopvelavela)
                        stopenganancias=stopvelavela

        tamanioactual=ut.get_positionamt(par)

    print("\nupdating-Final del trade "+par+" en "+lado)
    print("\nSaldo: "+str(ut.truncate(ut.balancetotal(),2))+"\n")
    print("\nObjetivo a: "+str(ut.truncate(balanceobjetivo-ut.balancetotal(),2))+"\n")

def trading(par,lado):
    #updatea...
    updating(par,lado)
    #cierra todo porque se terminó el trade
    ut.closeallopenorders(par)
    #se quita la moneda del arhivo ya que no se está operando
    #leo
    with open(operandofile, 'r') as filehandle:
        operando = [current_place.rstrip() for current_place in filehandle.readlines()]
    # remove the item for all its occurrences
    c = operando.count(par)
    for i in range(c):
        operando.remove(par)
    #borro todo
    open(operandofile, "w").close()
    ##agrego
    with open(operandofile, 'a') as filehandle:
        filehandle.writelines("%s\n" % place for place in operando)

def cantcompensacionesparacrear(cantidadtotalconataqueusdt,cantidadtotalconataque,precioinicial,incrementocompensacionporc,perdida):
    numerador=(math.log10(perdida+cantidadtotalconataqueusdt)
                /
                (cantidadtotalconataque*precioinicial))

    denominador = math.log10(1-incrementocompensacionporc/100)
    
    return ut.truncate(numerador/denominador,0)   

def main() -> None:

    ##PARAMETROS##########################################################################################
    mazmorra=['1000SHIBUSDT','1000XECUSDT','BTCUSDT_220624','ETHUSDT_220624','ETHUSDT_220930','BTCUSDT_220930','BTCDOMUSDT','FOOTBALLUSDT'
    ] #Monedas que no quiero operar 
    toppar=['ADAUSDT','BNBUSDT','BTCUSDT','AXSUSDT','DOGEUSDT','ETHUSDT','MATICUSDT','TRXUSDT','SOLUSDT','XRPUSDT','ETCUSDT','DOTUSDT'
    ,'AVAXUSDT'] #monedas top
    
    lista_de_monedas = client.futures_exchange_info()['symbols'] #obtiene lista de monedas
    posicioncreada = False
    minvolumen24h=float(100000000)
    mincapitalizacion = float(35000000)
    vueltas=0
    minutes_diff=0
    lista_monedas_filtradas=[]
    mensaje=''

    mensajeposicioncompleta=''        
    margen = 'CROSSED'
    
    tradessimultaneos = 2 #Número máximo de operaciones en simultaneo
    distanciatoppar = 1 # distancia entre compensaciones cuando el par está en el top
    distancianotoppar = 1.7 # distancia entre compensaciones cuando el par no está en el top
    cantidadcompensaciones = 5 #compensaciones
    maximavariacion=0.0
    maximavariacionhora=''
    ##############START    
    
    ut.clear() #limpia terminal
    print("Saldo: "+str(ut.truncate(ut.balancetotal(),2)))
    print("Objetivo a: "+str(ut.truncate(balanceobjetivo-ut.balancetotal(),2)))
    for s in lista_de_monedas:
        try:  
            par = s['symbol']
            sys.stdout.write("\rFiltrando monedas: "+par+"\033[K")
            sys.stdout.flush()
            if (float(client.futures_ticker(symbol=par)['quoteVolume'])>minvolumen24h and 'USDT' in par and par not in mazmorra
                and ut.capitalizacion(par)>=mincapitalizacion):
                lista_monedas_filtradas.append(par)
        except Exception as ex:
            pass        
        except KeyboardInterrupt as ky:
            print("\nSalida solicitada. ")
            sys.exit()

    try:

        while True:
            #en operaciones riesgosas las variaciones deben ser mayores
            if dt.datetime.today().hour == 21:
                porcentaje = porcentajevariacionriesgo
            else:
                porcentaje = porcentajevariacionnormal
            
            for par in lista_monedas_filtradas:
                #leo file
                with open(operandofile, 'r') as filehandle:
                    operando = [current_place.rstrip() for current_place in filehandle.readlines()]
                if len(operando)>=tradessimultaneos:
                    print("\nSe alcanzó el número máximo de trades simultaneos.")
                while len(operando)>=tradessimultaneos:           
                    with open(operandofile, 'r') as filehandle:
                        operando = [current_place.rstrip() for current_place in filehandle.readlines()]                         
                    ut.waiting(1)

                # para calcular tiempo de vuelta completa                
                if vueltas == 0:
                    datetime_start = datetime.today()
                    vueltas = 1
                else:
                    if vueltas == len(lista_monedas_filtradas):
                        datetime_end = datetime.today()
                        minutes_diff = (datetime_end - datetime_start).total_seconds() / 60.0
                        vueltas = 0
                    else:
                        vueltas = vueltas+1
                
                try:

                    try:
                        
                        if par not in operando:     

                            df=ut.calculardf (par,temporalidad,ventana)
                            df = df[:-1]
                            preciomenor=df.close.min()
                            preciomayor=df.close.max()
                            precioactual=ut.currentprice(par)

                            variacion = ((preciomayor/preciomenor)-1)*100
                            
                            if variacion > maximavariacion:
                                maximavariacion = variacion
                                maximavariacionpar = par
                                maximavariacionhora = str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))
                            
                            sys.stdout.write("\r"+par+" - Variación: "+str(ut.truncate(variacion,2))+"% - Tiempo de vuelta: "+str(ut.truncate(minutes_diff,2))+" min - Monedas analizadas: "+ str(len(lista_monedas_filtradas))+" - máxima variación "+maximavariacionpar+" "+str(ut.truncate(maximavariacion,2))+"%"+" Hora: "+maximavariacionhora+"\033[K")
                            sys.stdout.flush()       

                            if  variacion >= porcentaje and precioactual >= preciomayor:                                
                                ############################
                                ####### POSICION SELL ######
                                ############################
                                ut.sound()
                                print("\rDefiniendo apalancamiento...")
                                client.futures_change_leverage(symbol=par, leverage=apalancamiento)
                                try: 
                                    print("\rDefiniendo Cross/Isolated...")
                                    client.futures_change_margin_type(symbol=par, marginType=margen)
                                except BinanceAPIException as a:
                                    if a.message!="No need to change margin type.":
                                        print("Except 7",a.status_code,a.message)
                                    else:
                                        print("Done!")   
                                    pass

                                lado='SELL'
                                print("\n*********************************************************************************************")
                                mensaje="Trade - "+par+" - "+lado
                                mensaje=mensaje+"\nSubió un "+str(ut.truncate(variacion,3))+" %"
                                mensaje=mensaje+"\nInicio: "+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))
                                print(mensaje)
                                if par in toppar:
                                    paso = distanciatoppar
                                else:
                                    paso = distancianotoppar  
                                posicioncreada,mensajeposicioncompleta=ut.posicioncompletasanta(par,lado,porcentajeentrada) 
                                print(mensajeposicioncompleta)
                                mensaje=mensaje+mensajeposicioncompleta                                
                              
                            else:
                                if  variacion >= porcentaje and precioactual <= preciomenor:                                    
                                    ############################
                                    ####### POSICION BUY ######
                                    ############################
                                    ut.sound()
                                    print("\rDefiniendo apalancamiento...")
                                    client.futures_change_leverage(symbol=par, leverage=apalancamiento)
                                    try: 
                                        print("\rDefiniendo Cross/Isolated...")
                                        client.futures_change_margin_type(symbol=par, marginType=margen)
                                    except BinanceAPIException as a:
                                        if a.message!="No need to change margin type.":
                                            print("Except 7",a.status_code,a.message)
                                        else:
                                            print("Done!")   
                                        pass

                                    lado='BUY'
                                    print("\n*********************************************************************************************")
                                    mensaje="Trade - "+par+" - "+lado
                                    mensaje=mensaje+"\nBajó un "+str(ut.truncate(variacion,3))+" %"
                                    mensaje=mensaje+"\nInicio: "+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))
                                    print(mensaje)    
                                    if par in toppar:
                                        paso = distanciatoppar
                                    else:
                                        paso = distancianotoppar
                                    posicioncreada,mensajeposicioncompleta=ut.posicioncompletasanta(par,lado,porcentajeentrada) 
                                    print(mensajeposicioncompleta)
                                    mensaje=mensaje+mensajeposicioncompleta

                            if posicioncreada==True:     
                                
                                #agrego el par al file
                                with open(operandofile, 'a') as filehandle:
                                    filehandle.writelines("%s\n" % place for place in [par])

                                balancetotal = ut.balancetotal()
                                perdida = (balancetotal*procentajeperdida/100)*-1
                                hayguita = True
                                distanciaporc = 0.0
                                cantidadtotal = 0.0
                                cantidadtotalusdt = 0.0  
                                precioinicial = ut.getentryprice(par)
                                cantidad = abs(ut.get_positionamt(par))
                                cantidadusdt = cantidad*ut.getentryprice(par)
                                cantidadtotal = cantidadtotal+cantidad
                                cantidadtotalusdt = cantidadtotalusdt+cantidadusdt
                                cantidadtotalconataque = cantidadtotal+(cantidadtotal*3)
                                if lado == 'BUY':
                                    preciodeataque = precioinicial*(1-paso/100)
                                else:
                                    preciodeataque = precioinicial*(1+paso/100)                                
                                cantidadtotalconataqueusdt = cantidadtotalusdt+(cantidadtotal*3*preciodeataque)
                                preciodondequedariaposicionalfinal = cantidadtotalconataqueusdt/cantidadtotalconataque    
                                
                                print("precioinicial: "+str(precioinicial)) 	
                                print("cantidad: "+str(cantidad)) 	 				
                                print("cantidadtotal: "+str(cantidadtotal)) 	 			
                                print("cantidadtotalconataque: "+str(cantidadtotalconataque))                                     
                                print("cantidadtotalusdt: "+str(cantidadtotalusdt)) 	
                                print("cantidadtotalconataqueusdt: "+str(cantidadtotalconataqueusdt)) 	                                 	
                                print("preciodondequedariaposicionalfinal: "+str(preciodondequedariaposicionalfinal)) 
                                preciostopsanta= ut.preciostopsanta(lado,cantidadtotalconataqueusdt,preciodondequedariaposicionalfinal,perdida)
                                print("preciostopsanta: "+str(preciostopsanta)) 

                                #CREA COMPENSACIONES         
                                while (cantidadtotalconataqueusdt <= balancetotal*apalancamiento # pregunta si supera mi capital
                                       and (
                                       (lado=='BUY' and preciodeataque > preciostopsanta)
                                       or 
                                       (lado=='SELL' and preciodeataque < preciostopsanta)
                                       ) 
                                    ):
                                    cantidad = cantidad*(1+incrementocompensacionporc/100) ##                       
                                    distanciaporc = distanciaporc+paso ##                                   
                                    hayguita,preciolimit,cantidadformateada,compensacionid = ut.compensaciones(par,client,lado,cantidad,distanciaporc) ##
                                    if hayguita == True:
                                        cantidadtotal = cantidadtotal+cantidadformateada
                                        cantidadtotalusdt = cantidadtotalusdt+(cantidadformateada*preciolimit) ##
                                        cantidadtotalconataque = cantidadtotal+(cantidadtotal*3) ##  
                                        if lado == 'BUY':                                      
                                            preciodeataque = preciolimit*(1-paso/100)                                            
                                        else:
                                            preciodeataque = preciolimit*(1+paso/100)
                                        cantidadtotalconataqueusdt = cantidadtotalusdt+(cantidadtotal*3*preciodeataque)
                                        preciodondequedariaposicionalfinal=cantidadtotalconataqueusdt/cantidadtotalconataque ##
 	
                                    print("\ncantidadformateada: "+str(cantidadformateada)+". preciolimit: "+str(preciolimit))
                                    print("cantidadtotal: "+str(cantidadtotal)) 	 			
                                    print("cantidadtotalconataque: "+str(cantidadtotalconataque))                                     
                                    print("cantidadtotalusdt: "+str(cantidadtotalusdt)) 	
                                    print("cantidadtotalconataqueusdt: "+str(cantidadtotalconataqueusdt)) 	                                     	
                                    print("preciodondequedariaposicionalfinal: "+str(preciodondequedariaposicionalfinal)) 
                                    preciostopsanta= ut.preciostopsanta(lado,cantidadtotalconataqueusdt,preciodondequedariaposicionalfinal,perdida)
                                    print("preciostopsanta: "+str(preciostopsanta)) 

                                print("Cancela última compensación. ")
                                try:
                                    exchange.cancel_order(compensacionid, par)  
                                    print("Cancelada. ")
                                    cantidadtotal = cantidadtotal-cantidadformateada      
                                    cantidadtotalusdt = cantidadtotalusdt-(cantidadformateada*preciolimit)   
                                    cantidad = cantidadtotal*3  #cantidad nueva para mandar a crear              
                                    cantidadtotalconataque = cantidadtotal+cantidad
                                    cantidadtotalconataqueusdt = cantidadtotalusdt+(cantidadtotal*3*preciolimit)
                                    preciodondequedariaposicionalfinal = cantidadtotalconataqueusdt/cantidadtotalconataque ##
                                except Exception as ex:
                                    print("Error cancela última compensación: "+str(ex)+"\n")
                                    pass   
                                
                                print("LUEGO DE LA CANCELACIÓN:")	
                                print("cantidad: "+str(cantidad)) 	 				
                                print("cantidadtotal: "+str(cantidadtotal)) 	 			
                                print("cantidadtotalconataque: "+str(cantidadtotalconataque))                                     
                                print("cantidadtotalusdt: "+str(cantidadtotalusdt)) 	
                                print("cantidadtotalconataqueusdt: "+str(cantidadtotalconataqueusdt)) 	                                 	
                                print("preciodondequedariaposicionalfinal: "+str(preciodondequedariaposicionalfinal)) 
                                preciostopsanta= ut.preciostopsanta(lado,cantidadtotalconataqueusdt,preciodondequedariaposicionalfinal,perdida)
                                print("preciostopsanta: "+str(preciostopsanta)) 

                                # PUNTO DE ATAQUE                                
                                hayguita,preciolimit,cantidadformateada,compensacionid = ut.compensaciones(par,client,lado,cantidad,distanciaporc)    
                                if hayguita == False:
                                    print("\nNo se pudo crear la compensación de ataque...\n")
                                else:
                                    print("\nCompensación de ataque creada...\n")     
                                    cantidadtotalconataqueusdt = cantidadtotalusdt+(cantidadformateada*preciolimit)                                    
                                    preciodondequedariaposicionalfinal = cantidadtotalconataqueusdt/cantidadtotalconataque

                                print("Luego de la creacion del atque:")
                                print("\ncantidadformateada: "+str(cantidadformateada)+". preciolimit: "+str(preciolimit))
                                print("cantidadtotal: "+str(cantidadtotal)) 	 			
                                print("cantidadtotalusdt: "+str(cantidadtotalusdt)) 	 		
                                print("cantidadtotalconataque: "+str(cantidadtotalconataque)) 
                                print("cantidadtotalconataqueusdt: "+str(cantidadtotalconataqueusdt)) 	                                 	
                                print("preciodondequedariaposicionalfinal: "+str(preciodondequedariaposicionalfinal)) 
                                preciostopsanta= ut.preciostopsanta(lado,cantidadtotalconataqueusdt,preciodondequedariaposicionalfinal,perdida)
                                print("preciostopsanta: "+str(preciostopsanta))                                    
                                ut.binancestoploss (par,lado,preciostopsanta) 

                                hilo = threading.Thread(target=trading, args=(par,lado))
                                hilo.start()

                                posicioncreada=False   
                                maximavariacion = 0.0    
                                
                                print("\n*********************************************************************************************")
                                #escribo file
                                f = open(nombrelog, "a")
                                f.write(mensaje)
                                f.write("\n*********************************************************************************************\n")
                                f.close()

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
                        print("\nError4: "+str(falla)+" - line: "+str(exc_tb.tb_lineno)+" - file: "+str(fname)+" - par: "+par)
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

