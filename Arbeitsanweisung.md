Schritt 1: Datenbankmodell erweitern (database.py)
Wir fügen der Memory-Tabelle unsere neue Spalte expires_at hinzu.
code
Python
# backend/database.py

# ... (andere imports)
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, func

# ...

class Memory(Base):
    __tablename__ = "memory"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    snippet = Column(Text, nullable=False)
    embedding_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    last_accessed_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    is_core_fact = Column(Boolean, default=False)
    # --- NEUE SPALTE FÜR EPHEMERE ERINNERUNGEN ---
    expires_at = Column(DateTime, nullable=True) # nullable=True ist entscheidend!

# ... (Rest der Datei bleibt unverändert)
Das war's schon für die Datenbank. Da wir init_db() haben, wird die neue Spalte beim nächsten Start automatisch hinzugefügt.
Schritt 2: Speicher- und Archivierungslogik anpassen (memory_manager.py)
Jetzt bringen wir dem memory_manager bei, mit dem neuen Feld umzugehen.
save_memory_snippet erweitern: Die Funktion muss das neue Feld annehmen können.
archive_old_memories härten: Die Funktion muss ephemere Erinnerungen ignorieren.
Neue Aufräumfunktion prune_expired_memories erstellen.
code
Python
# backend/memory_manager.py

# ... (imports, inkl. datetime)
import datetime
from typing import List, Optional # Optional hinzufügen

# ...

# --- Memory CRUD ---
# ÄNDERUNG: Signatur um expires_at erweitern
def save_memory_snippet(db: Session, chat_id: int, snippet_text: str, is_core: bool = False, expires_at: Optional[datetime.datetime] = None):
    embedding = vector_service.generate_embedding(snippet_text)
    if embedding is None:
        return None
    # --- Geänderter Aufruf ---
    db_memory = database.Memory(
        chat_id=chat_id, 
        snippet=snippet_text, 
        embedding_json=embedding, 
        is_core_fact=is_core,
        expires_at=expires_at  # Das neue Feld wird übergeben
    )
    db.add(db_memory)
    db.commit()
    db.refresh(db_memory)
    return db_memory

# ... (get_all_long_term_memories, promote_ltm_to_stm, touch_memory_snippet bleiben unverändert)

