FROM python:3.10-slim

# Dépendances système pour PostGIS et l'informatique scientifique
RUN apt-get update && apt-get install -y \
    libpq-dev gcc g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Script de démarrage
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]