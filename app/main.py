# importar librerias
import os
import requests
import json
from typing import List
from bs4 import BeautifulSoup
from IPython.display import Markdown, display, update_display
from urllib.parse import urljoin
from openai import OpenAI
import pandas as pd
from readability import Document
from dotenv import load_dotenv  # para cargar el archivo .env
from concurrent.futures import ThreadPoolExecutor


# Cargar variables del archivo .env
load_dotenv()
API_KEY = os.getenv("API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")

MODELO_RESUMEN = "phi3:3.8b"
# MODELO_RESUMEN = "gemma3:4b"
# MODELO_RESUMEN = "wizardlm2:7b"
# MODELO_RESUMEN = "qwen2.5vl:3b"

# MODELO_FILTRO = "phi3:3.8b"
MODELO_FILTRO = "gemma3:4b"
# MODELO_FILTRO = "wizardlm2:7b"
# MODELO_FILTRO = "qwen2.5vl:3b"

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
        noticas_final = selector_noticias_relevantes(news_list)
        return noticas_final

    except requests.exceptions.RequestException as e:
        print(f"Error de conexión: {e}")
        return None
    except Exception as e:
        print(f"Error: {e}")    
        return None


def obtener_noticia(url):
    """
    Dada una URL, realiza scraping del contenido principal de la noticia
    y devuelve el texto limpio para ser resumido posteriormente.
    """
    if url:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            # Extraer HTML limpio con Readability
            doc = Document(response.text)
            html_limpio = doc.summary()

            # Parsear con BeautifulSoup para limpiar etiquetas
            soup = BeautifulSoup(html_limpio, 'html.parser')
            texto = soup.get_text(separator='\n')

            # Limpiar espacios en blanco
            texto = '\n'.join([line.strip() for line in texto.splitlines() if line.strip()])

            return texto

        except Exception as e:
            print("[ERROR] ", e)
            return ""
    else:
        return None


def resumir_web(url , modelo):
    texto = obtener_noticia(url)
    if texto:
        # Creamos el mensaje para el modelo
        msg = [
        {
            "role": "system",
            "content": """Eres un editor experto en análisis de noticias. Tu tarea es resumir la 
                        noticia al maximo, de unos aproximadamente 70 caracteres, captando la 
                        atencion del lector. No debes inventar nada, ni ser sensacionalista,
                        pero si debes intentar captar la atencion del lector con el resumen
                        maximo posible.
                        """
        },
        {
            "role": "user",
            "content": f"LISTA DE TITULARES:\n{texto}"
        }
        ]

        print(" - M * * * * * Comienza resumen")
        print(texto)
        # Enviamos el mensaje al modelo junto al texto para resumirlo
        response = modelo.chat.completions.create(
        model=MODELO_RESUMEN,
        messages=msg
        )
        # print(response.choices[0].message.content)

        return response.choices[0].message.content
    else:
        return None


