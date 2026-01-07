# backend/utils/encryption.py
import os
import logging
import sys
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.types import TypeDecorator, LargeBinary
from dotenv import load_dotenv, set_key

logger = logging.getLogger("janus_backend")

# --- Schlüssel-Management ---

def generate_key() -> bytes:
    """Generiert einen neuen Fernet-Schlüssel."""
    return Fernet.generate_key()

def get_config_path() -> str:
    """Liefert den Pfad zur .env Datei im AppData Ordner"""
    # Hole den AppData Pfad des Users (z.B. C:\Users\Name\AppData\Roaming)
    app_data = os.getenv('APPDATA')
    if not app_data:
        # Fallback für nicht-Windows oder wenn Variable fehlt
        app_data = os.path.expanduser("~")
    
    # Ordner für die App erstellen
    janus_config_dir = os.path.join(app_data, "Janus Projekt")
    os.makedirs(janus_config_dir, exist_ok=True)
    
    return os.path.join(janus_config_dir, ".env")

def get_encryption_key() -> bytes:
    """
    Lädt den Verschlüsselungsschlüssel aus der .env-Datei im AppData-Ordner.
    Wenn kein Schlüssel existiert, wird ein neuer generiert und gespeichert.
    """
    # 1. Bestimme den sicheren Pfad im AppData Ordner
    env_path = get_config_path()
    logger.info(f"Lade Konfiguration aus: {env_path}")
    
    # 2. Lade existierende Env-Datei, falls vorhanden
    load_dotenv(env_path)

    # 3. Versuche, den Key zu lesen
    key = os.getenv("ENCRYPTION_KEY")

    if key:
        logger.info("ENCRYPTION_KEY erfolgreich aus der Konfiguration geladen.")
        return key.encode('utf-8')

    # 4. Wenn kein Schlüssel gefunden wurde, generiere einen neuen
    logger.warning("ENCRYPTION_KEY nicht gefunden. Generiere einen neuen Schlüssel...")
    
    try:
        new_key_bytes = generate_key()
        new_key_str = new_key_bytes.decode('utf-8')
        
        # 5. Speichere den Key im APPDATA Ordner
        set_key(env_path, "ENCRYPTION_KEY", new_key_str)
        logger.info(f"Neuer Schlüssel erfolgreich gespeichert in: {env_path}")
        
        # 6. Setze die Umgebungsvariable für den aktuellen Prozess
        os.environ["ENCRYPTION_KEY"] = new_key_str
        
        return new_key_bytes
        
    except Exception as e:
        logger.error(f"KRITISCHER FEHLER: Konnte Key nicht in {env_path} speichern: {e}", exc_info=True)
        # Zur Not im Speicher behalten, aber er ist beim Neustart weg
        os.environ["ENCRYPTION_KEY"] = new_key_str
        return new_key_bytes


# --- SQLAlchemy TypeDecorator für Verschlüsselung ---

# Lade den Schlüssel beim Start der Anwendung.
# Wenn der Schlüssel nicht geladen werden kann, wird die Anwendung mit einem Fehler beendet.
try:
    ENCRYPTION_KEY = get_encryption_key()
    FERNET = Fernet(ENCRYPTION_KEY)
except (ValueError, TypeError) as e:
    logger.error(f"Kritischer Fehler beim Laden des Verschlüsselungsschlüssels: {e}")
    # Beende die Anwendung, wenn kein Schlüssel konfiguriert werden kann.
    # In einer echten Server-Anwendung würde dies einen sauberen Exit auslösen.
    # Für diese Implementierung drucken wir den Fehler und beenden hart.
    import sys
    sys.exit(1)


class EncryptedString(TypeDecorator):
    """
    Ein SQLAlchemy TypeDecorator, der Textwerte vor dem Speichern in der
    Datenbank verschlüsselt und beim Laden wieder entschlüsselt.
    """
    impl = LargeBinary
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Wird aufgerufen, wenn Daten IN die Datenbank geschrieben werden."""
        if value is None:
            return None
        if not isinstance(value, str):
            value = str(value)
        
        # Verschlüssele den String
        return FERNET.encrypt(value.encode('utf-8'))

    def process_result_value(self, value, dialect):
        """Wird aufgerufen, wenn Daten AUS der Datenbank gelesen werden."""
        if value is None:
            return None
            
        try:
            # Entschlüssele die Bytes zurück zu einem String
            return FERNET.decrypt(value).decode('utf-8')
        except InvalidToken:
            # Wenn die Daten nicht entschlüsselt werden können (z.B. alter Klartext),
            # gib den Originalwert zurück (als String, falls es Bytes sind).
            logger.warning("Konnte einen Wert aus der Datenbank nicht entschlüsseln. Gebe Rohwert zurück. Dies ist bei der Datenmigration zu erwarten.")
            if isinstance(value, bytes):
                try:
                    return value.decode('utf-8')
                except UnicodeDecodeError:
                    return repr(value) # Fallback für non-utf8 bytes
            return value

    def copy(self, **kw):
        return EncryptedString(self.impl.length)
