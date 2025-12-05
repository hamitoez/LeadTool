# LeadTool Web App - Deployment Guide

## DigitalOcean Deployment (Empfohlen)

### Option 1: Droplet mit Docker (Beste Option)

**1. Droplet erstellen:**
- Ubuntu 22.04
- $6/Monat (1GB RAM reicht)
- Docker Marketplace Image wählen

**2. Per SSH verbinden:**
```bash
ssh root@deine-ip
```

**3. Projekt hochladen:**
```bash
git clone https://github.com/dein-repo/leadtool.git
cd leadtool
```

**4. .env Datei erstellen:**
```bash
echo "DEEPSEEK_API_KEY=dein-api-key" > .env
```

**5. Mit Docker starten:**
```bash
docker-compose up -d
```

**6. Fertig!** App ist erreichbar unter `http://deine-ip:8501`

### Option 2: App Platform

1. GitHub Repo verbinden
2. "Python" als Typ wählen
3. Run Command: `streamlit run streamlit_app.py --server.port=8080`
4. Environment Variable hinzufügen: `DEEPSEEK_API_KEY`

---

## Lokal starten

### 1. Abhängigkeiten installieren
```bash
pip install -r requirements.txt
```

### 2. Web App starten
```bash
streamlit run streamlit_app.py
```

Die App öffnet sich automatisch im Browser unter `http://localhost:8501`

---

## Streamlit Cloud Deployment

### 1. Repository vorbereiten
Lade deinen Code auf GitHub hoch (öffentlich oder privat).

### 2. Streamlit Cloud
1. Gehe zu [share.streamlit.io](https://share.streamlit.io)
2. Melde dich mit GitHub an
3. Klicke auf "New app"
4. Wähle dein Repository
5. Wähle `streamlit_app.py` als Main file
6. Klicke "Deploy"

### 3. Secrets konfigurieren
In Streamlit Cloud unter "Settings" > "Secrets":

```toml
DEEPSEEK_API_KEY = "dein-api-key-hier"
```

### 4. Requirements anpassen
Für Streamlit Cloud die `requirements_web.txt` verwenden:
- Benenne `requirements_web.txt` in `requirements.txt` um
- Oder erstelle eine `requirements.txt` mit dem Inhalt von `requirements_web.txt`

**Wichtig:** Selenium funktioniert auf Streamlit Cloud nicht!
Das Impressum-Scraping ist daher eingeschränkt.

---

## Alternative: Eigener Server

### Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Docker Compose
```yaml
version: '3.8'
services:
  leadtool:
    build: .
    ports:
      - "8501:8501"
    environment:
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
    volumes:
      - ./data:/app/data
```

---

## Funktionen

| Feature | Lokal | Streamlit Cloud |
|---------|-------|-----------------|
| CSV Import | ✅ | ✅ |
| Lead Filter | ✅ | ✅ |
| KI-Komplimente | ✅ | ✅ |
| Export CSV | ✅ | ✅ |
| Impressum Scraping | ✅ | ⚠️ Eingeschränkt |

---

## Tipps

1. **Datenbank**: SQLite wird lokal gespeichert. Bei Streamlit Cloud geht sie bei Neustart verloren!
   Für persistente Daten externe Datenbank nutzen (z.B. PostgreSQL).

2. **API Keys**: Niemals im Code speichern! Immer über Umgebungsvariablen oder Secrets.

3. **Performance**: Bei vielen Leads kann die Anwendung langsamer werden.
   Pagination und Limits nutzen.
