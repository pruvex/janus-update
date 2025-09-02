Schlachtplan zur finalen Reparatur
Teil 1: Gemini wieder zum Leben erwecken (und den Summarizer robust machen)
Wir müssen sicherstellen, dass die Zusammenfassung immer das Modell und den Provider verwendet, das/der gerade aktiv ist.
Öffnen Sie backend/chat_summarizer.py.
Passen Sie die Funktion summarize_and_store_chat an. Sie muss provider und model als Argumente akzeptieren.
code
Python
# In chat_summarizer.py
# ... (imports)

async def summarize_and_store_chat(db: Session, chat_id: int, api_key: str, provider: str, model: str): # Hinzugefügte Argumente
    # ... (der Rest der Funktion bleibt gleich, sie verwendet jetzt die übergebenen provider und model)
Öffnen Sie backend/main.py.
Finden Sie den Endpunkt @app.post("/api/chats").
Passen Sie den Aufruf von summarize_and_store_chat an, damit er den zuletzt verwendeten Provider und das Modell aus der Konfiguration übergibt.
code
Python
# In main.py
@app.post("/api/chats", response_model=schemas.ChatResponse)
async def create_chat(chat: schemas.ChatCreate, db: Session = Depends(get_db)):
    existing_chats = crud.get_chats(db)
    if existing_chats:
        last_chat = existing_chats[-1]
        messages = crud.get_messages_by_chat_id(db, chat_id=last_chat.id)
        if messages:
            config = load_config()
            # HIER DIE ÄNDERUNG: Lade die zuletzt verwendeten Daten
            provider = config.get("last_used_provider", "openai")
            model = config.get("last_used_model", "gpt-4o-mini") # Fallback, falls nichts gespeichert ist
            api_key = keyring.get_password("Janus-Projekt", provider)
            
            if api_key:
                asyncio.create_task(chat_summarizer.summarize_and_store_chat(db, last_chat.id, api_key, provider, model))
            else:
                logger.warning(f"API key for {provider} not found. Skipping chat summarization.")
    return crud.create_chat(db, title=chat.title)
Teil 2: Den Relevanz-Filter im Gedächtnis reparieren
Wir müssen den Prompt für den Filter in llm_gateway.py verbessern. Er muss weniger streng und allgemeiner sein.
Öffnen Sie backend/llm_gateway.py.
Suchen Sie die reason_and_respond-Funktion.
Finden Sie den filtering_prompt.
Ersetzen Sie den Prompt durch diese neue, verbesserte Version:
code
Python
# In llm_gateway.py, in reason_and_respond

filtering_prompt = (
    "Du bist ein Relevanz-Analyst. Deine Aufgabe ist es, aus einer Liste von Fakten diejenigen auszuwählen, die potenziell zur Beantwortung einer Benutzerfrage beitragen könnten. "
    "Sei dabei nicht zu streng. Es ist besser, einen möglicherweise nützlichen Fakt mehr zu inkludieren als einen wichtigen zu übersehen.\n"
    "Gib jeden relevanten Fakt in einer neuen Zeile aus. Wenn keine Fakten relevant sind, antworte nur mit dem Wort 'Keine'.\n\n"
    "--- FAKTEN-LISTE ---\n"
    f"{memory_context}\n\n"
    "--- BENUTZERFRAGE ---\n"
    f"{user_prompt}\n\n"
    "--- POTENZIELL RELEVANTE FAKTEN ---"
)

# Passen Sie auch die Prüfung danach an
filter_response = await call_llm(provider, model, filtering_prompt, api_key, chat_history=[])
filtered_facts = filter_response.get("text") or ""
if filtered_facts.strip().lower() != 'keine': # Prüfe auf 'Keine'
    relevant_memory_context = filtered_facts
    logger.info(f"Filtered relevant facts: {relevant_memory_context}")
else:
    logger.info("No relevant facts found by the filter.")