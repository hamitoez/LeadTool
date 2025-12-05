"""
Build Configuration - Lead Enrichment Tool
Zentrale Konfiguration für PyInstaller Builds
"""

APP_NAME = "LeadTool"
APP_VERSION = "4.0.0"
APP_AUTHOR = "Lead Enrichment"
APP_DESCRIPTION = "Lead Enrichment Tool - Clay Alternative"

# Hauptdatei
MAIN_SCRIPT = "gui_modern.py"

# Dateien die EINGESCHLOSSEN werden sollen
INCLUDE_FILES = [
    # Konfigurationsdateien (als Vorlagen)
    ("api_config.json", "."),
    ("compliment_prompts.json", "."),
    ("custom_prompts.json", "."),
    ("category_hierarchy.json", "."),
    (".env.example", "."),
]

# Dateien die AUSGESCHLOSSEN werden sollen
EXCLUDE_FILES = [
    # Datenbank - User soll eigene erstellen
    "lead_enrichment_v3.db",
    "*.db",

    # Cache-Dateien
    "impressum_cache.json",

    # Persönliche Daten
    ".env",
    "leads.csv",

    # Entwicklungs-Dateien
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "venv",
    ".git",
    ".claude",

    # Uploads/Logs
    "uploads/*",
    "logs/*",
    "leads/*",
]

# Python Module die eingeschlossen werden müssen
HIDDEN_IMPORTS = [
    "customtkinter",
    "tkinter",
    "PIL",
    "PIL._tkinter_finder",
    "requests",
    "bs4",
    "selenium",
    "selenium.webdriver",
    "selenium.webdriver.chrome.options",
    "selenium.webdriver.chrome.service",
    "webdriver_manager",
    "webdriver_manager.chrome",
    "sqlalchemy",
    "sqlalchemy.orm",
    "sqlalchemy.ext.declarative",
    "lxml",
    "dotenv",
]

# Binäre Dateien die eingeschlossen werden müssen
BINARIES = []

# Icon-Dateien (falls vorhanden)
ICON_WINDOWS = "icon.ico"  # Falls vorhanden
ICON_MAC = "icon.icns"     # Falls vorhanden
