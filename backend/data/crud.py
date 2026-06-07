# backend/data/crud.py
from collections import defaultdict
import os
import re
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
import json
from datetime import datetime

from backend.data import database, models, schemas
# Wir nutzen models für ALLES was Tabellen angeht
import backend.data.models as models 

# Optional: Contact Schemas falls vorhanden
try:
    from backend.data import contact_schemas
except ImportError:
    pass

from backend.logger_config import setup_logging
from backend.services import vector_service
from backend.services.cost_service import (
    ATTRIBUTION_STATUS_EXTERNAL_BILLING,
    ATTRIBUTION_STATUS_INTERNAL,
    ATTRIBUTION_STATUS_UNATTRIBUTED,
    normalize_attribution_status,
)
from sqlalchemy.exc import IntegrityError

setup_logging()
logger = logging.getLogger("janus_backend")


ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"
CHAT_UPDATE_UNSET = object()


def _serialize_embedding_json(embedding_json: str) -> bytes:
    """Serialisiert Embedding-JSON als UTF-8-Bytes für LargeBinary-Spalten."""
    if embedding_json is None:
        return None
    if isinstance(embedding_json, bytes):
        return embedding_json
    return embedding_json.encode("utf-8")


# --- Chat CRUD ---
def create_chat(db: Session, title: Optional[str] = "Neuer Chat", project_id: Optional[int] = None):
    if title is None:
        title = "Neuer Chat"
    db_chat = database.Chat(title=title, project_id=project_id, auto_generated=True)
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    return db_chat


def get_chats(db: Session, include_archived: bool = False, project_id: Optional[int] = None):
    query = db.query(database.Chat)
    
    # FIX: models.Chat statt database.Chat
    if not include_archived:
        query = query.filter(database.Chat.is_archived == False)
    
    if project_id is not None:
        query = query.filter(database.Chat.project_id == project_id)
    else:
        # If no project_id is provided, only show chats without a project
        query = query.filter(database.Chat.project_id == None)

    # Newest chats first (sidebar: highest id / most recently created on top)
    return query.order_by(database.Chat.id.desc()).all()


def get_chat_by_id(db: Session, chat_id: int):
    return db.query(database.Chat).filter(database.Chat.id == chat_id).first()


def get_messages_by_chat_id(db: Session, chat_id: int):
    return (
        db.query(database.Message)
        .filter(database.Message.chat_id == chat_id)
        .order_by(database.Message.created_at)
        .all()
    )


def create_message(
    db: Session,
    chat_id: int,
    sender: str,
    content: str,
    image_path: str = None,
    metadata: Optional[Dict[str, Any]] = None,
    modal_request: Optional[Dict[str, Any]] = None,
):
    """Create a chat message using canonical DB roles (user/assistant)."""
    normalized_sender = str(sender or "").strip().lower()
    role = ROLE_USER if normalized_sender == ROLE_USER else ROLE_ASSISTANT

    db_message = database.Message(
        chat_id=chat_id,
        role=role,
        content=content,
    )

    metadata_payload: Dict[str, Any] = {}
    if isinstance(metadata, dict):
        metadata_payload.update(metadata)
    if image_path:
        metadata_payload["image_path"] = image_path
    if isinstance(modal_request, dict):
        metadata_payload["modal_request"] = modal_request
    if isinstance(metadata, dict) and "video_list_metadata" in metadata:
        metadata_payload["video_list_metadata"] = metadata["video_list_metadata"]
    if metadata_payload:
        db_message.metadata_json = json.dumps(metadata_payload, ensure_ascii=False)

    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def update_chat_title(db: Session, chat_id: int, new_title: str):
    chat = get_chat_by_id(db, chat_id)
    if chat:
        chat.title = new_title
        chat.auto_generated = False
        db.commit()
        db.refresh(chat)
    return chat


def update_chat_header_llm(
    db: Session,
    chat_id: int,
    provider=CHAT_UPDATE_UNSET,
    model=CHAT_UPDATE_UNSET,
):
    chat = get_chat_by_id(db, chat_id)
    if not chat:
        return None

    if provider is not CHAT_UPDATE_UNSET:
        if provider is None:
            chat.header_provider = None
        else:
            provider_value = str(provider).strip()
            chat.header_provider = provider_value or None

    if model is not CHAT_UPDATE_UNSET:
        if model is None:
            chat.header_model = None
        else:
            model_value = str(model).strip()
            chat.header_model = model_value or None

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


def get_document_by_filename(db: Session, filename: str) -> Optional[models.Document]:
    return db.query(models.Document).filter(models.Document.filename == filename).first()


