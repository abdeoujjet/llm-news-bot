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

MODELO_RESUMEN = "phi3:3.8b"
MODELO_FILTRO = "gemma3:4b"




def enviar_telegram(contenido: str, modo_test: bool = True):
    """
    Envía mensajes a Telegram con opción de modo test
    
    Args:
        contenido (str): Texto a enviar
        modo_test (bool): Si True, solo simula el envío
    """
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Credenciales de Telegram no configuradas")
        return False
    
    if modo_test:
        print("\n🔷 --- MODO TEST ACTIVADO ---")
        print(f"🔷 Mensaje:\n{contenido}")
        print("🔷 --- ENVÍO SIMULADO COMPLETADO ---")
        return True
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": contenido,
            "parse_mode": "HTML"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("✅ Mensaje enviado a Telegram")
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
            f"----------------------------\n\n"
        )
    return mensaje



import ast


if __name__ == "__main__":
    print("* * * * * Comienzo programa ")
    # noticias = get_news_ultima_hora("https://www.ultimahora.es/sucesos.html")
    with open(r"app\noticias.txt", "r", encoding="utf-8") as f:
        noticias = f.read()

    noticias = ast.literal_eval(noticias) 
    if noticias:
        # Guardar en JSON
        with open('app\noticias.json', 'w', encoding='utf-8') as f:
            json.dump(noticias, f, ensure_ascii=False, indent=2)
        
        # Enviar a Telegram
        mensaje = preparar_mensaje_telegram(noticias)
        enviar_telegram(mensaje, modo_test=False)  # Cambiar a True para pruebas
        
        print("\nResumen de noticias enviado")
    else:
        print("No se encontraron noticias relevantes")