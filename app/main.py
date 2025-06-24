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
from typing import Optional


# Cargar variables del archivo .env
load_dotenv()
API_KEY = os.getenv("API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")
CACHE_FILE = os.getenv("CACHE_FILE")
PORTALS_FILE = os.getenv("PORTALS_FILE")

MODELO_RESUMEN = "phi3:3.8b"
# MODELO_RESUMEN = "gemma3:4b"
# MODELO_RESUMEN = "wizardlm2:7b"
# MODELO_RESUMEN = "qwen2.5vl:3b"

# MODELO_FILTRO = "phi3:3.8b"
MODELO_FILTRO = "gemma3:4b"
# MODELO_FILTRO = "wizardlm2:7b"
# MODELO_FILTRO = "qwen2.5vl:3b"



import feedparser
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# --- Scraper específico para UltimaHora (HTML) ---
def scrape_ultimahora(url: str):
    print(f"🔍 scrape_ultimahora: {url}")
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, 'html.parser')

    news = []
    for idx, c in enumerate(soup.select("div.news-item")):
        h = c.select_one("h2.news-heading, h3.news-heading")
        a = h and h.select_one("a[href]")
        if not a:
            continue
        news.append({
            "title": a.get_text(strip=True),
            "url":   urljoin(url, a["href"]),
            "id":    idx
        })
    print(f"  → {len(news)} noticias crudas de UltimaHora")
    return news

# --- Scraper genérico para feeds RSS ---
def scrape_rss(url: str):
    print(f"🔍 scrape_rss: {url}")
    feed = feedparser.parse(url)
    news = []
    for idx, entry in enumerate(feed.entries):
        title = entry.get("title", "").strip()
        link  = entry.get("link", "").strip()
        if not title or not link:
            continue
        news.append({"title": title, "url": link, "id": idx})
    print(f"  → {len(news)} noticias crudas de RSS")
    return news

# --- Función unificadora ---
def get_news_from_portal(url: str):
    """
    Elige scraper según tipo de portal:
      - UltimaHora (HTML)
      - Cualquier URL que contenga '/rss' → RSS
    Luego filtra+resume con selector_noticias_relevantes.
    """
    domain = urlparse(url).netloc.lower()
    if "ultimahora.es" in domain and not url.lower().endswith(".rss"):
        raw = scrape_ultimahora(url)
    else:
        # cubre todos los RSS: diariodemallorca, fibwidiario, etc.
        raw = scrape_rss(url)

    # Aquí llama a tu pipeline de filtrado + resumen
    return selector_noticias_relevantes(raw)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 


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
                        2. Seleccionar los 3 más relevantes según estos criterios:
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