def create_document(db: Session, filename: str, file_path: str, project_id: Optional[int] = None) -> models.Document:
    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
    new_doc = models.Document(
        filename=filename,
        file_path=file_path,
        file_size=file_size,
        project_id=project_id,
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    return new_doc


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
    return db.query(models.Memory).filter(models.Memory.chat_id == chat_id).all()


# In backend/crud.py
# ... (am Ende der Datei hinzufügen)
# from typing import Optional # This is already imported above, so no need to import again


def get_default_user_suggestion_mode(db: Session) -> int:
    """Return ``users.suggestion_mode`` for the primary user row, or ``1`` if unavailable."""
    try:
        row = db.query(models.User).order_by(models.User.id.asc()).first()
        if row is not None:
            raw = getattr(row, "suggestion_mode", None)
            if raw is not None:
                return int(raw)
    except Exception:
        logger.debug("get_default_user_suggestion_mode: fallback to 1", exc_info=True)
    return 1


def get_user_name(db: Session) -> Optional[str]:
    """Sucht im Gedächtnis nach dem Namen des Benutzers mit neuer, robuster Methode."""
    import json as _json, re as _re

    # 1. Bevorzugte Methode: Suche nach der dedizierten Kategorie
    memory_entry = (
        db.query(models.Memory).filter(models.Memory.category == "USER_NAME").first()
    )

    if memory_entry:
        try:
            # Extrahiert den Namen aus dem Snippet, z.B. "Der Benutzer heißt Peter."
            name = memory_entry.snippet.split(" ", 3)[-1].strip().rstrip(".")
            return name
        except IndexError:
            return None

    memory_entry_old = (
        db.query(models.Memory)
        .filter(models.Memory.snippet.like("Der Benutzer heißt %"))
        .first()
    )

    if memory_entry_old:
        try:
            name = memory_entry_old.snippet.split("Der Benutzer heißt ")[1].strip().replace(".", "")
            update_memory_category(db, memory_entry_old.id, "USER_NAME")
            return name
        except IndexError:
            return None

    # 3. Memory-V2 canonical_key lookup (Task 014)
    # Identity facts from the pre-pass are stored with canonical_key='user:physis:heisst:name'
    identity_entry = (
        db.query(models.Memory)
        .filter(models.Memory.canonical_key == "user:physis:heisst:name")
        .order_by(models.Memory.priority.desc())
        .first()
    )
    if identity_entry:
        try:
            snippet_obj = _json.loads(identity_entry.snippet or "{}")
            raw = snippet_obj.get("object_value") or snippet_obj.get("fact", "")
            _m = _re.search(r'hei(?:ß|ss)t\s+(.+)', str(raw), _re.IGNORECASE)
            if _m:
                return _m.group(1).strip().rstrip(".,!? ").title()
            if raw:
                return str(raw).strip().title()
        except (_json.JSONDecodeError, TypeError):
            pass
    return None


def update_memory_category(db: Session, memory_id: int, new_category: str) -> bool:
    """Aktualisiert die Kategorie eines Memory-Eintrags."""
    db_memory = db.query(models.Memory).filter(models.Memory.id == memory_id).first()
    if db_memory:
        db_memory.category = new_category
        db.commit()
        return True
    return False


# --- START OF CODE ---
# CRUD-Operationen für die Gedächtnis-Verwaltung
def get_all_memories(db: Session) -> List[models.Memory]:
    """Ruft alle Memory-Einträge ab, die neuesten zuerst."""
    return db.query(models.Memory).order_by(models.Memory.last_accessed_at.desc()).all()


def update_memory(
    db: Session, memory_id: int, snippet: str, category: str
) -> Optional[models.Memory]:
    db_memory = db.query(models.Memory).filter(models.Memory.id == memory_id).first()
    if db_memory:
        db_memory.snippet = snippet
        db_memory.category = category
        db_memory.embedding_json = _serialize_embedding_json(
            vector_service.generate_embedding(snippet)
        )
        db.commit()
        db.refresh(db_memory)
    return db_memory


def delete_memory(db: Session, memory_id: int) -> bool:
    """Löscht einen bestimmten Memory-Eintrag."""
    db_memory = db.query(models.Memory).filter(models.Memory.id == memory_id).first()
    if db_memory:
        db.delete(db_memory)
        db.commit()
        return True
    return False


# --- END OF CODE ---


# --- Contact CRUD ---
def _contact_response_from_model(contact: models.Contact) -> contact_schemas.ContactResponse:
    return contact_schemas.ContactResponse.model_validate(
        {
            "id": contact.id,
            "name": contact.name,
            "contact_type": getattr(contact, "contact_type", None),
            "category": contact.category,
            "email": contact.email,
            "phone": contact.phone,
            "address": contact.address,
            "website": contact.website,
            "preferences": getattr(contact, "preferences", None),
            "dislikes": getattr(contact, "dislikes", None),
            "personal_details": getattr(contact, "personal_details", None),
            "notes": contact.notes,
            "proposal_status": getattr(contact, "proposal_status", None),
            "proposal_source_context": getattr(contact, "proposal_source_context", None),
            "proposal_last_outcome": getattr(contact, "proposal_last_outcome", None),
            "memory_sync_status": getattr(contact, "memory_sync_status", None),
            "created_at": contact.created_at,
        }
    )


def get_contact(db: Session, contact_id: int) -> Optional[contact_schemas.ContactResponse]:
    db_contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    if db_contact:
        return _contact_response_from_model(db_contact)
    return None


def get_contact_by_email(db: Session, email: str) -> Optional[contact_schemas.ContactResponse]:
    db_contact = db.query(models.Contact).filter(models.Contact.email == email).first()
    if db_contact:
        return _contact_response_from_model(db_contact)
    return None


def get_contacts(
    db: Session, skip: int = 0, limit: int = 100
) -> List[contact_schemas.ContactResponse]:
    contacts = db.query(models.Contact).offset(skip).limit(limit).all()
    return [_contact_response_from_model(contact) for contact in contacts]


def create_contact(
    db: Session, contact: contact_schemas.ContactCreate
) -> Optional[contact_schemas.ContactResponse]:
    try:
        db_contact = models.Contact(
            name=contact.name,
            contact_type=contact.contact_type or "private_person",
            email=contact.email,
            phone=contact.phone,
            address=contact.address,
            website=contact.website,
            preferences=contact.preferences or [],
            dislikes=contact.dislikes or [],
            personal_details=contact.personal_details or [],
            notes=contact.notes,
            category=contact.category or "Unkategorisiert",
            proposal_status=contact.proposal_status or "confirmed",
            proposal_source_context=contact.proposal_source_context,
            proposal_last_outcome=contact.proposal_last_outcome,
            memory_sync_status=contact.memory_sync_status or "unlinked",
        )
        db.add(db_contact)
        db.commit()
        db.refresh(db_contact)
        return _contact_response_from_model(db_contact)
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
    return [contact.name for contact in db.query(models.Contact).all() if contact.name]


def get_incomplete_contacts(db: Session) -> List[contact_schemas.ContactResponse]:
    """
    Ruft Kontakte ab, denen wichtige Informationen (Adresse, Telefon, E-Mail) fehlen.
    """
    contacts = db.query(models.Contact).all()
    incomplete = []
    for contact in contacts:
        missing = []
        if not contact.email:
            missing.append("E-Mail")
        if not contact.phone:
            missing.append("Telefon")
        if not contact.address:
            missing.append("Adresse")
            
        if missing:
            incomplete.append({
                'id': contact.id,
                'name': contact.name,
                'missing': ", ".join(missing)
            })
    return [contact_schemas.ContactResponse.model_validate(contact) for contact in incomplete]


def update_contact(db: Session, contact_id: int, updates: dict) -> Optional[models.Contact]:
    """
    Aktualisiert einen Kontakt in der Datenbank und gibt das aktualisierte Objekt zurück.
    Verhindert doppelte E-Mail-Adressen und fügt die E-Mail stattdessen zu den Notizen hinzu.
    """
    db_contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    if not db_contact:
        return None

    # Prüfe auf E-Mail-Duplikate, wenn eine E-Mail aktualisiert wird
    if "email" in updates and updates["email"]:
        duplicate_email = updates["email"]
        existing_contact = (
            db.query(models.Contact)
            .filter(models.Contact.email == updates["email"], models.Contact.id != contact_id)
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
                f"E-Mail '{duplicate_email}' wird bereits von Kontakt ID {existing_contact.id} verwendet. "
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
    except Exception:
        db.rollback()
        logger.error("Error in crud.update_contact: commit failed", exc_info=True)
        return None


def search_contacts_by_name(db: Session, name_query: str) -> List[contact_schemas.ContactResponse]:
    """
    Sucht nach Kontakten, deren Name den Suchbegriff enthält (case-insensitive).
    """
    contacts = (
        db.query(models.Contact).filter(
            models.Contact.name.ilike(f'%{name_query}%')
        ).all()
    )
    return [_contact_response_from_model(contact) for contact in contacts]


def delete_contact(db: Session, contact_id: int) -> bool:
    """
    Löscht einen Kontakt anhand seiner ID.
    """
    # --- START GOLDSTANDARD-FIX ---
    # Wir müssen sicherstellen, dass wir das echte Datenbank-Objekt (Model) löschen,
    # nicht ein Pydantic-Schema. 'get_contact' gibt das korrekte Model zurück.
    db_contact_model = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    # --- ENDE GOLDSTANDARD-FIX ---

    if db_contact_model:
        db.delete(db_contact_model)
        db.commit()
        logger.info(f"Kontakt mit ID {contact_id} wurde gelöscht.")
        return True
    logger.warning(f"Kontakt mit ID {contact_id} zum Löschen nicht gefunden.")
    return False


# --- Contact Proposal CRUD ---

def get_contact_proposal_by_key(db: Session, proposal_key: str) -> Optional[models.ContactProposal]:
    return (
        db.query(models.ContactProposal)
        .filter(models.ContactProposal.proposal_key == proposal_key)
        .first()
    )


def create_or_update_contact_proposal(
    db: Session,
    *,
    proposal_batch_id: str,
    proposal_key: str,
    chat_id: Optional[int],
    contact_id: Optional[int],
    contact_name: str,
    proposal_type: str,
    status: str,
    evidence_hash: str,
    source_context: Optional[str],
    payload_json: Optional[Dict[str, Any]],
) -> Optional[models.ContactProposal]:
    record = get_contact_proposal_by_key(db, proposal_key)
    now = datetime.utcnow()
    if record is None:
        record = models.ContactProposal(
            proposal_batch_id=proposal_batch_id,
            proposal_key=proposal_key,
            chat_id=chat_id,
            contact_id=contact_id,
            contact_name=contact_name,
            proposal_type=proposal_type,
            status=status,
            evidence_hash=evidence_hash,
            source_context=source_context,
            payload_json=payload_json or {},
            resolved_at=now if status in {"rejected", "applied", "failed"} else None,
        )
        db.add(record)
    else:
        record.proposal_batch_id = proposal_batch_id
        record.chat_id = chat_id
        record.contact_id = contact_id
        record.contact_name = contact_name
        record.proposal_type = proposal_type
        record.status = status
        record.evidence_hash = evidence_hash
        record.source_context = source_context
        record.payload_json = payload_json or {}
        record.updated_at = now
        record.resolved_at = now if status in {"rejected", "applied", "failed"} else None

    try:
        db.commit()
        db.refresh(record)
        return record
    except Exception:
        db.rollback()
        logger.error("Error in create_or_update_contact_proposal: commit failed", exc_info=True)
        return None


def update_contact_proposal_status(
    db: Session,
    *,
    proposal_id: int,
    status: str,
    contact_id: Optional[int] = None,
    payload_json: Optional[Dict[str, Any]] = None,
) -> Optional[models.ContactProposal]:
    record = db.query(models.ContactProposal).filter(models.ContactProposal.id == proposal_id).first()
    if not record:
        return None

    record.status = status
    record.updated_at = datetime.utcnow()
    record.resolved_at = datetime.utcnow() if status in {"rejected", "applied", "failed"} else None
    if contact_id is not None:
        record.contact_id = contact_id
    if payload_json is not None:
        record.payload_json = payload_json

    try:
        db.commit()
        db.refresh(record)
        return record
    except Exception:
        db.rollback()
        logger.error("Error in update_contact_proposal_status: commit failed", exc_info=True)
        return None


def update_contact_proposals_batch_status(
    db: Session,
    *,
    proposal_batch_id: str,
    status: str,
) -> int:
    records = (
        db.query(models.ContactProposal)
        .filter(models.ContactProposal.proposal_batch_id == proposal_batch_id)
        .all()
    )
    if not records:
        return 0

    now = datetime.utcnow()
    for record in records:
        record.status = status
        record.updated_at = now
        record.resolved_at = now if status in {"rejected", "applied", "failed"} else None

    try:
        db.commit()
        return len(records)
    except Exception:
        db.rollback()
        logger.error("Error in update_contact_proposals_batch_status: commit failed", exc_info=True)
        return 0


def _serialize_contact_proposal(record: models.ContactProposal) -> Dict[str, Any]:
    return {
        "id": record.id,
        "proposal_batch_id": record.proposal_batch_id,
        "proposal_key": record.proposal_key,
        "chat_id": record.chat_id,
        "contact_id": record.contact_id,
        "contact_name": record.contact_name,
        "proposal_type": record.proposal_type,
        "status": record.status,
        "evidence_hash": record.evidence_hash,
        "source_context": record.source_context,
        "payload_json": record.payload_json or {},
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
        "resolved_at": record.resolved_at.isoformat() if record.resolved_at else None,
    }


def list_contact_proposals(
    db: Session,
    *,
    contact_id: int,
    status: Optional[str] = None,
) -> List[Dict[str, Any]]:
    query = (
        db.query(models.ContactProposal)
        .filter(models.ContactProposal.contact_id == contact_id)
        .order_by(models.ContactProposal.created_at.desc())
    )
    if status:
        query = query.filter(models.ContactProposal.status == status)
    return [_serialize_contact_proposal(record) for record in query.all()]


# --- Project CRUD ---

def create_project(db: Session, name: str, description: Optional[str] = None) -> models.Project:
    """Erstellt ein neues Projekt."""
    db_project = models.Project(name=name, description=description)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def get_project(db: Session, project_id: int) -> Optional[models.Project]:
    """Holt ein Projekt anhand seiner ID."""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    return project


def get_all_projects(db: Session) -> List[models.Project]:
    """Holt alle Projekte."""
    return db.query(models.Project).all()


def add_file_to_project(
    db: Session, project_id: int, filename: str, local_path: str, file_type: str
) -> models.ProjectFile:
    db_file = models.ProjectFile(
        project_id=project_id,
        filename=filename,
        file_path=local_path, # FIX: Feldname in models.py ist file_path
        file_type=file_type
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


# --- Image Studio CRUD ---

def create_generated_image(db: Session, image_data: schemas.GeneratedImageCreate, image_url: str) -> models.GeneratedImage:
    """Erstellt einen neuen Eintrag für ein generiertes oder hochgeladenes Bild."""
    # Parameter sicher extrahieren
    params_to_save = {}
    if image_data.parameters:
        if isinstance(image_data.parameters, dict):
            params_to_save = image_data.parameters
        elif hasattr(image_data.parameters, "model_dump"):
            params_to_save = image_data.parameters.model_dump()
        elif hasattr(image_data.parameters, "dict"):
            params_to_save = image_data.parameters.dict()

    # --- FIX: Safe Access mit getattr ---
    # Falls das Schema diese Felder nicht hat (z.B. bei Generierung), nutzen wir None
    content_hash = getattr(image_data, 'content_hash', None)
    tags = getattr(image_data, 'tags', None)
    is_uploaded = getattr(image_data, 'is_uploaded', False)
    provider_response_id = getattr(image_data, 'provider_response_id', None)

    db_image = models.GeneratedImage(
        prompt=image_data.prompt,
        style_preset=image_data.style_preset,
        variation_preset=image_data.variation_preset,
        provider=image_data.provider,
        model=image_data.model,
        parameters=params_to_save, 
        
        # Wichtig: Mapping auf die richtigen Model-Felder
        url=image_url, 
        file_path=image_url, 
        
        is_uploaded=is_uploaded,
        previous_response_id=image_data.previous_response_id,
        previous_image_id=image_data.previous_image_id,
        quality_gate_stats=image_data.quality_gate_stats,
        provider_response_id=provider_response_id,
        
        # Hier knallte es vorher:
        tags=tags,
        content_hash=content_hash
    )
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image


def create_orchestrator_kpi(
    db: Session,
    *,
    provider: str,
    model: Optional[str],
    chat_id: Optional[int],
    is_meta_agent_run: bool,
    t_phase1_research_ms: Optional[float],
    t_phase2_pdf_ms: Optional[float],
    t_final_response_ms: float,
    retry_path: str,
    retry_count: int,
    success: bool,
    error_code: Optional[str],
) -> models.OrchestratorKPI:
    row = models.OrchestratorKPI(
        provider=str(provider or "unknown").lower(),
        model=str(model or "").strip() or None,
        chat_id=chat_id if isinstance(chat_id, int) else None,
        is_meta_agent_run=bool(is_meta_agent_run),
        t_phase1_research_ms=(float(t_phase1_research_ms) if t_phase1_research_ms is not None else None),
        t_phase2_pdf_ms=(float(t_phase2_pdf_ms) if t_phase2_pdf_ms is not None else None),
        t_final_response_ms=max(0.0, float(t_final_response_ms)),
        retry_path=str(retry_path or "none").strip() or "none",
        retry_count=max(0, int(retry_count or 0)),
        success=bool(success),
        error_code=str(error_code or "").strip() or None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _calc_percentile(values: List[float], percentile: float) -> Optional[float]:
    if not values:
        return None
    sorted_values = sorted(float(v) for v in values)
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = (len(sorted_values) - 1) * max(0.0, min(100.0, float(percentile))) / 100.0
    lower = int(rank)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = rank - lower
    return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight


def get_orchestrator_kpi_dashboard(db: Session, year: int, month: int) -> Dict[str, Any]:
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    rows = (
        db.query(models.OrchestratorKPI)
        .filter(
            models.OrchestratorKPI.timestamp >= start_date,
            models.OrchestratorKPI.timestamp < end_date,
        )
        .all()
    )

    provider_stats: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {
            "count": 0,
            "phase1": [],
            "phase2": [],
            "final": [],
            "errors": 0,
            "meta_runs": 0,
        }
    )
    retry_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"count": 0, "errors": 0})

    for row in rows:
        provider = str(row.provider or "unknown").lower()
        p = provider_stats[provider]
        p["count"] += 1
        p["meta_runs"] += 1 if row.is_meta_agent_run else 0
        if row.t_phase1_research_ms is not None:
            p["phase1"].append(float(row.t_phase1_research_ms))
        if row.t_phase2_pdf_ms is not None:
            p["phase2"].append(float(row.t_phase2_pdf_ms))
        p["final"].append(float(row.t_final_response_ms or 0.0))
        if not row.success:
            p["errors"] += 1

        retry_key = str(row.retry_path or "none")
        retry_stats[retry_key]["count"] += 1
        if not row.success:
            retry_stats[retry_key]["errors"] += 1

    providers_payload = {}
    for provider, values in provider_stats.items():
        providers_payload[provider] = {
            "count": values["count"],
            "meta_runs": values["meta_runs"],
            "error_rate": (values["errors"] / values["count"]) if values["count"] else 0.0,
            "t_phase1_research_ms": {
                "p50": _calc_percentile(values["phase1"], 50),
                "p95": _calc_percentile(values["phase1"], 95),
            },
            "t_phase2_pdf_ms": {
                "p50": _calc_percentile(values["phase2"], 50),
                "p95": _calc_percentile(values["phase2"], 95),
            },
            "t_final_response_ms": {
                "p50": _calc_percentile(values["final"], 50),
                "p95": _calc_percentile(values["final"], 95),
            },
        }

    retry_payload = {}
    for retry_path, values in retry_stats.items():
        count = int(values["count"])
        errors = int(values["errors"])
        retry_payload[retry_path] = {
            "count": count,
            "errors": errors,
            "error_rate": (errors / count) if count else 0.0,
        }

    return {
        "period": f"{year:04d}-{month:02d}",
        "total_runs": len(rows),
        "providers": providers_payload,
        "retry_paths": retry_payload,
    }


# --- NEU: Kosten-Funktion (Ersatz für database.get_costs_for_month) ---
def get_costs_for_month(db: Session, year: int, month: int):
    """Berechnet die Gesamtkosten für einen bestimmten Monat."""
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
        
    costs = db.query(models.Cost).filter(
        models.Cost.timestamp >= start_date,
        models.Cost.timestamp < end_date
    ).all()
    return sum(cost.total_cost for cost in costs)


def get_monthly_cost_summary_by_model(db: Session, year: int, month: int) -> List[Dict[str, Any]]:
    """
    Erstellt eine zusammengefasste Kostenübersicht für den angegebenen Monat,
    gruppiert nach Modell, inklusive Web-Recherche-Kosten aus orchestrator_kpis.
    """
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    # DIAGNOSTIC: log query parameters
    total_all = db.query(models.Cost).count()
    print(f"[COST-AUDIT] start_date={start_date!r}, end_date={end_date!r}, total_costs_in_db={total_all}")
    logger.warning(f"[COST-AUDIT] start_date={start_date!r}, end_date={end_date!r}, total_costs_in_db={total_all}")

    # Query 1: Cost data grouped by model — use date range (SQLite-compatible, not extract())
    costs = db.query(models.Cost).filter(
        models.Cost.timestamp >= start_date,
        models.Cost.timestamp < end_date
    ).all()
    print(f"[COST-AUDIT] filtered by month: {len(costs)} rows found")
    logger.warning(f"[COST-AUDIT] filtered by month: {len(costs)} rows found")

    # Fallback: if no costs for current month, get all costs
    if not costs:
        costs = db.query(models.Cost).all()
        print(f"[COST-AUDIT] FALLBACK: using all {len(costs)} rows (month filter returned 0)")
        logger.warning(f"[COST-AUDIT] FALLBACK: using all {len(costs)} rows (month filter returned 0)")

    summary = defaultdict(lambda: {
        "total_cost": 0.0, 
        "total_input_tokens": 0, 
        "total_output_tokens": 0, 
        "total_cached_tokens": 0,
        "total_tokens": 0,
        "image_count": 0,
        "total_tokens_saved": 0,
        "total_cost_saved": 0.0,
        "image_details": defaultdict(lambda: {"count": 0, "cost": 0.0}),
        "context_breakdown": defaultdict(lambda: {"count": 0, "cost": 0.0, "input_tokens": 0, "output_tokens": 0, "cached_tokens": 0, "total_tokens": 0})
    })

    # Separate websearch costs from LLM costs using context field prefix
    web_search_total_cost = 0.0
    web_search_query_count = 0

    for cost in costs:
        ctx = str(cost.context or "").strip()
        if ctx.startswith("websearch"):
            # Accumulate websearch costs separately
            web_search_total_cost += cost.total_cost
            # Extract query_count from context like "websearch (query_count=3)"
            qc_match = re.search(r"query_count=(\d+)", ctx)
            web_search_query_count += int(qc_match.group(1)) if qc_match else 1
            continue  # Don't add to model summary

        key = cost.model or "Unbekannt"
        summary[key]["total_cost"] += cost.total_cost
        summary[key]["total_input_tokens"] += cost.input_tokens
        summary[key]["total_output_tokens"] += cost.output_tokens
        cached_tokens = int(getattr(cost, "cached_tokens", 0) or 0)
        total_tokens = int(getattr(cost, "total_tokens", 0) or 0) or int((cost.input_tokens or 0) + (cost.output_tokens or 0))
        summary[key]["total_cached_tokens"] += cached_tokens
        summary[key]["total_tokens"] += total_tokens
        summary[key]["total_tokens_saved"] += int(cost.tokens_saved or 0)
        summary[key]["total_cost_saved"] += float(cost.cost_saved or 0.0)
        context_key = ctx or "conversation"
        summary[key]["context_breakdown"][context_key]["count"] += 1
        summary[key]["context_breakdown"][context_key]["cost"] += cost.total_cost
        summary[key]["context_breakdown"][context_key]["input_tokens"] += cost.input_tokens
        summary[key]["context_breakdown"][context_key]["output_tokens"] += cost.output_tokens
        summary[key]["context_breakdown"][context_key]["cached_tokens"] += cached_tokens
        summary[key]["context_breakdown"][context_key]["total_tokens"] += total_tokens

        if cost.context and "image" in cost.context:
            summary[key]["image_count"] += 1
            match = re.search(r"Size: (.*?), Quality: (.*?)\)", cost.context)
            if match:
                size, quality = match.groups()
                detail_key = f"{quality}_{size}"
                summary[key]["image_details"][detail_key]["count"] += 1
                summary[key]["image_details"][detail_key]["cost"] += cost.total_cost
    
    # Build results
    results = []
    
    # Add model-based cost entries
    for model, data in summary.items():
        image_details_list = [
            {"quality": k.split('_')[0], "size": k.split('_')[1], "count": v["count"], "cost": v["cost"]}
            for k, v in data["image_details"].items()
        ]
        context_breakdown_list = [
            {
                "context": context,
                "count": values["count"],
                "cost": values["cost"],
                "input_tokens": values["input_tokens"],
                "output_tokens": values["output_tokens"],
                "cached_tokens": values["cached_tokens"],
                "total_tokens": values["total_tokens"],
            }
            for context, values in sorted(
                data["context_breakdown"].items(),
                key=lambda item: item[1]["cost"],
                reverse=True,
            )
        ]
        results.append({
            "model": model,
            "total_cost": data["total_cost"],
            "total_input_tokens": data["total_input_tokens"],
            "total_output_tokens": data["total_output_tokens"],
            "total_cached_tokens": data["total_cached_tokens"],
            "total_tokens": data["total_tokens"],
            "image_count": data["image_count"],
            "total_tokens_saved": data["total_tokens_saved"],
            "total_cost_saved": data["total_cost_saved"],
            "image_details": image_details_list,
            "context_breakdown": context_breakdown_list,
            "search_count": 0,  # Model entries don't have search count
            "search_cost": 0.0,
        })
    
    # Add web search entry if there are searches (from costs table, context starts with 'websearch')
    if web_search_total_cost > 0:
        results.append({
            "model": "__WEB_SEARCHES__",  # Special marker for frontend
            "display_name": "Web-Recherchen",
            "total_cost": web_search_total_cost,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "image_count": 0,
            "image_details": [],
            "context_breakdown": [],
            "search_count": web_search_query_count,
            "search_cost": web_search_total_cost,
        })
    
    return results


def _cost_month_bounds(year: int, month: int) -> tuple[datetime, datetime]:
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    return start_date, end_date


def _cost_component_name(cost: models.Cost) -> str:
    component = str(getattr(cost, "attribution_component", "") or "").strip()
    if component:
        return component
    context = str(getattr(cost, "context", "") or "").strip().casefold()
    if context.startswith("websearch"):
        return "grounding_websearch"
    if context.startswith("conversation"):
        return "conversation"
    return "unknown"


def _cost_group_identity(cost: models.Cost) -> tuple[str, str, str]:
    test_run_id = str(getattr(cost, "attribution_test_run_id", "") or "").strip()
    if test_run_id:
        return "test_run", test_run_id, f"Testlauf {test_run_id}"
    session_id = str(getattr(cost, "attribution_session_id", "") or "").strip()
    if session_id:
        return "session", session_id, f"Session {session_id}"
    return "unscoped", "__unscoped__", "Nicht gruppiert"


def _extract_external_billing_reference(metadata: Dict[str, Any]) -> Optional[float]:
    if not isinstance(metadata, dict):
        return None
    for key in (
        "external_billing_total_eur",
        "external_billing_total",
        "billing_reference_total_eur",
        "billing_reference_total",
    ):
        value = metadata.get(key)
        if isinstance(value, (int, float)):
            return float(value)
        try:
            if value is not None and str(value).strip():
                return float(str(value).strip())
        except (TypeError, ValueError):
            continue
    return None


def _cost_has_request_identity(cost: models.Cost) -> bool:
    return bool(
        str(getattr(cost, "attribution_request_id", "") or "").strip()
        or str(getattr(cost, "attribution_group_id", "") or "").strip()
    )


def _new_cost_totals() -> Dict[str, Any]:
    return {
        "total_cost": 0.0,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_cached_tokens": 0,
        "total_tokens": 0,
        "total_tokens_saved": 0,
        "total_cost_saved": 0.0,
    }


def _build_truthfulness_hints(
    *,
    unattributed_residual_total: float,
    deviation_total: float,
    historical_mode: bool,
    cross_provider_totals: Dict[str, Any],
    model_breakdown: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    hints: List[Dict[str, Any]] = []
    if unattributed_residual_total > 0:
        hints.append(
            {
                "type": "attribution_partial",
                "severity": "warning",
                "cost": round(unattributed_residual_total, 6),
                "message": (
                    "Ein historischer Kostenanteil bleibt noch als sichtbarer Rest bestehen."
                    if historical_mode
                    else "Ein kleiner Kostenanteil ist noch nicht eindeutig zugeordnet."
                ),
            }
        )
    if abs(deviation_total) > 1e-9:
        hints.append(
            {
                "type": "billing_alignment_partial",
                "severity": "info",
                "cost": round(abs(deviation_total), 6),
                "message": "Die interne Kostensicht ist noch nicht vollstaendig mit der Billing-Referenz abgeglichen.",
            }
        )
    if cross_provider_totals["total_cost"] > 0 and not model_breakdown:
        hints.append(
            {
                "type": "model_visibility_partial",
                "severity": "info",
                "cost": 0.0,
                "message": "Fuer einen Teil der Kosten ist derzeit keine belastbare Modellsicht verfuegbar.",
            }
        )
    return hints


def _accumulate_cost_totals(target: Dict[str, Any], cost: models.Cost, total_cost: float) -> None:
    cached_tokens = int(getattr(cost, "cached_tokens", 0) or 0)
    total_tokens = int(getattr(cost, "total_tokens", 0) or 0) or int((cost.input_tokens or 0) + (cost.output_tokens or 0))
    target["total_cost"] += total_cost
    target["total_input_tokens"] += int(cost.input_tokens or 0)
    target["total_output_tokens"] += int(cost.output_tokens or 0)
    target["total_cached_tokens"] += cached_tokens
    target["total_tokens"] += total_tokens
    target["total_tokens_saved"] += int(getattr(cost, "tokens_saved", 0) or 0)
    target["total_cost_saved"] += float(getattr(cost, "cost_saved", 0.0) or 0.0)


def get_costs_deep_dive_summary(db: Session, year: int, month: int) -> Dict[str, Any]:
    start_date, end_date = _cost_month_bounds(year, month)
    costs = (
        db.query(models.Cost)
        .filter(
            models.Cost.timestamp >= start_date,
            models.Cost.timestamp < end_date,
        )
        .order_by(models.Cost.timestamp.asc(), models.Cost.id.asc())
        .all()
    )

    groups_index: Dict[str, Dict[str, Any]] = {}
    request_index: Dict[tuple[str, str], Dict[str, Any]] = {}
    request_order: List[tuple[str, str]] = []
    provider_index: Dict[str, Dict[str, Any]] = {}
    model_index: Dict[tuple[str, str], Dict[str, Any]] = {}
    gemini_external_reference_values: List[float] = []
    gemini_total_billed_cost = 0.0
    gemini_internal_attributed_total = 0.0
    gemini_unattributed_residual_total = 0.0
    gemini_avoidable_pro_total = 0.0
    historical_mode = year == 2026 and month == 5
    cross_provider_totals = _new_cost_totals()

    for cost in costs:
        provider = str(cost.provider or "unknown")
        model = str(cost.model or "Unbekannt")
        metadata = dict(cost.attribution_metadata or {}) if isinstance(cost.attribution_metadata, dict) else {}
        total_cost = float(cost.total_cost or 0.0)
        component_name = _cost_component_name(cost)

        _accumulate_cost_totals(cross_provider_totals, cost, total_cost)

        provider_entry = provider_index.setdefault(
            provider,
            {
                "provider": provider,
                **_new_cost_totals(),
                "_models": set(),
            },
        )
        _accumulate_cost_totals(provider_entry, cost, total_cost)
        provider_entry["_models"].add(model)

        model_entry = model_index.setdefault(
            (provider, model),
            {
                "provider": provider,
                "model": model,
                **_new_cost_totals(),
                "request_count": 0,
                "component_breakdown": defaultdict(lambda: {"count": 0, "total_cost": 0.0}),
            },
        )
        _accumulate_cost_totals(model_entry, cost, total_cost)
        model_entry["component_breakdown"][component_name]["count"] += 1
        model_entry["component_breakdown"][component_name]["total_cost"] += total_cost

        group_kind, group_value, group_label = _cost_group_identity(cost)
        has_request_identity = _cost_has_request_identity(cost)
        gemini_gap = provider == "gemini" and not has_request_identity
        if group_kind == "unscoped" and provider != "gemini":
            group_kind = "provider"
            group_value = provider
            group_label = f"Provider {provider}"
        group_key = f"{group_kind}:{group_value}"

        group = groups_index.setdefault(
            group_key,
            {
                "group_key": group_key,
                "group_kind": group_kind,
                "group_value": group_value,
                "group_label": group_label,
                "request_count": 0,
                "total_cost": 0.0,
                "total_cached_tokens": 0,
                "total_tokens_saved": 0,
                "total_cost_saved": 0.0,
                "internal_attributed_total": 0.0,
                "unattributed_residual_total": 0.0,
                "providers": set(),
                "models": set(),
                "requests": [],
            },
        )
        group["providers"].add(provider)
        group["models"].add(model)

        request_value = (
            str(getattr(cost, "attribution_request_id", "") or "").strip()
            or str(getattr(cost, "attribution_group_id", "") or "").strip()
            or (f"legacy-cost:{cost.id}" if provider == "gemini" else f"{provider}-cost:{cost.id}")
        )
        request_lookup_key = (group_key, request_value)
        request = request_index.get(request_lookup_key)
        if request is None:
            request = {
                "request_id": request_value,
                "request_label": (
                    request_value
                    if has_request_identity
                    else (f"Legacy-Kostenblock {cost.id}" if provider == "gemini" else f"{model} Kostenblock {cost.id}")
                ),
                "group_key": group_key,
                "group_kind": group_kind,
                "group_label": group_label,
                "timestamp": cost.timestamp.isoformat() if getattr(cost, "timestamp", None) else None,
                "provider": provider,
                "models": [],
                "total_cost": 0.0,
                "total_cached_tokens": 0,
                "total_tokens_saved": 0,
                "total_cost_saved": 0.0,
                "internal_attributed_total": 0.0,
                "unattributed_residual_total": 0.0,
                "attribution_status": ATTRIBUTION_STATUS_INTERNAL,
                "manual_override": False,
                "components": [],
                "anomaly_flags": [],
            }
            request_index[request_lookup_key] = request
            request_order.append(request_lookup_key)
            group["requests"].append(request)
            group["request_count"] += 1
            model_entry["request_count"] += 1

        request_status = normalize_attribution_status(getattr(cost, "attribution_status", None))
        if gemini_gap:
            request_status = ATTRIBUTION_STATUS_UNATTRIBUTED

        manual_override = bool(getattr(cost, "attribution_manual_override", False))
        request["manual_override"] = request["manual_override"] or manual_override
        if model and model not in request["models"]:
            request["models"].append(model)

        component_entry = {
            "cost_id": cost.id,
            "provider": provider,
            "component": component_name,
            "status": request_status,
            "model": model,
            "context": str(cost.context or ""),
            "timestamp": cost.timestamp.isoformat() if getattr(cost, "timestamp", None) else None,
            "total_cost": total_cost,
            "input_tokens": int(cost.input_tokens or 0),
            "output_tokens": int(cost.output_tokens or 0),
            "cached_tokens": int(getattr(cost, "cached_tokens", 0) or 0),
            "total_tokens": int(getattr(cost, "total_tokens", 0) or 0),
            "tokens_saved": int(getattr(cost, "tokens_saved", 0) or 0),
            "cost_saved": float(getattr(cost, "cost_saved", 0.0) or 0.0),
            "manual_override": manual_override,
            "metadata": metadata,
        }
        request["components"].append(component_entry)
        request["total_cost"] += total_cost
        request["total_cached_tokens"] += component_entry["cached_tokens"]
        request["total_tokens_saved"] += component_entry["tokens_saved"]
        request["total_cost_saved"] += component_entry["cost_saved"]
        group["total_cost"] += total_cost
        group["total_cached_tokens"] += component_entry["cached_tokens"]
        group["total_tokens_saved"] += component_entry["tokens_saved"]
        group["total_cost_saved"] += component_entry["cost_saved"]

        if provider == "gemini":
            external_reference = _extract_external_billing_reference(metadata)
            if external_reference is not None:
                gemini_external_reference_values.append(external_reference)
            gemini_total_billed_cost += total_cost

            if request_status == ATTRIBUTION_STATUS_INTERNAL and has_request_identity:
                request["internal_attributed_total"] += total_cost
                group["internal_attributed_total"] += total_cost
                gemini_internal_attributed_total += total_cost
            else:
                request["unattributed_residual_total"] += total_cost
                group["unattributed_residual_total"] += total_cost
                gemini_unattributed_residual_total += total_cost
                if "attribution_gap" not in request["anomaly_flags"]:
                    request["anomaly_flags"].append("attribution_gap")

            if request["unattributed_residual_total"] > 0:
                request["attribution_status"] = ATTRIBUTION_STATUS_UNATTRIBUTED

            if "pro" in model.casefold() and not manual_override:
                gemini_avoidable_pro_total += total_cost
                if "avoidable_pro" not in request["anomaly_flags"]:
                    request["anomaly_flags"].append("avoidable_pro")

    gemini_external_billing_total = (
        max(gemini_external_reference_values) if gemini_external_reference_values else gemini_total_billed_cost
    )
    gemini_deviation_total = gemini_external_billing_total - gemini_internal_attributed_total

    anomalies: List[Dict[str, Any]] = []
    if gemini_unattributed_residual_total > 0:
        anomalies.append(
            {
                "type": "attribution_gap",
                "severity": "critical" if historical_mode else "warning",
                "label": "Attributionsluecke",
                "cost": round(gemini_unattributed_residual_total, 6),
                "message": (
                    "Historische Gemini-Kosten bleiben als sichtbarer Restposten erhalten."
                    if historical_mode
                    else "Mindestens ein Gemini-Kostenblock ist nicht eindeutig attribuiert."
                ),
            }
        )
    if abs(gemini_deviation_total) > 1e-9:
        anomalies.append(
            {
                "type": "billing_deviation",
                "severity": "warning",
                "label": "Billing-Abweichung",
                "cost": round(abs(gemini_deviation_total), 6),
                "message": "Interne Attribution und externe Billing-Summe laufen auseinander.",
            }
        )
    if gemini_avoidable_pro_total > 0:
        anomalies.append(
            {
                "type": "avoidable_pro",
                "severity": "info",
                "label": "Vermeidbarer Pro-Verbrauch",
                "cost": round(gemini_avoidable_pro_total, 6),
                "message": "Pro-Kosten ohne sichtbaren manuellen Override wurden erkannt.",
            }
        )

    for request_key in request_order:
        request = request_index[request_key]
        request["models"].sort()
        request["components"].sort(key=lambda item: item["total_cost"], reverse=True)

    groups = list(groups_index.values())
    for group in groups:
        group["providers"] = sorted(group["providers"])
        group["models"] = sorted(group["models"])
        group["requests"].sort(key=lambda item: item["total_cost"], reverse=True)
    groups.sort(key=lambda item: item["total_cost"], reverse=True)
    anomalies.sort(key=lambda item: item["cost"], reverse=True)

    provider_breakdown = []
    for provider_entry in sorted(provider_index.values(), key=lambda item: item["total_cost"], reverse=True):
        provider_breakdown.append(
            {
                "provider": provider_entry["provider"],
                "total_cost": round(provider_entry["total_cost"], 6),
                "total_input_tokens": provider_entry["total_input_tokens"],
                "total_output_tokens": provider_entry["total_output_tokens"],
                "total_cached_tokens": provider_entry["total_cached_tokens"],
                "total_tokens": provider_entry["total_tokens"],
                "total_tokens_saved": provider_entry["total_tokens_saved"],
                "total_cost_saved": round(provider_entry["total_cost_saved"], 6),
                "models": sorted(provider_entry["_models"]),
            }
        )

    model_breakdown = []
    for model_entry in sorted(model_index.values(), key=lambda item: item["total_cost"], reverse=True):
        component_breakdown = [
            {
                "component": component,
                "count": values["count"],
                "total_cost": round(values["total_cost"], 6),
            }
            for component, values in sorted(
                model_entry["component_breakdown"].items(),
                key=lambda item: item[1]["total_cost"],
                reverse=True,
            )
        ]
        model_breakdown.append(
            {
                "provider": model_entry["provider"],
                "model": model_entry["model"],
                "request_count": model_entry["request_count"],
                "total_cost": round(model_entry["total_cost"], 6),
                "total_input_tokens": model_entry["total_input_tokens"],
                "total_output_tokens": model_entry["total_output_tokens"],
                "total_cached_tokens": model_entry["total_cached_tokens"],
                "total_tokens": model_entry["total_tokens"],
                "total_tokens_saved": model_entry["total_tokens_saved"],
                "total_cost_saved": round(model_entry["total_cost_saved"], 6),
                "component_breakdown": component_breakdown,
            }
        )

    truthfulness_hints = _build_truthfulness_hints(
        unattributed_residual_total=gemini_unattributed_residual_total,
        deviation_total=gemini_deviation_total,
        historical_mode=historical_mode,
        cross_provider_totals=cross_provider_totals,
        model_breakdown=model_breakdown,
    )
    truthfulness_status = "partial" if truthfulness_hints else "complete"

    return {
        "provider_scope": "cross_provider",
        "period": f"{year:04d}-{month:02d}",
        "ui_contract": {
            "primary_surface": "user_cost_overview",
            "default_focus": "cost_understanding_and_optimization",
            "detail_surface": "forensic_followup",
            "debug_surface": "separate_dev_log",
        },
        "user_summary": {
            "primary_message": "Kosten verstehen und Optimierungspotenziale erkennen.",
            "total_cost": round(cross_provider_totals["total_cost"], 6),
            "provider_count": len(provider_breakdown),
            "model_count": len(model_breakdown),
            "total_cached_tokens": cross_provider_totals["total_cached_tokens"],
            "total_tokens_saved": cross_provider_totals["total_tokens_saved"],
            "total_cost_saved": round(cross_provider_totals["total_cost_saved"], 6),
            "top_providers": [item["provider"] for item in provider_breakdown[:3]],
            "top_models": [item["model"] for item in model_breakdown[:5]],
        },
        "truthfulness_hints": truthfulness_hints,
        "anomaly_overview": anomalies,
        "cross_provider_summary": {
            "total_cost": round(cross_provider_totals["total_cost"], 6),
            "provider_count": len(provider_breakdown),
            "model_count": len(model_breakdown),
            "total_cached_tokens": cross_provider_totals["total_cached_tokens"],
            "total_tokens_saved": cross_provider_totals["total_tokens_saved"],
            "total_cost_saved": round(cross_provider_totals["total_cost_saved"], 6),
            "provider_breakdown": provider_breakdown,
            "model_breakdown": model_breakdown,
        },
        "summary": {
            "forensic_provider_scope": "gemini",
            "request_count": len(request_index),
            "group_count": len(groups),
            "internal_attributed_total": round(gemini_internal_attributed_total, 6),
            "unattributed_residual_total": round(gemini_unattributed_residual_total, 6),
            "external_billing_total": round(gemini_external_billing_total, 6),
            "deviation_total": round(gemini_deviation_total, 6),
            "truthfulness_status": truthfulness_status,
            "truthfulness_message": (
                truthfulness_hints[0]["message"]
                if truthfulness_hints
                else "Die sichtbare Kostensicht ist fuer diesen Zeitraum belastbar."
            ),
            "status_buckets": [
                {
                    "status": ATTRIBUTION_STATUS_INTERNAL,
                    "total_cost": round(gemini_internal_attributed_total, 6),
                },
                {
                    "status": ATTRIBUTION_STATUS_UNATTRIBUTED,
                    "total_cost": round(gemini_unattributed_residual_total, 6),
                },
                {
                    "status": ATTRIBUTION_STATUS_EXTERNAL_BILLING,
                    "total_cost": round(gemini_external_billing_total, 6),
                },
            ],
        },
        "historical_reconciliation": {
            "mode": "may_2026_forensic_reconstruction" if historical_mode else "standard",
            "visible_residual_required": historical_mode,
            "billing_reference_source": (
                "persisted_external_reference"
                if gemini_external_reference_values
                else "persisted_gemini_cost_records_proxy"
            ),
        },
        "groups": groups,
    }


def get_gemini_deep_dive_summary(db: Session, year: int, month: int) -> Dict[str, Any]:
    return get_costs_deep_dive_summary(db, year, month)
