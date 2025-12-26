# Am Anfang von backend/memory_manager.py
import datetime
import logging
from typing import Dict, List, Optional

from backend.data import (
    crud,  # Importiert die crud.py Datei
    database,  # Importiert die gesamte database.py Datei
)
from backend.logger_config import setup_logging
from backend.services import llm_gateway  # NEU
from sqlalchemy.orm import Session

from . import vector_service

setup_logging()
logger = logging.getLogger("janus_backend")


def save_memory_snippet(
    db: Session,
    chat_id: int,
    snippet_text: str,
    category: str = "General Fact",
    expires_at: Optional[datetime.datetime] = None,
    is_core: bool = False,  # NEU
):
    """Speichert einen Gedächtnisschnipsel mit einer spezifischen Kategorie."""
    embedding = vector_service.generate_embedding(snippet_text)
    if embedding is None:
        logger.error(
            f"Konnte kein Embedding für '{snippet_text}' erstellen. Speichern abgebrochen."
        )
        return None

    db_memory = database.Memory(
        chat_id=chat_id,
        snippet=snippet_text,
        embedding_json=embedding,
        category=category,
        expires_at=expires_at,
        is_core_fact=is_core,  # NEU
    )
    db.add(db_memory)
    db.commit()
    db.refresh(db_memory)
    return db_memory


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
    """Sucht und löscht alle ephemeren Erinnerungen, deren Ablaufdatum überschritten ist."""
    try:
        now = datetime.datetime.now()
        # Finde alle Erinnerungen, deren expires_at in der Vergangenheit liegt
        expired_memories = (
            db.query(database.Memory)
            .filter(database.Memory.expires_at is not None, database.Memory.expires_at < now)
            .all()
        )

        if not expired_memories:
            logger.info("No expired memories to prune.")
            return

        count = len(expired_memories)
        for mem in expired_memories:
            logger.info(f"Pruning expired memory (ID: {mem.id}): '{mem.snippet}'")
            db.delete(mem)

        db.commit()
        logger.info(f"Successfully pruned {count} expired memory snippets.")
    except Exception as e:
        logger.error(f"Error during memory pruning: {e}")
        db.rollback()


def find_similar_memory_snippet(db: Session, text: str):
    all_memories = get_all_memories(db)
    similar = vector_service.find_similar_snippets(text, all_memories, top_k=1, threshold=0.7)
    return similar[0] if similar else None


def get_all_memories(db: Session):
    return db.query(database.Memory).all()


def update_memory_snippet(db: Session, memory_id: int, new_snippet: str, is_core: bool):
    memory_item = db.query(database.Memory).filter(database.Memory.id == memory_id).first()
    if memory_item:
        memory_item.snippet = new_snippet
        memory_item.embedding_json = vector_service.generate_embedding(new_snippet)
        # Stelle sicher, dass der 'is_core' Status mit dem des neuen Fakts aktualisiert wird
        memory_item.is_core_fact = is_core
        # Aktualisiere den Zeitstempel, da dieser Fakt nun relevant ist
        memory_item.last_accessed_at = datetime.datetime.now()
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

        # Wichtig: is_core_fact wird auf True gesetzt
        db_memory = database.Memory(
            chat_id=1,  # Wir weisen es einem "globalen" Chat zu oder dem letzten Chat
            snippet=fact,
            embedding_json=embedding,
            category=category,
            is_core_fact=True,  # Das ist der entscheidende Punkt
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
async def call_llm(prompt: str, api_key: str, provider: str, model: str) -> str:
    """
    Führt einen internen LLM-Aufruf durch, um die Benutzeranfrage anzureichern.
    """
    messages = [{"role": "user", "content": prompt}]
    response = await llm_gateway.call_llm(
        provider=provider,
        model_id=model,
        api_key=api_key,
        messages=messages,
        force_no_tools=True,  # Wichtig: Keine Tools für diesen internen Aufruf!
    )
    return response.get("text", "").strip()


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
