import datetime
import logging
from backend.data.database import save_cost_entry

logger = logging.getLogger("janus_backend")

def create_cost_entry(db, amount, model, provider, source_type, input_tokens=0, output_tokens=0):
    """
    Speichert einen Kosteneintrag in der Datenbank.
    Der Parameter 'db' wird für zukünftige Erweiterungen beibehalten, ist aber
    für die aktuelle Implementierung (eigene Session in save_cost_entry) nicht notwendig.
    """
    try:
        save_cost_entry(
            date=datetime.datetime.now(),
            model=model,
            provider=provider,
            source_type=source_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            image_quality=None,
            image_cost=0.0,
            total_cost=amount
        )
        logger.info(f"Kosten gespeichert: {amount:.6f}€ für {model} ({provider}/{source_type})")
    except Exception as e:
        logger.error(f"Fehler beim Speichern der Kosten: {e}")
