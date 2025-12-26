import logging

from sqlalchemy.orm import Session

from backend.services import contact_manager

logger = logging.getLogger("janus_backend")


async def extract_and_save_contact_from_text(
    text: str, db: Session, api_key: str, provider: str, model: str, location_context: str = None
) -> dict:
    """
    Analysiert einen Textblock und extrahiert explizite Kontaktinformationen (Namen, Adressen, etc.), um sie im Adressbuch zu speichern.

    WICHTIG: Benutze dieses Werkzeug AUCH DANN, wenn die primäre Anfrage eine andere Aktion ist (z.B. einen Kalendertermin erstellen),
    aber der Text trotzdem Kontaktinformationen enthält. Du kannst mehrere Werkzeuge parallel aufrufen.

    Args:
        text: Der zu analysierende Text.
        db: Die aktive Datenbank-Session.
        api_key: Der API-Schlüssel für den LLM-Aufruf.
        provider: Der LLM-Anbieter (z.B. 'openai').
        model: Das zu verwendende LLM (z.B. 'gpt-4o-mini').
        location_context: Der vom Benutzer genannte Ort (z.B. 'Köln'), um die Suche zu verfeinern.

    Returns:
        Ein Dictionary mit einer Erfolgs- oder Fehlermeldung.
    """
    try:
        await contact_manager.extract_and_save_contact(
            db=db,
            text_block=text,
            api_key=api_key,
            provider=provider,
            model=model,
            location_context=location_context,
        )
        # Da die Funktion im contact_manager bereits detailliert loggt, geben wir hier nur eine einfache Erfolgsmeldung zurück.
        return {
            "status": "success",
            "message": "Die Extraktion wurde erfolgreich durchgeführt. Neue Kontakte wurden gespeichert, falls gefunden.",
        }
    except Exception as e:
        logger.error(f"Fehler im Werkzeug 'extract_and_save_contact_from_text': {e}", exc_info=True)
        return {"status": "error", "message": f"Ein Fehler ist aufgetreten: {e}"}
