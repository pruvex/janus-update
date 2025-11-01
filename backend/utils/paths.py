import sys
import os
from platformdirs import user_data_dir

APP_NAME = "Janus Projekt"
APP_AUTHOR = "JanusDev"


def get_app_data_dir():
    """
    Gibt das benutzerspezifische Anwendungsdatenverzeichnis zurück.
    Erstellt das Verzeichnis, wenn es nicht existiert.
    """
    app_data_dir = user_data_dir(APP_NAME, APP_AUTHOR)
    os.makedirs(app_data_dir, exist_ok=True)
    return app_data_dir


def resource_path(relative_path):
    """
    Ermittelt den absoluten Pfad zu einer Ressource, funktioniert für Entwicklung und PyInstaller.
    """
    try:
        # PyInstaller erstellt einen temporären Ordner und speichert den Pfad in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Im Entwicklungsmodus ist der base_path das Root-Verzeichnis des Backends
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

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
    return os.path.join(os.path.expanduser('~'), 'Desktop')
