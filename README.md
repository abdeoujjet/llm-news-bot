# 🗞️ Relevant News with AI

This project performs an automatic analysis of news headlines from **any online newspaper** and selects the most relevant ones using advanced open-source language models.  

The selected news stories are classified by impact, severity, and relevance, and are summarized very concisely to capture the reader's attention. The result is sent directly to Telegram.

---

## ✨ What does this project do?

- Extracts headlines from a news portal (you can adapt the source).
- Filters the most relevant news using a language model.
- Classifies each news story by:
  - Category (`murder`, `theft`, `corruption`, etc.)
  - Emotional impact
  - Priority (`high`, `medium`, `low`)
- Summarizes each news story in ~70 characters using another LLM.
- Sends the news to a Telegram channel or chat.

---

## 💡 Example of use

```python
from main import get_news_ultima_hora

url = "https://www.ejemplo-de-periodico.com/sucesos.html"
noticias_procesadas = get_news_ultima_hora(url)
```

---

## 🧠 Language models used

The project is designed to work with open-source models run locally via [Ollama](https://ollama.com/), as:

- `phi3:3.8b`
- `gemma3:4b`
- `wizardlm2:7b`
- `qwen2.5vl:3b`

The models can be easily configured using the `MODELO_RESUMEN` and `MODELO_FILTRO`.

---

## 📲 Telegram delivery

The system allows automatic delivery of the results to a Telegram chat and channel, splitting messages if they exceed the 4096-character limit.

You only need to configure:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `CHANNEL_ID`

---

## 📌 Important notes

- This project uses an example website as a source (it can be adapted to any newspaper).

---

## 👨‍💻 Author

Created by **Abde Oujjet Moumen**  
[LinkedIn](https://www.linkedin.com/in/abde-oujjet-moumen-962402143/)
