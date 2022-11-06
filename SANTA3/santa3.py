#****************************************************************************************
# version 3.0
#
#****************************************************************************************

from this import d
import sys, os
sys.path.insert(1,'./')
import util as ut
import datetime as dt
from datetime import datetime
import threading
import numpy as np
from playsound import playsound
import variables as var
from binance.exceptions import BinanceAPIException

##CONFIG
client = ut.client
exchange = ut.exchange
nombrelog = "log_santa2.txt"
operandofile = "operando.txt"
lista_monedas_filtradas_file = "lista_monedas_filtradas.txt"
lanzadorfile = "lanzador.py"
## PARAMETROS FUNDAMENTALES 
temporalidad = '1m'
apalancamiento = 10
margen = 'CROSSED'
procentajeperdida = 10 #porcentaje de mi capital total maximo a perder (10)
porcentajeentrada = 6 #porcentaje de la cuenta para crear la posición (6)
ventana = 30 #Ventana de búsqueda en minutos.   
porcentaje = 15 #porcentaje de variacion para el cual se dispara el trade estandar.
cantidadcompensaciones = 2
## VARIABLES GLOBALES 
operando=[] #lista de monedas que se están operando
incrementocompensacionporc = 30 #porcentaje de incremento del tamaño de la compensacion con respecto a su anterior
balanceobjetivo = 24.00+24.88+71.53+71.62+106.01+105.3+103.14+101.55+102.03+102.49+400 #los 400 son los del prestamo del dpto que quiero recuperar
lista_monedas_filtradas_nueva = []
flagpuntodeataque = 0 # Ataque automatico. 0 desactivado - 1 activado 
###################################################################################################################
###################################################################################################################
###################################################################################################################

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
            print(str(ex))
            pass        
        except KeyboardInterrupt as ky:
            print("\nSalida solicitada. ")
            sys.exit()   

    global lista_monedas_filtradas_nueva
    lista_monedas_filtradas_nueva = lista_monedas_filtradas_aux

def loopfiltradodemonedas ():
    while True:
        filtradodemonedas ()

def main() -> None:

    ##PARAMETROS##########################################################################################
    print("Buscando equipos liquidando...")
    listaequipoliquidando=ut.equipoliquidando()
    vueltas=0
    minutes_diff=0    
    mensaje=''
    tradessimultaneos = 4 #Número máximo de operaciones en simultaneo
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
                                
                                if 3.5 >= variacion >= 2.5:
                                    
                                    #crea archivo lanzador por si quiero ejecutarlo manualmente
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
                                    lanzadorscript = lanzadorscript+"\n#se2.trading(par,lado,"+str(porcentajeentrada)+")"
                                    lanzadorscript = lanzadorscript+"\nse2.updating(par,lado)"
                                    ut.printandlog(lanzadorfile,lanzadorscript,pal=1,mode='w')

                                    #EJECUTA MINITRADE                                    
                                    if (flecha==" ↑" and precioactual>=preciomayor):
                                        ###########para la variacion diaria  
                                        df2=ut.calculardf (par,'1d',1)
                                        df2['variaciondiaria']=np.where((df2.open<df2.close),((df2.close/df2.open)-1)*100,((df2.open/df2.close)-1)*-100)
                                        variaciondiaria = abs(ut.truncate((df2.variaciondiaria.iloc[-1]),2))
                                        #####################################
                                        if par not in listaequipoliquidando and variaciondiaria <= 10:
                                            ut.sound(duration = 200,freq = 800)
                                            ut.sound(duration = 200,freq = 800)   
                                            ut.printandlog(nombrelog,"\nPar: "+par+" - Variación: "+str(ut.truncate(variacion,2))+"% - Variación diaria: "+str(variaciondiaria)+"%")
                                            lado='SELL'
                                            #trading(par,lado,porcentajeentrada)
                                    else:
                                        if (flecha==" ↓" and precioactual<=preciomenor):
                                            ###########para la variacion diaria  
                                            df2=ut.calculardf (par,'1d',1)
                                            df2['variaciondiaria']=np.where((df2.open<df2.close),((df2.close/df2.open)-1)*100,((df2.open/df2.close)-1)*-100)
                                            variaciondiaria = abs(ut.truncate((df2.variaciondiaria.iloc[-1]),2))                                            
                                            #####################################
                                            if variaciondiaria <= 10:
                                                ut.sound(duration = 200,freq = 800)
                                                ut.sound(duration = 200,freq = 800)
                                                ut.printandlog(nombrelog,"\nPar: "+par+" - Variación: "+str(ut.truncate(variacion,2))+"% - Variación diaria: "+str(variaciondiaria)+"%")
                                                lado='BUY'
                                                #trading(par,lado,porcentajeentrada)  

                                if par[0:6] =='BTCUSDT':
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

