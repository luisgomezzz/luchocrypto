import sys, os
sys.path.insert(1,'./')
from playsound import playsound
import variables as var

pathroot=os.path.dirname(os.path.abspath(__file__))+'/'
pathsound=pathroot+'sounds/'

print(pathroot)


with open(os.path.join(pathroot, var.operandofile), 'r') as filehandle:
    operando = [current_place.rstrip() for current_place in filehandle.readlines()]