def guardar_html(contenido: str, filename: str = "noticias.html") -> bool:
    """
    Guarda el contenido HTML de las noticias en un archivo local con un estilo básico.

    Args:
        contenido (str): HTML con las noticias (p. ej. lo que produce preparar_mensaje_telegram).
        filename (str): Nombre del archivo de salida.

    Returns:
        bool: True si el archivo se creó correctamente, False en caso contrario.
    """

    # Plantilla HTML con algo de CSS para que quede "bonito"
    html_template = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flash Noticias | Últimas actualizaciones</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=Roboto+Slab:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #2563eb;
            --secondary: #1e40af;
            --accent: #f59e0b;
            --light: #f8fafc;
            --dark: #1e293b;
            --gray: #64748b;
            --border: #e2e8f0;
            --card-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Poppins', sans-serif;
            background: #f0f4f8;
            color: var(--dark);
            line-height: 1.6;
            min-height: 100vh;
            padding: 2rem 1rem;
        }}
        
        .container {{
            max-width: 800px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            margin-bottom: 2.5rem;
            padding: 1rem;
        }}
        
        .header-content {{
            display: inline-flex;
            align-items: center;
            gap: 1rem;
            background: white;
            padding: 0.8rem 2rem;
            border-radius: 50px;
            box-shadow: var(--card-shadow);
            margin-bottom: 1rem;
        }}
        
        h1 {{
            font-family: 'Roboto Slab', serif;
            font-size: 2.2rem;
            font-weight: 600;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .news-container {{
            display: flex;
            flex-direction: column;
            gap: 1.8rem;
        }}
        
        .news-card {{
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: var(--card-shadow);
            transition: all 0.3s ease;
        }}
        
        .news-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12);
        }}
        
        .card-header {{
            padding: 1.2rem 1.5rem;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
        }}
        
        .card-header h2 {{
            font-size: 1.3rem;
            margin-bottom: 0.3rem;
        }}
        
        .news-card a {{
            color: white;
            text-decoration: none;
            transition: all 0.2s;
            display: block;
        }}
        
        .news-card a:hover {{
            color: var(--accent);
        }}
        
        .card-body {{
            padding: 1.5rem;
        }}
        
        .news-content {{
            margin-bottom: 1.2rem;
            color: #444;
            line-height: 1.7;
        }}
        
        .card-footer {{
            display: flex;
            justify-content: space-between;
            padding: 0.8rem 1.5rem;
            background-color: #f8fafc;
            border-top: 1px solid var(--border);
            font-size: 0.85rem;
            color: var(--gray);
        }}
        
        .source-badge {{
            background: var(--accent);
            color: white;
            font-weight: 500;
            padding: 0.25rem 0.8rem;
            border-radius: 20px;
            font-size: 0.8rem;
        }}
        
        .date {{
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }}
        
        .icon {{
            font-size: 1.2rem;
            vertical-align: middle;
            margin-right: 0.5rem;
            color: var(--accent);
        }}
        
        footer {{
            text-align: center;
            margin-top: 3.5rem;
            padding: 1.5rem;
            color: var(--gray);
            font-size: 0.9rem;
        }}
        
        @media (max-width: 768px) {{
            h1 {{
                font-size: 1.8rem;
            }}
            
            .header-content {{
                padding: 0.6rem 1.5rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="header-content">
                <i class="fas fa-newspaper fa-2x icon"></i>
                <h1>Flash Noticias</h1>
            </div>
            <p style="margin-top: 0.8rem; color: var(--gray); font-style: italic; font-size: 0.95rem;">
                Actualizado al minuto con las últimas novedades
            </p>
        </header>
        
        <div class="news-container">
            {contenido}
        </div>
        
        <footer>
            <p>© 2023 Flash Noticias | Fuentes verificadas</p>
            <p style="margin-top: 0.5rem;">
                <i class="fab fa-twitter"></i> 
                <i class="fab fa-facebook"></i> 
                <i class="fab fa-instagram"></i>
            </p>
        </footer>
    </div>
</body>
</html>"""


    try:
        # Asegurarse de que el directorio existe
        os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_template)

        print(f"✅ Archivo HTML guardado en: {filename}")
        return True

    except Exception as e:
        print(f"❌ Error al guardar HTML: {e}")
        return False



def load_portals(filename: str = PORTALS_FILE) -> list:
    """
    Lee un fichero JSON que contenga directamente una lista de URLs,
    o un objeto con clave "portales": [...]
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"No existe el fichero de portales: {filename}")
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "portales" in data:
        return data["portales"]
    if isinstance(data, list):
        return data
    raise ValueError(f"Formato no válido en {filename}. Debe ser lista o {{'portales': [...]}}")

def cache_message(mensaje: str, filename: str = CACHE_FILE) -> None:
    os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump({"mensaje": mensaje}, f, ensure_ascii=False)

def load_cached_message(filename: str = CACHE_FILE) -> Optional[str]:
    """
    Si existe el fichero de caché, devuelve el mensaje guardado. Si no, devuelve None.
    """
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f).get("mensaje")
    return None


# if __name__ == "__main__":
#     # 1) Intentamos cargar mensaje de caché
#     mensaje = load_cached_message()
#     if mensaje is None:
#         # 2) Si no existe, recorremos todos los portales
#         portals = load_portals()
#         todas_noticias = []
#         for portal in portals:
#             print(f"▶️ Procesando portal: {portal}")
#             noticias = get_news_ultima_hora(portal)
#             if noticias:
#                 todas_noticias.extend(noticias)

#         # 3) Eliminamos duplicados por URL
#         seen_urls = set()
#         unique_noticias = []
#         for n in todas_noticias:
#             if n["url"] not in seen_urls:
#                 unique_noticias.append(n)
#                 seen_urls.add(n["url"])

#         # 4) Preparamos el mensaje y lo guardamos en caché
#         mensaje = preparar_mensaje_telegram(unique_noticias)
#         cache_message(mensaje)
#         print("✅ Mensaje generado y cacheado")
#     else:
#         print("✅ Mensaje cargado desde caché")

#     # 5) Guardamos el HTML final
#     guardar_html(mensaje, filename="noticias.html")
#     print("✅ HTML actualizado: noticias.html")
 

if __name__ == "__main__":
    MAX_RESUMEN_LEN = 200  # numero de caracteres como máximo

    with open("news_portals.json", "r", encoding="utf-8") as f:
        portals = json.load(f)["portales"]

    todas_noticias = []
    for portal in portals:
        try:
            print(f"▶️ Procesando {portal}")
            noticias = get_news_from_portal(portal)
            if noticias:
                todas_noticias.extend(noticias)
        except Exception as e:
            print(f"⚠️ Error en {portal}: {e}")

    if not todas_noticias:
        print("❌ No se encontraron noticias relevantes")
        exit(1)

    # 3) Eliminar duplicados por URL
    seen = set(); unique = []
    for n in todas_noticias:
        if n["url"] not in seen:
            seen.add(n["url"])
            unique.append(n)

    # 4) Filtrar resúmenes vacíos o demasiado largos
    filtered = []
    for n in unique:
        resumen = n.get("resumen_breve", "") or ""
        if resumen and len(resumen) <= MAX_RESUMEN_LEN:
            filtered.append(n)
        else:
            print(f"❌ Descartada (resumen inválido): {n.get('titulo')}")

    if not filtered:
        print("❌ No quedan noticias con resúmenes válidos")
        exit(1)

    # 5) Preparar y guardar
    mensaje = preparar_mensaje_telegram(filtered)
    guardar_html(mensaje, filename="noticias.html")
    # enviar_telegram(mensaje)
    print("✅ HTML actualizado: noticias.html")
