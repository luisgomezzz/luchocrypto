#****************************************************************************************
# version 2.0
#
#****************************************************************************************

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
operandofile = 'operando.txt'
## PARAMETROS FUNDAMENTALES 
temporalidad = '1m'
apalancamiento = 10 #siempre en 10 segun la estrategia de santi
procentajeperdida = 7 #porcentaje de mi capital total maximo a perder
porcentajeentrada = 7 #porcentaje de la cuenta para crear la posición (10)
ventana = 30 #Ventana de búsqueda en minutos.   
## VARIABLES GLOBALES 
operando=[] #lista de monedas que se están operando
incrementocompensacionporc = 30 #porcentaje de incremento del tamaño de la compensacion con respecto a su anterior

###################################################################################################################
###################################################################################################################
###################################################################################################################

def updating(par,lado):
    
    profitnormalporc = 1.1 
    profitmedioporc = 0.5
    profitaltoporc = 0.2
    cuentacompensaciones = 0
    tamanioposicionguardado = ut.get_positionamt(par)
    tamanioactual = tamanioposicionguardado

    while tamanioactual!=0.0: 
        
        print("Precio Stop debería ser: "+str(ut.truncate(ut.preciostop(par,procentajeperdida),2)))

        if tamanioposicionguardado!=tamanioactual:

            ut.sound(duration = 250,freq = 659)
            
            cuentacompensaciones=cuentacompensaciones+1

            if cuentacompensaciones <= 2:
                profitporc = profitnormalporc
            else:
                if cuentacompensaciones >= 4:
                    profitporc=profitaltoporc
                else:
                    profitporc=profitmedioporc
            
            if lado=='BUY':
                profitprice = ut.getentryprice(par)*(1+profitporc/100)                
            else:
                profitprice = ut.getentryprice(par)*(1-profitporc/100)
                
            ut.binancetakeprofit(par,lado,profitprice)
            tamanioposicionguardado = tamanioactual            
    
        tamanioactual=ut.get_positionamt(par)

    print("Final del trade "+par+" en "+lado)

def trading(par,lado):
    print("Trading... "+par+"-"+lado)
    updating(par,lado)
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

def main() -> None:

    ##PARAMETROS##########################################################################################
    mazmorra=['1000SHIBUSDT','1000XECUSDT','BTCUSDT_220624','ETHUSDT_220624','ETHUSDT_220930','BTCUSDT_220930','BTCDOMUSDT'
    ,'RLCUSDT','TRBUSDT'] #Monedas que no quiero operar 
    toppar=['ADAUSDT','BNBUSDT','BTCUSDT','AXSUSDT','DOGEUSDT','ETHUSDT','MATICUSDT','TRXUSDT','SOLUSDT','XRPUSDT','ETCUSDT','DOTUSDT'
    ,'AVAXUSDT'] #monedas top
    
    lista_de_monedas = client.futures_exchange_info()['symbols'] #obtiene lista de monedas
    posicioncreada = False
    minvolumen24h=float(100000000.00)
    vueltas=0
    minutes_diff=0
    lista_monedas_filtradas=[]
    mensaje=''
    balanceobjetivo = 24.00+24.88+71.53+71.62
    mensajeposicioncompleta=''        
    margen = 'CROSSED'
    
    tradessimultaneos = 2 #Número máximo de operaciones en simultaneo
    distanciatoppar = 1 # distancia entre compensaciones cuando el par está en el top
    distancianotoppar = 1.7 # distancia entre compensaciones cuando el par no está en el top
    cantidadcompensaciones = 8 #compensaciones
    porcentajevariacionnormal=5.0
    porcentajevariacionriesgo=10.0
    maximavariacion=0.0
    maximavariacionhora=''
    ##############START    
    
    ut.clear() #limpia terminal
    print("Objetivo a: "+str(ut.truncate(balanceobjetivo-ut.balancetotal(),2)))
    for s in lista_de_monedas:
        try:  
            par = s['symbol']
            sys.stdout.write("\rFiltrando monedas: "+par+"\033[K")
            sys.stdout.flush()
            if float(client.futures_ticker(symbol=par)['quoteVolume'])>minvolumen24h and 'USDT' in par and par not in mazmorra:
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
                # se lee el file 
                with open(operandofile, 'r') as filehandle:
                    operando = [current_place.rstrip() for current_place in filehandle.readlines()]

                # para calcular tiempo de vuelta completa                
                if vueltas==0:
                    datetime_start = datetime.today()
                else:
                    if vueltas == len(lista_monedas_filtradas):
                        datetime_end = datetime.today()
                        minutes_diff = (datetime_end - datetime_start).total_seconds() / 60.0
                        vueltas==0
                
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
                                distanciaporc=(cantidadcompensaciones+2)*paso                               
                                posicioncreada,mensajeposicioncompleta=ut.posicioncompletasanta(par,lado,porcentajeentrada,distanciaporc) 
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
                                    distanciaporc=(cantidadcompensaciones+2)*paso
                                    posicioncreada,mensajeposicioncompleta=ut.posicioncompletasanta(par,lado,porcentajeentrada,distanciaporc) 
                                    print(mensajeposicioncompleta)
                                    mensaje=mensaje+mensajeposicioncompleta

                            if posicioncreada==True:     

                                #agrego el par al file
                                with open(operandofile, 'a') as filehandle:
                                    filehandle.writelines("%s\n" % place for place in [par])

                                hayguita = True
                                i = 1
                                distanciaporc = 0.0
                                tamanio = ut.get_positionamt(par)
                                tamaniototal = 0.0

                                #CREA COMPENSACIONES
                                while hayguita==True and i<=cantidadcompensaciones:
                                    tamanio=tamanio*(1+incrementocompensacionporc/100)
                                    tamaniototal=tamaniototal+tamanio
                                    distanciaporc=distanciaporc+paso                                    
                                    hayguita = ut.compensaciones(par,client,lado,tamanio,distanciaporc)                       
                                    i=i+1            

                                # PUNTO DE ATAQUE
                                ut.compensaciones(par,client,lado,tamaniototal*3,distanciaporc+1)    

                                hilo = threading.Thread(target=trading, args=(par,lado))
                                hilo.start()

                                posicioncreada=False       
                                
                                print("\n*********************************************************************************************")
                                #escribo file
                                f = open(nombrelog, "a")
                                f.write(mensaje)
                                f.write("\n*********************************************************************************************\n")
                                f.close()

                                #leo file
                                with open(operandofile, 'r') as filehandle:
                                    operando = [current_place.rstrip() for current_place in filehandle.readlines()]
                                if len(operando)>=tradessimultaneos:
                                    print("\nSe alcanzó el número máximo de trades simultaneos.")
                                while len(operando)>=tradessimultaneos:           
                                    with open(operandofile, 'r') as filehandle:
                                        operando = [current_place.rstrip() for current_place in filehandle.readlines()]                         
                                    ut.waiting(1)

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
            
                vueltas=vueltas+1

    except BinanceAPIException as a:
       print("Error6 - Par:",par,"-",a.status_code,a.message)
       pass

if __name__ == '__main__':
    main()

