import json
import random
from gtts import gTTS
import os

def reproducir_pronunciacion(texto, idioma='en'):
    tts = gTTS(text=texto, lang=idioma, slow=False)
    tts.save("INGLES\pronunciacion.mp3")
    os.system("start INGLES\pronunciacion.mp3")

# Cargar el diccionario desde el archivo JSON
try:
    with open("INGLES\diccionario.json", "r") as archivo:
        diccionario = json.load(archivo)
except FileNotFoundError:
    print("El archivo 'diccionario.json' no se encontró.")
    exit()
except json.JSONDecodeError:
    print("Error al decodificar el contenido del archivo JSON.")
    exit()

# Elegir de forma aleatoria una clave del diccionario
oracion_elegida = random.choice(list(diccionario.keys()))

# Imprimir de forma aleatoria todos los elementos de la clave elegida
print(f"\nOración elegida: {oracion_elegida}")

# Pausar después de la oración elegida
input("...")

tiempos = diccionario[oracion_elegida]

# Mezclar de forma aleatoria los tiempos verbales
tiempos_mezclados = random.sample(list(tiempos.keys()), len(tiempos))

for tiempo in tiempos_mezclados:
    print(f"\n  Tiempo: {tiempo}")

    # Pausar después de cada tiempo verbal
    input("...")

    formas = tiempos[tiempo]
    
    # Mezclar de forma aleatoria los tipos de formas verbales
    formas_mezcladas = random.sample(list(formas.keys()), len(formas))
    
    for tipo in formas_mezcladas:
        # Imprimir la etiqueta antes de la oración
        print(f"    {tipo.capitalize()}:")
        
        # Pausar antes de imprimir la oración
        input("Presiona Enter para ver la oración...")

        # Imprimir la oración correspondiente
        print(f"      {formas[tipo]}")

        # Reproducir la pronunciación en inglés
        reproducir_pronunciacion(formas[tipo])

        # Pausar después de cada tipo de forma verbal
        input("...")
