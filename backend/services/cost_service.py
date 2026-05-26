import logging
from datetime import datetime
from sqlalchemy.orm import Session

# Wir importieren das Model direkt
import backend.data.models as models

logger = logging.getLogger("janus_backend")


def _calculate_cost_saved(model_id: str, tokens_saved: int) -> float:
    """Berechnet die Ersparnis in EUR basierend auf gesparten Tokens und Modell-Preis."""
    if tokens_saved <= 0:
        return 0.0
    try:
        from backend.services.cost_calculator import load_model_prices, USD_TO_EUR_CONVERSION_RATE
        prices = load_model_prices()
        model_info = prices.get(model_id) or {}
        input_cost_per_token = model_info.get("cost_per_token_input", 0.0)
        if not input_cost_per_token:
            return 0.0
        return float(tokens_saved) * float(input_cost_per_token) * USD_TO_EUR_CONVERSION_RATE
    except Exception as e:
        logger.warning("cost_saved calculation failed for model %s: %s", model_id, e)
        return 0.0


def create_cost_entry(
    db: Session, 
    amount: float, 
    model: str, 
    provider: str, 
    source_type: str, 
    input_tokens: int = 0, 
    output_tokens: int = 0,
    cached_tokens: int = 0,
    total_tokens: int = 0,
    image_quality: str = None,
    image_size: str = None,
    image_cost: float = 0.0,
    context_details: str = None,
    tokens_saved: int = 0,
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

        input_tokens = int(input_tokens or 0)
        output_tokens = int(output_tokens or 0)
        cached_tokens = int(cached_tokens or 0)
        total_tokens = int(total_tokens or 0) or (input_tokens + output_tokens)
        cost_saved = _calculate_cost_saved(model, tokens_saved)

        # Erstelle das Datenbank-Objekt
        cost_entry = models.Cost(
            timestamp=datetime.utcnow(),
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_tokens=cached_tokens,
            total_tokens=total_tokens,
            total_cost=amount, # Der Betrag ist bereits korrekt berechnet
            context=context_str,
            tokens_saved=int(tokens_saved),
            cost_saved=cost_saved,
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
