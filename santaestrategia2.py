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

##CONFIG
client = ut.client
exchange = ut.exchange
nombrelog = "log_santa2.txt"
operandofile = "operando.txt"
lista_monedas_filtradas_file = "lista_monedas_filtradas.txt"
lanzadorfile = "lanzador.py"
## PARAMETROS FUNDAMENTALES 
temporalidad = '1m'
apalancamiento = 10 #(10)
apalancamientoposta = 25 #este es el apalancamiento de verdad para que permita tradear más de una moneda
procentajeperdida = 10 #porcentaje de mi capital total maximo a perder (10)
porcentajeentrada = 6 #porcentaje de la cuenta para crear la posición (6)
ventana = 30 #Ventana de búsqueda en minutos.   
porcentajevariacionnormal = 5
porcentajevariacionriesgo = 5
cantidadcompensaciones = 3
## VARIABLES GLOBALES 
operando=[] #lista de monedas que se están operando
incrementocompensacionporc = 30 #porcentaje de incremento del tamaño de la compensacion con respecto a su anterior
balanceobjetivo = 24.00+24.88+71.53+71.62+106.01+105.3+103.14+101.55+102.03+400 #los 400 son los del prestamo del dpto que quiero recuperar
lista_monedas_filtradas_nueva = []
flagpuntodeataque = 0 # Ataque automatico. 0 desactivado - 1 activado 
###################################################################################################################
###################################################################################################################
###################################################################################################################

# MANEJO DE TPs
def creaactualizatps (par,lado,limitorders=[]):
    print("creaactualizatps-limitorders: "+str(limitorders))
    limitordersnuevos=[]
    tp = 1
    dict = {     #porcentaje de variacion - porcentaje a desocupar   
        1.4 : 50
        #,1.15: 20
        #,1.3 : 20
        #,1.5 : 15
        #,2   : 15
    }
    profitnormalporc = 1
    profitmedioporc = 2
    profitaltoporc = 3    
    balancetotal=ut.balancetotal() 
    tamanioactualusdt=abs(ut.get_positionamtusdt(par))
    try:
        
        if tamanioactualusdt <= (balancetotal*procentajeperdida/100)*1.8:
            divisor = profitnormalporc
        else:
            if tamanioactualusdt >= (balancetotal*procentajeperdida/100)*4:
                divisor=profitaltoporc
            else:
                divisor=profitmedioporc    

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
    
    tamanioposicionguardado = ut.get_positionamt(par)
    tamanioactual = tamanioposicionguardado
    limitorders = []
    creado = False
    orderid = 0
    orderidanterior = 0
    #crea TPs
    print("\nupdating-CREA TPs..."+par)
    limitorders=creaactualizatps (par,lado,limitorders)
    stopenganancias = 0.0

    #actualiza tps y stops
    while tamanioactual!=0.0: 

        if tamanioposicionguardado!=tamanioactual:

            ut.sound(duration = 250,freq = 659)

            if ut.pnl(par) > 0.0:
                try:
                    # stop en ganancias cuando tocó un TP
                    print("\nupdating-CREA STOP EN GANANCIAS PORQUE TOCÓ UN TP..."+par)
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
                print("\nupdating-ACTUALIZAR TPs PORQUE TOCÓ UNA COMPENSACIÓN..."+par)
                limitorders=creaactualizatps (par,lado,limitorders)
            
            tamanioposicionguardado = tamanioactual            
    
        else:
            if ut.pnl(par) > 0.0 and stopenganancias != 0.0:
                stopvelavela=ut.stopvelavela (par,lado,temporalidad)
                if lado=='SELL':
                    if stopvelavela!=0.0 and stopvelavela<stopenganancias:
                        print("crea stopvelavela. "+par)
                        creado,orderid=ut.binancestoploss (par,lado,stopvelavela)
                        stopenganancias=stopvelavela
                        if creado==True:
                            if orderidanterior==0:
                                orderidanterior=orderid
                            else:
                                try:
                                    exchange.cancel_order(orderidanterior, par)
                                    orderidanterior=orderid
                                    print("Stopvelavela anterior cancelado. "+par)
                                except:
                                    orderidanterior=orderid
                                    pass
                else:
                    if stopvelavela!=0.0 and stopvelavela>stopenganancias:
                        print("crea stopvelavela. "+par)
                        creado,orderid=ut.binancestoploss (par,lado,stopvelavela)
                        stopenganancias=stopvelavela
                        if creado==True:
                            if orderidanterior==0:
                                orderidanterior=orderid
                            else:
                                try:
                                    exchange.cancel_order(orderidanterior, par)
                                    orderidanterior=orderid
                                    print("Stopvelavela anterior cancelado. "+par)
                                except:
                                    orderidanterior=orderid
                                    pass

        tamanioactual=ut.get_positionamt(par)   

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
    
    print("\nTrading-Final del trade "+par+" en "+lado+" - Saldo: "+str(ut.truncate(ut.balancetotal(),2))+"- Objetivo a: "+str(ut.truncate(balanceobjetivo-ut.balancetotal(),2))+"\n") 

