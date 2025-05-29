# importar librerias
import os
import requests
import json
from typing import List
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from IPython.display import Markdown, display, update_display
from urllib.parse import urljoin
from openai import OpenAI
import pandas as pd
from readability import Document


def get_news_ultima_hora(url):
    # url de noticias de mallorca
    # url = "https://www.ultimahora.es/sucesos.html"
    id = 0
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        news_list = []

        # Encontrar todos los contenedores de noticias
        news_containers = soup.find_all('div', class_='news-item')

        for container in news_containers:
            # Extraer titulo
            title_element = container.find(['h2', 'h3'], class_='news-heading')
            if not title_element:
                continue

            link_element = title_element.find('a', href=True)
            if not link_element:
                continue

            title = title_element.get_text(strip=True)
            link = urljoin(url, link_element['href'])

            news_list.append({
                'title': title,
                'url': link,
                'id' : id
            })
            id = id + 1

        # Mostrar resultados
        print(f"Noticias encontradas: {len(news_list)}")
        return news_list

    except requests.exceptions.RequestException as e:
        print(f"Error de conexión: {e}")
        return None

    except Exception as e:
        print(f"Error: {e}")    
        return None



# if main == '__main__' :




