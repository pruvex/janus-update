from sqlalchemy.orm import Session
from . import database, schemas
from datetime import datetime

def get_chat(db: Session, chat_id: int):
    return db.query(database.Chat).filter(database.Chat.id == chat_id).first()

def get_chats(db: Session, skip: int = 0, limit: int = 100):
    return db.query(database.Chat).offset(skip).limit(limit).all()

def create_chat(db: Session, chat: schemas.ChatCreate):
    db_chat = database.Chat(title=chat.title, created_at=datetime.utcnow())
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    return db_chat

def create_chat_message(db: Session, message: schemas.MessageCreate, chat_id: int):
    db_message = database.Message(
        chat_id=chat_id,
        sender=message.sender,
        content=message.content,
        image_path=message.image_path, # Use image_path
        timestamp=datetime.utcnow()
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_messages_for_chat(db: Session, chat_id: int, skip: int = 0, limit: int = 100):
    return db.query(database.Message).filter(database.Message.chat_id == chat_id).offset(skip).limit(limit).all()

def delete_chat(db: Session, chat_id: int):
    db_chat = db.query(database.Chat).filter(database.Chat.id == chat_id).first()
    if db_chat:
        db.delete(db_chat)
        db.commit()
        return True
    return False