def trading(par,lado,porcentajeentrada):
    mensajelog="Trade - "+par+" - "+lado
    ut.printandlog(nombrelog,mensajelog)    
    posicioncreada=formacioninicial(par,lado,porcentajeentrada) 
    hilo = threading.Thread(target=updating, args=(par,lado))
    hilo.start()    
    return posicioncreada

def filtradodemonedas ():
    
    lista_monedas_filtradas_aux = []
    lista_de_monedas = client.futures_exchange_info()['symbols'] #obtiene lista de monedas
    minvolumen24h=float(100000000)
    mincapitalizacion = float(80000000)    
    mazmorra=['1000SHIBUSDT','1000XECUSDT','BTCUSDT_220624','ETHUSDT_220624','ETHUSDT_220930','BTCUSDT_220930','BTCDOMUSDT','FOOTBALLUSDT'
    ,'ETHUSDT_221230'] #Monedas que no quiero operar (muchas estan aqui porque fallan en algun momento al crear el dataframe)     
    for s in lista_de_monedas:
        try:  
            par = s['symbol']
            #sys.stdout.write("\rFiltrando monedas: "+par+"\033[K")
            #sys.stdout.flush()
            if (float(client.futures_ticker(symbol=par)['quoteVolume'])>minvolumen24h and 'USDT' in par and par not in mazmorra
                and ut.capitalizacion(par)>=mincapitalizacion):
                lista_monedas_filtradas_aux.append(par)
        except Exception as ex:
            pass        
        except KeyboardInterrupt as ky:
            print("\nSalida solicitada. ")
            sys.exit()   

    global lista_monedas_filtradas_nueva
    lista_monedas_filtradas_nueva = lista_monedas_filtradas_aux

def loopfiltradodemonedas ():
    while True:
        filtradodemonedas ()

