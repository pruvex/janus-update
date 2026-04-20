import datetime
import logging

from backend.data import crud, database
from backend.services import llm_gateway, vector_service
from sqlalchemy.orm import Session

logger = logging.getLogger("janus_backend")


async def summarize_and_store_chat(
    db: Session, chat_id: int, api_key: str, provider: str, model: str
):
    try:
        logger.info(f"Beginne Zusammenfassung für Chat ID: {chat_id}")
        messages = crud.get_messages_by_chat_id(db, chat_id)
        if not messages:
            return

        # Konvertiere die Nachrichten in das Format, das die LLM erwartet.
        history_for_summary = [
            {
                "role": "assistant" if m.sender == "model" else m.sender,
                "content": m.content,
            }
            for m in messages
        ]

        # KORREKTUR: Wir erstellen einen expliziten Prompt und verwenden die Standard-call_llm-Funktion.
        summary_prompt = "Fasse den folgenden Chatverlauf in einem einzigen, prägnanten Satz als Titel für eine Chat-Liste zusammen. Antworte nur mit dem Titel."

        # Füge den System-Prompt an den Anfang der History.
        messages_for_llm = [{"role": "system", "content": summary_prompt}]
        messages_for_llm.extend(history_for_summary)

        # Rufe den Standard-Gateway auf.
        summary_response = await llm_gateway.call_llm(
            provider=provider,
            model_id=model,
            api_key=api_key,
            messages=messages_for_llm,
        )

        summary = summary_response.get("text", "Unbenannter Chat").strip()

        # Kosten für die Chat-Zusammenfassung speichern
        usage = summary_response.get("usage")
        cost = summary_response.get("cost", {})
        if usage and cost.get("total_cost", 0) > 0:
            database.save_cost_entry(
                date=datetime.datetime.now(),
                model=model,
                input_tokens=usage.get("input_tokens"),
                output_tokens=usage.get("output_tokens"),
                image_quality=None,  # Zusammenfassungen haben keine Bildkosten
                image_cost=None,
                total_cost=cost.get("total_cost", 0),
            )

        embedding = vector_service.generate_embedding(summary)
        # Die Spalte heißt summary_embedding_json
        crud.update_chat_summary(db, chat_id, summary, embedding)
        logger.info(f"Chat {chat_id} erfolgreich zusammengefasst: '{summary}'")
    except Exception as e:
        logger.error(f"Fehler beim Zusammenfassen von Chat {chat_id}: {e}", exc_info=True)
