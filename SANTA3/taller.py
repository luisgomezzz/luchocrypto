import sys, os
sys.path.insert(1,'./')
from playsound import playsound
import variables as var

pathroot=os.path.dirname(os.path.abspath(__file__))+'/'
pathsound=pathroot+'sounds/'

print(pathroot)


f = open(os.path.join(var.pathroot, var.lanzadorfile), 'w',encoding="utf-8")
f.write('prueba')
f.close() 