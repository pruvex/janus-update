# Am Anfang von backend/memory_manager.py
import datetime
import hashlib
import json  # Added for JSON handling
import logging
import re
from typing import Dict, List, Optional, Any

from backend.data import (
    crud,  # Importiert die crud.py Datei
    database,  # Importiert die gesamte database.py Datei
)
from backend.data.schemas import ExtractedFact, MemoryCategory
from backend.logger_config import setup_logging
from backend.services import llm_gateway  # NEU
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, not_
from typing import List, Optional, Dict, Any
import json

from . import vector_service

setup_logging()
logger = logging.getLogger("janus_backend")


# --- Constants for Diamond Memory Architecture ---
MAX_CORE_ALWAYS_TOKENS = 400
MAX_CORE_QUERY_TOKENS = 600
MAX_STM_TOKENS = 1500
SIMILARITY_THRESHOLD = 0.35
GRACE_PERIOD_DAYS = 7


def estimate_tokens(text: str) -> int:
    """Grobe Schätzung der Tokenanzahl (3-4 Zeichen pro Token)."""
    return len(text) // 3

def normalize_text(text: str) -> str:
    """Normalisiert Text für konsistentes Hashing."""
    text = text.lower()  # Kleinschreibung
    text = re.sub(r'[^\w\s]', '', text)  # Satzzeichen entfernen
    text = re.sub(r'\s+', ' ', text).strip()  # Leerzeichen normalisieren
    return text

