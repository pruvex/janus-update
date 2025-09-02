Schritt 1: Den Fakten-Extraktor disziplinieren (Halluzinationen stoppen)
Wir müssen verhindern, dass der memory_extractor die Erfindungen der KI als Fakten speichert.
Öffnen Sie backend/memory_extractor.py.
Suchen Sie den extraction_prompt.
Ersetzen Sie ihn durch diesen neuen, viel strengeren Prompt, der sich nur auf die Aussagen des Benutzers konzentriert:
code
Python
# In memory_extractor.py
extraction_prompt = (
    "Du bist ein Analyst für Faktenextraktion. Deine Aufgabe ist es, aus einem Dialog zwischen einem Benutzer und einem Assistenten FAKTEN zu extrahieren. "
    "**REGEL 1: Extrahiere NUR Fakten, die der BENUTZER in seiner LETZTEN Nachricht explizit genannt hat.**\n"
    "**REGEL 2: Ignoriere die Schlussfolgerungen, Meinungen oder Fragen des Assistenten VOLLSTÄNDIG.**\n"
    "Formuliere die Fakten als einfache, neutrale Aussagen über den Benutzer (z.B. 'Der Benutzer heißt Klaus', 'Der Benutzer mag die Farbe Blau').\n"
    "Wenn der Benutzer keine neuen Fakten nennt, antworte NUR mit dem Wort 'Keine'.\n\n"
    "--- DIALOG ---\n"
    "{text_block}\n\n"
    "--- EXTRAHIERTE FAKTEN ---"
)
Schritt 2: Das LLM zum "Detektiv" machen (Konsistenz erzwingen)
Wir ersetzen die fehleranfällige Filter-Logik in llm_gateway.py durch einen einzigen, extrem robusten "Master-Prompt".
Öffnen Sie backend/llm_gateway.py.
Suchen Sie die reason_and_respond-Funktion.
Ersetzen Sie den gesamten Inhalt der Funktion durch diese finale Version, die das Detektiv-Prinzip anwendet:
code
Python
# In llm_gateway.py

async def reason_and_respond(user_prompt: str, chat_history: List[Dict], memory_context: str, db: Session, api_key: str, model: str, provider: str, context_manager: ContextManager) -> Dict:
    logger.info(f"reason_and_respond: Original user_prompt={user_prompt}")
    
    # Der System-Prompt wird jetzt hier dynamisch aufgebaut
    # und enthält die unmissverständlichen Anweisungen.
    system_rules = (
        "Du bist Janus, ein hilfreicher KI-Detektiv. Deine Aufgabe ist es, die Frage des Benutzers ausschließlich auf Basis der unten stehenden BEWEISE zu beantworten. Erfinde oder schlussfolgere nichts, was nicht direkt durch die Beweise gestützt wird.\n"
        "**REGEL 1: Die 'FAKTEN AUS DEM LANGZEITGEDÄCHTNIS' sind die absolute Wahrheit.**\n"
        "**REGEL 2: Der 'AKTUELLE GESPRÄCHSVERLAUF' liefert den unmittelbaren Kontext.**\n"
        "**REGEL 3: Wenn die Beweise nicht ausreichen, um die Frage zu beantworten, antworte, dass du die Information nicht hast.**"
    )

    # Wir bauen den finalen Prompt für das LLM zusammen
    final_prompt_for_llm = f"{system_rules}\n\n"
    
    if memory_context:
        final_prompt_for_llm += f"--- FAKTEN AUS DEM LANGZEITGEDÄCHTNIS ---\n{memory_context}\n\n"
        
    # Wir übergeben den Chat-Verlauf als Teil des Prompts, um die Struktur zu wahren
    history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history])
    final_prompt_for_llm += f"--- AKTUELLER GESPRÄCHSVERLAUF ---\n{history_str}\n\n"
    
    final_prompt_for_llm += f"--- FRAGE DES BENUTZERS ---\n{user_prompt}\n\n--- ANTWORT ---"

    # Wir rufen das LLM mit einem leeren Chat-Verlauf auf, da alles im Prompt steht
    response = await call_llm(provider, model, final_prompt_for_llm, api_key, chat_history=[])
    
    # Die Auswertung der LLM-Antwort bleibt gleich (für den Tool-Fall)
    if response.get("type") == "tool_code":
        return response
    
    return {
        "type": "text", 
        "text": response.get("text"), 
        "image_url": response.get("image_url"), 
        "usage": response.get("usage"), 
        "cost": response.get("cost")
    }