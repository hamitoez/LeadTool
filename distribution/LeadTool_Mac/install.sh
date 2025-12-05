#!/bin/bash
# LeadTool Installer - Einfache Version

echo ""
echo "========================================"
echo "  LeadTool Installation"
echo "========================================"
echo ""

cd "$(dirname "$0")"

# Python Check
if ! command -v python3 &> /dev/null; then
    echo "FEHLER: Python3 nicht installiert!"
    echo "Installiere von: https://www.python.org/downloads/"
    exit 1
fi

echo "[1/4] Python gefunden: $(python3 --version)"

# Venv erstellen
echo "[2/4] Erstelle Umgebung..."
python3 -m venv venv
source venv/bin/activate

# Dependencies installieren
echo "[3/4] Installiere Pakete (dauert 1-2 Min)..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Datenbank erstellen
echo "[4/4] Erstelle Datenbank..."
python3 -c "
from models_v3 import DatabaseV3, seed_standard_tags
db = DatabaseV3('lead_enrichment_v3.db')
db.create_all()
seed_standard_tags(db)
"

# Starter erstellen
echo '#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python3 gui_modern.py' > start.sh
chmod +x start.sh

deactivate

echo ""
echo "========================================"
echo "  FERTIG!"
echo "========================================"
echo ""
echo "Starten mit: ./start.sh"
echo ""
echo "WICHTIG: API-Key in .env eintragen!"
echo ""
