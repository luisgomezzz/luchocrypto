#****************************************************************************************
# version 2. bb para que entre cuando el precio sale de las bandas
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
                                variaciontrigger=ut.leeconfiguracion("variaciontrigger")
                                ventana=ut.leeconfiguracion('ventana')
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

                                sideflag=ut.leeconfiguracion('sideflag')

                                df=ind.get_bollinger_bands(df)
                                currentprice = ut.currentprice(par)
                                profitprice = (pta.sma(low=df.low,close=df.close,high=df.high).iloc[-1])

                                # #######################################################################################################
                                ######################################TRADE MECHA
                                # #######################################################################################################

                                if  (variacionmecha >= variaciontrigger and
                                     df.close.iloc[-2] < df.lower2.iloc[-2]
                                    and df.close.iloc[-3] > df.lower2.iloc[-3]
                                    and currentprice < df.lower2.iloc[-1]
                                    ):  ###################
                                        ###### SHORT ######
                                        ###################
                                        ut.sound()
                                        ut.sound()  
                                        print("*********************************************************************************************")
                                        ut.printandlog(cons.nombrelog,"\nPar: "+par+" - Entrar en short. Variacion: "+str(ut.truncate(variacionmecha,2))+" - Hora:"+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))
                                        tradingflag=True

                                else:
                                    if  (variacionmecha >= variaciontrigger and
                                        df.close.iloc[-2] > df.upper2.iloc[-2] 
                                        and df.close.iloc[-3] < df.upper2.iloc[-3] 
                                        and currentprice > df.upper2.iloc[-1]
                                        ):  ###################
                                            ###### LONG #######
                                            ###################
                                            ut.sound()
                                            ut.sound()
                                            print("*********************************************************************************************")
                                            ut.printandlog(cons.nombrelog,"\nPar: "+par+" - entrar en long. Variacion: "+str(ut.truncate(variacionmecha,2))+" - Hora:"+str(dt.datetime.today().strftime('%d/%b/%Y %H:%M:%S')))
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

    except BinanceAPIException as a:
       print("Error6 - Par:",par,"-",a.status_code,a.message)
       pass

if __name__ == '__main__':
    main()

