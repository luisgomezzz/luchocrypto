#****************************************************************************************
# version 3.0
#****************************************************************************************
import sys, os
import util as ut
import datetime as dt
from datetime import datetime
import threading
from playsound import playsound
import variables as var
from binance.exceptions import BinanceAPIException

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
    lista_monedas_filtradas_aux = []
    lista_de_monedas = ut.lista_de_monedas ()
    mazmorra=['1000SHIBUSDT','1000XECUSDT','BTCUSDT_220624','ETHUSDT_220624','ETHUSDT_220930','BTCUSDT_220930','BTCDOMUSDT','FOOTBALLUSDT'
    ,'ETHUSDT_221230'] #Monedas que no quiero operar (muchas estan aqui porque fallan en algun momento al crear el dataframe)     
    for par in lista_de_monedas:
        try:  
            if par not in mazmorra:                
                if (
                    ut.volumeOf24h(par)>var.minvolumen24h 
                    and ut.capitalizacion(par)>=var.mincapitalizacion
                    ):
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
    if var.exchange_name == 'kucoinfutures':
        multiplier=float(var.clientmarket.get_contract_detail(par)['multiplier'])
    else:
        multiplier=1
    posicioncreada,mensajeposicioncompleta=posicionsanta(par,lado,porcentajeentrada)
    if posicioncreada==True:    
        ut.printandlog(var.nombrelog,mensajeposicioncompleta+"\nQuantity: "+str(ut.get_positionamt(par)))
        ut.printandlog(var.nombrelog,"distancia: "+str(var.paso))
        #agrego el par al file
        with open(os.path.join(var.pathroot, var.operandofile), 'a') as filehandle:            
            filehandle.writelines("%s\n" % place for place in [par])
        balancetotal = ut.balancetotal()
        perdida = (balancetotal*var.procentajeperdida/100)*-1
        hayguita = True
        distanciaporc = 0.0
        cantidadtotal = 0.0
        cantidadtotalusdt = 0.0  
        precioinicial = ut.getentryprice(par)
        cantidad = abs(ut.get_positionamt(par))
        cantidadusdt = cantidad*ut.getentryprice(par)*multiplier
        cantidadtotal = cantidadtotal+cantidad
        cantidadtotalusdt = cantidadtotalusdt+cantidadusdt
        cantidadtotalconataque = cantidadtotal+(cantidadtotal*3)
        if lado == 'BUY':
            preciodeataque = precioinicial*(1-var.paso/2/100)
        else:
            preciodeataque = precioinicial*(1+var.paso/2/100)                                
        cantidadtotalconataqueusdt = cantidadtotalusdt+(cantidadtotal*3*preciodeataque*multiplier)
        preciodondequedariaposicionalfinal = cantidadtotalconataqueusdt/cantidadtotalconataque    
        preciostopsanta= preciostopsantasugerido(lado,cantidadtotalconataqueusdt,preciodondequedariaposicionalfinal,perdida)/multiplier
        i=0
        #CREA COMPENSACIONES         
        while (cantidadtotalconataqueusdt <= balancetotal*var.apalancamiento # pregunta si supera mi capital
            and (
            (lado=='BUY' and preciodeataque > preciostopsanta)
            or 
            (lado=='SELL' and preciodeataque < preciostopsanta)
            ) 
            and i<=var.cantidadcompensaciones
            ):
            i=i+1
            if i==1:
                cantidad = cantidad
            else:
                cantidad = cantidad*(1+var.incrementocompensacionporc/100)
            distanciaporc = distanciaporc+var.paso              
            hayguita,preciolimit,cantidadformateada,compensacionid = ut.compensaciones(par,var.client,lado,cantidad,distanciaporc)
            if hayguita == True:
                cantidadtotal = cantidadtotal+cantidadformateada
                cantidadtotalusdt = cantidadtotalusdt+(cantidadformateada*preciolimit*multiplier)
                cantidadtotalconataque = cantidadtotal+(cantidadtotal*3)
                if lado == 'BUY':                                      
                    preciodeataque = preciolimit*(1-var.paso/2/100)                                            
                else:
                    preciodeataque = preciolimit*(1+var.paso/2/100)
                cantidadtotalconataqueusdt = cantidadtotalusdt+(cantidadtotal*3*preciodeataque*multiplier)
                preciodondequedariaposicionalfinal = cantidadtotalconataqueusdt/cantidadtotalconataque ##
            ut.printandlog(var.nombrelog,"Compensación "+str(i)+" cantidadformateada: "+str(cantidadformateada)+". preciolimit: "+str(preciolimit))
            preciostopsanta= preciostopsantasugerido(lado,cantidadtotalconataqueusdt,preciodondequedariaposicionalfinal,perdida)/multiplier        
        # CANCELA ÚLTIMA COMPENSACIÓN
        try:
            ut.printandlog(var.nombrelog,"Cancela última compensación ("+str(i)+")")
            var.exchange.cancel_order(compensacionid, par)  
            ut.printandlog(var.nombrelog,"Cancelada. ")
            cantidadtotal = cantidadtotal-cantidadformateada      
            cantidadtotalusdt = cantidadtotalusdt-(cantidadformateada*preciolimit)   
        except Exception as ex:
            print("Error cancela última compensación: "+str(ex)+"\n")
            pass          
        '''                                  
        # PUNTO DE ATAQUE  
        if var.flagpuntodeataque ==1:
            cantidad = cantidadtotal*3  #cantidad nueva para mandar a crear              
            cantidadtotalconataque = cantidadtotal+cantidad
            distanciaporc = (distanciaporc-var.paso)+(var.paso/3)
            ut.printandlog(var.nombrelog,"Punto de atque sugerido. Cantidad: "+str(cantidad)+". Distancia porcentaje: "+str(distanciaporc))
            hayguita,preciolimit,cantidadformateada,compensacionid = ut.compensaciones(par,var.client,lado,cantidad,distanciaporc)    
            if hayguita == False:
                print("No se pudo crear la compensación de ataque.")
                cantidadtotalconataqueusdt = cantidadtotalusdt #seria la cantidad total sin ataque
                preciodondequedariaposicionalfinal = cantidadtotalusdt/cantidadtotal # totales sin ataque
            else:
                ut.printandlog(var.nombrelog,"Ataque creado. "+"Cantidadformateada: "+str(cantidadformateada)+". preciolimit: "+str(preciolimit))     
                cantidadtotalconataqueusdt = cantidadtotalusdt+(cantidadformateada*preciolimit)                                    
                preciodondequedariaposicionalfinal = cantidadtotalconataqueusdt/cantidadtotalconataque
        else:
            cantidadtotalconataqueusdt = cantidadtotalusdt #seria la cantidad total sin ataque
            preciodondequedariaposicionalfinal = cantidadtotalusdt/cantidadtotal # totales sin ataque
        '''
        # STOP LOSS
        preciostopsanta= preciostopsantasugerido(lado,cantidadtotalconataqueusdt,preciodondequedariaposicionalfinal,perdida)/multiplier
        ut.printandlog(var.nombrelog,"Precio Stop sugerido: "+str(preciostopsanta))
        ut.creostoploss (par,lado,preciostopsanta,cantidadtotal)         
        ut.printandlog(var.nombrelog,"\n*********************************************************************************************")    
    return posicioncreada        

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
    profitnormalporc = 2 # probando con 2 (va 1)
    profitmedioporc = 2
    balancetotal=ut.balancetotal() 
    tamanioactualusdt=abs(ut.get_positionamtusdt(par))
    try:        
        if tamanioactualusdt <= (balancetotal*var.procentajeperdida/100)*1.8:
            divisor = profitnormalporc
        else:
            divisor=profitmedioporc
        #crea los TPs
        for porc, tamanio in dict.items():
            print("tp "+str(tp))
            if lado=='BUY':
                preciolimit = ut.getentryprice(par)*(1+((porc/divisor)/100))                
            else:
                preciolimit = ut.getentryprice(par)*(1-((porc/divisor)/100))
            creado,orderid=ut.creotakeprofit(par,preciolimit,tamanio,lado)
            if creado==True:
                limitordersnuevos.append(orderid)
            tp=tp+1
        #cancela los TPs viejos
        for id in limitorders:
            print("Cancela "+str(id))
            try:
                var.exchange.cancel_order(id, par)   
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
    compensacioncount=0
    #actualiza tps y stops
    while tamanioactual!=0.0: 
        if tamanioposicionguardado!=tamanioactual:
            if ut.pnl(par) > 0.0:
                try:
                    # stop en ganancias cuando tocó un TP
                    precioactual=ut.currentprice(par)
                    precioposicion=ut.getentryprice(par)
                    if lado=='BUY':
                        stopenganancias=precioposicion+((precioactual-precioposicion)/2)
                    else:
                        stopenganancias=precioposicion-((precioposicion-precioactual)/2)
                    ut.creostoploss (par,lado,stopenganancias) 
                    playsound(var.pathsound+"cash-register-purchase.mp3")
                    print("\nupdating-CREA STOP EN GANANCIAS PORQUE TOCÓ UN TP..."+par)
                except Exception as ex:
                    pass
            else:
                # take profit que persigue al precio cuando toma compensaciones 
                compensacioncount=compensacioncount+1
                limitorders=creaactualizatps (par,lado,limitorders)
                if compensacioncount<=1:
                    ut.sound(duration = 250,freq = 659)                
                else:
                    playsound(var.pathsound+"call-to-attention.mp3")
                print("\nupdating-ACTUALIZAR TPs PORQUE TOCÓ UNA COMPENSACIÓN..."+par)
            tamanioposicionguardado = tamanioactual    
        else:
            if ut.pnl(par) > 0.0 and stopenganancias != 0.0:
                stopvelavela=ut.stopvelavela (par,lado,var.temporalidad)
                if lado=='SELL':
                    if stopvelavela!=0.0 and stopvelavela<stopenganancias:
                        print("\nCrea stopvelavela. "+par)
                        creado,orderid=ut.creostoploss (par,lado,stopvelavela)
                        stopenganancias=stopvelavela
                        if creado==True:
                            if orderidanterior==0:
                                orderidanterior=orderid
                            else:
                                try:
                                    var.exchange.cancel_order(orderidanterior, par)
                                    orderidanterior=orderid
                                    print("\nStopvelavela anterior cancelado. "+par)
                                except:
                                    orderidanterior=orderid
                                    pass
                else:
                    if stopvelavela!=0.0 and stopvelavela>stopenganancias:
                        print("\ncrea stopvelavela. "+par)
                        creado,orderid=ut.creostoploss (par,lado,stopvelavela)
                        stopenganancias=stopvelavela
                        if creado==True:
                            if orderidanterior==0:
                                orderidanterior=orderid
                            else:
                                try:
                                    var.exchange.cancel_order(orderidanterior, par)
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
    with open(os.path.join(var.pathroot,var.operandofile), 'r') as filehandle:
        operando = [current_place.rstrip() for current_place in filehandle.readlines()]
    # remove the item for all its occurrences
    c = operando.count(par)
    for i in range(c):
        operando.remove(par)
    #borro todo
    open(os.path.join(var.pathroot,var.operandofile), "w").close()
    ##agrego
    with open(os.path.join(var.pathroot,var.operandofile), 'a') as filehandle:
        filehandle.writelines("%s\n" % place for place in operando)       
    playsound(var.pathsound+"computer-processing.mp3")
    print("\nTrading-Final del trade "+par+" en "+lado+" - Saldo: "+str(ut.truncate(ut.balancetotal(),2))+"- Objetivo a: "+str(ut.truncate(var.balanceobjetivo-ut.balancetotal(),2))+"\n") 

