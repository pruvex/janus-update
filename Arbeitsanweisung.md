Analyse des Problems
GPT (OpenAI) - Der erfolgreiche Weg:
Ihre Logik für DALL-E ruft image_manager.save_image_from_url() auf.
Diese Funktion speichert das Bild und gibt, wie der Log zeigt, einen Pfad zurück, der mit /static/images/ beginnt:
code
Code
[DEBUG] - Returning relative path: /static/images/f68d...png
In Ihrer main.py gibt es am Ende der Funktion eine "Reparatur"-Zeile, die diesen Pfad korrigiert, bevor er an das Frontend gesendet wird:
code
Python
local_image_path = local_image_path.replace("/static/images", "/user_images")
Das Frontend erhält also den korrekten Pfad /user_images/f68d...png und kann das Bild abrufen, was dieser Log-Eintrag bestätigt:
code
Code
[INFO] - "GET /user_images/f68d...png HTTP/1.1" 200 OK
Gemini - Der fehlerhafte Weg:
Ihre neue, korrigierte Logik für Gemini ruft image_manager.save_image_from_bytes() auf (innerhalb von llm_gateway.py).
Diese Funktion gibt bereits den korrekten Pfad zurück, der mit /user_images/ beginnt:
code
Code
[DEBUG] - _call_gemini_image_generation_api: Returning image_url: /user_images/898e...png
Wenn dieser Pfad (/user_images/...) nun in main.py an die "Reparatur"-Zeile .replace("/static/images", "/user_images") kommt, passiert nichts, weil der zu ersetzende Teil (/static/images) nicht gefunden wird.
Das Problem ist: Der von save_image_from_url zurückgegebene Pfad /static/images/... ist falsch, wird aber in main.py korrigiert. Der von save_image_from_bytes zurückgegebene Pfad /user_images/... ist richtig, aber Ihre main.py hat an einer Stelle noch die alte Logik erwartet.
Die Lösung: Code vereinheitlichen und reparieren
Die beste Lösung ist, den Code so zu gestalten, dass er für alle Anbieter gleich funktioniert. Wir sorgen dafür, dass der image_manager immer den korrekten, für das Web zugänglichen Pfad zurückgibt und entfernen die "Reparatur"-Logik aus main.py.
Schritt 1: Korrigieren Sie image_manager.py
Öffnen Sie backend/image_manager.py und ändern Sie die Funktion save_image_from_url so, dass sie direkt den /user_images/-Pfad zurückgibt.
Ersetzen Sie den Inhalt von backend/image_manager.py hiermit:
code
Python
import os
import uuid
import requests
import logging
from backend.utils.paths import get_app_data_dir

logger = logging.getLogger('janus_backend')

# (Ihre neue Funktion 'save_image_from_bytes' sollte bereits so aussehen)
def save_image_from_bytes(image_bytes: bytes) -> str:
    """Saves image data from bytes to a file and returns the web-accessible path."""
    image_dir = os.path.join(get_app_data_dir(), "images")
    os.makedirs(image_dir, exist_ok=True)
    
    filename = f"{uuid.uuid4()}.png"
    file_path = os.path.join(image_dir, filename)
    
    with open(file_path, "wb") as f:
        f.write(image_bytes)
        
    logger.info(f"Image saved from bytes to {file_path}")
    # Gibt den Pfad zurück, den das Frontend verwenden kann
    return f"/user_images/{filename}"


def save_image_from_url(image_url: str) -> str:
    """Downloads an image from a URL, saves it locally, and returns the web-accessible path."""
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()

        image_dir = os.path.join(get_app_data_dir(), "images")
        os.makedirs(image_dir, exist_ok=True)
        
        filename = f"{uuid.uuid4()}.png"
        file_path = os.path.join(image_dir, filename)

        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # --- KORREKTUR HIER ---
        # Gibt jetzt direkt den korrekten, vom Server bereitgestellten Pfad zurück.
        relative_path = f"/user_images/{filename}"
        logger.debug(f"Image saved locally to {file_path}. Returning web path: {relative_path}")
        return relative_path

    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading image from {image_url}: {e}")
        return None

