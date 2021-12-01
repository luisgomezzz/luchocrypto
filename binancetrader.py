#binancetrader
import tradeando as tr
from binance.client import Client

binance_api="N7yU75L3CNJg2RW0TcJBAW2cUjhPGvyuSFUgnRHvMSMMiS8WpZ8Yd8yn70evqKl0"
binance_secret="2HfMkleskGwTb6KQn0AKUQfjBDd5dArBW3Ykd2uTeOiv9VZ6qSU2L1yWM1ZlQ5RH"
client = Client(binance_api, binance_secret)

def binancetrader(pair,side,bot):
    # Si no hay posiciones la creo. Si existe una posicion para el par analizado entonces se cierra en caso de que 
    # cambie de sentido.
    porcentajeentrada=200
    exchange=tr.binanceexchange(binance_api,binance_secret)
    micapital = float(exchange.fetch_balance()['info']['totalWalletBalance'])
    size = (micapital*porcentajeentrada/100)/(float(client.get_symbol_ticker(symbol=pair)["price"]))
    try:
        if float(exchange.fetch_balance()['info']['totalPositionInitialMargin'])==0.0: #si no hay posiciones abiertas creo la alertada.
            if tr.binancecreoposicion (pair,client,size,side)==True:
                bot.send_text(pair+" - POSICION CREADA "+ side)

                currentprice = float(client.get_symbol_ticker(symbol=pair)["price"]) 

                if side =='BUY':
                    stopprice = currentprice-(currentprice*0.2/100)
                else:
                    stopprice = currentprice+(currentprice*0.2/100)

                tr.binancestoploss (pair,client,side,stopprice)

                #if side == 'BUY':
                #    limitside = 'SELL'
                #else:
                #    limitside = 'BUY'
                #if tr.binancecrearlimite(exchange,pair,client,posicionporc=90,distanciaproc=0.38,lado=limitside,tamanio='')==True:
                #    bot.send_text(pair+" - LIMIT GANANCIA CREADO "+ side)

                #if tr.binancetakeprofit(pair,client,side,porc=0.32)==True:
                #    bot.send_text(pair+" - TAKE_PROFIT_MARKET created "+ side)
        else:
            
            if tr.binancetamanioposicion(exchange,pair) > 0.0 and side=='SELL': #cierro posicion en BUY 
                print("Cierro por cambio de tendencia")
                tr.binancecierrotodo(client,pair,exchange,side) 
            else:
                if tr.binancetamanioposicion(exchange,pair) < 0.0 and side=='BUY': #cierro posicion en SELL 
                    print("Cierro por cambio de tendencia")
                    tr.binancecierrotodo(client,pair,exchange,side) 

    except:
        pass           