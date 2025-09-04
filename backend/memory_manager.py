# Am Anfang von backend/memory_manager.py
from sqlalchemy.orm import Session
from typing import List
from . import database # Importiert die gesamte database.py Datei
from . import crud # Importiert die crud.py Datei
from . import vector_service

import logging
from backend.logger_config import setup_logging

setup_logging()
logger = logging.getLogger('janus_backend')

# --- Memory CRUD ---
def save_memory_snippet(db: Session, chat_id: int, snippet_text: str):
    embedding = vector_service.generate_embedding(snippet_text)
    if embedding is None:
        return None
    db_memory = database.Memory(chat_id=chat_id, snippet=snippet_text, embedding_json=embedding)
    db.add(db_memory)
    db.commit()
    db.refresh(db_memory)
    return db_memory

def find_similar_memory_snippet(db: Session, text: str):
    all_memories = get_all_memories(db)
    similar = vector_service.find_similar_snippets(text, all_memories, top_k=1, threshold=0.7)
    return similar[0] if similar else None

def get_all_memories(db: Session):
    return db.query(database.Memory).all()

def update_memory_snippet(db: Session, memory_id: int, new_snippet: str):
    memory_item = db.query(database.Memory).filter(database.Memory.id == memory_id).first()
    if memory_item:
        memory_item.snippet = new_snippet
        memory_item.embedding_json = vector_service.generate_embedding(new_snippet)
        db.commit()

def save_raw_memory(db: Session, chat_id: int, user_input: str):
    """Speichert die rohe Benutzereingabe als Gedächtnis."""
    current_logger = logging.getLogger('janus_backend') # Get logger inside function
    current_logger.info(f"Attempting to save raw memory for chat {chat_id}: '{user_input}'")
    saved_memory = save_memory_snippet(db, chat_id, user_input)
    if saved_memory:
        current_logger.info(f"Raw memory saved successfully: '{user_input}'")
    else:
        current_logger.warning(f"Failed to save raw memory for chat {chat_id}: '{user_input}'")
    return saved_memory

# In backend/memory_manager.py
def get_all_facts(db: Session) -> List[database.Memory]: # Verwende database.Memory
    """Gibt alle Erinnerungen zurück, die als Fakten und nicht als Fragen oder rohe Eingaben gelten."""
    return db.query(database.Memory).filter( # Verwende database.Memory
        ~database.Memory.snippet.startswith("wie "),
        ~database.Memory.snippet.startswith("was "),
        ~database.Memory.snippet.startswith("wer "),
        ~database.Memory.snippet.startswith("wo "),
        ~database.Memory.snippet.startswith("wann "),
        ~database.Memory.snippet.startswith("warum ")
    ).all()

def cross_chat_memory_tool(query: str, db: Session):
    """Ruft Zusammenfassungen der letzten Konversationen ab, um Fragen über die Vergangenheit zu beantworten."""
    all_chats = crud.get_chats(db, include_archived=True)
    recent_chats = sorted(all_chats, key=lambda chat: chat.created_at, reverse=True)[1:6]
    if not recent_chats:
        return {"output": "Keine früheren Chats zum Überprüfen gefunden."}
    output_snippets = ["--- ZUSAMMENFASSUNGEN DER LETZTEN CHATS ---"]
    for chat in recent_chats:
        if chat.summary:
            output_snippets.append(f"Thema des Chats '{chat.title}': {chat.summary}")
    if len(output_snippets) == 1:
        return {"output": "Keine relevanten Zusammenfassungen in früheren Chats gefunden."}
    return {"output": "\n".join(output_snippets)}