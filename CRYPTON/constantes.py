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

api_key="NYRJeyPdSulRAL1Chx79V36zXcZ6TmhKGZGkoU2vQSq9elCyJqjq8c8ixywv5Yn0"
api_secret="5Omvt1ChDkW0ddH51s8X6tXb4rei6TfL3kCllnDFl2Tm3Q3noECOyL6uVzBpxMqJ"
api_passphares=''
cliente = Client(api_key, api_secret,api_passphares)

margen = 'CROSSED'