def trading(par,lado,porcentajeentrada):
    mensajelog="Trade - "+par+" - "+lado+" - Hora:"+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S'))
    ut.printandlog(var.nombrelog,mensajelog)    
    posicioncreada=formacioninicial(par,lado,porcentajeentrada) 
    hilo = threading.Thread(target=updating, args=(par,lado))
    hilo.start()    
    return posicioncreada        

def main() -> None:
    ##PARAMETROS##########################################################################################
    print("Buscando equipos liquidando...")
    listaequipoliquidando=ut.equipoliquidando()
    vueltas=0
    minutes_diff=0    
    maximavariacion=0.0
    maximavariacionhora=''
    maximavariacionhoracomienzo = float(dt.datetime.today().hour)
    btcvariacion = 0
    btcflecha = ''    
    ##############START        
    print("Saldo: "+str(ut.truncate(ut.balancetotal(),2)))
    print("Objetivo a: "+str(ut.truncate(var.balanceobjetivo-ut.balancetotal(),2)))
    print("Equipos liquidando: "+str(listaequipoliquidando))
    print("Filtrando monedas...")
    filtradodemonedas()
    lista_monedas_filtradas = lista_monedas_filtradas_nueva
    ut.printandlog(var.lista_monedas_filtradas_file,str(lista_monedas_filtradas),pal=1,mode='w')
    try:

        #lanza filtrado de monedas paralelo
        hilofiltramoneda = threading.Thread(target=loopfiltradodemonedas)
        hilofiltramoneda.daemon = True
        hilofiltramoneda.start()        

        while True:
            if dt.datetime.today().hour !=18: #se detecta q a esa hora (utc-3) existen variaciones altas.

                res = [x for x in lista_monedas_filtradas + lista_monedas_filtradas_nueva if x not in lista_monedas_filtradas or x not in lista_monedas_filtradas_nueva]
                
                if res:
                    print("\nCambios en monedas filtradas: ")     
                    print(res)
                    lista_monedas_filtradas = lista_monedas_filtradas_nueva
                    ut.printandlog(var.lista_monedas_filtradas_file,str(lista_monedas_filtradas),pal=1,mode='w')
                
                for par in lista_monedas_filtradas:
                    #leo file
                    with open(os.path.join(var.pathroot,var.operandofile), 'r') as filehandle:
                        operando = [current_place.rstrip() for current_place in filehandle.readlines()]
                    if len(operando)>=var.tradessimultaneos:
                        print("\nSe alcanzó el número máximo de trades simultaneos.")
                    while len(operando)>=var.tradessimultaneos:           
                        with open(os.path.join(var.pathroot,var.operandofile), 'r') as filehandle:
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

                                df=ut.calculardf (par,var.temporalidad,var.ventana)
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
                                
                                if 3.5 >= variacion >= 2.5:
                                    
                                    #crea archivo lanzador por si quiero ejecutarlo manualmente
                                    lanzadorscript = "# https://www.binance.com/en/futures/"+par
                                    lanzadorscript = lanzadorscript+"\n# https://www.tradingview.com/chart/Wo0HiKnm/?symbol=BINANCE%3A"+par
                                    lanzadorscript = lanzadorscript+"\nimport sys"
                                    lanzadorscript = lanzadorscript+"\nsys.path.insert(1,'./')"
                                    lanzadorscript = lanzadorscript+"\nimport santa3 as san"
                                    lanzadorscript = lanzadorscript+"\npar='"+par+"'"
                                    if flecha == " ↑":
                                        lanzadorscript = lanzadorscript+"\nlado='SELL'"
                                    else:
                                        lanzadorscript = lanzadorscript+"\nlado='BUY'"
                                    lanzadorscript = lanzadorscript+"\n#san.trading(par,lado,"+str(var.porcentajeentrada)+")"
                                    lanzadorscript = lanzadorscript+"\nsan.updating(par,lado)"
                                    ut.printandlog(var.lanzadorfile,lanzadorscript,pal=1,mode='w')

                                    f = open(os.path.join(var.pathroot, var.lanzadorfile), 'w',encoding="utf-8")
                                    f.write(lanzadorscript)
                                    f.close() 

                                    #EJECUTA MINITRADE                                    
                                    if (flecha==" ↑" and precioactual>=preciomayor):
                                        ###########para la variacion diaria (aunque tomo 12 hs para atrás ;)
                                        df2=ut.calculardf (par,'1h',12)
                                        df2preciomenor=df2.low.min()
                                        df2preciomayor=df2.high.max()
                                        variaciondiaria = ut.truncate((((df2preciomayor/df2preciomenor)-1)*100),2) # se toma como si siempre fuese una subida ya que sería el caso más alto.
                                        #####################################
                                        if par not in listaequipoliquidando and variaciondiaria <= var.maximavariaciondiaria:
                                            ut.sound(duration = 200,freq = 800)
                                            ut.sound(duration = 200,freq = 800)   
                                            ut.printandlog(var.nombrelog,"\nPar: "+par+" - Variación: "+str(ut.truncate(variacion,2))+"% - Variación diaria: "+str(variaciondiaria)+"%")
                                            lado='SELL'
                                            trading(par,lado,var.porcentajeentrada)
                                    else:
                                        if (flecha==" ↓" and precioactual<=preciomenor):
                                            ###########para la variacion diaria (aunque tomo 12 hs para atrás ;)
                                            df2=ut.calculardf (par,'1h',12)
                                            df2preciomenor=df2.low.min()
                                            df2preciomayor=df2.high.max()
                                            variaciondiaria = ut.truncate((((df2preciomayor/df2preciomenor)-1)*100),2) # se toma como si siempre fuese una subida ya que sería el caso más alto.
                                            #####################################
                                            if variaciondiaria <= var.maximavariaciondiaria:
                                                ut.sound(duration = 200,freq = 800)
                                                ut.sound(duration = 200,freq = 800)
                                                ut.printandlog(var.nombrelog,"\nPar: "+par+" - Variación: "+str(ut.truncate(variacion,2))+"% - Variación diaria: "+str(variaciondiaria)+"%")
                                                lado='BUY'
                                                trading(par,lado,var.porcentajeentrada)  

                                if par[0:7] =='BTCUSDT':
                                    btcvariacion = variacion
                                    btcflecha = flecha
                                
                                sys.stdout.write("\r"+par+" -"+flecha+str(ut.truncate(variacion,2))+"% - T. vuelta: "+str(ut.truncate(minutes_diff,2))+" min - Monedas filtradas: "+ str(len(lista_monedas_filtradas))+" - máxima variación "+maximavariacionpar+maximavariacionflecha+str(ut.truncate(maximavariacion,2))+"% Hora: "+maximavariacionhora+" - BTCUSDT:"+btcflecha+str(ut.truncate(btcvariacion,2))+"%"+"\033[K")
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

