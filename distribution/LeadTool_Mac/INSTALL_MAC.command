#!/bin/bash
# ========================================
#   LeadTool - Mac Installation
#   Doppelklick zum Installieren!
# ========================================

clear
echo "========================================"
echo "   LeadTool - Mac Installation"
echo "   Lead Enrichment Tool v4.0"
echo "========================================"
echo ""

# Wechsel zum Skript-Verzeichnis
cd "$(dirname "$0")"
INSTALL_DIR="$(pwd)"

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}[1/5]${NC} Prüfe Voraussetzungen..."

# === PRÜFE PYTHON ===
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo -e "  ${GREEN}✓${NC} Python gefunden: $PYTHON_VERSION"
else
    echo -e "  ${RED}✗${NC} Python3 nicht gefunden!"
    echo ""
    echo "  Bitte installiere Python von:"
    echo "  https://www.python.org/downloads/"
    echo ""
    echo "  Oder mit Homebrew:"
    echo "  brew install python3"
    echo ""
    read -p "Drücke Enter zum Beenden..."
    exit 1
fi

# === ERSTELLE VIRTUAL ENVIRONMENT ===
echo ""
echo -e "${YELLOW}[2/5]${NC} Erstelle virtuelle Umgebung..."

if [ -d "venv" ]; then
    echo "  Lösche alte venv..."
    rm -rf venv
fi

python3 -m venv venv
if [ $? -ne 0 ]; then
    echo -e "  ${RED}✗${NC} Konnte venv nicht erstellen!"
    read -p "Drücke Enter zum Beenden..."
    exit 1
fi
echo -e "  ${GREEN}✓${NC} Virtuelle Umgebung erstellt"

# Aktiviere venv
source venv/bin/activate

# === INSTALLIERE ABHÄNGIGKEITEN ===
echo ""
echo -e "${YELLOW}[3/5]${NC} Installiere Abhängigkeiten..."
echo "  (Dies kann einige Minuten dauern...)"

pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

if [ $? -ne 0 ]; then
    echo -e "  ${RED}✗${NC} Installation fehlgeschlagen!"
    deactivate
    read -p "Drücke Enter zum Beenden..."
    exit 1
fi
echo -e "  ${GREEN}✓${NC} Alle Abhängigkeiten installiert"

# === ERSTELLE DATENBANK ===
echo ""
echo -e "${YELLOW}[4/5]${NC} Initialisiere Datenbank..."

python3 -c "
from models_v3 import DatabaseV3, seed_standard_tags
import os

db_path = 'lead_enrichment_v3.db'
if not os.path.exists(db_path):
    db = DatabaseV3(db_path)
    db.create_all()
    seed_standard_tags(db)
    print('  Datenbank erstellt!')
else:
    print('  Datenbank bereits vorhanden')
"

echo -e "  ${GREEN}✓${NC} Datenbank bereit"

# === ERSTELLE STARTER-SKRIPT ===
echo ""
echo -e "${YELLOW}[5/5]${NC} Erstelle Starter..."

cat > "LeadTool.command" << 'STARTER'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python3 gui_modern.py
STARTER

chmod +x "LeadTool.command"
echo -e "  ${GREEN}✓${NC} Starter erstellt"

# === ERSTELLE VERZEICHNISSE ===
mkdir -p logs uploads leads

# Deaktiviere venv
deactivate

# === FERTIG ===
echo ""
echo "========================================"
echo -e "  ${GREEN}INSTALLATION ERFOLGREICH!${NC}"
echo "========================================"
echo ""
echo "  Starte LeadTool mit Doppelklick auf:"
echo -e "  ${GREEN}LeadTool.command${NC}"
echo ""
echo "  WICHTIG - API-Key einrichten:"
echo "  1. Öffne die Datei '.env' mit TextEdit"
echo "  2. Trage deinen DeepSeek API-Key ein:"
echo "     DEEPSEEK_API_KEY=dein-key-hier"
echo ""
echo "========================================"
echo ""

# Frage ob App gestartet werden soll
read -p "Möchtest du LeadTool jetzt starten? (j/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Jj]$ ]]; then
    echo "Starte LeadTool..."
    source venv/bin/activate
    python3 gui_modern.py &
    deactivate
fi

echo ""
echo "Installation abgeschlossen!"
