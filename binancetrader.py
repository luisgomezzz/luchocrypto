#binancetrader
import tradeando as tr
from binance.client import Client

binance_api="N7yU75L3CNJg2RW0TcJBAW2cUjhPGvyuSFUgnRHvMSMMiS8WpZ8Yd8yn70evqKl0"
binance_secret="2HfMkleskGwTb6KQn0AKUQfjBDd5dArBW3Ykd2uTeOiv9VZ6qSU2L1yWM1ZlQ5RH"
client = Client(binance_api, binance_secret)

def binancetrader(pair,side,bot):
    # Si no hay posiciones la creo. Si existe una posicion para el par analizado entonces se cierra en caso de que 
    # cambie de sentido.
    size=10
    exchange=tr.binanceexchange(binance_api,binance_secret)
    if float(exchange.fetch_balance()['info']['totalPositionInitialMargin'])==0.0: #si no hay posiciones abiertas creo la alertada.
        tr.binancecreoposicion (pair,client,size,side)        
        bot.send_text(pair+" - POSICION CREADA "+ side)

        currentprice = float(client.get_symbol_ticker(symbol=pair)["price"]) 

        if side =='BUY':
            stopprice = currentprice-currentprice+1.5/100
        else:
            stopprice = currentprice+currentprice+1.5/100

        tr.binancestoploss (pair,client,side,stopprice)

        bot.send_text(pair+" - STOPLOSS CREADO "+ side)

        if side == 'BUY':
            limitside = 'SELL'
        else:
            limitside = 'BUY'

        tr.binancecrearlimite(exchange,pair,client,posicionporc=80,distanciaproc=2,lado=limitside,tamanio='')

        bot.send_text(pair+" - LIMIT GANANCIA CREADO "+ side)
    else:
        if tr.binancetamanioposicion(exchange,pair) > 0.0 and side=='SELL': #cierro posicion en BUY 
            tr.binancecierrotodo(client,pair,exchange,'SELL') #cierro BUY
            bot.send_text(pair+" - POSICION CERRADA "+ side)
        else:
            if tr.binancetamanioposicion(exchange,pair) < 0.0 and side=='BUY': #cierro posicion en SELL 
                tr.binancecierrotodo(client,pair,exchange,'BUY') #cierro SELL
                bot.send_text(pair+" - POSICION CERRADA "+ side)


            