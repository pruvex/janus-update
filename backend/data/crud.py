import logging
from typing import List, Optional  # Added List here

from backend.logger_config import setup_logging
from backend.services import vector_service
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import contact_schemas, database, schemas

setup_logging()
logger = logging.getLogger("janus_backend")


# --- Chat CRUD ---
def create_chat(db: Session, title: Optional[str] = "Neuer Chat", project_id: Optional[int] = None):
    if title is None:
        title = "Neuer Chat"
    db_chat = database.Chat(title=title, project_id=project_id)
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    return db_chat


def get_chats(db: Session, include_archived: bool = False, project_id: Optional[int] = None):
    query = db.query(database.Chat)
    
    # Filter by archive status if needed
    if not include_archived:
        query = query.filter(database.Chat.is_archived == False)
    
    # Filter by project_id if provided
    if project_id is not None:
        query = query.filter(database.Chat.project_id == project_id)
    else:
        # If no project_id is provided, only show chats without a project
        query = query.filter(database.Chat.project_id == None)
        
    return query.all()


def get_chat_by_id(db: Session, chat_id: int):
    return db.query(database.Chat).filter(database.Chat.id == chat_id).first()


def get_messages_by_chat_id(db: Session, chat_id: int):
    return (
        db.query(database.Message)
        .filter(database.Message.chat_id == chat_id)
        .order_by(database.Message.timestamp)
        .all()
    )


def create_message(db: Session, chat_id: int, sender: str, content: str, image_path: str = None):
    db_message = database.Message(
        chat_id=chat_id, sender=sender, content=content, image_path=image_path
    )
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
    return db.query(database.Chat).filter(database.Chat.summary is not None).all()


def get_memory_by_chat_id(db: Session, chat_id: int):
    return db.query(database.Memory).filter(database.Memory.chat_id == chat_id).all()


# In backend/crud.py
# ... (am Ende der Datei hinzufügen)
# from typing import Optional # This is already imported above, so no need to import again


def get_user_name(db: Session) -> Optional[str]:
    """Sucht im Gedächtnis nach dem Namen des Benutzers."""
    # Wir suchen nach dem spezifischen Fakt, der den Namen festlegt.
    memory_entry = (
        db.query(database.Memory)
        .filter(database.Memory.snippet.like("Der Benutzer heißt %"))
        .first()
    )
    if memory_entry:
        try:
            # Extrahiert den Namen nach dem Muster "Der Benutzer heißt [Name]."
            name = memory_entry.snippet.split("Der Benutzer heißt ")[1].strip().replace(".", "")
            logger.info(f"Benutzername '{name}' aus dem Gedächtnis geladen.")
            return name
        except IndexError:
            return None
    return None


# --- START OF CODE ---
# CRUD-Operationen für die Gedächtnis-Verwaltung
def get_all_memories(db: Session) -> List[database.Memory]:
    """Ruft alle Memory-Einträge ab, die neuesten zuerst."""
    return db.query(database.Memory).order_by(database.Memory.last_accessed_at.desc()).all()


def update_memory(
    db: Session, memory_id: int, snippet: str, category: str
) -> Optional[database.Memory]:
    """Aktualisiert einen bestimmten Memory-Eintrag."""
    db_memory = db.query(database.Memory).filter(database.Memory.id == memory_id).first()
    if db_memory:
        db_memory.snippet = snippet
        db_memory.category = category
        # Wichtig: Bei einer Änderung muss das Embedding neu generiert werden!
        db_memory.embedding_json = vector_service.generate_embedding(snippet)
        db.commit()
        db.refresh(db_memory)
    return db_memory


def delete_memory(db: Session, memory_id: int) -> bool:
    """Löscht einen bestimmten Memory-Eintrag."""
    db_memory = db.query(database.Memory).filter(database.Memory.id == memory_id).first()
    if db_memory:
        db.delete(db_memory)
        db.commit()
        return True
    return False


# --- END OF CODE ---


# --- Contact CRUD ---
def get_contact(db: Session, contact_id: int) -> Optional[contact_schemas.ContactResponse]:
    """Ruft einen einzelnen Kontakt anhand seiner ID ab."""
    db_contact = db.query(database.Contact).filter(database.Contact.id == contact_id).first()
    if db_contact:
        return contact_schemas.ContactResponse.model_validate(db_contact)
    return None


def get_contact_by_email(db: Session, email: str) -> Optional[contact_schemas.ContactResponse]:
    """Ruft einen einzelnen Kontakt anhand seiner E-Mail-Adresse ab."""
    db_contact = db.query(database.Contact).filter(database.Contact.email == email).first()
    if db_contact:
        return contact_schemas.ContactResponse.model_validate(db_contact)
    return None


def get_contacts(
    db: Session, skip: int = 0, limit: int = 100
) -> List[contact_schemas.ContactResponse]:
    """Ruft eine Liste von Kontakten ab."""
    contacts = db.query(database.Contact).offset(skip).limit(limit).all()
    return [contact_schemas.ContactResponse.model_validate(contact) for contact in contacts]


def create_contact(
    db: Session, contact: contact_schemas.ContactCreate
) -> Optional[contact_schemas.ContactResponse]:
    """Erstellt einen neuen Kontakt in der Datenbank mit robuster Fehlerbehandlung."""
    try:
        db_contact = database.Contact(**contact.model_dump())
        db.add(db_contact)
        db.commit()
        db.refresh(db_contact)
        return contact_schemas.ContactResponse.model_validate(db_contact)
    except IntegrityError:
        db.rollback()  # Wichtig: Transaktion bei Duplikat-Fehler zurückrollen
        logger.warning(
            f"Datenbank-Integritätsfehler beim Erstellen des Kontakts '{contact.name}'. Wahrscheinlich ein Duplikat. Überspringe."
        )
        return None
    except Exception as e:
        db.rollback()
        logger.error(
            f"Unerwarteter Datenbankfehler beim Erstellen des Kontakts '{contact.name}': {e}",
            exc_info=True,
        )
        return None


