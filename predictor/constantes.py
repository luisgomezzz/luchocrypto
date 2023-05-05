from os import system, name
import os
import ccxt as ccxt
from binance.client import Client as binanceClient
from colors import *
import sys

RED   = "\033[1;31m"  
BLUE  = "\033[1;34m"
CYAN  = "\033[1;36m"
GREEN = "\033[0;32m"
RESET = "\033[0;0m"
BOLD    = "\033[;1m"
REVERSE = "\033[;7m"
YELLOW = "\33[33m"

sys.stdout.write(RED)
pathroot=os.path.dirname(os.path.abspath(__file__))+'/'

def clear():  
    # for windows
    if name == 'nt':
        _ = system('cls')
    # for mac and linux(here, os.name is 'posix')
    else:
        _ = system('clear')

##FILES
nombrelog = "log_finandy.txt"
f = open(os.path.join(pathroot, nombrelog), 'a',encoding="utf-8")
f.close() 

api_key="qycthSI8s5HH0b95MxH3lFKPPUeZu8mCSgztp00x2d7SdHmfOp2U9qBeCCbxPyDg"
api_secret="zeJqYkyWzBIdGDMmyfUnofQiThirgEgOCDYvS3rzcq4yle1afD7YEQkciCI43yNs"
api_passphares=''
exchange_name = 'binance'
client = binanceClient(api_key, api_secret,api_passphares)
exchange_class = getattr(ccxt, exchange_name)
exchange =   exchange_class({            
            'apiKey': api_key,
            'secret': api_secret,
            'password': api_passphares,
            'options': {  
            'defaultType': 'future',  
            },
            })

margen = 'CROSSED'

clear() #limpia terminal


