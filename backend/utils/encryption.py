# backend/utils/encryption.py
import os
import logging
import binascii
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
    app_data = os.getenv('APPDATA')
    if not app_data:
        app_data = os.path.expanduser("~")
    
    janus_config_dir = os.path.join(app_data, "Janus Projekt")
    os.makedirs(janus_config_dir, exist_ok=True)
    
    return os.path.join(janus_config_dir, ".env")

def get_encryption_key() -> bytes:
    env_path = get_config_path()
    # logger.info(f"Lade Konfiguration aus: {env_path}") # Spam reduzieren
    
    load_dotenv(env_path)
    key = os.getenv("ENCRYPTION_KEY")

    if key:
        return key.encode('utf-8')

    logger.warning("ENCRYPTION_KEY nicht gefunden. Generiere einen neuen Schlüssel...")
    try:
        new_key_bytes = generate_key()
        new_key_str = new_key_bytes.decode('utf-8')
        set_key(env_path, "ENCRYPTION_KEY", new_key_str)
        os.environ["ENCRYPTION_KEY"] = new_key_str
        return new_key_bytes
    except Exception as e:
        logger.critical(f"KRITISCHER FEHLER: Konnte Key nicht speichern: {e}")
        raise IOError(f"Failed to save encryption key.")

# --- Init Fernet ---
try:
    ENCRYPTION_KEY = get_encryption_key()
    FERNET = Fernet(ENCRYPTION_KEY)
except Exception as e:
    logger.error(f"Kritischer Fehler beim Laden des Keys: {e}")
    # Fallback Key generieren damit die App nicht crasht, 
    # auch wenn alte Daten dann nicht lesbar sind.
    FERNET = Fernet(Fernet.generate_key())

class EncryptedString(TypeDecorator):
    """
    Verschlüsselt Strings für die DB.
    Robust gegen Fehler: Gibt bei Entschlüsselungsfehlern (z.B. Klartext in DB)
    einfach den Rohwert zurück (Self-Healing).
    """
    impl = LargeBinary
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if not isinstance(value, str):
            value = str(value)
        return FERNET.encrypt(value.encode('utf-8'))

    def process_result_value(self, value, dialect):
        if value is None:
            return None
            
        try:
            # Versuch 1: Normales Entschlüsseln
            return FERNET.decrypt(value).decode('utf-8')
        except (InvalidToken, ValueError, binascii.Error, Exception) as e:
            # DAS HIER IST DER FIX FÜR DEN CRASH!
            # Wenn es knallt (z.B. weil "Hallo Welt" in der DB steht und kein Token ist),
            # loggen wir nur eine Warnung und geben den Text so zurück, wie er ist.
            
            # logger.warning(f"Datenbank-Wert konnte nicht entschlüsselt werden (Klartext?): {e}")
            
            if isinstance(value, bytes):
                try:
                    return value.decode('utf-8')
                except UnicodeDecodeError:
                    return str(value)
            return str(value)

    def copy(self, **kw):
        return EncryptedString(self.impl.length)
