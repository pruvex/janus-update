import sys
import os

def get_app_data_dir():
    """
    Gibt den Pfad zum schreibbaren Benutzer-Ordner zurück.
    Windows: %APPDATA%\Janus Projekt
    """
    app_name = "Janus Projekt"
    if sys.platform == "win32":
        base_path = os.getenv("APPDATA")
    else:
        base_path = os.path.expanduser("~")
        app_name = ".janus_project"
    
    path = os.path.join(base_path, app_name)
    os.makedirs(path, exist_ok=True)
    return path

def resource_path(relative_path):
    """
    Findet statische Ressourcen (Code, Templates, Defaults) im Installationsordner.
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller Mode
        base_path = os.path.dirname(sys.executable)
    else:
        # Dev Mode
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

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
