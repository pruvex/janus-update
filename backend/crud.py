from sqlalchemy.orm import Session
from . import database, schemas, vector_service

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