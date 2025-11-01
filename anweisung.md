Hier sind die konkreten Code-Änderungen, die wir dafür benötigen:
1. Anpassung des memory_extractor.py
Wir müssen der Faktenextraktion beibringen, auch zeitkritische Fakten zu erkennen und ihnen ein Ablaufdatum zu geben.
code
Python
# backend/services/memory_extractor.py

# ... (andere Imports bleiben gleich)
import datetime

# ...

# NEUER PROMPT, um die Zeitkritikalität zu bewerten
IS_TIME_SENSITIVE_PROMPT = (
    "Du bist ein Daten-Analyst. Deine Aufgabe ist es zu bewerten, ob eine Information zeitkritisch oder zeitlos ist.\n"
    "Zeitkritische Informationen sind Dinge wie aktuelle Preise, Nachrichten, Termine, Wetter oder temporäre Zustände, die wahrscheinlich in weniger als 48 Stunden ihre Relevanz verlieren.\n"
    "Zeitlose Informationen sind Anleitungen, Fakten, technische Daten, biografische Details oder historisches Wissen.\n\n"
    "FAKT: '{fact}'\n\n"
    "Ist dieser Fakt wahrscheinlich zeitkritisch? Antworte NUR mit 'JA' oder 'NEIN'."
)


async def extract_and_save_fact(
    db: Session,
    chat_id: int,
    text_block: str,
    main_api_key: str,
    provider: str,
    model: str,
):
    """
    Extrahiert Fakten aus einem Textblock, klassifiziert sie (Core vs. Non-Core, Zeitkritisch vs. Zeitlos) 
    und speichert sie intelligent in der Datenbank.
    """
    # ... (Anfang der Funktion bleibt gleich) ...

        for fact in extracted_facts:
            # ... (Logik zur Duplikaterkennung bleibt gleich) ...

            is_core = False
            expires_at = None # Standardmäßig kein Ablaufdatum

            try:
                # ... (Core-Fact-Klassifizierung bleibt gleich) ...
            except Exception as e:
                logger.error(f"Konnte Fakt nicht als Core/Non-Core klassifizieren: {e}. Standard: Non-Core.")

            # --- START: NEUE LOGIK FÜR ZEITKRITISCHE FAKTEN ---
            # Wir prüfen nur bei nicht-essenziellen Fakten, ob sie zeitkritisch sind.
            if not is_core:
                try:
                    time_history = [{"role": "user", "content": IS_TIME_SENSITIVE_PROMPT.format(fact=fact)}]
                    time_response = await llm_gateway.call_llm(
                        provider=provider, model_id=model, api_key=main_api_key, messages=time_history
                    )
                    if "ja" in time_response.get("text", "").lower():
                        # Setze ein Ablaufdatum von 2 Tagen für zeitkritische Infos
                        expires_at = datetime.datetime.now() + datetime.timedelta(days=2)
                        logger.info(f"Fakt als ZEITKRITISCH klassifiziert. Läuft ab am: {expires_at}")
                except Exception as e:
                    logger.error(f"Konnte Fakt nicht als zeitkritisch klassifizieren: {e}. Standard: Zeitlos.")
            # --- ENDE: NEUE LOGIK ---
            
            logger.info(f"[NEW FACT] Speichere neuen Fakt: '{fact}' (Core: {is_core}, Expires: {expires_at})")
            memory_manager.save_memory_snippet(
                db, chat_id=chat_id, snippet_text=fact, is_core=is_core, expires_at=expires_at
            )

        return extracted_facts
    # ... (Ende der Funktion bleibt gleich) ...
2. Anpassung des memory_manager.py und der Datenbank
Wir müssen das Memory-Modell anpassen, um das expires_at-Feld zu speichern und eine Funktion zum Aufräumen abgelaufener Fakten hinzufügen.
Änderung in backend/data/database.py:
code
Python
# backend/data/database.py
# ...
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey, Text
import datetime
# ...

class Memory(Base):
    __tablename__ = "memories"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    snippet = Column(String, nullable=False)
    embedding_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)
    last_accessed_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    is_core_fact = Column(Boolean, default=False)
    # --- DIESE ZEILE HINZUFÜGEN ---
    expires_at = Column(DateTime, nullable=True, default=None)
Änderungen in backend/memory_manager.py:
code
Python
# backend/memory_manager.py
# ...
import datetime

# --- ÄNDERUNG: Signatur um expires_at erweitern ---
def save_memory_snippet(
    db: Session,
    chat_id: int,
    snippet_text: str,
    is_core: bool = False,
    expires_at: Optional[datetime.datetime] = None, # Hinzufügen
):
    embedding = vector_service.generate_embedding(snippet_text)
    if embedding is None:
        return None
    # --- Geänderter Aufruf ---
    db_memory = database.Memory(
        chat_id=chat_id,
        snippet=snippet_text,
        embedding_json=embedding,
        is_core_fact=is_core,
        expires_at=expires_at,  # Das neue Feld wird übergeben
    )
    db.add(db_memory)
    db.commit()
    db.refresh(db_memory)
    return db_memory

