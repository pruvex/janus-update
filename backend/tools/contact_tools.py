import logging
import time

from sqlalchemy.orm import Session

from backend.data.schemas_tools import ToolResultV1
from backend.services import contact_manager
from backend.tools.tool_contract_v1 import tool_err_v1, tool_ok_v1

logger = logging.getLogger("janus_backend")

_CONTACT_TAGS = ["contact", "address_book"]


async def extract_and_save_contact_from_text(
    text: str, db: Session, api_key: str, provider: str, model: str, location_context: str = None
) -> ToolResultV1:
    """
    Analysiert einen Textblock und extrahiert explizite Kontaktinformationen (Namen, Adressen, etc.), um sie im Adressbuch zu speichern.

    WICHTIG: Benutze dieses Werkzeug AUCH DANN, wenn die primäre Anfrage eine andere Aktion ist (z.B. einen Kalendertermin erstellen),
    aber der Text trotzdem Kontaktinformationen enthält. Du kannst mehrere Werkzeuge parallel aufrufen.

    Args:
        text: Der zu analysierende Text.
        db: Die aktive Datenbank-Session.
        api_key: Der API-Schlüssel für den LLM-Aufruf.
        provider: Der LLM-Anbieter (z.B. 'openai').
        model: Das zu verwendende LLM (z.B. 'gpt-5.4-nano').
        location_context: Der vom Benutzer genannte Ort (z.B. 'Köln'), um die Suche zu verfeinern.

    Returns:
        ToolResultV1 mit Erfolg oder Fehler.
    """
    t0 = time.perf_counter()
    try:
        await contact_manager.extract_and_save_contact(
            text_block=text,
            api_key=api_key,
            provider=provider,
            model=model,
            location_context=location_context,
        )
        return tool_ok_v1(
            {"saved": True},
            message="Die Extraktion wurde erfolgreich durchgeführt. Neue Kontakte wurden gespeichert, falls gefunden.",
            tags=_CONTACT_TAGS,
            started_at=t0,
        )
    except Exception as e:
        logger.error(f"Fehler im Werkzeug 'extract_and_save_contact_from_text': {e}", exc_info=True)
        return tool_err_v1(
            "CONTACT_EXTRACT_FAILED",
            f"Ein Fehler ist aufgetreten: {e}",
            tags=_CONTACT_TAGS,
            started_at=t0,
        )
