import logging
import sys
import os # NEU: Importiere os

def setup_logging():
    """Konfiguriert das Root-Logging-System für die Anwendung."""
    
    # NEU: Log-Level basierend auf Umgebungsvariable
    log_level = os.getenv("JANUS_LOG_LEVEL", "DEBUG").upper()
    numeric_level = getattr(logging, log_level, None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    # NEU: Handler basierend auf Umgebung
    handlers = [logging.StreamHandler(sys.stdout)]
    if os.getenv("JANUS_ENV") == "production":
        # Aktiviere FileHandler nur in Produktion
        # Stellen Sie sicher, dass das Verzeichnis existiert, wenn Sie einen festen Pfad verwenden
        # Für eine Electron-App könnten Logs auch im AppData-Verzeichnis gespeichert werden
        log_file_path = os.path.join(os.getenv("APPDATA") or os.path.expanduser("~"), "Janus Projekt", "janus_backend.log")
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True) # Stelle sicher, dass Verzeichnis existiert
        handlers.append(logging.FileHandler(log_file_path, mode='a', encoding='utf-8'))


    logging.basicConfig(
        level=numeric_level, # Angepasst
        format="%(asctime)s - %(name)s - [%(levelname)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        encoding="utf-8",
        force=True,
        handlers=handlers, # Angepasst
    )
    logging.getLogger("janus_backend").info("Logger wurde re-initialisiert mit UTF-8-Erzwingung.")
