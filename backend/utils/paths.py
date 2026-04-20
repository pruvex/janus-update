import sys
import os
from pathlib import Path

USER_DOCS_DIR = Path.home() / "Documents" / "JanusPDFs"
USER_DOCS_DIR.mkdir(parents=True, exist_ok=True)


def get_user_docs_dir() -> str:
    """Zentrale Location für alle vom Benutzer sichtbaren Janus-PDFs."""
    USER_DOCS_DIR.mkdir(parents=True, exist_ok=True)
    return str(USER_DOCS_DIR)


def get_app_data_dir():
    """
    Liefert IMMER den Pfad zum Roaming AppData Ordner des Users.
    Z.B. C:\\Users\\DeinName\\AppData\\Roaming\\Janus Projekt
    Hier haben wir immer Schreibrechte.
    """
    # 1. Hole den Standard Windows AppData Pfad
    app_data = os.getenv('APPDATA')
    
    # 2. Fallback für Entwicklung oder nicht-Windows (Home-Verzeichnis)
    if not app_data:
        app_data = os.path.expanduser("~")
    
    # 3. Erstelle den Pfad zum Janus-Ordner
    data_dir = os.path.join(app_data, "Janus Projekt")
    
    # 4. Stelle sicher, dass der Ordner existiert
    os.makedirs(data_dir, exist_ok=True)
    
    return data_dir

def get_resource_path(relative_path):
    """
    Liefert den Pfad zu Ressourcen (Code, Assets), die im Installer liegen.
    Hier haben wir NUR Lese-Rechte.
    """
    try:
        # PyInstaller: Temporärer Ordner (_MEIPASS)
        base_path = sys._MEIPASS
    except Exception:
        # Entwicklung: Projekt-Root (stabil, unabhängig vom aktuellen Working Directory)
        base_path = Path(__file__).resolve().parent.parent.parent

    return os.path.join(str(base_path), relative_path)

def get_model_cache_dir():
    """
    Gibt das Verzeichnis für den Modell-Cache zurück.
    Erstellt das Verzeichnis, wenn es nicht existiert.
    """
    cache_dir = os.path.join(get_app_data_dir(), "model_cache")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir

def get_desktop_path() -> str:
    """Gibt den plattformunabhängigen Pfad zum Desktop des Benutzers zurück."""
    return os.path.join(os.path.expanduser("~"), "Desktop")

def get_images_dir() -> str:
    """
    Gibt den Pfad zum öffentlichen Bilder-Ordner des Benutzers zurück.
    Ziel: C:/Users/Name/Pictures/Janus Images
    """
    home = Path.home()
    
    # Versuche englisch "Pictures"
    pictures_dir = home / "Pictures"
    if not pictures_dir.exists():
        # Fallback deutsch "Bilder" (falls das OS es nicht automatisch mapped)
        pictures_dir = home / "Bilder"
        
    # Wenn gar nichts da ist, fallback auf Home
    if not pictures_dir.exists():
         pictures_dir = home
    
    janus_images_dir = pictures_dir / "Janus Images"
    
    # Ordner erstellen
    janus_images_dir.mkdir(parents=True, exist_ok=True)
    (janus_images_dir / "uploads").mkdir(exist_ok=True)
    
    return str(janus_images_dir)

# Legacy-Support, falls alter Code 'resource_path' aufruft
resource_path = get_resource_path
