import logging
import sys

def setup_logging():
    """Konfiguriert das Root-Logging-System für die Anwendung."""
    # Erstelle einen Logger
    logger = logging.getLogger('janus_backend')
    # logger.setLevel(logging.DEBUG) # Level wird jetzt von basicConfig gesetzt

    # Verhindere, dass Logs doppelt ausgegeben werden
    if logger.hasHandlers():
        logger.handlers.clear()

    # Definiere das Format der Log-Nachrichten
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Erstelle einen Handler, der Logs in die Konsole schreibt
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    # console_handler.setLevel(logging.DEBUG) # Level wird jetzt von basicConfig gesetzt

    # Füge einen FileHandler hinzu, falls benötigt (nicht explizit in Arbeitsanweisung, aber gute Praxis)
    # file_handler = logging.FileHandler("janus_backend.log", encoding='utf-8')
    # file_handler.setFormatter(formatter)

    # Konfiguriere das Root-Logging-System mit basicConfig
    # Dies ist die sicherste Variante, um die Kodierung zu setzen
    logging.basicConfig(
        level=logging.DEBUG, # Setze das globale Logging-Level
        handlers=[console_handler], # Füge hier auch file_handler hinzu, falls verwendet
        encoding='utf-8' # Setze die Kodierung für alle Handler
    )

    logger.info("Logger wurde initialisiert.")