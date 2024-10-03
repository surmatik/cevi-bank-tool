# Basis-Image verwenden
FROM python:3.9-slim

# Arbeitsverzeichnis festlegen
WORKDIR /app

# Abhängigkeiten kopieren
COPY requirements.txt .

# Installiere Python-Abhängigkeiten
RUN pip install --no-cache-dir -r requirements.txt

# Quellcode der App kopieren
COPY . .

# Port 5000 freigeben (Standard-Flask-Port)
EXPOSE 5000

# Flask-Umgebung festlegen und App starten
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Startbefehl für Flask-App
CMD ["flask", "run", "--host=0.0.0.0"]
