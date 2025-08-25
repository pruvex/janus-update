from sqlalchemy.orm import Session
from . import database, schemas, vector_service
import logging
from backend.logger_config import setup_logging
import requests
import uuid
import os
import asyncio # NEW
import concurrent.futures # NEW

from .utils.paths import get_app_data_dir

setup_logging()
logger = logging.getLogger('janus_backend')

IMAGE_DIR = os.path.join(get_app_data_dir(), "images")
os.makedirs(IMAGE_DIR, exist_ok=True)

def save_image_from_url(image_url: str) -> str:
    """Lädt ein Bild von einer URL herunter und speichert es lokal."""
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

        # Dateinamen aus der URL extrahieren oder UUID verwenden
        file_name = str(uuid.uuid4()) + ".png" # Annahme: immer PNG
        file_path = os.path.join(IMAGE_DIR, file_name)

        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Rückgabe des relativen Pfades, der vom Frontend über /static/images/ erreichbar ist
        return f"/static/images/{file_name}"
    except Exception as e:
        logger.error(f"Fehler beim Speichern des Bildes von URL {image_url}: {e}")
        return None

async def migrate_image_paths(db: Session):
    logger.info("Starting image path migration...")
    messages_with_images = db.query(database.Message).filter(database.Message.image_path.isnot(None)).all()
    
    loop = asyncio.get_running_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        tasks = []
        for message in messages_with_images:
            original_path = message.image_path
            # Check if it's an external DALL-E URL (heuristic: starts with http and contains "oaidalleapiprodscus")
            if original_path.startswith("http") and "oaidalleapiprodscus" in original_path:
                logger.info(f"Migrating image for message ID {message.id}: {original_path}")
                # Run the synchronous save_image_from_url in a thread pool
                task = loop.run_in_executor(pool, save_image_from_url, original_path)
                tasks.append((message, task))
            else:
                logger.debug(f"Image path for message ID {message.id} is already local or not a DALL-E URL: {original_path}")
        
        for message, task in tasks:
            local_path = await task # Await the result from the thread pool
            if local_path: # If download was successful
                if local_path != message.image_path: # Ensure it was successfully saved and is a new local path
                    message.image_path = local_path
                    db.add(message)
                    db.commit()
                    logger.info(f"Successfully migrated image for message ID {message.id} to {local_path}")
            else: # If download failed (local_path is None)
                logger.warning(f"Failed to migrate image for message ID {message.id} from {message.image_path}. Setting image_path to NULL.")
                message.image_path = None # Set to NULL
                db.add(message)
                db.commit()
    logger.info("Image path migration complete.")

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
