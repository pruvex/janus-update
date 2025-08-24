import logging
from sqlalchemy.orm import Session
from backend import crud, llm_gateway, vector_service
from typing import List, Dict

logger = logging.getLogger('janus_backend')

async def summarize_and_store_chat(db: Session, chat_id: int, api_key: str, provider: str, model: str):
    try:
        logger.info(f"Beginne Zusammenfassung für Chat ID: {chat_id}")
        messages = crud.get_messages_by_chat_id(db, chat_id)
        if not messages:
            return
        history = [{'role': 'assistant' if m.sender == 'model' else m.sender, 'content': m.content} for m in messages]
        summary = await llm_gateway.summarize_chat_topic(history, api_key, provider, model)
        embedding = vector_service.generate_embedding(summary)
        crud.update_chat_summary(db, chat_id, summary, embedding)
        logger.info(f"Chat {chat_id} erfolgreich zusammengefasst: '{summary}'")
    except Exception as e:
        logger.error(f"Fehler beim Zusammenfassen von Chat {chat_id}: {e}")