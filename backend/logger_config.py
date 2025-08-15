import logging
import sys

def setup_logging():
    """Konfiguriert das Root-Logging-System für die Anwendung."""
    # Erstelle einen Logger
    logger = logging.getLogger('janus_backend')
    logger.setLevel(logging.DEBUG) # Logge alle Nachrichten ab DEBUG Level

    # Verhindere, dass Logs doppelt ausgegeben werden
    if logger.hasHandlers():
        logger.handlers.clear()

    # Erstelle einen Handler, der Logs in die Konsole schreibt
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)

    # Definiere das Format der Log-Nachrichten
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)

    # Füge den Handler zum Logger hinzu
    logger.addHandler(handler)

    print("Logger wurde initialisiert.")