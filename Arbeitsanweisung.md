ARBEITSANWEISUNG: Finale Korrektur der Chat-Route
Ziel: Die /api/chat-Route in backend/main.py so korrigieren, dass sie die korrekte Datenbank-Session verwendet und die Chat-Historie erfolgreich an den ContextManager übergibt.
Aktueller Branch: dev/multichat-Kontextmemory1
Schritt 1: Austausch der main.py
Aktion: Ersetze den gesamten Inhalt der Datei backend/main.py mit der folgenden, final korrigierten Version.
Tool: write_file
Datei: backend/main.py
Inhalt (Final und Korrigiert):
code
Python
# Alle imports bleiben gleich wie in der letzten Version...
import json
import os
import keyring
import logging
# ... etc ...
from backend.context_manager import ContextManager # Wichtig!

# ... (app, startup, etc. bleiben gleich)

# --- Hinzufügen des ContextManager ---
model_catalog = load_model_catalog()
context_manager = ContextManager(model_catalog=model_catalog)

# ... (alle anderen Routen bleiben gleich) ...

# --- FINAL KORRIGIERTE CHAT-ROUTE ---
@app.post("/api/chat")
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        api_key = keyring.get_password("Janus-Projekt", request.provider)
        if not api_key:
            raise HTTPException(status_code=400, detail=f"API Key for {request.provider} not found.")
        
        chat_history_for_prompt = []
        if request.chat_id:
            # 1. Lade die Historie aus der DB
            messages_from_db = crud.get_messages_by_chat_id(db, chat_id=request.chat_id)
            
            # 2. Formatiere die Historie für den Context Manager
            formatted_history = [
                {"role": "user" if msg.sender == "user" else "assistant", "content": msg.content}
                for msg in messages_from_db
            ]
            
            # Füge die aktuelle Nachricht des Benutzers für die Kontext-Erstellung hinzu
            formatted_history.append({"role": "user", "content": request.prompt})
            
            # 3. Baue den Prompt mit dem ContextManager
            chat_history_for_prompt = context_manager.build_prompt_history(formatted_history, request.model)
        else:
            # Fallback für Chats ohne Historie (sollte nicht passieren)
            chat_history_for_prompt = [{"role": "user", "content": request.prompt}]

        # 4. Rufe die LLM-API auf
        gateway_response = await llm_gateway.call_llm(
            request.provider, 
            request.model, 
            "", # Prompt ist jetzt in der History
            api_key, 
            chat_history=chat_history_for_prompt
        )

        # 5. Speichere die Konversation
        if request.chat_id:
            user_message = Message(chat_id=request.chat_id, sender="user", content=request.prompt)
            db.add(user_message)
            
            model_message = Message(
                chat_id=request.chat_id,
                sender="model",
                content=gateway_response.get("text", ""),
                image_path=gateway_response.get("image_url")
            )
            db.add(model_message)
            db.commit()

        # ... Kosten-Logik ...

        return {
            "sender": "model",
            "text": gateway_response.get("text", ""),
            "image_url": gateway_response.get("image_url")
        }
    except Exception as e:
        tb_str = traceback.format_exc()
        logger.error(f"Error in chat endpoint: {e}\n{tb_str}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

# ... (Rest der Datei bleibt gleich)