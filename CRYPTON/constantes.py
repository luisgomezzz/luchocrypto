from os import system, name
import os
from binance.client import Client 

pathroot=os.path.dirname(os.path.abspath(__file__))+'/'

def clear():  
    # for windows
    if name == 'nt':
        _ = system('cls')
    # for mac and linux(here, os.name is 'posix')
    else:
        _ = system('clear')

clear() #limpia terminal        

api_key="qReDQIVrlOiPUBG8EdflTSmymj2aUaaGMBP6u0RzRylUAo3sisHX6c7K9TKTKVt3"
api_secret="8aYWkwSKJHQhmkPFsIl66wPHk8rk3k28GiMFe9i82I7KvdQhbWea2CaUqO6Wd9Rv"
api_passphares=''
cliente = Client(api_key, api_secret,api_passphares)

margen = 'CROSSED'
