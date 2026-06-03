import logging
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

# Wir importieren das Model direkt
import backend.data.models as models

logger = logging.getLogger("janus_backend")

ATTRIBUTION_STATUS_INTERNAL = "intern attribuiert"
ATTRIBUTION_STATUS_UNATTRIBUTED = "nicht eindeutig attribuiert"
ATTRIBUTION_STATUS_EXTERNAL_BILLING = "externe Billing-Summe"

_SENSITIVE_ATTRIBUTION_KEYS = {
    "prompt",
    "response",
    "messages",
    "chat_history",
    "full_prompt",
    "full_response",
    "raw_prompt",
    "raw_response",
}


def _sanitize_attribution_value(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized_dict: Dict[str, Any] = {}
        for key, nested_value in value.items():
            normalized_key = str(key).strip()
            if not normalized_key:
                continue
            if normalized_key.casefold() in _SENSITIVE_ATTRIBUTION_KEYS:
                continue
            sanitized_nested = _sanitize_attribution_value(nested_value)
            if sanitized_nested is None:
                continue
            sanitized_dict[normalized_key] = sanitized_nested
        return sanitized_dict or None
    if isinstance(value, list):
        sanitized_list = []
        for item in value:
            sanitized_item = _sanitize_attribution_value(item)
            if sanitized_item is None:
                continue
            sanitized_list.append(sanitized_item)
        return sanitized_list
    return value


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


def _coerce_optional_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def normalize_attribution_status(value: Any) -> str:
    normalized = str(value or "").strip().casefold()
    if normalized in {
        "intern attribuiert",
        "intern_attribuiert",
        "internal",
        "internal_attributed",
    }:
        return ATTRIBUTION_STATUS_INTERNAL
    if normalized in {
        "nicht eindeutig attribuiert",
        "nicht_eindeutig_attribuiert",
        "unattributed",
        "partially_attributed",
        "partial",
    }:
        return ATTRIBUTION_STATUS_UNATTRIBUTED
    if normalized in {
        "externe billing-summe",
        "externe_billing_summe",
        "external_billing_sum",
        "external billing total",
    }:
        return ATTRIBUTION_STATUS_EXTERNAL_BILLING
    return ATTRIBUTION_STATUS_UNATTRIBUTED


def _sanitize_attribution_metadata(
    attribution_metadata: Optional[Dict[str, Any]],
    context_details: Optional[str],
) -> Optional[Dict[str, Any]]:
    sanitized: Dict[str, Any] = {}
    if isinstance(attribution_metadata, dict):
        for key, value in attribution_metadata.items():
            normalized_key = str(key).strip()
            if not normalized_key:
                continue
            if normalized_key.casefold() in _SENSITIVE_ATTRIBUTION_KEYS:
                continue
            sanitized_value = _sanitize_attribution_value(value)
            if sanitized_value is None:
                continue
            sanitized[normalized_key] = sanitized_value

    compact_context = _coerce_optional_str(context_details)
    if compact_context and "compact_cause_context" not in sanitized:
        sanitized["compact_cause_context"] = compact_context

    return sanitized or None


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
    attribution_group_id: str = None,
    attribution_request_id: str = None,
    attribution_session_id: str = None,
    attribution_test_run_id: str = None,
    attribution_status: str = None,
    attribution_component: str = None,
    attribution_manual_override: bool = False,
    attribution_metadata: Optional[Dict[str, Any]] = None,
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
        sanitized_attribution_metadata = _sanitize_attribution_metadata(
            attribution_metadata=attribution_metadata,
            context_details=context_details,
        )

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
            attribution_group_id=_coerce_optional_str(attribution_group_id),
            attribution_request_id=_coerce_optional_str(attribution_request_id),
            attribution_session_id=_coerce_optional_str(attribution_session_id),
            attribution_test_run_id=_coerce_optional_str(attribution_test_run_id),
            attribution_status=_coerce_optional_str(attribution_status),
            attribution_component=_coerce_optional_str(attribution_component),
            attribution_manual_override=bool(attribution_manual_override),
            attribution_metadata=sanitized_attribution_metadata,
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