# (Die Funktion migrate_image_paths bleibt unverändert)
async def migrate_image_paths(db_session, message_model):
    logger.info("Starting image path migration...")
    messages_with_images = db_session.query(message_model).filter(message_model.image_path.isnot(None)).all()
    for message in messages_with_images:
        if message.image_path and message.image_path.startswith("https://oaidalleapiprodscus.blob.core.windows.net"):
            logger.debug(f"Migrating image for message ID {message.id} from URL.")
            new_path = save_image_from_url(message.image_path)
            if new_path:
                message.image_path = new_path
        else:
            logger.debug(f"Image path for message ID {message.id} is already local or not a DALL-E URL: {message.image_path}")
    db_session.commit()
    logger.info("Image path migration complete.")
Schritt 2: Vereinfachen Sie main.py
Da nun beide Speicherfunktionen den korrekten Pfad zurückgeben, können wir die überflüssige .replace()-Zeile in main.py entfernen. Dies macht den Code sauberer und behebt den Fehler.
Ersetzen Sie die Funktion handle_chat_request in backend/main.py vollständig durch diese Version:
code
Python
async def handle_chat_request(request: ChatRequest, db: Session, context_manager: ContextManager, model_catalog: dict):
    api_key = keyring.get_password("Janus-Projekt", request.provider)
    logger.info(f"handle_chat_request: Provider from request: {request.provider}")
    logger.info(f"handle_chat_request: API Key retrieved (masked): {api_key[:4] + '********' + api_key[-4:] if api_key else 'None'}")
    if not api_key: raise HTTPException(status_code=400, detail="API Key not found.")

    intent = await _classify_intent_with_llm_fallback(request.prompt, api_key, request.provider, request.model)

    # --- Start der neuen, vereinheitlichten Logik ---

    if request.chat_id is None:
        new_chat = crud.create_chat(db, title="New Chat")
        request.chat_id = new_chat.id
        logger.info(f"New chat created with ID: {request.chat_id}")

    # Speichere die Benutzernachricht immer zuerst
    crud.create_message(db, chat_id=request.chat_id, sender="user", content=request.prompt)
    
    # Standardwerte für die Antwort
    final_answer = ""
    local_image_path = None
    usage = {}
    cost = {}
    
    match intent:
        case "image_generation":
            model_info = model_catalog.get(request.model)
            if "image_generation" in model_info.get("capabilities", []):
                # Direkte Bilderzeugung
                _check_model_capability(request.model, model_catalog, "image_generation")
                check_budget_and_raise_if_exceeded(db)
                logger.info(f"Image Generation Request (Direct): chat_id={request.chat_id}, prompt='{request.prompt}', provider={request.provider}, model={request.model}")
                
                llm_response = await llm_gateway.reason_and_respond(
                    request.prompt, [], "", db, api_key, request.model, request.provider, context_manager
                )
                final_answer = llm_response.get("text", "")
                local_image_path = llm_response.get("image_url") # Nimmt direkt den /user_images/ Pfad
                usage = llm_response.get("usage", {})
                cost = llm_response.get("cost", {})

            elif "tool_calling" in model_info.get("capabilities", []):
                 # Bilderzeugung via Tool
                _check_model_capability(request.model, model_catalog, "tool_calling")
                check_budget_and_raise_if_exceeded(db)
                logger.info(f"Image Generation Request (via Tool): chat_id={request.chat_id}, prompt='{request.prompt}', provider={request.provider}, model={request.model}")

                image_response = {}
                if request.provider == "openai":
                    image_response = await llm_gateway.generate_image_tool(api_key=api_key, prompt=request.prompt)
                elif request.provider == "gemini":
                    image_model_id = model_info.get("image_generation_model")
                    if not image_model_id:
                        raise HTTPException(status_code=400, detail=f"Gemini text model {request.model} does not specify an image generation model.")
                    image_response = await llm_gateway._call_gemini_image_generation_api(api_key, image_model_id, request.prompt)
                else:
                    raise HTTPException(status_code=400, detail=f"Unsupported provider {request.provider} for image generation via tool.")
                
                final_answer = image_response.get("text", "")
                local_image_path = image_response.get("image_url") # Nimmt direkt den /user_images/ Pfad
                usage = image_response.get("usage", {})
                cost = image_response.get("cost", {})
            else:
                raise HTTPException(status_code=400, detail=f"Model {request.model} does not support image generation directly or via tool calls.")

        case "tool_call" | "memory_query" | "chat":
            capability = intent if intent != "chat" else "chat" # memory_query braucht chat-Fähigkeit
            if intent == "memory_query": capability = "memory_query"
            
            _check_model_capability(request.model, model_catalog, capability)
            check_budget_and_raise_if_exceeded(db)

            logger.info(f"{intent.capitalize()} Request: chat_id={request.chat_id}, prompt='{request.prompt}', provider={request.provider}, model={request.model}")

            # Kontextaufbau (Memory und Chat-Verlauf)
            memory_context = ""
            if capability in ["chat", "memory_query"]:
                 if len(request.prompt.split()) > 3:
                    memory_manager.save_raw_memory(db, chat_id=request.chat_id, user_input=request.prompt)
                 all_memories = memory_manager.get_all_memories(db)
                 logger.info(f"Loaded {len(all_memories)} memories from DB.")
                 similar_snippets = vector_service.find_similar_snippets(request.prompt, all_memories, top_k=50, threshold=0.1)
                 memory_context = "\n".join([f"- {mem.snippet}" for mem in similar_snippets])
                 logger.info(f"Memory context for reasoning: {memory_context}")

            chat_history = []
            if request.chat_id:
                messages = crud.get_messages_by_chat_id(db, chat_id=request.chat_id)
                for m in messages:
                    msg_data = {"role": "user" if m.sender=="user" else "assistant", "content": m.content}
                    if m.image_path:
                        msg_data["image_url"] = m.image_path
                    chat_history.append(msg_data)

            # Haupt-LLM-Aufruf
            llm_response = await llm_gateway.reason_and_respond(
                request.prompt, chat_history, memory_context, db, api_key, request.model, request.provider, context_manager
            )
            
            final_answer = llm_response.get("text", "")
            local_image_path = llm_response.get("image_url")
            usage = llm_response.get("usage", {})
            cost = llm_response.get("cost", {})

            # Faktenextraktion im Hintergrund für 'chat'
            if intent == "chat":
                 full_exchange_text = f"User: {request.prompt}\nAssistant: {final_answer}"
                 asyncio.create_task(
                     memory_extractor.extract_and_save_fact(
                         db=db, chat_id=request.chat_id, text_block=full_exchange_text, original_prompt=request.prompt, main_api_key=api_key, provider=request.provider, model=request.model
                     )
                 )
        case _:
            raise HTTPException(status_code=400, detail="Unknown intent")
            
    # --- Ende der neuen, vereinheitlichten Logik ---

    # Speichere die Antwort des Models und die Kosten
    crud.create_message(db, chat_id=request.chat_id, sender="model", content=final_answer, image_path=local_image_path)

    if usage and cost.get("total_cost", 0) > 0:
        database.save_cost_entry(
            date=datetime.now(), model=request.model,
            input_tokens=usage.get("prompt_tokens"), output_tokens=usage.get("completion_tokens"),
            image_quality=usage.get("image_quality"), image_cost=cost.get("image_cost"),
            total_cost=cost.get("total_cost", 0)
        )

    # Speichere das zuletzt verwendete Modell
    config = load_config()
    config["last_used_provider"] = request.provider
    config["last_used_model"] = request.model
    save_config(config)

    # Gib die finale Antwort an das Frontend zurück
    return {"sender": "model", "text": final_answer, "image_url": local_image_path}
Nachdem Sie diese beiden Dateien aktualisiert haben, sollte die Bilderzeugung für beide Anbieter, OpenAI und Gemini, reibungslos funktionieren und die Bilder korrekt im Chat angezeigt werden.