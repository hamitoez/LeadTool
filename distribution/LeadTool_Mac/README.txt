========================================
  LeadTool v4.0 - Mac
  Lead Enrichment Tool
========================================

INSTALLATION:
-------------
1. Kopiere den gesamten Ordner an einen beliebigen Ort
   (z.B. Desktop oder Programme)

2. Öffne Terminal und führe aus:
   chmod +x INSTALL_MAC.command

3. Doppelklick auf "INSTALL_MAC.command"
   (Bei Sicherheitswarnung: Rechtsklick -> Öffnen)

4. Die Installation dauert ca. 2-3 Minuten

5. Nach der Installation: Doppelklick auf "LeadTool.command"


ALTERNATIVE INSTALLATION (Terminal):
------------------------------------
cd /pfad/zum/LeadTool_Mac
chmod +x INSTALL_MAC.command
./INSTALL_MAC.command


API-KEY EINRICHTEN:
-------------------
Damit die KI-Funktionen arbeiten, benötigst du einen DeepSeek API-Key:

1. Öffne die Datei ".env" mit TextEdit
2. Ersetze die leere Zeile:
   DEEPSEEK_API_KEY=DEIN-API-KEY-HIER

3. Speichern und LeadTool neu starten

API-Key erhältst du unter: https://platform.deepseek.com/


VORAUSSETZUNGEN:
----------------
- macOS 10.14 oder neuer
- Python 3.9+ (wird bei Installation geprüft)
- Internetverbindung für Installation


FEATURES:
---------
- CSV Import von Leads
- Impressum-Scraping (Namen + E-Mail)
- KI-generierte Komplimente
- KI-Spalten (Clay.com Style)
- Export für Mailmerge


PROBLEMLÖSUNG:
--------------
"App kann nicht geöffnet werden":
-> Rechtsklick auf die Datei -> "Öffnen"

"Python nicht gefunden":
-> Installiere Python von python.org
-> Oder: brew install python3

"Permission denied":
-> Terminal: chmod +x *.command


SUPPORT:
--------
Bei Fragen wende dich an den Entwickler.

========================================
