from builtins import pow
import os
from binance.client import Client
from datetime import datetime
import time
from datetime import timedelta
import sys
from binance.exceptions import BinanceAPIException
import math
import ccxt
from pprint import pprint

#procentajes de subida al cual se
porcentajedia = 5

#mazmorra - monedas que no quiero operar en orden de castigo
mazmorra=['GTCUSDT','TLMUSDT','KEEPUSDT','SFPUSDT','ALICEUSDT','SANDUSDT','STORJUSDT','RUNEUSDT','FTMUSDT','HBARUSDT','CVCUSDT','LRCUSDT','LINAUSDT','CELRUSDT','SKLUSDT','CTKUSDT','SNXUSDT','SRMUSDT','1INCHUSDT','ANKRUSDT'] 
#mazmorra=['LRCUSDT '] 

primer_stop_loss_porc = 0.6 #porcentaje mínimo de ganancia para crear el primer stopp loss

#alarma
duration = 1000  # milliseconds
freq = 440  # Hz

def precioactual (client,par)->float:
   return float(client.get_symbol_ticker(symbol=par)["price"])

def tamanioposicion(exchange,par) -> float:
   position = exchange.fetch_balance()['info']['positions']
   return float([p for p in position if p['symbol'] == par][0]['notional'])

def obtengo_balance_disponible (client) -> float:
   return client.futures_account_balance()[1]['withdrawAvailable']

def truncate(number, digits) -> float:
    stepper = 10.0 ** digits
    return math.trunc(stepper * number) / stepper

def cierrotodo(client,par,exchange,lado) -> bool:
   
   print("FUNCION CIERROTODO")
   cerrado = False 
   
   try:      
      position = exchange.fetch_balance()['info']['positions']
      pos = abs(round(float([p for p in position if p['symbol'] == par][0]['notional']),1))
      print(pos)        
      print("Intento 0")
      client.futures_create_order(symbol=par, side=lado, type='MARKET', quantity=100000, reduceOnly='true')
   except BinanceAPIException as a:
      try:
         print(a.message)
         print("Intento 1")
         client.futures_create_order(symbol=par, side=lado, type='MARKET', quantity=100000, reduceOnly='true')               
         cerrado = True
      except BinanceAPIException as a:
         try:
            print(a.message)
            print("Intento 2")
            client.futures_create_order(symbol=par, side=lado, type='MARKET', quantity=10000, reduceOnly='true')               
            cerrado = True  
         except BinanceAPIException as a:
            try:
               print(a.message)
               print("Intento 3")
               client.futures_create_order(symbol=par, side=lado, type='MARKET', quantity=10000)               
               cerrado = True
            except BinanceAPIException as a:
               try:
                  print(a.message)
                  print("Intento 4")
                  client.futures_create_order(symbol=par, side=lado, type='MARKET', quantity=1000)               
                  cerrado = True  
               except BinanceAPIException as a:
                  try:
                     print(a.message)
                     print("Intento 5")
                     client.futures_create_order(symbol=par, side=lado, type='MARKET', quantity=100,reduceOnly='true')               
                     cerrado = True           
                  except BinanceAPIException as a:
                     try:
                        print(a.message)
                        print("Intento 6")
                        client.futures_create_order(symbol=par, side=lado, type='MARKET', quantity=100)               
                        cerrado = True  
                     except BinanceAPIException as a:
                        print(a.message)
                        print("Except FUNCION CIERROTODO",a.status_code,a.message)   
                        os.system('play -nq -t alsa synth 0.3 tri F5')
                        time.sleep(0.5)
                        os.system('play -nq -t alsa synth 0.3 tri F5')
                        time.sleep(0.5)
                        os.system('play -nq -t alsa synth 0.3 tri F5')
                        input("QUEDAN POSICIONES ABIERTAS!!! PRESIONE UNA TECLA LUEGO DE ARREGLARLO...")            

   client.futures_cancel_all_open_orders(symbol=par) 
   print("Órdenes canceladas.") 
   return cerrado