def get_all_contact_names(db: Session) -> List[str]:
    """Gibt eine Liste aller Namen aus der Kontakttabelle zurück."""
    return [name for (name,) in db.query(database.Contact.name).all()]


def get_incomplete_contacts(db: Session) -> List[contact_schemas.ContactResponse]:
    """
    Ruft Kontakte ab, denen wichtige Informationen (Adresse, Telefon, E-Mail) fehlen.
    """
    contacts = (
        db.query(database.Contact)
        .filter(
            (database.Contact.address is None)
            | (database.Contact.address == "")
            | (database.Contact.phone is None)
            | (database.Contact.phone == "")
            | (database.Contact.email is None)
            | (database.Contact.email == "")
        )
        .all()
    )
    return [contact_schemas.ContactResponse.model_validate(contact) for contact in contacts]


def update_contact(db: Session, contact_id: int, updates: dict) -> Optional[database.Contact]:
    """
    Aktualisiert einen Kontakt in der Datenbank und gibt das aktualisierte Objekt zurück.
    Verhindert doppelte E-Mail-Adressen und fügt die E-Mail stattdessen zu den Notizen hinzu.
    """
    db_contact = db.query(database.Contact).filter(database.Contact.id == contact_id).first()
    if not db_contact:
        return None

    # Prüfe auf E-Mail-Duplikate, wenn eine E-Mail aktualisiert wird
    if "email" in updates and updates["email"]:
        existing_contact = (
            db.query(database.Contact)
            .filter(database.Contact.email == updates["email"], database.Contact.id != contact_id)
            .first()
        )

        if existing_contact:
            # Füge die E-Mail zu den Notizen des bestehenden Kontakts hinzu
            if db_contact.notes:
                db_contact.notes += f"\nZugehörige E-Mail (nicht primär): {updates['email']}"
            else:
                db_contact.notes = f"Zugehörige E-Mail (nicht primär): {updates['email']}"

            # Entferne die E-Mail aus den Updates, da sie nicht als primäre E-Mail gesetzt werden soll
            updates.pop("email")
            logger.warning(
                f"E-Mail '{updates['email']}' wird bereits von Kontakt ID {existing_contact.id} verwendet. "
                f"Füge sie stattdessen zu den Notizen von Kontakt ID {contact_id} hinzu."
            )

    # Führe die restlichen Updates durch
    for key, value in updates.items():
        if hasattr(db_contact, key) and value is not None:  # Überspringe None-Werte
            setattr(db_contact, key, value)

    try:
        db.commit()
        db.refresh(db_contact)
        return db_contact
    except Exception as e:
        db.rollback()
        logger.error(f"Fehler beim Aktualisieren des Kontakts ID {contact_id}: {e}", exc_info=True)
        return None


def search_contacts_by_name(db: Session, name_query: str) -> List[contact_schemas.ContactResponse]:
    """
    Sucht nach Kontakten, deren Name den Suchbegriff enthält (case-insensitive).
    """
    contacts = (
        db.query(database.Contact).filter(database.Contact.name.ilike(f"%{name_query}%")).all()
    )
    return [contact_schemas.ContactResponse.model_validate(contact) for contact in contacts]


def delete_contact(db: Session, contact_id: int) -> bool:
    """
    Löscht einen Kontakt anhand seiner ID.
    """
    # --- START GOLDSTANDARD-FIX ---
    # Wir müssen sicherstellen, dass wir das echte Datenbank-Objekt (Model) löschen,
    # nicht ein Pydantic-Schema. 'get_contact' gibt das korrekte Model zurück.
    db_contact_model = db.query(database.Contact).filter(database.Contact.id == contact_id).first()
    # --- ENDE GOLDSTANDARD-FIX ---

    if db_contact_model:
        db.delete(db_contact_model)
        db.commit()
        logger.info(f"Kontakt mit ID {contact_id} wurde gelöscht.")
        return True
    logger.warning(f"Kontakt mit ID {contact_id} zum Löschen nicht gefunden.")
    return False


# --- Project CRUD ---

def create_project(db: Session, name: str, description: Optional[str] = None) -> database.Project:
    """Erstellt ein neues Projekt."""
    db_project = database.Project(name=name, description=description)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def get_project(db: Session, project_id: int) -> Optional[database.Project]:
    """Holt ein Projekt anhand seiner ID."""
    return db.query(database.Project).filter(database.Project.id == project_id).first()


def get_all_projects(db: Session) -> List[database.Project]:
    """Holt alle Projekte."""
    return db.query(database.Project).all()


def add_file_to_project(
    db: Session, project_id: int, filename: str, local_path: str, file_type: str
) -> database.ProjectFile:
    """Fügt eine Datei-Referenz zu einem Projekt hinzu."""
    db_file = database.ProjectFile(
        project_id=project_id,
        filename=filename,
        local_path=local_path,
        file_type=file_type,
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


# --- Image Studio CRUD ---

def create_generated_image(db: Session, image_data: schemas.GeneratedImageCreate, image_url: str) -> database.GeneratedImage:
    """Erstellt einen neuen Eintrag für ein generiertes oder hochgeladenes Bild."""
    db_image = database.GeneratedImage(
        prompt=image_data.prompt,
        style_preset=image_data.style_preset,
        provider=image_data.provider,
        model=image_data.model,
        parameters=image_data.parameters.model_dump(),
        image_url=image_url,
        is_uploaded=False, # Standard für Generierung
        previous_response_id=image_data.previous_response_id,
        previous_image_id=image_data.previous_image_id
    )
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image
