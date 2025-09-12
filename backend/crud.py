from sqlalchemy.orm import Session
from . import database, schemas
import logging
from backend.logger_config import setup_logging

setup_logging()
logger = logging.getLogger('janus_backend')

# --- Chat CRUD ---
def create_chat(db: Session, title: str):
    db_chat = database.Chat(title=title)
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    return db_chat

def get_chats(db: Session, include_archived: bool = False):
    if not include_archived:
        return db.query(database.Chat).filter(database.Chat.is_archived == False).all()
    else:
        return db.query(database.Chat).all()

def get_chat_by_id(db: Session, chat_id: int):
    return db.query(database.Chat).filter(database.Chat.id == chat_id).first()

def get_messages_by_chat_id(db: Session, chat_id: int):
    return db.query(database.Message).filter(database.Message.chat_id == chat_id).order_by(database.Message.timestamp).all()

def create_message(db: Session, chat_id: int, sender: str, content: str, image_path: str = None):
    db_message = database.Message(chat_id=chat_id, sender=sender, content=content, image_path=image_path)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def update_chat_title(db: Session, chat_id: int, new_title: str):
    chat = get_chat_by_id(db, chat_id)
    if chat:
        chat.title = new_title
        db.commit()
        db.refresh(chat)
    return chat

def toggle_archive_chat(db: Session, chat_id: int):
    chat = get_chat_by_id(db, chat_id)
    if chat:
        chat.is_archived = not chat.is_archived
        db.commit()
        db.refresh(chat)
    return chat

def get_chat_with_messages(db: Session, chat_id: int):
    chat = get_chat_by_id(db, chat_id)
    if not chat:
        return None, []
    messages = get_messages_by_chat_id(db, chat_id)
    return chat, messages

def delete_chat(db: Session, chat_id: int):
    chat = get_chat_by_id(db, chat_id)
    if chat:
        db.delete(chat)
        db.commit()
        return True
    return False

def update_chat_summary(db: Session, chat_id: int, summary: str, embedding: str):
    chat = get_chat_by_id(db, chat_id)
    if chat:
        chat.summary = summary
        chat.summary_embedding_json = embedding
        db.commit()
        db.refresh(chat)
    return chat

def get_all_chat_summaries(db: Session):
    return db.query(database.Chat).filter(database.Chat.summary != None).all()

def get_memory_by_chat_id(db: Session, chat_id: int):
    return db.query(database.Memory).filter(database.Memory.chat_id == chat_id).all()

# In backend/crud.py
# ... (am Ende der Datei hinzufügen)
from typing import Optional

def get_user_name(db: Session) -> Optional[str]:
    """Sucht im Gedächtnis nach dem Namen des Benutzers."""
    # Wir suchen nach dem spezifischen Fakt, der den Namen festlegt.
    memory_entry = db.query(database.Memory).filter(database.Memory.snippet.like("Der Benutzer heißt %")).first()
    if memory_entry:
        try:
            # Extrahiert den Namen nach dem Muster "Der Benutzer heißt [Name]."
            name = memory_entry.snippet.split("Der Benutzer heißt ")[1].strip().replace('.', '')
            logger.info(f"Benutzername '{name}' aus dem Gedächtnis geladen.")
            return name
        except IndexError:
            return None
    return None