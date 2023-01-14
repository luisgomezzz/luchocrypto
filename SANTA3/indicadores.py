import pandas as pd
import util as ut

def PPSR(symbol,temporalidad='1d',ventana=15): #PIVOT POINTS STANDARD  
    data = ut.calculardf (symbol,temporalidad,ventana)
    PP = pd.Series((data['high'] + data['low'] + data['close']) / 3)  
    R1 = pd.Series(2 * PP - data['low'])  
    S1 = pd.Series(2 * PP - data['high'])  
    R2 = pd.Series(PP + data['high'] - data['low'])  
    S2 = pd.Series(PP - data['high'] + data['low'])  
    R3 = pd.Series(data['high'] + 2 * (PP - data['low']))  
    S3 = pd.Series(data['low'] - 2 * (data['high'] - PP)) 
    R4 = pd.Series(data['high'] + 3 * (PP - data['low']))  
    S4 = pd.Series(data['low'] - 3 * (data['high'] - PP))  
    R5 = pd.Series(data['high'] + 4 * (PP - data['low']))  
    S5 = pd.Series(data['low'] - 4 * (data['high'] - PP))      
    psr = {'PP':PP, 'R1':R1, 'S1':S1, 'R2':R2, 'S2':S2, 'R3':R3, 'S3':S3, 'R4':R4, 'S4':S4, 'R5':R5, 'S5':S5}  
    PSR = pd.DataFrame(psr)  
    return PSR.iloc[-2]