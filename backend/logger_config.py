import logging
import sys


def setup_logging():
    """Konfiguriert das Root-Logging-System für die Anwendung."""
    # Der Parameter force=True (verfügbar ab Python 3.8) überschreibt alle
    # bestehenden Konfigurationen des Root-Loggers.
    # `encoding='utf-8'` wird an alle Handler weitergegeben, die es unterstützen.
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - [%(levelname)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        encoding='utf-8',
        force=True,
        handlers=[
            # logging.FileHandler("janus_backend.log", mode='a', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.getLogger("janus_backend").info("Logger wurde re-initialisiert mit UTF-8-Erzwingung.")
