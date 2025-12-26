import os
import sys
import logging

# Konfiguration
REQUIRED_DIRS = [
    "backend",
    "backend/api/routers",
    "backend/services",
    "frontend",
    "frontend/js",
    "frontend/css"
]
REQUIRED_FILES = [
    "backend/main.py",
    "backend/config/config.json",
    "frontend/index.html",
    "frontend/package.json"
]

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("JANUS_HEALTH")

def check_structure():
    """Prüft, ob alle notwendigen Ordner und Dateien existieren."""
    logger.info("--- 1. Struktur-Check ---")
    missing = []
    for d in REQUIRED_DIRS:
        if not os.path.isdir(d):
            missing.append(f"Verzeichnis fehlt: {d}")
    
    for f in REQUIRED_FILES:
        if not os.path.isfile(f):
            missing.append(f"Datei fehlt: {f}")

    if missing:
        for m in missing:
            logger.error(m)
        return False
    logger.info("✅ Dateistruktur ist vollständig.")
    return True

def check_python_environment():
    """Prüft wichtige Python-Imports und fügt venv zum sys.path hinzu."""
    logger.info("--- 2. Backend-Umgebungs-Check ---")
    try:
        # Füge das site-packages Verzeichnis des venv zum sys.path hinzu
        venv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", "venv")
        site_packages_path = os.path.join(venv_path, "Lib", "site-packages")
        if site_packages_path not in sys.path:
            sys.path.insert(0, site_packages_path)
            logger.info(f"Manually added venv site-packages path to sys.path: {site_packages_path}")

        import fastapi
        import sqlalchemy
        import openai
        import google.generativeai # <-- Dies sollte jetzt die neue google-genai Bibliothek importieren
        from google.generativeai import types # <-- Prüfe auch das types Modul
        logger.info("✅ Wichtige Python-Bibliotheken gefunden.")
        return True
    except ImportError as e:
        logger.error(f"❌ Fehlende Bibliothek: {e}")
        return False

def check_backend_runnable():
    """Versucht, das Backend-Modul zu importieren (Syntax-Check)."""
    logger.info("--- 3. Backend-Import-Check ---")
    try:
        # Wir fügen das aktuelle Verzeichnis zum Pfad hinzu, damit 'backend' als Modul gefunden wird
        sys.path.insert(0, os.path.abspath("."))
        
        # Import-Versuch
        from backend.main import app
        logger.info("✅ Backend 'main.py' lässt sich fehlerfrei importieren.")
        return True
    except Exception as e:
        logger.error(f"❌ Backend-Code hat Fehler: {e}")
        return False

def run_health_check():
    print("\n🏥 JANUS GOLDSTANDARD HEALTH CHECK 🏥\n")
    
    checks = [
        check_structure(),
        check_python_environment(),
        check_backend_runnable()
    ]

    print("\n---------------------------------------")
    if all(checks):
        logger.info("🚀 SYSTEM STATUS: GRÜN. Janus ist bereit zum Start.")
        print("\nDu kannst das System jetzt starten:")
        print("  1. Backend:  cd backend; uvicorn main:app --reload --port 8001")
        print("  2. Frontend: cd frontend; npm start")
    else:
        logger.error("🔥 SYSTEM STATUS: ROT. Bitte Fehler oben prüfen.")

if __name__ == "__main__":
    run_health_check()