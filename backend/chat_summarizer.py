import logging
from sqlalchemy.orm import Session
from backend import crud, llm_gateway, vector_service, database
from typing import List, Dict
import datetime

logger = logging.getLogger('janus_backend')

async def summarize_and_store_chat(db: Session, chat_id: int, api_key: str, provider: str, model: str):
    try:
        logger.info(f"Beginne Zusammenfassung für Chat ID: {chat_id}")
        messages = crud.get_messages_by_chat_id(db, chat_id)
        if not messages:
            return
        history = [{'role': 'assistant' if m.sender == 'model' else m.sender, 'content': m.content} for m in messages]
        summary_response = await llm_gateway.summarize_chat_topic(history, api_key, provider, model)
        summary = summary_response.get("text", "Unbenannter Chat")
        
        # Kosten für die Chat-Zusammenfassung speichern
        usage = summary_response.get("usage")
        cost = summary_response.get("cost", {})
        if usage and cost.get("total_cost", 0) > 0:
            database.save_cost_entry(
                date=datetime.datetime.now(), model=model,
                input_tokens=usage.get("input_tokens"), output_tokens=usage.get("output_tokens"),
                image_quality=usage.get("image_quality"), image_cost=cost.get("image_cost"),
                total_cost=cost.get("total_cost", 0)
            )

        embedding = vector_service.generate_embedding(summary)
        crud.update_chat_summary(db, chat_id, summary, embedding)
        logger.info(f"Chat {chat_id} erfolgreich zusammengefasst: '{summary}'")
    except Exception as e:
        logger.error(f"Fehler beim Zusammenfassen von Chat {chat_id}: {e}")