def selector_noticias_relevantes(news_list):
    # cargamos el modelo filtrador
    modelo_filtro_titulos = OpenAI( base_url="http://localhost:11434/v1" , api_key = API_KEY)

    # Crear lista simplificada con solo title e id para ahorrar tiempo y tokens
    datos_simplificados = [
        {"title": item["title"], "id": item["id"]}
        for item in news_list
    ]
    print("* * * * * Datos simplificados")

    msg = [
        {
            "role": "system",
            "content": """Eres un editor experto en análisis de noticias que escribe estructuras JSON. Tu tarea es:
            
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
                        ]
                        """
        },
        {
            "role": "user",
            # "content": f"LISTA DE TITULARES:\n{datos_simplificados}"
            "content": f"{datos_simplificados}"

        }
    ]

    print(" - M * * * * * Comienza modelo filtrado")
    print(datos_simplificados)
    # obtenemos JSON con los filtros mas relevantes y si id
    response = modelo_filtro_titulos.chat.completions.create(
        model=MODELO_FILTRO,
        messages=msg,
        response_format={"type": "json_object"}  # forzar al modelo a que devulva un json
    )

    # respuesta_modelo = json.loads(response.choices[0].message.content)

    try:
        respuesta_modelo = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError as e:
        print("Error en la respuesta del modelo:", e)
        return response.choices[0].message.content

    # crear una variable auxiliar para unificar los titulos con la informacion de la noticia
    link_por_id = {noticia['id']: noticia['url'] for noticia in news_list}

    # añadir el link a cada entrada en respuesta_modelo
    for entrada in respuesta_modelo['noticias_relevantes']:
        noticia_id = entrada['id']
        if noticia_id in link_por_id:
            entrada['url'] = link_por_id[noticia_id]
        else:
            entrada['url'] = None

    # obtener JSON con el resumen añadido
    modelo_resumen_noticia = OpenAI( base_url="http://localhost:11434/v1" , api_key = API_KEY)

    print(" - M * * * * *  Comienza resumen web: ")

    for noticias in respuesta_modelo['noticias_relevantes']:
        # noticias['resumen_breve'] = resumir_web(noticias['url'] , modelo_resumen_noticia)
        resumen = resumir_web(noticias['url'] , modelo_resumen_noticia)
        noticias['resumen_breve'] = resumen if resumen else "[Resumen no disponible]"

    return respuesta_modelo['noticias_relevantes']


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  
def enviar_telegram(contenido: str):
    """
    Envía mensajes a Telegram (tanto a usuario como a canal), dividiéndolo en partes si supera los 4096 caracteres.

    Args:
        contenido (str): Texto a enviar
    """
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID or not CHANNEL_ID:
        print("⚠️ Credenciales de Telegram no configuradas")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        chat_ids = [TELEGRAM_CHAT_ID, CHANNEL_ID]

        # Divide el contenido en bloques de hasta 4096 caracteres sin cortar etiquetas HTML
        max_length = 4096
        partes = []
        while len(contenido) > max_length:
            # Busca el último salto de línea antes del límite
            corte = contenido.rfind('\n', 0, max_length)
            if corte == -1:
                corte = max_length  # Si no hay saltos, corta directamente
            partes.append(contenido[:corte])
            contenido = contenido[corte:]
        partes.append(contenido)  # Agrega la última parte

        for chat_id in chat_ids:
            for i, parte in enumerate(partes):
                payload = {
                    "chat_id": chat_id,
                    "text": parte.strip(),
                    "parse_mode": "HTML"
                }
                response = requests.post(url, json=payload, timeout=10)
                response.raise_for_status()
                print(f"✅ Parte {i+1}/{len(partes)} enviada a {chat_id}")

        return True

    except Exception as e:
        print(f"❌ Error al enviar a Telegram: {str(e)}")
        return False




def preparar_mensaje_telegram(noticias: list) -> str:
    """Formatea las noticias para enviar por Telegram"""
    if not noticias:
        return "No hay noticias relevantes hoy"
    
    mensaje = "<b>📰 Últimas noticias relevantes</b>\n\n"
    for i, noticia in enumerate(noticias, 1):
        mensaje += (
            f"<b>🚨 Noticia {i}:</b> {noticia.get('titulo', 'Sin título')}\n"
            f"🔗 <a href='{noticia.get('url', '#')}'>Enlace</a>\n"
            f"📌 <b>Resumen:</b> {noticia.get('resumen_breve', 'Sin resumen')}\n"
            f"⚠️ <b>Prioridad:</b> {noticia.get('prioridad', 'No especificada').capitalize()}\n"
            f"⚠️ <b>Impacto:</b> {noticia.get('impacto_emocional', 'No especificado')}\n"
            f"----------------------------\n\n"
        )
    return mensaje




if __name__ == "__main__":
    print("* * * * * Comienzo programa ")
    noticias = get_news_ultima_hora("https://www.ultimahora.es/sucesos.html")

    if noticias:
        # Enviar a Telegram
        mensaje = preparar_mensaje_telegram(noticias)
        enviar_telegram(mensaje)  # Cambiar a True para pruebas
        
        print("\nResumen de noticias enviado")
    else:
        print("No se encontraron noticias relevantes")
