import json
import requests
from textblob import TextBlob
import time
import os
import constantes as cons

cryptos = ['BTC','ETH','XRP','EOS','LTC','ETC','LINK','ADA','BNB','ATOM','ONT','NEO','IOST','ZRX',
'DOGE','SXP','MKR','DOT','SOL','ICX','AVAX','FTM','FIL','MATIC','CHZ','SAND','LINA','C98','MASK','DYDX',
'GALA','KLAY','OP','INJ','STG','LDO','APT','CFX','ARB'
] # Lista de criptomonedas
filename = 'noticias.txt' # Archivo para guardar un registro de las noticias
f = open(os.path.join(cons.pathroot,filename), 'a', encoding="utf-8")
f.close() 

def get_news(crypto):
    url = f"https://cryptopanic.com/api/posts/?auth_token=bf5c32abc504095fe017190ab1e51082e52ae016&currencies={crypto}"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    data = json.loads(response.content.decode('utf-8'))
    news = []
    for result in data['results']:
        if 'title' in result and crypto in result['title']:
            title = result['title']
        else:
            title = ""
        if 'body' in result and crypto in result['body']:
            body = result['body']
        else:
            body = ""
        sentiment = TextBlob(title + ' ' + body).sentiment.polarity
        if sentiment > 0.3:
            signal = 'ALCISTA'
        elif sentiment < -0.3:
            signal = 'BAJISTA'
        else:
            signal = 'NEUTRAL'
        news.append({'title': title, 'url': result['url'], 'signal': signal})
    return news

def save_news(news, filename):
    with open(os.path.join(cons.pathroot, filename), 'a') as f:
        for item in news:
            f.write(item['title'] + '\n')

def load_news(filename):
    with open(os.path.join(cons.pathroot, filename), 'r') as f:
        lines = f.readlines()
        return set(line.strip() for line in lines)

seen_news = load_news(filename) # Cargar las noticias ya vistas

while True:
    for crypto in cryptos:
        news = get_news(crypto)
        if news:
            for item in news:
                if item['title'] not in seen_news: # Si la noticia no se ha visto antes
                    seen_news.add(item['title']) # Agregar la noticia al conjunto de noticias vistas
                    try:
                        save_news([item], filename) # Guardar la noticia en el archivo
                    except UnicodeEncodeError:
                        pass # Ignorar los caracteres que no se pueden codificar
                    if item['signal'] == 'ALCISTA':
                        print(f"Noticia alcista para {crypto}: {item['title']}")
                    elif item['signal'] == 'BAJISTA':
                        print(f"Noticia bajista para {crypto}: {item['title']}")
    time.sleep(30) # Esperar 5 minutos antes de buscar nuevas noticias