def formacioninicial(par,lado,porcentajeentrada):
    posicioncreada,mensajeposicioncompleta=ut.posicionsanta(par,lado,porcentajeentrada)
    paso = 1.7
    
    if posicioncreada==True:    
        ut.printandlog(nombrelog,mensajeposicioncompleta+"\nQuantity: "+str(ut.get_positionamt(par)))
        ut.printandlog(nombrelog,"distancia: "+str(paso))
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
            preciodeataque = precioinicial*(1-paso/2/100)
        else:
            preciodeataque = precioinicial*(1+paso/2/100)                                
        cantidadtotalconataqueusdt = cantidadtotalusdt+(cantidadtotal*3*preciodeataque)
        preciodondequedariaposicionalfinal = cantidadtotalconataqueusdt/cantidadtotalconataque    
        preciostopsanta= ut.preciostopsanta(lado,cantidadtotalconataqueusdt,preciodondequedariaposicionalfinal,perdida)

        i=0
        #CREA COMPENSACIONES         
        while (cantidadtotalconataqueusdt <= balancetotal*apalancamiento # pregunta si supera mi capital
            and (
            (lado=='BUY' and preciodeataque > preciostopsanta)
            or 
            (lado=='SELL' and preciodeataque < preciostopsanta)
            ) 
            and i<=cantidadcompensaciones
            ):
            i=i+1
            cantidad = cantidad*(1+incrementocompensacionporc/100) ##                       
            distanciaporc = distanciaporc+paso ##                                   
            hayguita,preciolimit,cantidadformateada,compensacionid = ut.compensaciones(par,client,lado,cantidad,distanciaporc) ##
            if hayguita == True:
                cantidadtotal = cantidadtotal+cantidadformateada
                cantidadtotalusdt = cantidadtotalusdt+(cantidadformateada*preciolimit) ##
                cantidadtotalconataque = cantidadtotal+(cantidadtotal*3) ##  
                if lado == 'BUY':                                      
                    preciodeataque = preciolimit*(1-paso/2/100)                                            
                else:
                    preciodeataque = preciolimit*(1+paso/2/100)
                cantidadtotalconataqueusdt = cantidadtotalusdt+(cantidadtotal*3*preciodeataque)
                preciodondequedariaposicionalfinal = cantidadtotalconataqueusdt/cantidadtotalconataque ##

            ut.printandlog(nombrelog,"Compensación "+str(i)+" cantidadformateada: "+str(cantidadformateada)+". preciolimit: "+str(preciolimit))
            preciostopsanta= ut.preciostopsanta(lado,cantidadtotalconataqueusdt,preciodondequedariaposicionalfinal,perdida)                                        
        
        # CANCELA ÚLTIMA COMPENSACIÓN
        try:
            ut.printandlog(nombrelog,"Cancela última compensación ("+str(i)+")")
            exchange.cancel_order(compensacionid, par)  
            ut.printandlog(nombrelog,"Cancelada. ")
            cantidadtotal = cantidadtotal-cantidadformateada      
            cantidadtotalusdt = cantidadtotalusdt-(cantidadformateada*preciolimit)   
        except Exception as ex:
            print("Error cancela última compensación: "+str(ex)+"\n")
            pass
                                            
        # PUNTO DE ATAQUE  
        if flagpuntodeataque ==1:
            cantidad = cantidadtotal*3  #cantidad nueva para mandar a crear              
            cantidadtotalconataque = cantidadtotal+cantidad
            distanciaporc = (distanciaporc-paso)+(paso/3)
            ut.printandlog(nombrelog,"Punto de atque sugerido. Cantidad: "+str(cantidad)+". Distancia porcentaje: "+str(distanciaporc))
            hayguita,preciolimit,cantidadformateada,compensacionid = ut.compensaciones(par,client,lado,cantidad,distanciaporc)    
            if hayguita == False:
                print("No se pudo crear la compensación de ataque.")
                cantidadtotalconataqueusdt = cantidadtotalusdt #seria la cantidad total sin ataque
                preciodondequedariaposicionalfinal = cantidadtotalusdt/cantidadtotal # totales sin ataque
            else:
                ut.printandlog(nombrelog,"Ataque creado. "+"Cantidadformateada: "+str(cantidadformateada)+". preciolimit: "+str(preciolimit))     
                cantidadtotalconataqueusdt = cantidadtotalusdt+(cantidadformateada*preciolimit)                                    
                preciodondequedariaposicionalfinal = cantidadtotalconataqueusdt/cantidadtotalconataque
        else:
            cantidadtotalconataqueusdt = cantidadtotalusdt #seria la cantidad total sin ataque
            preciodondequedariaposicionalfinal = cantidadtotalusdt/cantidadtotal # totales sin ataque

        # STOP LOSS
        preciostopsanta= ut.preciostopsanta(lado,cantidadtotalconataqueusdt,preciodondequedariaposicionalfinal,perdida)
        ut.printandlog(nombrelog,"Precio Stop sugerido: "+str(preciostopsanta))
        ut.binancestoploss (par,lado,preciostopsanta) 
        ut.printandlog(nombrelog,"Precio Stop creado.",pal=1)
        ut.printandlog(nombrelog,"\n*********************************************************************************************")
    
    return posicioncreada

