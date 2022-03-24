#binancetrader
import utilidades as ut
from binance.client import Client

binance_api="N7yU75L3CNJg2RW0TcJBAW2cUjhPGvyuSFUgnRHvMSMMiS8WpZ8Yd8yn70evqKl0"
binance_secret="2HfMkleskGwTb6KQn0AKUQfjBDd5dArBW3Ykd2uTeOiv9VZ6qSU2L1yWM1ZlQ5RH"
client = Client(binance_api, binance_secret)

def binancetrader(pair,side,bot):
    # Si no hay posiciones la creo. 
    porcentajeentrada=2200
    exchange=ut.binanceexchange(binance_api,binance_secret)
    micapital = float(exchange.fetch_balance()['info']['totalWalletBalance'])
    size = (micapital*porcentajeentrada/100)/(float(client.get_symbol_ticker(symbol=pair)["price"]))
    try:
        if float(exchange.fetch_balance()['info']['totalPositionInitialMargin'])==0.0: #si no hay posiciones abiertas creo la alertada.
            if ut.binancecreoposicion (pair,client,size,side)==True:

                currentprice = float(client.get_symbol_ticker(symbol=pair)["price"]) 

                if side =='BUY':
                    stopprice = currentprice-(currentprice*1/100)
                else:
                    stopprice = currentprice+(currentprice*1/100)

                ut.binancestoploss (pair,client,side,stopprice)

                if ut.binancetakeprofit(pair,client,side,porc=0.20)==True:
                    bot.send_text(pair+" - TAKE_PROFIT_MARKET created "+ side)
    except:
        pass           