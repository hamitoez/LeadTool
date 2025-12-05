#!/bin/bash
# ========================================
#   LeadTool - Mac Build
#   Erstellt eine standalone .app
# ========================================

echo "========================================"
echo "  LeadTool - Mac Build"
echo "  Erstellt eine standalone .app"
echo "========================================"
echo ""

# Wechsel zum Skript-Verzeichnis
cd "$(dirname "$0")"

# === PRÜFE PYTHON ===
if ! command -v python3 &> /dev/null; then
    echo "[FEHLER] Python3 nicht gefunden!"
    echo "Bitte installiere Python von https://www.python.org/downloads/"
    exit 1
fi

echo "[OK] Python gefunden"
python3 --version
echo ""

# === ERSTELLE VIRTUAL ENVIRONMENT ===
if [ ! -d "venv_build" ]; then
    echo "[1/5] Erstelle Build-Environment..."
    python3 -m venv venv_build
fi

# Aktiviere venv
source venv_build/bin/activate

# === INSTALLIERE PYINSTALLER ===
echo "[2/5] Installiere PyInstaller..."
pip install --upgrade pip --quiet
pip install pyinstaller --quiet

if [ $? -ne 0 ]; then
    echo "[FEHLER] PyInstaller konnte nicht installiert werden!"
    exit 1
fi
echo "[OK] PyInstaller installiert"
echo ""

# === INSTALLIERE ABHÄNGIGKEITEN ===
echo "[3/5] Installiere Abhängigkeiten..."
pip install -r requirements.txt --quiet
echo "[OK] Abhängigkeiten installiert"
echo ""

# === LÖSCHE ALTE BUILDS ===
echo "[4/5] Lösche alte Build-Dateien..."
rm -rf dist build
echo "[OK] Alte Builds gelöscht"
echo ""

# === STARTE BUILD ===
echo "[5/5] Erstelle Mac App..."
echo "Dies kann einige Minuten dauern..."
echo ""

pyinstaller LeadTool.spec --noconfirm

if [ $? -ne 0 ]; then
    echo ""
    echo "[FEHLER] Build fehlgeschlagen!"
    deactivate
    exit 1
fi

# Deaktiviere venv
deactivate

echo ""
echo "========================================"
echo "  BUILD ERFOLGREICH!"
echo "========================================"
echo ""
echo "Die App wurde erstellt unter:"
echo "  dist/LeadTool.app"
echo ""
echo "WICHTIG: Beim ersten Start:"
echo "  1. Die App erstellt automatisch eine neue Datenbank"
echo "  2. Kopiere deine .env Datei in den App-Ordner"
echo "  3. Oder trage den API-Key in api_config.json ein"
echo ""

# === ÖFFNE DIST-ORDNER ===
open dist

echo "Drücke Enter zum Beenden..."
read
