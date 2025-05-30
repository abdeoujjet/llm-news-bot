from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from openai import OpenAI
from readability import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

load_dotenv()
API_KEY = os.getenv("API_KEY")

app = FastAPI(title="API de noticias Mallorca")



def get_news_ultima_hora(url: str):
    print("Dentro de get_news_ultima_hora")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        news_list = []
        seen_titles = set()
        seen_urls = set()
        id_counter = 0

        for a_tag in soup.find_all('a', href=True):
            text = a_tag.get_text(strip=True)
            href = a_tag['href']

            # Validaciones
            if not text or len(text) < 30:
                continue
            if not href or href.startswith('#'):
                continue

            full_url = urljoin(url, href)

            if text in seen_titles or full_url in seen_urls:
                continue

            news_list.append({
                'title': text,
                'url': full_url,
                'id': id_counter
            })

            seen_titles.add(text)
            seen_urls.add(full_url)
            id_counter += 1
        print(" - - -  - - -  - - -  - - -  - - -  - - -  - - -  - - -  - - -  - - -  - - - ")
        print(f"Total noticias encontradas: {len(news_list)}")
        noticias_relevantes  = selector_noticias_relevantes(news_list)
        return noticias_relevantes 

    except requests.exceptions.RequestException as e:
        print("Error de conexión:", e)
        raise HTTPException(status_code=503, detail=f"Error de conexión: {e}")
    except Exception as e:
        print("Error general:", e)
        raise HTTPException(status_code=500, detail=f"Error: {e}")



def obtener_noticia(url):
    if url:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            doc = Document(response.text)
            html_limpio = doc.summary()
            soup = BeautifulSoup(html_limpio, 'html.parser')
            texto = soup.get_text(separator='\n')
            texto = '\n'.join([line.strip() for line in texto.splitlines() if line.strip()])
            return texto

        except Exception:
            return ""
    else:
        return None

def resumir_web(url, modelo):
    print(" - - -  - - -  - - -  - - -  - - -  - - -  - - -  - - -  - - -  - - -  - - - ")
    print("Dentro de resumir_web")
    texto = obtener_noticia(url)
    if texto:
        msg = [
            {
                "role": "system",
                "content": """Eres un editor experto en análisis de noticias. Tu tarea es resumir la 
                            noticia al maximo, resumelo en unos 120 caracteres, captando la 
                            atencion del lector y dejando muy claro quien protagoniza la noticia, que es lo que pasa exactamente y donde.
                            No debes inventar nada, ni ser sensacionalista. Solamente resumelo dejando claro exactamente lo que pasa en la noticia."""
            },
            {
                "role": "user",
                "content": f"LISTA DE TITULARES:\n{texto}"
            }
        ]
        response = modelo.chat.completions.create(
            model="gemma3:4b",
            messages=msg
        )
        print(" - - -  - - -  - - -  - - -  - - -  - - -  - - -  - - -  - - -  - - -  - - - ")
        print("response.choices[0].message.content: " , response.choices[0].message.content)
        return response.choices[0].message.content
    else:
        return None

def selector_noticias_relevantes(news_list):
    modelo_filtro_titulos = OpenAI(base_url="http://localhost:11434/v1", api_key=API_KEY)
    datos_simplificados = [{"title": item["title"], "id": item["id"]} for item in news_list]

    msg = [
        {
            "role": "system",
            "content": """Eres un editor experto en análisis de noticias. Tu tarea es:
                        1. Analizar esta lista de titulares de noticias
                        2. Seleccionar los 10 más relevantes según estos criterios:
                        - Impacto social
                        - Gravedad del suceso
                        - Relevancia pública
                        - Novedad del acontecimiento

                        REQUISITOS DE RESPUESTA:
                        - Devuelve ÚNICAMENTE un array JSON válido, sin comentario adicionales ni nada mas.
                        - Usa EXACTAMENTE los mismos títulos recibidos
                        - Devuelve exactamente el mismo id relacionado al título de la noticia
                        - Estructura exacta requerida:
                        "noticias_relevantes": [
                                {
                            "titulo": "Texto exacto del titular original",
                            "categoria": "asesinato|violencia|robo|accidente|corrupción|otros",
                            "id": id exacto de la noticia,
                            "impacto_emocional": 0-10,
                            "prioridad": "alta|media|baja"
                            },
                        ]"""
        },
        {
            "role": "user",
            "content": f"{datos_simplificados}"
        }
    ]
    print(" - - -  - - -  - - -  - - -  - - -  - - -  - - -  - - -  - - -  - - -  - - - ")
    print("Modelo datos_simplificados: " , datos_simplificados)
    response = modelo_filtro_titulos.chat.completions.create(
        model="gemma3:4b",
        messages=msg,
        response_format={"type": "json_object"}
    )

    try:
        respuesta_modelo = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        return response.choices[0].message.content

    link_por_id = {noticia['id']: noticia['url'] for noticia in news_list}

    modelo_resumen_noticia = OpenAI(base_url="http://localhost:11434/v1", api_key=API_KEY)

    urls_vistas = set()
    noticias_filtradas = []

    for entrada in respuesta_modelo['noticias_relevantes']:
        noticia_id = entrada['id']
        entrada['url'] = link_por_id.get(noticia_id, None)

        if entrada['url'] and entrada['url'] not in urls_vistas:
            urls_vistas.add(entrada['url'])
            noticias_filtradas.append(entrada)

    # Hacer resúmenes solo de noticias con URLs únicas
    for entrada in noticias_filtradas:
        resumen = resumir_web(entrada['url'], modelo_resumen_noticia)
        entrada['resumen_breve'] = resumen if resumen else "[Resumen no disponible]"

    return noticias_filtradas


def prova(url):
    print(" - - -  - - -  - - -  - - -  - - -  - - -  - - -  - - -  - - -  - - -  - - - ")
    print("Recibida la url:", url)
    return url


@app.get("/noticias")
def api_get_noticias(url):
    print("- - - - Comienza - - - -")
    prova(url)
    noticias = get_news_ultima_hora(url)
    print(noticias)
    return noticias

