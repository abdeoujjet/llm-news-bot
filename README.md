# 🗞️ Noticias Relevantes con IA

Este proyecto realiza un análisis automático de titulares de noticias de **cualquier periódico online** y selecciona los más relevantes usando modelos de lenguaje avanzados de código abierto. 

Las noticias seleccionadas son clasificadas por impacto, gravedad y relevancia, y se resumen de forma muy concisa para captar la atención del lector. El resultado se envia directamente a Telegram.

---

## ✨ ¿Qué hace este proyecto?

- Extrae titulares desde un portal de noticias (puedes adaptar la fuente).
- Filtra las noticias más relevantes mediante un modelo de lenguaje.
- Clasifica cada noticia por:
  - Categoría (`asesinato`, `robo`, `corrupción`, etc.)
  - Impacto emocional
  - Prioridad (`alta`, `media`, `baja`)
- Resume cada noticia en ~70 caracteres usando otro LLM.
- Envía las noticias a un canal o chat de Telegram.

---

## 💡 Ejemplo de uso

```python
from main import get_news_ultima_hora

url = "https://www.ejemplo-de-periodico.com/sucesos.html"
noticias_procesadas = get_news_ultima_hora(url)
```

---

## 🧠 Modelos de lenguaje usados

El proyecto está pensado para funcionar con modelos open-source ejecutados en local a través de [Ollama](https://ollama.com/), como:

- `phi3:3.8b`
- `gemma3:4b`
- `wizardlm2:7b`
- `qwen2.5vl:3b`

Los modelos pueden configurarse fácilmente mediante variables `MODELO_RESUMEN` y `MODELO_FILTRO`.

---

## 📲 Envío a Telegram

El sistema permite el envío automático del resultado a un chat y canal de Telegram, fragmentando los mensajes si superan el límite de 4096 caracteres.

Solo necesitas configurar:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `CHANNEL_ID`

---

## 📌 Notas importantes

- Este proyecto usa como fuente una web de ejemplo (puede adaptarse a cualquier periódico).
- El scraping está diseñado con fines **educativos y demostrativos**.
- No se almacena ni redistribuye contenido original de terceros.

---

## 👨‍💻 Autor

Creado por **Abde Oujjet Moumen**  
[LinkedIn](https://www.linkedin.com/in/abde-oujjet-moumen-962402143/)

---
> ⚠️ Este proyecto no representa a ningún medio oficial. Está enfocado en mostrar cómo la inteligencia artificial puede utilizarse para seleccionar y resumir información relevante de forma automática.
