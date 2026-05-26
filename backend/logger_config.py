import logging
import sys
import os
from pathlib import Path

from backend.utils.redaction import redact_sensitive_text, redact_sensitive_value


NOISE_PATTERNS = (
    "Request Autofill.enable failed",
    "Request Autofill.setAddresses failed",
    "Request Storage.getStorageKeyForFrame failed",
)


class NoiseSuppressFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        return not any(pattern in message for pattern in NOISE_PATTERNS)


class SensitiveRedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact_sensitive_text(str(record.msg))
        if record.args:
            record.args = redact_sensitive_value(record.args)
        return True


def setup_logging():
    """Konfiguriert das Logging. Schreibt IMMER in AppData."""
    
    # 1. Log Level bestimmen
    log_level_str = os.getenv("JANUS_LOG_LEVEL", "DEBUG").upper()
    numeric_level = getattr(logging, log_level_str, logging.DEBUG)

    # 2. Handler definieren
    handlers = [logging.StreamHandler(sys.stdout)]
    
    # DATEI-HANDLER IMMER HINZUFÜGEN (nicht nur bei Production)
    try:
        # Pfad: %APPDATA%/Janus Projekt/logs/janus_backend.log
        app_data = os.getenv("APPDATA") or os.path.expanduser("~")
        log_dir = os.path.join(app_data, "Janus Projekt", "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        log_file_path = os.path.join(log_dir, "janus_backend.log")
        
        file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
        handlers.append(file_handler)
        
        # Einmalig printen, damit wir wissen wo das Log ist (wenn man Konsole hat)
        print(f"DEBUG: Logging to {log_file_path}")
        
    except Exception as e:
        print(f"WARNUNG: Konnte Logfile nicht erstellen: {e}")

    # Zusätzlicher zentraler Log-Ort im Repo für einfache Auswertung:
    # C:\KI\Janus-Projekt\documentation\logs\janus_backend.log
    try:
        backend_dir = Path(__file__).resolve().parent
        repo_root = backend_dir.parent
        docs_log_dir = repo_root / "documentation" / "logs"
        docs_log_dir.mkdir(parents=True, exist_ok=True)
        docs_log_file = docs_log_dir / "janus_backend.log"
        docs_file_handler = logging.FileHandler(str(docs_log_file), mode="a", encoding="utf-8")
        handlers.append(docs_file_handler)
        print(f"DEBUG: Logging mirror to {docs_log_file}")
    except Exception as e:
        print(f"WARNUNG: Konnte documentation/logs Logfile nicht erstellen: {e}")

    # 3. Config anwenden
    noise_filter = NoiseSuppressFilter()
    redaction_filter = SensitiveRedactionFilter()
    for handler in handlers:
        handler.addFilter(noise_filter)
        handler.addFilter(redaction_filter)

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - [%(levelname)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        encoding="utf-8",
        force=True, # WICHTIG: Überschreibt Konfiguration aus main.py
        handlers=handlers
    )
    
    # 4. Externe Libs ruhig stellen
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("openai._base_client").setLevel(logging.WARNING)
    logging.getLogger("hpack").setLevel(logging.WARNING)
    logging.getLogger("h2").setLevel(logging.WARNING)
    logging.getLogger("multipart").setLevel(logging.WARNING)
    logging.getLogger("watchfiles").setLevel(logging.WARNING)
    logging.getLogger("fontTools.subset").setLevel(logging.WARNING)
    logging.getLogger("fontTools.subset.timer").setLevel(logging.WARNING)
    
    logger = logging.getLogger("janus_backend")
    logger.info("Logging initialisiert.")
