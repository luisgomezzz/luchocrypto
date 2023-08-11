import sys
import constantes as cons
import util as ut
sys.path.insert(0, 'C:/LUCHO/personal/repopersonal/luchocrypto/FENIX')
import modulos as md
    
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
warnings.filterwarnings("ignore")
for symbol in dict_monedas_filtradas_aux:    
    try:
        data,_ = md.estrategia_santa(symbol,tp_flag = True)
        resultado = md.backtestingsanta(data, plot_flag = False)
        if resultado['Return [%]'] >= 0:
                dict_filtrada[symbol]={"volumeOf24h":dict_monedas_filtradas_aux[symbol]['volumeOf24h'],"capitalizacion":0}
        else:
            print(f"agregar a mazmorra: {symbol}")
    except Exception as ex:
        pass        
    except KeyboardInterrupt as ky:
        print("\nSalida solicitada. ")
        sys.exit() 

global dict_monedas_filtradas_nueva
dict_monedas_filtradas_nueva = dict_filtrada
print(dict_filtrada)