def crearlimite(exchange,par,client,posicionporc,distanciaproc,lado,tamanio):
   print("Creo el limit ...")
   precio=precioactual(client,par)
   
   if lado=='BUY':
      precioprofit=precio-(precio*distanciaproc/100)
   else:
      precioprofit=precio+(precio*distanciaproc/100)
   
   if tamanio=='':
      sizedesocupar=abs(math.trunc(tamanioposicion(exchange,par)*posicionporc/100))
   else:
      sizedesocupar=math.trunc(tamanio) # esto se hace porque el tamanio puede ir variando y la idea es que se tome una porcion del valor original.

   print("Limit a:", sizedesocupar)

   try:
      client.futures_create_order(symbol=par, side=lado, type='LIMIT', timeInForce='GTC', quantity=sizedesocupar,price=truncate(precioprofit,4))
      print("Limit creado1. \033[K")            
   except BinanceAPIException as a:
      try:
         print(a.message)
         client.futures_create_order(symbol=par, side=lado, type='LIMIT', timeInForce='GTC', quantity=sizedesocupar,price=truncate(precioprofit,3))
         print("Limit creado2. \033[K")               
      except BinanceAPIException as a:
         try:
            print(a.message)
            client.futures_create_order(symbol=par, side=lado, type='LIMIT', timeInForce='GTC', quantity=sizedesocupar,price=truncate(precioprofit,2))
            print("Limit creado3. \033[K")
         except BinanceAPIException as a:
            try:
               print(a.message)
               client.futures_create_order(symbol=par, side=lado, type='LIMIT', timeInForce='GTC', quantity=sizedesocupar,price=truncate(precioprofit,1))
               print("Limit creado4. \033[K")
            except BinanceAPIException as a:
               try:
                  print(a.message)
                  client.futures_create_order(symbol=par, side=lado, type='LIMIT', timeInForce='GTC', quantity=sizedesocupar,price=math.trunc(precioprofit))
                  print("Limit creado5. \033[K")
               except BinanceAPIException as a:
                  print(a.message,"no se pudo crear el Limit.")
                  pass   

