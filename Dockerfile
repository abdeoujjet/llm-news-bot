FROM python:3.13-slim

# Instalar compiladores y dependencias
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    musl-dev \
    libffi-dev \
    libpq-dev \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Comando para arrancar la app
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
