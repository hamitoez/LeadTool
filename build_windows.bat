@echo off
chcp 65001 > nul
echo ========================================
echo   LeadTool - Windows Build
echo   Erstellt eine standalone EXE
echo ========================================
echo.

cd /d "%~dp0"

REM === PRÜFE PYTHON ===
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [FEHLER] Python nicht gefunden!
    echo Bitte installiere Python von https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python gefunden
python --version
echo.

REM === INSTALLIERE PYINSTALLER ===
echo [1/4] Installiere PyInstaller...
pip install pyinstaller --quiet
if %errorlevel% neq 0 (
    echo [FEHLER] PyInstaller konnte nicht installiert werden!
    pause
    exit /b 1
)
echo [OK] PyInstaller installiert
echo.

REM === INSTALLIERE ABHÄNGIGKEITEN ===
echo [2/4] Installiere Abhängigkeiten...
pip install -r requirements.txt --quiet
echo [OK] Abhängigkeiten installiert
echo.

REM === LÖSCHE ALTE BUILDS ===
echo [3/4] Lösche alte Build-Dateien...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
echo [OK] Alte Builds gelöscht
echo.

REM === STARTE BUILD ===
echo [4/4] Erstelle EXE...
echo Dies kann einige Minuten dauern...
echo.

pyinstaller LeadTool.spec --noconfirm

if %errorlevel% neq 0 (
    echo.
    echo [FEHLER] Build fehlgeschlagen!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   BUILD ERFOLGREICH!
echo ========================================
echo.
echo Die EXE-Datei wurde erstellt unter:
echo   dist\LeadTool.exe
echo.
echo WICHTIG: Beim ersten Start:
echo   1. Die App erstellt automatisch eine neue Datenbank
echo   2. Kopiere deine .env Datei in den gleichen Ordner
echo   3. Oder trage den API-Key in api_config.json ein
echo.

REM === ÖFFNE DIST-ORDNER ===
explorer dist

pause
