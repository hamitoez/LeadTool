"""
First Run Setup - LeadTool
Wird beim ersten Start ausgeführt um die Datenbank zu initialisieren
"""
import os
import sys
import shutil


def get_app_dir():
    """Ermittelt das Anwendungsverzeichnis"""
    if getattr(sys, 'frozen', False):
        # PyInstaller Bundle
        return os.path.dirname(sys.executable)
    else:
        # Normale Python-Ausführung
        return os.path.dirname(os.path.abspath(__file__))


def setup_database():
    """Erstellt die Datenbank falls nicht vorhanden"""
    from models_v3 import DatabaseV3, seed_standard_tags

    app_dir = get_app_dir()
    db_path = os.path.join(app_dir, "lead_enrichment_v3.db")

    if not os.path.exists(db_path):
        print("📦 Erstelle neue Datenbank...")
        db = DatabaseV3(db_path)
        db.create_all()

        print("🏷️ Erstelle Standard-Tags...")
        seed_standard_tags(db)

        print("✅ Datenbank erfolgreich erstellt!")
        return True
    else:
        print("✅ Datenbank bereits vorhanden")
        return False


def setup_config_files():
    """Kopiert Konfigurationsdateien falls nicht vorhanden"""
    app_dir = get_app_dir()

    config_files = [
        'api_config.json',
        'compliment_prompts.json',
        'custom_prompts.json',
        'category_hierarchy.json',
    ]

    for filename in config_files:
        filepath = os.path.join(app_dir, filename)
        if not os.path.exists(filepath):
            # Suche nach Vorlage
            template_path = os.path.join(app_dir, f"{filename}.template")
            if os.path.exists(template_path):
                shutil.copy(template_path, filepath)
                print(f"📄 {filename} erstellt")


def setup_directories():
    """Erstellt benötigte Verzeichnisse"""
    app_dir = get_app_dir()

    directories = ['logs', 'uploads', 'leads']

    for dirname in directories:
        dirpath = os.path.join(app_dir, dirname)
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
            print(f"📁 Verzeichnis '{dirname}' erstellt")


def check_env_file():
    """Prüft ob .env Datei vorhanden ist und zeigt Warnung"""
    app_dir = get_app_dir()
    env_path = os.path.join(app_dir, ".env")
    env_example = os.path.join(app_dir, ".env.example")

    if not os.path.exists(env_path):
        print("")
        print("⚠️  WICHTIG: API-Key nicht konfiguriert!")
        print("   Optionen:")
        print("   1. Erstelle eine .env Datei mit: DEEPSEEK_API_KEY=dein-key")
        print("   2. Oder trage den Key direkt in api_config.json ein")
        print("")

        # Kopiere .env.example als Vorlage
        if os.path.exists(env_example) and not os.path.exists(env_path):
            # Erstelle leere .env als Platzhalter
            with open(env_path, 'w') as f:
                f.write("# API Keys\n")
                f.write("DEEPSEEK_API_KEY=\n")
                f.write("OPENAI_API_KEY=\n")
            print("   📄 Leere .env Datei erstellt - bitte API-Key eintragen!")

        return False
    return True


def run_first_time_setup():
    """Führt alle First-Run Setup-Schritte aus"""
    print("=" * 50)
    print("  LeadTool - Erste Einrichtung")
    print("=" * 50)
    print("")

    # 1. Verzeichnisse erstellen
    setup_directories()

    # 2. Datenbank erstellen
    setup_database()

    # 3. Config-Dateien prüfen
    setup_config_files()

    # 4. .env prüfen
    check_env_file()

    print("")
    print("=" * 50)
    print("  Einrichtung abgeschlossen!")
    print("=" * 50)
    print("")


if __name__ == "__main__":
    run_first_time_setup()