def main() -> None:

    ##PARAMETROS##########################################################################################
    print("Equipos liquidando...")
    listaequipoliquidando=ut.equipoliquidando()
    vueltas=0
    minutes_diff=0    
    mensaje=''
    margen = 'CROSSED'
    
    tradessimultaneos = 2 #Número máximo de operaciones en simultaneo
    maximavariacion=0.0
    maximavariacionhora=''
    maximavariacionhoracomienzo = float(dt.datetime.today().hour)
    btcvariacion = 0
    btcflecha = ''
    ##############START    
    
    ut.clear() #limpia terminal
    print("Saldo: "+str(ut.truncate(ut.balancetotal(),2)))
    print("Objetivo a: "+str(ut.truncate(balanceobjetivo-ut.balancetotal(),2)))
    print("Equipos liquidando: "+str(listaequipoliquidando))
    print("Filtrando monedas...")
    filtradodemonedas()
    lista_monedas_filtradas = lista_monedas_filtradas_nueva
    ut.printandlog(lista_monedas_filtradas_file,str(lista_monedas_filtradas),pal=1,mode='w')

    try:

        #lanza filtrado de monedas paralelo
        hilofiltramoneda = threading.Thread(target=loopfiltradodemonedas)
        hilofiltramoneda.daemon = True
        hilofiltramoneda.start()        

        while True:
            if 1==1: #dt.datetime.today().hour >=5 and dt.datetime.today().hour <=23: 
                #en operaciones riesgosas las variaciones deben ser mayores
                if dt.datetime.today().hour == 21:
                    porcentaje = porcentajevariacionriesgo
                else:
                    porcentaje = porcentajevariacionnormal

                res = [x for x in lista_monedas_filtradas + lista_monedas_filtradas_nueva if x not in lista_monedas_filtradas or x not in lista_monedas_filtradas_nueva]
                if res:
                    print("\nCambios en monedas filtradas: ")     
                    print(res)
                    lista_monedas_filtradas = lista_monedas_filtradas_nueva
                    ut.printandlog(lista_monedas_filtradas_file,str(lista_monedas_filtradas),pal=1,mode='w')
                
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
                                    if 4 > variacion > 2.5:
                                        ut.sound(duration = 200,freq = 800)
                                        ut.sound(duration = 200,freq = 800)
                                        if par in listaequipoliquidando:
                                            print("\n"+par+" - PRECAUCIÓN. Equipo liquidando\n")
                                        lanzadorscript = "# https://www.binance.com/en/futures/"+par
                                        lanzadorscript = lanzadorscript+"\n# https://www.tradingview.com/chart/Wo0HiKnm/?symbol=BINANCE%3A"+par
                                        lanzadorscript = lanzadorscript+"\nimport sys"
                                        lanzadorscript = lanzadorscript+"\nsys.path.insert(1,'./')"
                                        lanzadorscript = lanzadorscript+"\nimport santaestrategia2 as se2"
                                        lanzadorscript = lanzadorscript+"\npar='"+par+"'"
                                        if flecha == " ↑":
                                            lanzadorscript = lanzadorscript+"\nlado='SELL'"
                                        else:
                                            lanzadorscript = lanzadorscript+"\nlado='BUY'"
                                        lanzadorscript = lanzadorscript+"\nse2.trading(par,lado,porcentajeentrada=19)"
                                        lanzadorscript = lanzadorscript+"\n#se2.updating(par,lado)"
                                        ut.printandlog("lanzador.py",lanzadorscript,pal=1,mode='w')

                                if par =='BTCUSDT':
                                    btcvariacion = variacion
                                    btcflecha = flecha
                                
                                sys.stdout.write("\r"+par+" -"+flecha+str(ut.truncate(variacion,2))+"% - T. vuelta: "+str(ut.truncate(minutes_diff,2))+" min - Monedas filtradas: "+ str(len(lista_monedas_filtradas))+" - máxima variación "+maximavariacionpar+maximavariacionflecha+str(ut.truncate(maximavariacion,2))+"% Hora: "+maximavariacionhora+" - BTCUSDT:"+btcflecha+str(ut.truncate(btcvariacion,2))+"%"+"\033[K")
                                sys.stdout.flush()       

                                if  variacion >= porcentaje and precioactual >= preciomayor:                                
                                    ############################
                                    ####### POSICION SELL ######
                                    ############################                                    
                                    client.futures_change_leverage(symbol=par, leverage=apalancamientoposta)
                                    try: 
                                        client.futures_change_margin_type(symbol=par, marginType=margen)
                                    except BinanceAPIException as a:
                                        if a.message!="No need to change margin type.":
                                            print("Except 7",a.status_code,a.message)
                                        pass

                                    lado='SELL'
                                    print("\n*********************************************************************************************")
                                    mensaje="Trade - "+par+" - "+lado
                                    mensaje=mensaje+"\nSubió un "+str(ut.truncate(variacion,3))+" %"
                                    mensaje=mensaje+"\nInicio: "+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))
                                    if par in listaequipoliquidando:
                                        mensaje=mensaje+"\nPRECAUCIÓN. Equipo liquidando"
                                    ut.printandlog(nombrelog,mensaje)
                                    posicioncreada=trading(par,lado,porcentajeentrada) 
                                    if posicioncreada==True:
                                        maximavariacion = 0.0   
                                    ut.sound() 
                                
                                else:
                                    if  variacion >= porcentaje and precioactual <= preciomenor:                                    
                                        ############################
                                        ####### POSICION BUY ######
                                        ############################                                        
                                        client.futures_change_leverage(symbol=par, leverage=apalancamiento)
                                        try: 
                                            client.futures_change_margin_type(symbol=par, marginType=margen)
                                        except BinanceAPIException as a:
                                            if a.message!="No need to change margin type.":
                                                print("Except 7",a.status_code,a.message)
                                            pass

                                        lado='BUY'
                                        print("\n*********************************************************************************************")
                                        mensaje="Trade - "+par+" - "+lado
                                        mensaje=mensaje+"\nBajó un "+str(ut.truncate(variacion,3))+" %"
                                        mensaje=mensaje+"\nInicio: "+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))
                                        if par in listaequipoliquidando:
                                            mensaje=mensaje+"\PRECAUCIÓN. Equipo liquidando"
                                        ut.printandlog(nombrelog,mensaje)
                                        posicioncreada=trading(par,lado,porcentajeentrada) 
                                        if posicioncreada==True:
                                            maximavariacion = 0.0 
                                        ut.sound()
                                
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
            else:
                sys.stdout.write("\rFuera de horario...\033[K")
                ut.waiting(60)
                sys.stdout.flush()    

    except BinanceAPIException as a:
       print("Error6 - Par:",par,"-",a.status_code,a.message)
       pass

if __name__ == '__main__':
    main()

