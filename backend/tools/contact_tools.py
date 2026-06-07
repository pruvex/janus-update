import logging
import time

from sqlalchemy.orm import Session

from backend.data.schemas_tools import ToolResultV1
from backend.services import contact_manager
from backend.tools.tool_contract_v1 import tool_err_v1, tool_ok_v1

logger = logging.getLogger("janus_backend")

_CONTACT_TAGS = ["contact", "address_book"]


async def extract_and_save_contact_from_text(
    text: str,
    db: Session,
    api_key: str,
    provider: str,
    model: str,
    location_context: str = None,
    chat_id: int = None,
) -> ToolResultV1:
    """
    Analysiert einen Textblock und extrahiert explizite Kontaktinformationen (Namen, Adressen, etc.), um sie im Adressbuch zu speichern.

    WICHTIG: Benutze dieses Werkzeug AUCH DANN, wenn die primaere Anfrage eine andere Aktion ist (z.B. einen Kalendertermin erstellen),
    aber der Text trotzdem Kontaktinformationen enthaelt. Du kannst mehrere Werkzeuge parallel aufrufen.

    Args:
        text: Der zu analysierende Text.
        db: Die aktive Datenbank-Session.
        api_key: Der API-Schluessel fuer den LLM-Aufruf.
        provider: Der LLM-Anbieter (z.B. 'openai').
        model: Das zu verwendende LLM (z.B. 'gpt-5.4-nano').
        location_context: Der vom Benutzer genannte Ort (z.B. 'Koeln'), um die Suche zu verfeinern.

    Returns:
        ToolResultV1 mit Erfolg oder Fehler.
    """
    t0 = time.perf_counter()
    try:
        extraction_result = await contact_manager.extract_and_save_contact(
            text_block=text,
            api_key=api_key,
            provider=provider,
            model=model,
            location_context=location_context,
            chat_id=chat_id,
        )
        user_message = extraction_result.get("user_message") or (
            "Die Extraktion wurde erfolgreich durchgefuehrt. Es waren keine bestaetigbaren Kontaktvorschlaege noetig."
        )
        return tool_ok_v1(
            {
                "saved": False,
                "proposals_staged": extraction_result.get("proposals_staged", 0),
                "suppressed": extraction_result.get("suppressed", 0),
                "proposal_id": extraction_result.get("proposal_id"),
            },
            message=user_message,
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