# --- NEUE AUFRÄUMFUNKTION HINZUFÜGEN ---
def prune_expired_memories(db: Session):
    """Sucht und löscht alle ephemeren Erinnerungen, deren Ablaufdatum überschritten ist."""
    try:
        now = datetime.datetime.now()
        # Finde alle Erinnerungen, deren expires_at in der Vergangenheit liegt
        expired_memories = (
            db.query(database.Memory)
            .filter(
                database.Memory.expires_at != None, database.Memory.expires_at < now
            )
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

# --- NUR FÜR DEN GOLD STANDARD: ARCHIVIERUNG ANPASSEN ---
def archive_old_memories(db: Session):
    """
    Prüft, ob das STM bereinigt werden muss und verschiebt die ältesten,
    am seltensten genutzten und nicht-essentiellen Erinnerungen ins LTM.
    WICHTIG: Zeitkritische Fakten werden nicht archiviert, sondern später von `prune` gelöscht.
    """
    # ... (Anfang der Funktion bleibt gleich) ...
        # Finde Kandidaten: Nicht "core", nicht ablaufend, sortiert nach letztem Zugriff
        candidates = (
            db.query(database.Memory)
            .filter(database.Memory.is_core_fact == False)
            .filter(database.Memory.expires_at == None)  # <-- WICHTIGE ÄNDERUNG!
            .order_by(database.Memory.last_accessed_at.asc())
            .limit(num_to_archive)
            .all()
        )
    # ... (Rest der Funktion bleibt gleich) ...
3. Die Aufräumfunktion beim Start ausführen
Wir müssen sicherstellen, dass abgelaufene Fakten regelmäßig gelöscht werden. Der beste Zeitpunkt dafür ist beim Start der Anwendung.
Änderung in backend/main.py:
code
Python
# backend/main.py
# ...
import asyncio
# ...

@app.on_event("startup")
async def startup_event():
    database.init_db()
    # --- START: HINZUFÜGEN ---
    logger.info("Scheduling initial memory maintenance tasks on startup.")
    # Wir erstellen eine dedizierte DB-Session für die Hintergrund-Tasks
    db_session_for_tasks = database.SessionLocal()
    try:
        # Führe die Wartung in Hintergrund-Tasks aus, damit der Start nicht blockiert wird.
        asyncio.create_task(run_archival(db_session_for_tasks))
        asyncio.create_task(run_pruning(db_session_for_tasks))
    except Exception as e:
        logger.error(f"Failed to schedule memory maintenance tasks on startup: {e}")
        db_session_for_tasks.close() # Nur bei Fehler hier schließen
    # --- ENDE: HINZUFÜGEN ---
    db = next(get_db())
    db.close()


# Füge diese neuen Helferfunktionen irgendwo in main.py auf der obersten Ebene hinzu
async def run_archival(db_session: Session):
    """
    Wrapper, um die synchrone DB-Operation in einer asyncio-Task auszuführen.
    """
    logger.info("Background memory archival task starting.")
    try:
        memory_manager.archive_old_memories(db_session)
        logger.info("Background memory archival task finished successfully.")
    except Exception as e:
        logger.error(
            f"An error occurred in the background archival task: {e}", exc_info=True
        )
    finally:
        # Diese Session wird nur einmal geschlossen, von dem Task, der als letztes fertig wird.
        if db_session.is_active:
             db_session.close()


async def run_pruning(db_session: Session):
    """
    Wrapper, um die synchrone DB-Operation zum Aufräumen in einer asyncio-Task auszuführen.
    """
    logger.info("Background memory pruning task starting.")
    try:
        memory_manager.prune_expired_memories(db_session)
        logger.info("Background memory pruning task finished successfully.")
    except Exception as e:
        logger.error(
            f"An error occurred in the background pruning task: {e}", exc_info=True
        )
Zusammenfassung
Mit diesen Änderungen haben wir Folgendes erreicht:
Intelligente Fakten-Extraktion: Unser System kann jetzt zwischen zeitlosen Fakten (die ins LTM wandern können) und zeitkritischen Fakten (wie Wetter) unterscheiden.
Temporäres Gedächtnis: Zeitkritische Fakten erhalten ein "Verfallsdatum" und werden im STM gespeichert.
Automatisches Aufräumen: Beim Start der Anwendung werden alle abgelaufenen Fakten automatisch gelöscht, sodass das STM sauber bleibt.
Effiziente Wiederverwendung: Wenn du jetzt nach dem Wetter fragst, wird die Antwort als Fakt mit Ablaufdatum gespeichert. Fragst du innerhalb dieses Zeitraums erneut (auch in einem neuen Chat), wird die Information aus dem Gedächtnis abgerufen (FINAL HYBRID Memory Context wird nicht mehr leer sein), und es findet keine erneute Websuche statt.