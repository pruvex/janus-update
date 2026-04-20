import logging
from datetime import datetime
from sqlalchemy.orm import Session

# Wir importieren das Model direkt
import backend.data.models as models

logger = logging.getLogger("janus_backend")

def create_cost_entry(
    db: Session, 
    amount: float, 
    model: str, 
    provider: str, 
    source_type: str, 
    input_tokens: int = 0, 
    output_tokens: int = 0,
    image_quality: str = None,
    image_size: str = None,
    image_cost: float = 0.0,
    context_details: str = None,
):
    """
    Speichert einen Kosteneintrag.
    Bild-Details werden in 'context' gespeichert, da die DB-Tabelle keine eigenen Spalten dafür hat.
    """
    try:
        # Wir bauen einen detailreichen Kontext-String
        context_str = source_type
        if image_size or image_quality:
            details = []
            if image_size: details.append(f"Size: {image_size}")
            if image_quality: details.append(f"Quality: {image_quality}")
            context_str = f"{source_type} ({', '.join(details)})"
        elif context_details:
            context_str = f"{source_type} ({context_details})"

        # Erstelle das Datenbank-Objekt
        cost_entry = models.Cost(
            timestamp=datetime.utcnow(),
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_cost=amount, # Der Betrag ist bereits korrekt berechnet
            context=context_str 
        )
        
        db.add(cost_entry)
        db.commit()
        db.refresh(cost_entry)
        
        logger.info(f"Kosten gespeichert: {amount:.6f}€ für {model} ({context_str})")
        return cost_entry
        
    except Exception as e:
        logger.error(f"Fehler beim Speichern der Kosten: {e}")
        return None

def get_total_costs(db: Session):
    result = db.query(models.Cost).all()
    return sum(c.total_cost for c in result)
