#binancetrader
import tradeando as tr
from binance.client import Client

binance_api="N7yU75L3CNJg2RW0TcJBAW2cUjhPGvyuSFUgnRHvMSMMiS8WpZ8Yd8yn70evqKl0"
binance_secret="2HfMkleskGwTb6KQn0AKUQfjBDd5dArBW3Ykd2uTeOiv9VZ6qSU2L1yWM1ZlQ5RH"
client = Client(binance_api, binance_secret)

def binancetrader(pair,side,bot):
    size=10
    exchange=tr.binanceexchange(binance_api,binance_secret)
    if float(exchange.fetch_balance()['info']['totalPositionInitialMargin'])==0.0: #si no hay posiciones abiertas creo la que me recomiendan
        tr.creoposicion (pair,client,size,side)
        bot.send_text(pair+" - CREO POSICION "+ side)
    else:
        if tr.tamanioposicion(exchange,pair) > 0.0 and side=='SHORT': #posicion en long cambiar a short
            tr.cierrotodo(client,pair,exchange,'SELL') #cierro LONG
            tr.creoposicion (pair,client,size,'SELL') #CREO SHORT
            bot.send_text(pair+" - CREO POSICION "+ side)
        else:
            if tr.tamanioposicion(exchange,pair) < 0.0 and side=='LONG': # posicion en short cambiar a long
                tr.cierrotodo(client,pair,exchange,'BUY') #cierro SHORT
                tr.creoposicion (pair,client,size,'BUY') #CREO LONG
                bot.send_text(pair+" - CREO POSICION "+ side)


            