def compute_hash(text: str) -> str:
    """Erstellt einen SHA256-Hash von einem Text."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def save_memory_snippet(
    db: Session,
    chat_id: int,
    fact_object: dict,  # <-- KORREKTER PARAMETER
) -> Optional[database.Memory]:
    """
    Speichert ein strukturiertes Fakten-Objekt und nutzt den canonical_key für Deduplizierung.
    """
    # 1. Extrahiere den canonical_key und berechne den Hash
    canonical_key = fact_object.get("canonical_key")
    if not canonical_key:
        logger.error("Fakt ohne canonical_key kann nicht gespeichert werden.")
        return None
    
    # Wir benutzen die Helferfunktionen, die wir bereits definiert haben
    text_hash = compute_hash(canonical_key)

    # 2. Auf exaktes Duplikat via Hash PRÜFEN (extrem schnell)
    existing = db.query(database.Memory).filter(
        database.Memory.chat_id == chat_id,
        database.Memory.text_hash == text_hash
    ).first()

    if existing:
        logger.info(f"[DUPLICATE HASH] Ignoriere bekannten Fakt (Key: {canonical_key})")
        existing.last_accessed_at = datetime.datetime.now()
        db.commit()
        return None

    # 3. Wenn kein Duplikat, fahre fort
    snippet_text = fact_object.get("fact")
    embedding = vector_service.generate_embedding(snippet_text)
    if embedding is None:
        logger.error(f"Konnte kein Embedding für '{snippet_text}' erstellen. Speichern abgebrochen.")
        return None

    # Konvertiere das ganze Objekt zu einem JSON-String für die Speicherung
    snippet_json = json.dumps(fact_object, ensure_ascii=False)

    try:
        # Extrahiere die restlichen Daten aus dem Objekt
        category = fact_object.get("category")
        memory_type = fact_object.get("type")
        expires_in = fact_object.get("expires_in_hours")

        core_priority = 0
        if memory_type == "CORE_IDENTITY":
            core_priority = 2
        elif memory_type == "CORE_DETAIL":
            core_priority = 1
            
        expires_at = datetime.datetime.now() + datetime.timedelta(hours=expires_in) if expires_in else None

        # Retain-until für ablaufende Erinnerungen berechnen
        retain_until = None
        if expires_at is not None:
            retain_until = expires_at + datetime.timedelta(days=GRACE_PERIOD_DAYS)

        db_memory = database.Memory(
            chat_id=chat_id,
            snippet=snippet_json,
            embedding_json=embedding,
            normalized_text=canonical_key,  # Verwende den canonical_key als normalisierten Text
            text_hash=text_hash,
            category=category,
            is_core_fact=(core_priority > 0),
            core_priority=core_priority,
            expires_at=expires_at,
            retain_until=retain_until,
        )
        db.add(db_memory)
        db.commit()
        db.refresh(db_memory)
        
        logger.info(f"Gespeichert (ID: {db_memory.id}, Key: {canonical_key})")

        # [NEU] Rufe den Konsolidierungs-Schritt auf, NACHDEM der Commit erfolgreich war.
        _consolidate_memory_after_save(db, fact_object)

        return db_memory
    except Exception as e:
        logger.error(f"Fehler beim Speichern des Memory-Snippets: {e}", exc_info=True)
        db.rollback()
        return None
        return None


# --- NEUE FUNKTION ---
def get_all_long_term_memories(db: Session) -> List[database.LongTermMemory]:
    """Gibt alle Erinnerungen aus dem Langzeitgedächtnis zurück."""
    return db.query(database.LongTermMemory).all()


# --- NEUE FUNKTION ---
def promote_ltm_to_stm(db: Session, ltm_item: database.LongTermMemory):
    """Befördert einen LTM-Eintrag zurück ins STM und löscht ihn aus dem LTM."""
    logger.info(f"Promoting memory from LTM to STM: '{ltm_item.snippet}'")
    # Im STM neu erstellen (is_core wird hier als False angenommen, da es nicht archiviert worden wäre, wenn es True wäre)
    reinstated_memory = save_memory_snippet(db, ltm_item.chat_id, ltm_item.snippet, is_core=False)

    # Aus dem LTM löschen
    db.delete(ltm_item)
    db.commit()
    return reinstated_memory


# --- NEUE FUNKTION ---
def touch_memory_snippet(db: Session, memory_id: int):
    """Aktualisiert den last_accessed_at Zeitstempel eines STM-Eintrags."""
    memory_item = db.query(database.Memory).filter(database.Memory.id == memory_id).first()
    if memory_item:
        memory_item.last_accessed_at = datetime.datetime.now()
        db.commit()


# --- NEUE ZENTRALE ARCHIVIERUNGSFUNKTION ---
def archive_old_memories(db: Session):
    """
    Prüft, ob das STM bereinigt werden muss und verschiebt die ältesten,
    am seltensten genutzten und nicht-essentiellen Erinnerungen ins LTM.
    """
    STM_LIMIT = 250
    STM_TARGET_SIZE = 200  # Reduzieren auf dieses Niveau, um nicht ständig zu archivieren

    try:
        stm_count = db.query(database.Memory).count()
        if stm_count <= STM_LIMIT:
            logger.info(
                f"STM size ({stm_count}) is within limit ({STM_LIMIT}). No archival needed."
            )
            return

        logger.info(
            f"STM size ({stm_count}) exceeds limit ({STM_LIMIT}). Starting archival process."
        )

        num_to_archive = stm_count - STM_TARGET_SIZE

        # Finde Kandidaten: Nicht "core", sortiert nach dem letzten Zugriff (älteste zuerst)
        # KORREKTUR: Die gesamte Abfrage wird in runde Klammern gesetzt, um IndentationErrors zu vermeiden.
        candidates = (
            db.query(database.Memory)
            .filter(not database.Memory.is_core_fact)
            .filter(
                database.Memory.expires_at is None
            )  # <-- GOLD STANDARD: Nur zeitlose Fakten archivieren!
            .order_by(database.Memory.last_accessed_at.asc())
            .limit(num_to_archive)
            .all()
        )

        if not candidates:
            logger.warning("STM is full but no non-core facts could be found to archive.")
            return

        for mem in candidates:
            # 1. In LTM kopieren
            new_ltm_entry = database.LongTermMemory(
                original_memory_id=mem.id,
                chat_id=mem.chat_id,
                snippet=mem.snippet,
                embedding_json=mem.embedding_json,
                created_at=mem.created_at,
            )
            db.add(new_ltm_entry)

            # 2. Aus STM löschen
            db.delete(mem)

        db.commit()
        logger.info(f"Successfully archived {len(candidates)} memory snippets.")

    except Exception as e:
        logger.error(f"Error during memory archival: {e}")
        db.rollback()


# --- NEUE AUFRÄUMFUNKTION ---
def prune_expired_memories(db: Session):
    """
    Prunes expired memories according to the Diamond Memory Architecture rules.
    
    This function will:
    1. Delete memories that have expired and passed their retain_until date
    2. Archive old, rarely used memories to LTM (Long-Term Memory)
    3. Enforce token limits for different memory types
    """
    from datetime import datetime, timedelta
    from sqlalchemy import or_, and_, func, text
    
    try:
        now = datetime.utcnow()
        
        # --- 1. Prune fully expired memories ---
        # Only delete memories that have both expired AND passed their retain_until date
        expired = db.query(database.Memory).filter(
            database.Memory.expires_at.isnot(None),
            database.Memory.retain_until.isnot(None),
            database.Memory.retain_until < now
        ).all()
        
        if expired:
            logger.info(f"Pruning {len(expired)} fully expired memories")
            for memory in expired:
                db.delete(memory)
            db.commit()
            logger.info(f"Successfully pruned {len(expired)} expired memories")
        
        # --- 2. Archive old, rarely used memories to LTM ---
        # Only archive non-core memories that are older than 30 days
        # and haven't been accessed in the last 7 days
        archive_cutoff = now - timedelta(days=30)
        last_access_cutoff = now - timedelta(days=7)
        
        # Get count of current LTM items to limit archiving if needed
        ltm_count = db.query(func.count(database.LongTermMemory.id)).scalar() or 0
        max_ltm_items = 5000  # Maximum number of items to keep in LTM
        
        if ltm_count < max_ltm_items:
            # Find memories to archive
            memories_to_archive = db.query(database.Memory).filter(
                database.Memory.is_core_fact == False,  # Don't archive core memories
                database.Memory.created_at < archive_cutoff,
                database.Memory.last_accessed_at < last_access_cutoff,
                or_(
                    database.Memory.expires_at.is_(None),  # Non-ephemeral
                    and_(
                        database.Memory.expires_at > now,  # Not yet expired
                        database.Memory.retain_until > now  # Not in grace period
                    )
                )
            ).order_by(
                database.Memory.last_accessed_at.asc()  # Oldest accessed first
            ).limit(max_ltm_items - ltm_count).all()
            
            # Archive the memories
            archived_count = 0
            for memory in memories_to_archive:
                try:
                    # Create LTM entry
                    ltm_entry = database.LongTermMemory(
                        original_memory_id=memory.id,
                        chat_id=memory.chat_id,
                        snippet=memory.snippet,
                        embedding_json=memory.embedding_json,
                        created_at=memory.created_at,
                        archived_at=now
                    )
                    db.add(ltm_entry)
                    
                    # Delete from main memory
                    db.delete(memory)
                    archived_count += 1
                    
                except Exception as e:
                    logger.error(f"Error archiving memory {memory.id}: {e}")
                    db.rollback()
                    continue
            
            if archived_count > 0:
                db.commit()
                logger.info(f"Archived {archived_count} memories to LTM")
        
        # --- 3. Enforce token limits for different memory types ---
        # This is a simplified version - in a real implementation, you'd want to
        # calculate actual token counts and enforce limits more precisely
        
        # Limit core always memories
        core_always_count = db.query(database.Memory).filter(
            database.Memory.is_core_fact == True,
            database.Memory.core_priority == 2  # Always include core
        ).count()
        
        max_core_always = 100  # Adjust based on your needs
        if core_always_count > max_core_always:
            # Find excess core always memories by least recently accessed
            excess_cores = db.query(database.Memory).filter(
                database.Memory.is_core_fact == True,
                database.Memory.core_priority == 2
            ).order_by(
                database.Memory.last_accessed_at.asc()
            ).limit(core_always_count - max_core_always).all()
            
            for memory in excess_cores:
                # Demote to queryable core instead of deleting
                memory.core_priority = 1
            
            if excess_cores:
                db.commit()
                logger.info(f"Demoted {len(excess_cores)} core always memories to queryable")
        
        return {
            "pruned": len(expired),
            "archived": archived_count if 'archived_count' in locals() else 0,
            "core_memories_demoted": len(excess_cores) if 'excess_cores' in locals() else 0
        }
        
    except Exception as e:
        logger.error(f"Error during memory pruning and maintenance: {e}", exc_info=True)
        db.rollback()
        return {"error": str(e)}


class RetrievalContext:
    def __init__(self):
        self.core_always: List[str] = []
        self.core_queryable: List[str] = []
        self.ephemeral_active: List[str] = [] # Gültige Fakten (Termine in Zukunft)
        self.ephemeral_echo: List[str] = []   # Grace Period Fakten (Rückschau)
        self.stm_context: List[str] = []      # Normaler Kontext

    def format_for_prompt(self) -> str:
        """Baut den Kontext-String mit klaren Sektionen."""
        sections = []
        
        if self.core_always:
            sections.append("### CORE IDENTITY (ALWAYS ACTIVE)\n" + "\n".join(f"- {s}" for s in self.core_always))
            
        if self.core_queryable:
            sections.append("### RELEVANT USER TRAITS\n" + "\n".join(f"- {s}" for s in self.core_queryable))
            
        # Ephemeral mischen wir intelligent
        active_facts = self.ephemeral_active
        if active_facts:
            sections.append("### ACTIVE FACTS & PLANS\n" + "\n".join(f"- {s}" for s in active_facts))
            
        if self.ephemeral_echo:
            sections.append("### RECENTLY EXPIRED (CONTEXT ONLY)\n" + "\n".join(f"- [PAST] {s}" for s in self.ephemeral_echo))
            
        if self.stm_context:
            sections.append("### CONVERSATION MEMORY\n" + "\n".join(f"- {s}" for s in self.stm_context))
            
        if not sections:
            return ""
            
        return "INFORMATIONEN AUS DEM LANGZEITGEDÄCHTNIS:\n" + "\n\n".join(sections)


def retrieve_diamond_context(
    db: Session, 
    chat_id: int, 
    query: str, 
    max_core_always_tokens: int = MAX_CORE_ALWAYS_TOKENS,
    max_core_query_tokens: int = MAX_CORE_QUERY_TOKENS,
    max_stm_tokens: int = MAX_STM_TOKENS,
    similarity_threshold: float = SIMILARITY_THRESHOLD
) -> str:
    """
    Diamond Standard Retrieval (CROSS-CHAT ENABLED).
    
    Logik:
    - Core Memories & Termine (Ephemeral) werden GLOBAL (chat-übergreifend) gesucht.
    - STM & Echo (Verlauf) bleiben LOKAL (chat-spezifisch).
    """
    ctx = RetrievalContext()
    now = datetime.datetime.now()
    
    # 1. CORE MEMORY (GLOBAL - Gilt für den User in ALLEN Chats)
    # ------------------------
    
    # A. Core-Always (Prio 2): Laden wir IMMER, egal aus welchem Chat
    core_always_objs = db.query(database.Memory).filter(
        database.Memory.core_priority == 2  # KEIN chat_id Filter!
    ).order_by(database.Memory.created_at.desc()).limit(15).all()
    ctx.core_always = [m.snippet for m in core_always_objs]

    # B. Core-Queryable (Prio 1): Suchen wir per Vektor in ALLEN Chats
    core_candidates = db.query(database.Memory).filter(
        database.Memory.core_priority == 1  # KEIN chat_id Filter!
    ).all()
    
    if core_candidates:
        candidate_embeddings = [json.loads(m.embedding_json) for m in core_candidates]
        # Suche nach relevanten Traits über alle Chats hinweg
        indices = vector_service.find_most_similar_indices(query, candidate_embeddings, top_k=5, threshold=0.25)
        
        used_tokens = 0
        for idx in indices:
            snippet = core_candidates[idx].snippet
            if used_tokens + estimate_tokens(snippet) < max_core_query_tokens:
                ctx.core_queryable.append(snippet)
                used_tokens += estimate_tokens(snippet)
                # Wir "touchen" hier nicht last_accessed_at, da es global ist und sonst das Archiving im Ursprungs-Chat durcheinander bringt
                # Oder wir touchen es doch, um es "am Leben" zu halten. Entscheiden wir uns für Touch:
                touch_memory_snippet(db, core_candidates[idx].id)

    # 2. EPHEMERAL MEMORY STRATEGY
    # ----------------------------
    is_past_query = any(w in query.lower() for w in ["gestern", "war", "letzte", "damals", "vorhin"])
    
    # A. Active Ephemeral (Gültig > JETZT): GLOBAL (Termine sind überall wichtig)
    active_candidates = db.query(database.Memory).filter(
        database.Memory.expires_at > now # KEIN chat_id Filter!
    ).all()
    
    # B. Echo Ephemeral (Abgelaufen < JETZT): LOKAL (Nur relevant für Rückblick in DIESEM Chat)
    echo_candidates = []
    if is_past_query:
        echo_candidates = db.query(database.Memory).filter(
            database.Memory.chat_id == chat_id, # LOKAL
            database.Memory.expires_at < now,
            database.Memory.retain_until > now
        ).all()
    
    if active_candidates:
         emb_active = [json.loads(m.embedding_json) for m in active_candidates]
         # Hier Vektor-Suche ODER einfach alles anzeigen wenn es wenige sind?
         # Besser Vektor für Skalierbarkeit, aber mit niedrigem Threshold
         idx_active = vector_service.find_most_similar_indices(query, emb_active, top_k=5, threshold=0.2)
         
         # Fallback: Wenn Query "was liegt an" ist, wollen wir vielleicht ALLES sehen.
         # Fürs erste bleiben wir bei Vektor.
         for idx in idx_active:
             ctx.ephemeral_active.append(active_candidates[idx].snippet)
             touch_memory_snippet(db, active_candidates[idx].id)

    if echo_candidates:
         emb_echo = [json.loads(m.embedding_json) for m in echo_candidates]
         idx_echo = vector_service.find_most_similar_indices(query, emb_echo, top_k=3, threshold=similarity_threshold)
         for idx in idx_echo:
             ctx.ephemeral_echo.append(echo_candidates[idx].snippet)

    # 3. STM RETRIEVAL (Der Rest)
    # ---------------------------
    # STM bleibt LOKAL! Wir wollen nicht den Kontext von Chat A in Chat B mischen.
    stm_candidates = db.query(database.Memory).filter(
        database.Memory.chat_id == chat_id, # LOKAL
        database.Memory.is_core_fact == False,
        or_(
            database.Memory.expires_at == None, 
            database.Memory.expires_at > now
        )
    ).order_by(database.Memory.last_accessed_at.desc()).limit(300).all()

    if stm_candidates:
        emb_stm = [json.loads(m.embedding_json) for m in stm_candidates]
        idx_stm = vector_service.find_most_similar_indices(query, emb_stm, top_k=10, threshold=similarity_threshold)
        
        stm_token_count = 0
        for idx in idx_stm:
            snippet = stm_candidates[idx].snippet
            if stm_token_count + estimate_tokens(snippet) < max_stm_tokens:
                ctx.stm_context.append(snippet)
                stm_token_count += estimate_tokens(snippet)
                touch_memory_snippet(db, stm_candidates[idx].id)

    return ctx.format_for_prompt()


def get_memories_for_management(db: Session) -> List[database.Memory]:
    """
    Holt alle Memories für das Frontend, sortiert nach Wichtigkeit (Diamond Standard).
    Sortierung: Core Identity (2) -> Core Detail (1) -> General (0) -> Erstellungsdatum
    
    Args:
        db: Database session
        
    Returns:
        List[Memory]: List of Memory objects sorted by priority and creation date
    """
    return db.query(database.Memory).order_by(
        database.Memory.core_priority.desc().nulls_last(),
        database.Memory.is_core_fact.desc(),
        database.Memory.created_at.desc()
    ).all()


def get_all_memories(db: Session):
    """DEPRECATED: Use retrieve_diamond_context or get_memories_for_management instead"""
    return db.query(database.Memory).all()


def update_memory_snippet(
    db: Session, 
    memory_id: int, 
    new_snippet: str, 
    is_core: bool = None,
    core_priority: int = None,
    expires_at: Optional[datetime] = None
):
    """
    Updates a memory snippet with new content and properties.
    
    Args:
        db: Database session
        memory_id: ID of the memory to update
        new_snippet: New content for the memory
        is_core: Whether this is a core memory (optional, keeps current if None)
        core_priority: New core priority (0=None, 1=Queryable, 2=Always, keeps current if None)
        expires_at: New expiration datetime (None for no expiration, keeps current if None)
        
    Returns:
        The updated Memory object or None if not found
    """
    memory_item = db.query(database.Memory).filter(database.Memory.id == memory_id).first()
    if not memory_item:
        return None
    
    try:
        # Update basic fields
        memory_item.snippet = new_snippet
        memory_item.embedding_json = vector_service.generate_embedding(new_snippet)
        
        # Update core status if provided
        if is_core is not None:
            memory_item.is_core_fact = is_core
            
            # If setting as core but no priority specified, default to Queryable
            if is_core and core_priority is None and memory_item.core_priority == 0:
                memory_item.core_priority = 1
        
        # Update core priority if provided
        if core_priority is not None:
            memory_item.core_priority = core_priority
            
            # If setting priority > 0, ensure is_core is True
            if core_priority > 0:
                memory_item.is_core_fact = True
        
        # Update expiration if provided
        if expires_at is not None:
            memory_item.expires_at = expires_at
            
            # Update retain_until based on the new expires_at
            if expires_at is not None:
                memory_item.retain_until = expires_at + datetime.timedelta(days=GRACE_PERIOD_DAYS)
            else:
                memory_item.retain_until = None
        
        # Update last_accessed timestamp
        memory_item.last_accessed_at = datetime.datetime.utcnow()
        
        db.commit()
        db.refresh(memory_item)
        
        logger.info(f"Updated memory {memory_id} (Core: {memory_item.is_core_fact}, "
                  f"Priority: {memory_item.core_priority}, Expires: {memory_item.expires_at})")
        
        return memory_item
    
    except Exception as e:
        logger.error(f"Error updating memory {memory_id}: {e}", exc_info=True)
        db.rollback()
        return None


def _consolidate_memory_after_save(db: Session, saved_fact_object: Dict[str, Any]) -> None:
    """
    Überprüft nach dem Speichern, ob der neue Fakt einen alten, allgemeineren Fakt redundant macht.
    Wird intern von save_memory_snippet aufgerufen.
    """
    predicate = saved_fact_object.get("predicate")
    subject_pet_type = saved_fact_object.get("subject_pet_type")
    subject_role = saved_fact_object.get("subject_role")
    subject_name = saved_fact_object.get("subject_name")
    chat_id = saved_fact_object.get("chat_id")

    # REGEL 1: Wenn ein Haustier einen Namen bekommt, ist der generische "owns|user|..."-Fakt redundant.
    if predicate == "name_is" and subject_pet_type in ["cat", "dog"] and subject_role == "pet":
        # Suche nach dem alten, generischen Fakt
        generic_key_to_delete = f"owns|user|{subject_pet_type}"
        generic_hash_to_delete = compute_hash(generic_key_to_delete)
        
        # Finde alle Chats des Users (für den Fall, dass der Fakt in einem anderen Chat erstellt wurde)
        fact_to_delete = db.query(database.Memory).filter(
            database.Memory.text_hash == generic_hash_to_delete
        ).first()

        if fact_to_delete:
            logger.info(
                f"KONSOLIDIERE (Regel 1): Neuer spezifischer Fakt '{saved_fact_object.get('canonical_key')}' "
                f"macht alten Fakt '{generic_key_to_delete}' (ID: {fact_to_delete.id}) redundant. Lösche alten Fakt."
            )
            db.delete(fact_to_delete)
            db.commit()
    
    # [FIX] REGEL 2: Wir entfernen die Prüfung auf 'predicate == "name_is"'.
    # Wenn wir IRGENDEINEN Fakt speichern, der einen konkreten Typ (cat/dog) UND einen Namen hat,
    # wissen wir genug, um den alten "unknown"-Eintrag zu löschen.
    if subject_pet_type in ["cat", "dog"] and subject_name:
        # Baue den Key für die "schlechtere" Version (unknown type)
        # Wir suchen nach dem spezifischen "name_is" Fakt mit "unknown" type
        redundant_unknown_key = f"name_is|pet:unknown:{subject_name.lower()}|{subject_name}"
        redundant_hash = compute_hash(redundant_unknown_key)

        fact_to_delete = db.query(database.Memory).filter(
            database.Memory.text_hash == redundant_hash
        ).first()

        if fact_to_delete:
            logger.info(
                f"KONSOLIDIERE (Regel 2): Neuer präziser Fakt '{saved_fact_object.get('canonical_key')}' "
                f"ersetzt ungenauen Fakt '{redundant_unknown_key}' (ID: {fact_to_delete.id}). Lösche alten Fakt."
            )
            db.delete(fact_to_delete)
            db.commit()


def save_raw_memory(db: Session, chat_id: int, user_input: str):
    """Speichert die rohe Benutzereingabe als Gedächtnis."""
    current_logger = logging.getLogger("janus_backend")  # Get logger inside function
    current_logger.info(f"Attempting to save raw memory for chat {chat_id}: '{user_input}'")
    saved_memory = save_memory_snippet(db, chat_id, user_input)
    if saved_memory:
        current_logger.info(f"Raw memory saved successfully: '{user_input}'")
    else:
        current_logger.warning(f"Failed to save raw memory for chat {chat_id}: '{user_input}'")
    return saved_memory


# In backend/memory_manager.py
def get_all_facts(db: Session) -> List[database.Memory]:  # Verwende database.Memory
    """Gibt alle Erinnerungen zurück, die als Fakten und nicht als Fragen oder rohe Eingaben gelten."""
    return (
        db.query(database.Memory)
        .filter(  # Verwende database.Memory
            ~database.Memory.snippet.startswith("wie "),
            ~database.Memory.snippet.startswith("was "),
            ~database.Memory.snippet.startswith("wer "),
            ~database.Memory.snippet.startswith("wo "),
            ~database.Memory.snippet.startswith("wann "),
            ~database.Memory.snippet.startswith("warum "),
        )
        .all()
    )


def search_past_conversation_summaries_tool(query: str):
    """Benutze dieses Werkzeug NUR, wenn der Benutzer explizit nach Informationen aus "anderen", "früheren" oder "letzten" Chats fragt. Es durchsucht die Zusammenfassungen abgeschlossener Konversationen. Für Informationen aus dem AKTUELLEN Chat ist dieses Werkzeug ungeeignet."""
    db = database.SessionLocal()
    try:
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
    finally:
        db.close()


def get_all_searchable_memories(db: Session):
    """
    Gibt eine kombinierte Liste aller Erinnerungen aus dem STM (Memory)
    und LTM (LongTermMemory) für eine umfassende Vektorsuche zurück.
    """
    stm_memories = db.query(database.Memory).all()
    ltm_memories = db.query(database.LongTermMemory).all()

    # Kombiniere die Erinnerungen und füge einen Typ-Hinweis hinzu
    combined = []
    for mem in stm_memories:
        # Füge die ursprünglichen Objekte hinzu, nicht Dictionaries
        setattr(mem, "memory_type", "stm")  # Füge den Typ als Attribut hinzu
        combined.append(mem)

    for mem in ltm_memories:
        # Füge die ursprünglichen Objekte hinzu, nicht Dictionaries
        setattr(mem, "memory_type", "ltm")  # Füge den Typ als Attribut hinzu
        combined.append(mem)

    return combined


def save_core_memory_fact(fact: str, category: str) -> Dict[str, str]:
    """
    Speichert einen Fakt explizit als Kern-Erinnerung (is_core_fact=True).
    Diese Funktion wird direkt vom save_core_memory_tool aufgerufen.
    """
    db = database.SessionLocal()
    try:
        embedding = vector_service.generate_embedding(fact)
        if embedding is None:
            raise ValueError(f"Konnte kein Embedding für '{fact}' erstellen.")

        # Wichtig: is_core_fact und core_priority=2 (Always Active) werden gesetzt
        db_memory = database.Memory(
            chat_id=1,  # Wir weisen es einem "globalen" Chat zu oder dem letzten Chat
            snippet=fact,
            embedding_json=embedding,
            category=category,
            is_core_fact=True,
            core_priority=2  # WICHTIG: Setzt die höchste Priorität für sofortige Verfügbarkeit
        )
        db.add(db_memory)
        db.commit()
        db.refresh(db_memory)

        success_message = f"Die Kern-Erinnerung '{fact}' wurde erfolgreich gespeichert."
        logger.info(success_message)
        return {"status": "success", "output": success_message}

    except Exception as e:
        db.rollback()
        error_message = f"Fehler beim Speichern der Kern-Erinnerung: {e}"
        logger.error(error_message, exc_info=True)
        return {"status": "error", "output": error_message}
    finally:
        db.close()


# Platzhalter für den LLM-Aufruf
async def call_llm(prompt: str, api_key: str, provider: str, model: str):
    """
    Führt einen internen LLM-Aufruf durch, um die Benutzeranfrage anzureichern.
    """
    try:
        response = llm_gateway.generate_text(
            prompt=prompt,
            api_key=api_key,
            provider=provider,
            model=model,
            temperature=0.3,  # Kreativität reduzieren für Faktenanreicherung
            max_tokens=500,
        )
        return response.strip()
    except Exception as e:
        logger.error(f"Fehler beim LLM-Aufruf: {e}")
        return ""


def get_relevant_facts_as_objects(db: Session, query: str, limit: int = 10) -> List[ExtractedFact]:
    """
    Sucht nach relevanten Fakten und gibt sie als strukturierte Pydantic-Objekte zurück.
    Wird vom Planner benötigt.
    """
    # 1. Hole alle potenziellen Kandidaten (STM + LTM + Core)
    # Vereinfachung: Wir suchen hier primär in den Memory-Tabellen
    candidates = db.query(database.Memory).filter(
        database.Memory.is_core_fact.is_(True) | 
        (database.Memory.expires_at.is_(None) | (database.Memory.expires_at > datetime.datetime.now()))
    ).all()
    
    if not candidates:
        return []

    # 2. Vektor-Suche (falls Embeddings vorhanden)
    candidate_embeddings = []
    valid_memories = []
    
    for mem in candidates:
        if mem.embedding_json:
            try:
                candidate_embeddings.append(json.loads(mem.embedding_json))
                valid_memories.append(mem)
            except Exception as e:
                logger.warning(f"Konnte Embedding für Memory {mem.id} nicht parsen: {e}")
                continue

    if not valid_memories:
        return []

    try:
        # Suche die ähnlichsten
        indices = vector_service.find_most_similar_indices(
            query, 
            candidate_embeddings, 
            top_k=limit, 
            threshold=0.25 # Etwas toleranter für den Planner
        )
        
        extracted_facts = []
        for idx in indices:
            mem = valid_memories[idx]
            try:
                # Parse das JSON-Snippet zurück in ein Dict
                fact_dict = json.loads(mem.snippet)
                
                # Stelle sicher, dass die Kategorie gültig ist
                category = fact_dict.get('category', 'Allgemein')
                if category not in [cat.value for cat in MemoryCategory]:
                    category = 'Allgemein'
                
                # Erstelle das ExtractedFact-Objekt mit validierter Kategorie
                fact_obj = ExtractedFact(
                    fact=fact_dict.get('fact', ''),
                    category=MemoryCategory(category),
                    canonical_key=fact_dict.get('canonical_key', '')  # Wichtig für die Deduplizierung
                )
                extracted_facts.append(fact_obj)
            except Exception as e:
                logger.warning(f"Konnte Memory {mem.id} nicht in ExtractedFact wandeln: {e}")
                continue

        return extracted_facts

    except Exception as e:
        logger.error(f"Fehler bei der Vektorsuche: {e}")
        return []


async def enrich_user_query_with_memory(
    original_query: str, relevant_memory_facts: List[str], api_key: str, provider: str, model: str
) -> str:
    """
    Reichert die Benutzeranfrage proaktiv mit relevanten Fakten an, ABER NUR, wenn es sich um einen Suchbefehl handelt.
    Fragen werden bewusst nicht verändert.
    """
    if not relevant_memory_facts:
        return original_query

    # Heuristik zur Erkennung von Fragen vs. Befehlen
    is_question = original_query.lower().strip().startswith(
        ("wie", "was", "wer", "wo", "wann", "warum", "welche")
    ) or original_query.strip().endswith("?")
    is_search_command = (
        "suche" in original_query.lower()
        or "empfiehl" in original_query.lower()
        or "news" in original_query.lower()
    )

    if is_question and not is_search_command:
        logger.info(
            f"Query '{original_query}' identified as a direct question. Passing through without enrichment to avoid corruption."
        )
        return original_query

    # Nur wenn es ein klarer Suchbefehl ist, versuchen wir eine Anreicherung.
    # Hier kann später eine komplexere LLM-basierte Anreicherung stehen, aber für den Moment
    # ist die sichere Nicht-Veränderung von Fragen wichtiger.
    logger.info(
        f"Query '{original_query}' is not a direct question. Applying context for potential enrichment by the main LLM."
    )

    # Wir geben die Query unverändert zurück, da der Kontext dem Haupt-LLM separat übergeben wird.
    # Die Anreicherung findet durch den System-Prompt im ChatOrchestrator statt.
    # Diese Funktion dient nun als Sicherheits-Gate.
    return original_query