class luchocripto():

   #parametros
   porcentajegananciadiario = 50 #porcentaje de ganancia de mi capital para el cual salgo.
   ventana = 40 #Ventana de búsqueda en minutos.   
   segundos_asedio = 1000000 #Segundos de asedio
   apalancamiento = 10 #siempre en 10 segun la estrategia de santi
   margen = 'CROSSED'
   porcentajeentrada = 10 #porcentaje de mi capital que coloco en entrada. poner en 10 segun estrategia de santi
   porcentajeperdida = 10 #porcentaje de mi capital que asumo de pérdida.

   #login
   binance_api="N7yU75L3CNJg2RW0TcJBAW2cUjhPGvyuSFUgnRHvMSMMiS8WpZ8Yd8yn70evqKl0"
   binance_secret="2HfMkleskGwTb6KQn0AKUQfjBDd5dArBW3Ykd2uTeOiv9VZ6qSU2L1yWM1ZlQ5RH"
   client = Client(binance_api, binance_secret)

   #permite obtener el pnl y mi capital
   exchange = ccxt.binance({
      'enableRateLimit': True,  
      'apiKey': binance_api,
      'secret': binance_secret,
      'options': {  
         'defaultType': 'future',  
      },
   })        

   #MÓDULO DE ASEDIO
   def asedio (client,par,segundos_asedio,apalancamiento,margen,exchange,porcentajeentrada,porcentajeperdida,subioun):                                                                                 

      #funcion de stop loss
      def stoploss (par,client,preciostop)-> int:
         i=5 # decimales
         retorno=0 # 0: creado, 1: Order would immediately trigger, 2: Reach max stop order limit, 3: otros
         while i>=0:
            try:
               if i!=0:       
                  preciostop = truncate(preciostop,i)
                  print("Intento con:",preciostop)
                  client.futures_create_order(symbol=par,side='BUY',type='STOP_MARKET', timeInForce='GTC', closePosition='True', stopPrice=preciostop)
                  print("Stop loss creado correctamente. Precio:",preciostop)
                  i=-1
               else:
                  preciostop = math.trunc(preciostop)
                  print("Intento con:",preciostop)
                  client.futures_create_order(symbol=par,side='BUY',type='STOP_MARKET', timeInForce='GTC', closePosition='True', stopPrice=preciostop)
                  print("Stop loss creado. Precio:",preciostop)
                  i=-1           
            except BinanceAPIException as a:  
               if a.message == "Order would immediately trigger.":                 
                  print("Se dispararía de inmediato.")
                  i=-1 #salgo del bucle
                  retorno = 1
               else:   
                  if a.message == "Reach max stop order limit.":
                     print("Número máximo de stop loss alcanzado.")
                     i=-1 #salgo del bucle
                     retorno = 2
                  else:
                     if i==-1: #otros errors.               
                        print("Except stoploss1")
                        print (a.status_code,a.message,preciostop)
                        retorno = 3
                     else: #aca entra si la presición no era la correcta y seguir sacando decimales.
                        i=i-1
               pass   
         return retorno

      def creoposicion (par,client,size,lado) -> bool:
         serror=True
         i=4 #decimales
         print("Creando posición...")
         while i>=0:
            try:  
               if i==0:
                  print("Intento con:",math.trunc(size))
                  client.futures_create_order(symbol=par, side=lado, type='MARKET', quantity=str(math.trunc(size))) #cambio str
                  i=-2
               else:
                  size = truncate(size,i) #cambio 
                  print("Intento con:",size)
                  client.futures_create_order(symbol=par, side=lado, type='MARKET', quantity=str(size))   
                  i=-2
            except BinanceAPIException as a:
               print ("Except 6",a.status_code,a.message)
               i=i-1
               pass
 
         if i==-2:
            print("Posición creada correctamente.")
         else:
            print("Falla al crear la posición.",size) 
            serror=False
            pass
         return serror

      def takeprofit(par,client):

         valor_actual=float(client.get_symbol_ticker(symbol=par)["price"])
         print("Creo el TAKE_PROFIT_MARKET...")
         precioprofit=valor_actual/(1+(4/100))# este es el precio donde mas o menos arrancó a subir.         
         try:
            client.futures_create_order(symbol=par, side='BUY', type='TAKE_PROFIT_MARKET', timeInForce='GTC', stopPrice=precioprofit,closePosition=True)
            print("Take profit creado1. \033[K")            
         except BinanceAPIException as a:
            try:
               print(a.message)
               client.futures_create_order(symbol=par, side='BUY', type='TAKE_PROFIT_MARKET', timeInForce='GTC', stopPrice=round(precioprofit,4),closePosition=True)
               print("Take profit creado2. \033[K")               
            except BinanceAPIException as a:
               try:
                  print(a.message)
                  client.futures_create_order(symbol=par, side='BUY', type='TAKE_PROFIT_MARKET', timeInForce='GTC', stopPrice=round(precioprofit,3),closePosition=True)
                  print("Take profit creado3. \033[K")
               except BinanceAPIException as a:
                  try:
                     print(a.message)
                     client.futures_create_order(symbol=par, side='BUY', type='TAKE_PROFIT_MARKET', timeInForce='GTC', stopPrice=round(precioprofit,2),closePosition=True)
                     print("Take profit creado3. \033[K")
                  except BinanceAPIException as a:
                     try:
                        print(a.message)
                        client.futures_create_order(symbol=par, side='BUY', type='TAKE_PROFIT_MARKET', timeInForce='GTC', stopPrice=round(precioprofit,1),closePosition=True)
                        print("Take profit creado3. \033[K")
                     except BinanceAPIException as a:
                        try:
                           print(a.message)
                           client.futures_create_order(symbol=par, side='BUY', type='TAKE_PROFIT_MARKET', timeInForce='GTC', stopPrice=math.trunc(precioprofit),closePosition=True)
                           print("Take profit creado3. \033[K")
                        except BinanceAPIException as a:
                           print(a.message,"no se pudo crear el take profit.")
                           pass

      #Función de compensaciones
      def compensaciones(par,client,size,valor_actual,i):         

         #valor de las compensaciones
         apreto= math.trunc(size*(1+i/7)) # antes 10 ... dro 
         apretocondec= size*(1+i/7) # antes 10 ... dro
         try:
            client.futures_create_order(symbol=par, side='SELL', type='LIMIT', timeInForce='GTC', quantity=apreto,price=valor_actual*(1+i/250))  #250 antes 200
            print("\rCompensación", i ,"creada. \033[K")
            return True
         except:
            try:
               client.futures_create_order(symbol=par, side='SELL', type='LIMIT', timeInForce='GTC', quantity=apreto,price=round(valor_actual*(1+i/250),4))
               print("\rCompensación", i ,"creada. \033[K")
               return True
            except:
               try:
                  client.futures_create_order(symbol=par, side='SELL', type='LIMIT', timeInForce='GTC', quantity=apreto,price=round(valor_actual*(1+i/250),3))
                  print("\rCompensación", i ,"creada. \033[K")
                  return True
               except:                       
                  try:
                     client.futures_create_order(symbol=par, side='SELL', type='LIMIT', timeInForce='GTC', quantity=apreto,price=round(valor_actual*(1+i/250),2))
                     print("\rCompensación", i ,"creada. \033[K")
                     return True
                  except:
                     try:
                        client.futures_create_order(symbol=par, side='SELL', type='LIMIT', timeInForce='GTC', quantity=apreto,price=round(valor_actual*(1+i/250),1))
                        print("\rCompensación", i ,"creada. \033[K")
                        return True
                     except:
                        try:
                           client.futures_create_order(symbol=par, side='SELL', type='LIMIT', timeInForce='GTC', quantity=apreto,price=math.trunc(valor_actual*(1+i/250)))
                           print("\rCompensación", i ,"creada. \033[K")
                           return True
                        except:
                           try:
                              client.futures_create_order(symbol=par, side='SELL', type='LIMIT', timeInForce='GTC', quantity=apretocondec,price=valor_actual*(1+i/250))  
                              print("\rCompensación", i ,"creada. \033[K")
                              return True
                           except:
                              try:
                                 client.futures_create_order(symbol=par, side='SELL', type='LIMIT', timeInForce='GTC', quantity=round(apretocondec,3),price=round(valor_actual*(1+i/250),4))
                                 print("\rCompensación", i ,"creada. \033[K")
                                 return True
                              except:
                                 try:
                                    client.futures_create_order(symbol=par, side='SELL', type='LIMIT', timeInForce='GTC', quantity=round(apretocondec,2),price=round(valor_actual*(1+i/250),3))
                                    print("\rCompensación", i ,"creada. \033[K")
                                    return True
                                 except:                       
                                    try:
                                       client.futures_create_order(symbol=par, side='SELL', type='LIMIT', timeInForce='GTC', quantity=round(apretocondec,1),price=round(valor_actual*(1+i/250),2))
                                       print("\rCompensación", i ,"creada. \033[K")
                                       return True
                                    except BinanceAPIException as a:                                       
                                       if a.message!="Margin is insufficient.":
                                          print("Except 8",a.status_code,a.message)
                                       else:
                                          print("Se crearon todas las compensaciones.")                                       
                                       return False

      try:
         print("\rEntrando en asedio...")
         
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

         """
         micapital = float(exchange.fetch_balance()['info']['totalWalletBalance'])
         size = (micapital*porcentajeentrada/100)/(float(client.get_symbol_ticker(symbol=par)["price"]))

         saldo_inicial_long=micapital
         #creo posición long
         print("Creo long..")
         longcreado=creoposicion (par,client,size/2,'BUY')
         #creo limit
         if longcreado == True:
            crearlimite(exchange,par,client,posicionporc=50,distanciaproc=1,lado='SELL',tamanio=size/4)
            segundos = segundos_asedio
         else:   
            segundos = 0               

         """

         print("\rDefiniendo valor pico...")
         valor_pico = float(client.get_symbol_ticker(symbol=par)["price"])

         try:

            while segundos !=0:
               print("\rEspero un segundo...",end="\033[K")
               time.sleep(1)  
               print("\rDefiniendo valor actual...",end="\033[K")
               valor_actual = float(client.get_symbol_ticker(symbol=par)["price"])
               if valor_actual > valor_pico:
                  print("\rDefiniendo valor pico...",end="\033[K")
                  valor_pico = float(client.get_symbol_ticker(symbol=par)["price"])
                  segundos = segundos-1
               else:

                  
                  if subioun <= 14:
                     long_porcentaje_permitido = 0.3                     
                     print("\rVelocidad Baja.",end="\033[K")
                  else:
                     if subioun <= 20:
                        long_porcentaje_permitido = 0.5
                        print("\rVelocidad Media..",end="\033[K")
                     else:
                        long_porcentaje_permitido = 1
                        print("\rVelocidad Alta...!!!",end="\033[K")

                  print("\rlong_porcentaje_permitido:",long_porcentaje_permitido,end="\033[K")
                  

                  if  valor_actual <= valor_pico*(1-(long_porcentaje_permitido/100)): #Bajó long_porcentaje_permitido %
                     
                     print("\rBajó un ",long_porcentaje_permitido,"\033[K")

                     """
                     print("\rCierro el long para crear el short.","\033[K")
                     cierrotodo(client,par,exchange,'SELL')
                     print("Ganancia en long: ",truncate(((float(exchange.fetch_balance()['info']['totalWalletBalance'])/saldo_inicial_long)-1)*100,3),"%\033[K", truncate(float(exchange.fetch_balance()['info']['totalWalletBalance'])-saldo_inicial_long,2),"USDT")
                     """

                     micapital = float(exchange.fetch_balance()['info']['totalWalletBalance'])
                     size = (micapital*porcentajeentrada/100)/valor_actual

                     #CREANDO POSICIÓN SHORT

                     scalping=creoposicion (par,client,size,'SELL')

                     if scalping==True:

                        takeprofit(par,client)

                        hayguita=True 
                        print("\rPar: ",par, "Asumo perdida a:",micapital*porcentajeperdida*-1/100,"totalPositionInitialMargin:",exchange.fetch_balance()['info']['totalPositionInitialMargin'],"Primer stop: >=",micapital/2500)               
                        i=1   
                        print("Sacalping...")
                        
                        primerstoploss = False

                        while scalping==True:      

                           #POR SI NECESITO VER LOS VALORES DEL PAR
                           #position = exchange.fetch_balance()['info']['positions']
                           #pos = [p for p in position if p['symbol'] == par][0]
                           #print("Cual es el margen ratio?:",pos)

                           #SKYNET------------------------------------------------------------------------------------------------------
                           
                           sstoploss = 0                           
                           preciostop=float(client.get_symbol_ticker(symbol=par)["price"])

                           valor_posicion = exchange.fetch_balance()['info']['positions']
                           posi = abs(float([p for p in valor_posicion if p['symbol'] == par][0]['notional']))
                           
                           margen_ratio=(100*posi)/(micapital*apalancamiento)
                           valor_primerstoploss=(margen_ratio*primer_stop_loss_porc/apalancamiento)*(micapital/200)
                           sys.stdout.write("\rPrimer stop loss a: "+str(truncate(valor_primerstoploss,2))+"\033[K")
                           sys.stdout.flush()

                           while float(exchange.fetch_balance()['info']['totalCrossUnPnl'])>valor_primerstoploss:# a veces coloca el stoploss en pérdida con lo cual tengo que habilitarlo cuando haya mucha ganancia para evitar que esto suceda. Mientras lo sigo manualmente
                              
                              print("Estoy en zona ganancias buenas. PNL:",float(exchange.fetch_balance()['info']['totalCrossUnPnl']))                                                            

                              if sstoploss == 2:
                                 print("No se pueden crear más stop loss.... ahora a esperar que alcance el último trigger....:D")   
                              else:
                                 if scalping == True:
                                    if primerstoploss == False:
                                       print("Creo el primer stop loss. ")
                                       sstoploss=stoploss(par,client,preciostop)
                                       if sstoploss == 0:
                                          primerstoploss=True
                                          ultimopreciostop=preciostop
                                          i=1
                                          j=10
                                    else:  
                                       while i<=3:  
                                          crearlimite(exchange,par,client,posicionporc=j,distanciaproc=i,lado='BUY',tamanio='')
                                          i=i+1
                                          j=j*i
                                       
                                       precioactualaux = float(client.get_symbol_ticker(symbol=par)["price"])                                       
                                       preciostop = precioactualaux+precioactualaux*0.15/100    
                                       if preciostop < ultimopreciostop:   
                                          #print("Cierro todas las órdenes para solo tener el stop loss más actual.")
                                          #client.futures_cancel_all_open_orders(symbol=par)                                 
                                          print("Actualizo stop loss")
                                          sstoploss=stoploss(par,client,preciostop)# no deberia fallar cuando se encuentre el porcentaje justo. En el hipotetico caso que falle de todos modos se actualiza el precio continuar.
                                          #print("Actualizo takeprofit")
                                          #takeprofit(par,client)
                                          if sstoploss==0:
                                             ultimopreciostop=preciostop
                                             time.sleep(5)#espero un poco para que no sea una ametralladora. 

                              if float(exchange.fetch_balance()['info']['totalPositionInitialMargin']) == 0.0 and scalping==True:
                                 print("Cierro todas las órdenes porque se alcanzó el trigger stop loss o take profit.")
                                 client.futures_cancel_all_open_orders(symbol=par) 
                                 print("Órdenes canceladas.") 
                                 scalping=False        
                           
                           #------------------------------------------------------------------------------------------------------      

                           #ASUME PÉRIDAS
                           if scalping==True and (float(exchange.fetch_balance()['info']['totalCrossUnPnl'])<=micapital*porcentajeperdida*-1/100):
                              print("Entro para asumir pérdidas. :( es de buen trader asumirla.")
                              cierrotodo(client,par,exchange,'BUY')      
                              scalping=False 
                              print("PNL:",float(exchange.fetch_balance()['info']['totalCrossUnPnl']))
                              sys.exit()

                           #CREA COMPENSACIONES
                           if scalping==True and hayguita==True:
                              hayguita=compensaciones(par,client,size,valor_actual,i)                       
                              i=i+1

                           if hayguita==False:
                              sys.stdout.write("\rEsperando a que empiece a haber ganancias... ;)\033[K")
                              sys.stdout.flush()

                           if float(exchange.fetch_balance()['info']['totalPositionInitialMargin']) == 0.0 and scalping==True:
                                 print("Cierro todas las órdenes porque se alcanzó el trigger stop loss (2).")
                                 client.futures_cancel_all_open_orders(symbol=par) 
                                 print("Órdenes canceladas.") 
                                 scalping=False     
                        segundos=0
                     else:
                        segundos=0   
                  else:
                     segundos=segundos-1
         except BinanceAPIException as a:
            print (a.status_code)
            print (a.message)  
         except Exception as ex:
            print("Except 3")  
            print(ex)   
      except BinanceAPIException as e:
         print("Except 4")
         print (e.status_code)
         print (e.message)
         pass
            
   #*****************************************************PROGRAMA PRINCIPAL *************************************************************
   #os.system("clear")

   exchange_info = client.futures_exchange_info()

   try:

      saldo_inicial=float(exchange.fetch_balance()['info']['totalWalletBalance'])

      while 1==1:#dt.datetime.today().hour >=10 and dt.datetime.today().hour <=16: #horario en donde las oportunidades no son tan volátiles. Además no jugar sábados y domingos.

         porcentaje=porcentajedia
            
         for s in exchange_info['symbols']:

            par = s['symbol']            

            if par not in mazmorra:

               comienzo = datetime.now() - timedelta(minutes=ventana)
               comienzoms = int(comienzo.timestamp() * 1000)

               finalms = int(datetime.now().timestamp() * 1000)

               try:
                  try:
                     volumen24h=client.futures_ticker(symbol=par)['quoteVolume']
                  except:
                     volumen24h=0

                  try:   

                     trades = client.get_aggregate_trades(symbol=par, startTime=comienzoms,endTime=finalms)

                     precioanterior = float(min(trades, key=lambda x:x['p'])['p'])
                     precioactual = float(client.get_symbol_ticker(symbol=par)["price"])  
                     preciomayor = float(max(trades, key=lambda x:x['p'])['p'])             
   
                     if float(exchange.fetch_balance()['info']['totalPositionInitialMargin'])==0.0:
                        if ((precioactual - precioanterior)*(100/precioanterior))>=porcentaje and (precioactual>=preciomayor) and float(volumen24h)>=float(100000000):
                           print("\rOportunidad "+par+" Subió un",round(((precioactual - precioanterior)*(100/precioanterior)),2),"%\033[K")
                           os.system('play -nq -t alsa synth %s sin %s' % (duration/1000, freq))
                           #input("Press Enter to continue...")

                           ################################ASEDIO###############################################################
                           asedio(client,par,segundos_asedio,apalancamiento,margen,exchange,porcentajeentrada,porcentajeperdida,subioun=round(((precioactual - precioanterior)*(100/precioanterior)),2))
                           #####################################################################################################
                           print("\rGANANCIA ACUMULADA: ",truncate(((float(exchange.fetch_balance()['info']['totalWalletBalance'])/saldo_inicial)-1)*100,3),"%\033[K", truncate(float(exchange.fetch_balance()['info']['totalWalletBalance'])-saldo_inicial,2),"USDT")
                           print("BALANCE TOTAL USDT: ",float(exchange.fetch_balance()['info']['totalWalletBalance']))
                           print("BALANCE TOTAL BNB: ",float((exchange.fetch_balance()['BNB']['total'])*float(client.get_symbol_ticker(symbol='BNBUSDT')["price"])))

                     else:
                        while float(exchange.fetch_balance()['info']['totalPositionInitialMargin'])!=0.0:
                           print("posiciones abiertas por esta guita: ",float(exchange.fetch_balance()['info']['totalPositionInitialMargin']))
                           os.system('play -nq -t alsa synth 0.1 tri F5')
                           time.sleep(0.5)               
                     
                     if float(exchange.fetch_balance()['info']['totalWalletBalance'])>=saldo_inicial*(1+(porcentajegananciadiario/100)):
                        print("\nUN ÉXITO!!! Salida por alcanzar ganancias mayores o igual al porcentaje de mi capital elegido. ")
                        print("NO ESTAR DEMASIADO EXPUESTO AL MERCADO. ")
                        print("DINERO GANADO:",truncate(float(exchange.fetch_balance()['info']['totalWalletBalance'])-saldo_inicial,2),"USDT")
                        ganancia_porc = ((float(exchange.fetch_balance()['info']['totalWalletBalance'])/saldo_inicial)-1)*100
                        print("PORCENTAJE DE GANANCIA: ",truncate(ganancia_porc,2),"%")         
                        ####       
                        dias=30
                        print("BALANCE TOTAL DE USDT:",float(exchange.fetch_balance()['info']['totalWalletBalance']))  
                        print("BALANCE APROXIMADO EN "+str(dias)+" DIAS CON ESTE PORCENTAJE DE GANANCIA:",pow((1+(ganancia_porc/100)),dias)*float(exchange.fetch_balance()['info']['totalWalletBalance']))
                        print("DINERO GANADO EN "+str(dias)+" DIAS:",(pow((1+(ganancia_porc/100)),dias)*float(exchange.fetch_balance()['info']['totalWalletBalance']))-float(exchange.fetch_balance()['info']['totalWalletBalance']))
                        print("BNB:",float((exchange.fetch_balance()['BNB']['total'])*float(client.get_symbol_ticker(symbol='BNBUSDT')["price"])))
                        sys.exit()        

                     sys.stdout.write("\rBuscando oportunidad. Ctrl+c para salir. Par: "+par+"\033[K")
                     sys.stdout.flush()
                  except:
                     sys.stdout.write("\rFalla típica de conexión catcheada...:D\033[K")
                     sys.stdout.flush()
                     pass

               except KeyboardInterrupt:
                  print("\rSalida solicitada.\033[K")
                  sys.exit()            
               except BinanceAPIException as a:
                  if a.message!="Invalid symbol.":
                     print("\rExcept 1 - Par:",par,"- Error:",a.status_code,a.message,"\033[K")
                  pass
      
      print("\rFuera del horario para operar. Hasta mañana :) \033[K")   
      ganancia_porc = ((float(exchange.fetch_balance()['info']['totalWalletBalance'])/saldo_inicial)-1)*100
      print("Porcentaje de ganancias: ",ganancia_porc)   
      sys.exit()

   except BinanceAPIException as a:
      print("\rExcept 2 - Par:",par,"- Error:",a.status_code,a.message,"\033[K")
      pass

app=luchocripto()      
