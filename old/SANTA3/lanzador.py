import sys
sys.path.insert(1,'./')
import santa3 as san
import asyncio
par='API3USDT'
distanciaentrecompensaciones = 1.7
porcentajeentrada = 8
lado='BUY'
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
#san.trading(par,lado,porcentajeentrada,distanciaentrecompensaciones)
loop.run_until_complete(san.updating(par,lado))