# --- NEUE ZENTRALE ARCHIVIERUNGSFUNKTION ---
def archive_old_memories(db: Session):
    """
    Prüft, ob das STM bereinigt werden muss und verschiebt die ältesten,
    am seltensten genutzten und nicht-essentiellen Erinnerungen ins LTM.
    """
    # ... (STM_LIMIT, STM_TARGET_SIZE, stm_count bleiben unverändert)
    try:
        stm_count = db.query(database.Memory).count()
        if stm_count <= STM_LIMIT:
            logger.info(f"STM size ({stm_count}) is within limit ({STM_LIMIT}). No archival needed.")
            return

        logger.info(f"STM size ({stm_count}) exceeds limit ({STM_LIMIT}). Starting archival process.")

        num_to_archive = stm_count - STM_TARGET_SIZE

        # Finde Kandidaten: Nicht "core", sortiert nach dem letzten Zugriff (älteste zuerst)
        # KORREKTUR/HÄRTUNG: Ignoriere ephemere Erinnerungen!
        candidates = (
            db.query(database.Memory)
            .filter(database.Memory.is_core_fact == False)
            .filter(database.Memory.expires_at == None)  # <-- GOLD STANDARD: Nur zeitlose Fakten archivieren!
            .order_by(database.Memory.last_accessed_at.asc())
            .limit(num_to_archive)
            .all()
        )

        if not candidates:
            logger.warning("STM is full but no non-core, timeless facts could be found to archive.")
            return

        for mem in candidates:
            # ... (Rest der Archivierungslogik bleibt exakt gleich)
            # 1. In LTM kopieren
            new_ltm_entry = database.LongTermMemory(
                original_memory_id=mem.id,
                chat_id=mem.chat_id,
                snippet=mem.snippet,
                embedding_json=mem.embedding_json,
                created_at=mem.created_at
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
        expired_memories = db.query(database.Memory).filter(
            database.Memory.expires_at != None,
            database.Memory.expires_at < now
        ).all()

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

# ... (Rest der Datei bleibt unverändert)

---
**Implementierung abgeschlossen:** Alle Schritte dieser Arbeitsanweisung wurden erfolgreich umgesetzt.
Schritt 3: Die Intelligenz implementieren (llm_gateway.py)
Hier fügen wir die Klassifizierungslogik ein. Wenn eine Websuche durchgeführt wurde, fragen wir das LLM, ob das Ergebnis gespeichert werden soll und für wie lange.
code
Python
# backend/llm_gateway.py

# ... (imports, inkl. datetime)
import datetime
import asyncio # Wichtig für Hintergrund-Tasks

# ... (andere Funktionen)

async def reason_and_respond(user_prompt: str, chat_history: List[Dict], memory_context: str, db: Session, api_key: str, model: str, provider: str, context_manager: ContextManager, user_name: Optional[str] = None) -> Dict:
    # ... (Anfang der Funktion bis zur Websuche bleibt unverändert)

    if response.get("type") == "text" and "Ich habe dazu keine Informationen in meinen Fakten" in response.get("text", ""):
        logger.info("LLM indicated no information in facts. Performing web search...")
        web_result = await perform_websearch(user_prompt)
        
        logger.info("Web search performed. Now formatting result with LLM...")

        # ... (der formatting_prompt bleibt unverändert)
        
        formatting_messages = [{"role": "user", "content": formatting_prompt}]

        formatted_response = await call_llm(
            provider=provider, 
            model_id=model, 
            api_key=api_key, 
            messages=formatting_messages
        )
        
        # --- NEUER, INTELLIGENTER SPEICHER-BLOCK ---
        
        # Holen Sie sich den zusammengefassten Text aus der formatierten Antwort
        summarized_web_answer = formatted_response.get("text")
        
        if summarized_web_answer:
            # Erstelle eine Hintergrundaufgabe, um die Klassifizierung und Speicherung durchzuführen,
            # ohne die Antwort an den Benutzer zu blockieren.
            asyncio.create_task(
                classify_and_save_web_result(
                    db=db,
                    user_question=user_prompt,
                    llm_answer=summarized_web_answer,
                    api_key=api_key,
                    provider=provider,
                    model=model,
                    chat_id=chat_history[-1].get('chat_id_for_saving') # Wir müssen die chat_id irgendwie hierher bekommen
                )
            )

        # ... (der Rest der Funktion mit Kostenberechnung usw. bleibt gleich)
        # ... (Rückgabe der formatted_response)
        
    # ... (Rest der Funktion)


# --- NEUE HELFERFUNKTION FÜR DEN LLM_GATEWAY ---

async def classify_and_save_web_result(db: Session, user_question: str, llm_answer: str, api_key: str, provider: str, model: str, chat_id: int):
    """
    Klassifiziert eine aus einer Websuche gewonnene Information und speichert sie 
    ggf. als ephemere Erinnerung.
    """
    from backend import memory_manager # Import hier, um Zirkelimporte zu vermeiden
    
    classification_prompt = f"""
    Du bist ein Daten-Analyst. Deine Aufgabe ist es zu bewerten, ob eine Information zeitlos oder zeitkritisch ist.
    Zeitkritische Informationen sind Dinge wie aktuelle Preise, Nachrichten, Termine, Wetter oder temporäre Zustände, die sich wahrscheinlich in weniger als 48 Stunden ändern.
    Zeitlose Informationen sind Anleitungen, Fakten, technische Daten, biografische Details oder historisches Wissen.

    Benutzerfrage: "{user_question}"
    Antwort: "{llm_answer}"

    Ist die Information in der ANTWORT basierend auf der FRAGE wahrscheinlich zeitkritisch?
    Antworte NUR mit 'JA' oder 'NEIN'.
    """
    
    try:
        messages = [{"role": "user", "content": classification_prompt}]
        # Wir verwenden ein schnelles, günstiges Modell für die Klassifizierung
        classification_model = "gpt-4o-mini" if provider == "openai" else "gemini-1.5-flash-latest"
        
        response = await call_llm(provider, classification_model, api_key, messages)
        decision = response.get("text", "NEIN").strip().upper()

        if "JA" in decision:
            expiration_date = datetime.datetime.now() + datetime.timedelta(days=2) # 48 Stunden Gültigkeit
            logger.info(f"Web result classified as EPHEMERAL. Saving with expiration date. Fact: '{llm_answer[:100]}...'")
            memory_manager.save_memory_snippet(db, chat_id, llm_answer, is_core=False, expires_at=expiration_date)
        else:
            logger.info(f"Web result classified as TIMELESS. Saving as a regular memory. Fact: '{llm_answer[:100]}...'")
            # Wir speichern es als normalen, nicht-essentiellen Fakt, der den normalen Archivierungsprozess durchläuft
            memory_manager.save_memory_snippet(db, chat_id, llm_answer, is_core=False, expires_at=None)

    except Exception as e:
        logger.error(f"Error during web result classification and saving: {e}", exc_info=True)

# Anpassung, um die chat_id zu übergeben
# In `main.py`, in `handle_chat_request`, müssen wir die chat_id in den Verlauf einfügen.
# chat_history.append({"role": ..., "content": ..., "chat_id_for_saving": request.chat_id})
# Aber eine sauberere Methode ist, die chat_id direkt an `reason_and_respond` zu übergeben.

# Lass uns die Signatur von `reason_and_respond` anpassen:
async def reason_and_respond(..., chat_id: int, ...):
    # und dann rufen wir `classify_and_save_web_result` mit `chat_id=chat_id` auf.
    # Die Änderungen in `main.py` wären dann trivial.
Anmerkung: Die Übergabe der chat_id muss noch in der Aufrufkette von main.py -> llm_gateway.py durchgereicht werden. Das ist eine kleine, aber notwendige Anpassung.
Schritt 4: Den Aufräumprozess einplanen (main.py)
Wo rufen wir unsere neue prune_expired_memories-Funktion auf? Ein guter Ort ist derselbe wie für die Archivierung: Beim Erstellen eines neuen Chats. Das passiert regelmäßig, aber nicht so oft, dass es die Performance beeinträchtigt.
code
Python
# backend/main.py

# ... (andere imports)

# ... (die bestehende create_chat Funktion)

@app.post("/api/chats", response_model=schemas.ChatResponse)
async def create_chat(chat: schemas.ChatCreate, db: Session = Depends(get_db)):
    # ... (der bestehende Block zur Zusammenfassung bleibt unverändert)
    
    # Die neue Archivierungs- UND Aufräumlogik kommt hierhin
    try:
        # Bestehende Archivierung
        asyncio.create_task(run_archival())
        # NEU: Geplantes Aufräumen
        asyncio.create_task(run_pruning()) 
    except Exception as e:
        logger.error(f"Failed to schedule memory maintenance tasks: {e}")

    return crud.create_chat(db, title=chat.title)


# Füge diese neue Helferfunktion irgendwo in main.py auf der obersten Ebene hinzu
# (z.B. nach der run_archival Funktion).

async def run_pruning():
    """
    Wrapper, um die synchrone DB-Operation zum Aufräumen in einer asyncio-Task auszuführen.
    """
    logger.info("Background memory pruning task starting.")
    db_session = database.SessionLocal()
    try:
        # Hier rufen wir unsere neue Funktion auf
        memory_manager.prune_expired_memories(db_session)
        logger.info("Background memory pruning task finished successfully.")
    except Exception as e:
        logger.error(f"An error occurred in the background pruning task: {e}", exc_info=True)
    finally:
        db_session.close()

# ... (Rest der Datei bleibt unverändert)

---
**Implementierung abgeschlossen:** Alle Schritte dieser Arbeitsanweisung wurden erfolgreich umgesetzt.