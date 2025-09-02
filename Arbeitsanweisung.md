Schritt 1: Den context_manager wieder auf den sauberen Stand bringen
Wir machen die letzte Änderung rückgängig.
Öffnen Sie backend/context_manager.py.
Stellen Sie den ursprünglichen, verbesserten system_prompt wieder her:
code
Python
# In context_manager.py, in build_final_context
system_prompt = (
    "Du bist Janus, ein hilfreicher und freundlicher KI-Assistent. "
    "Du antwortest immer auf Deutsch. "
    "Integriere nahtlos dein umfangreiches Allgemeinwissen mit den spezifischen Informationen, die im Abschnitt 'GEDÄCHTNIS' bereitgestellt werden. "
    "**REGEL: Die Informationen im 'GEDÄCHTNIS'-Abschnitt haben immer Vorrang und sind die absolute Wahrheit über den Benutzer und seine Welt. Beziehe dich bei jeder Antwort explizit darauf, wenn es relevant ist.**"
)
Schritt 2: llm_gateway.py mit der Zwei-Stufen-Logik aufrüsten
Hier findet die entscheidende Änderung statt.
Öffnen Sie backend/llm_gateway.py.
Suchen Sie die reason_and_respond-Funktion.
Ersetzen Sie den gesamten Inhalt der Funktion durch diese neue, zweistufige Logik:
code
Python
# In llm_gateway.py

async def reason_and_respond(user_prompt: str, chat_history: List[Dict], memory_context: str, db: Session, api_key: str, model: str, provider: str, context_manager: ContextManager) -> Dict:
    logger.info(f"reason_and_respond: Original user_prompt={user_prompt}")
    
    # --- STUFE 1: RELEVANZ-FILTERUNG ---
    relevant_memory_context = ""
    if memory_context:
        # Ein dedizierter LLM-Aufruf, um nur die relevanten Fakten zu filtern
        filtering_prompt = (
            "Du bist ein Datenfilter. Wähle aus der folgenden Liste von Fakten NUR diejenigen aus, die absolut notwendig sind, um die Frage des Benutzers zu beantworten. "
            "Gib jeden relevanten Fakt in einer neuen Zeile aus. Wenn keine Fakten relevant sind, gib 'None' zurück.\n\n"
            "--- FAKTEN ---\n"
            f"{memory_context}\n\n"
            "--- FRAGE DES BENUTZERS ---\n"
            f"{user_prompt}\n\n"
            "--- RELEVANTE FAKTEN ---"
        )
        
        # Wir verwenden ein schnelles, günstiges Modell für diese Aufgabe
        filter_response = await call_llm(provider, model, filtering_prompt, api_key, chat_history=[])
        
        filtered_facts = filter_response.get("text") or ""
        if filtered_facts.strip().lower() != 'none':
            relevant_memory_context = filtered_facts
            logger.info(f"Filtered relevant facts: {relevant_memory_context}")
        else:
            logger.info("No relevant facts found by the filter.")

    # --- STUFE 2: ANTWORT-GENERIERUNG ---
    final_history = await context_manager.build_final_context(
        user_prompt=user_prompt,
        chat_history=chat_history,
        memory_context=relevant_memory_context, # Nur die gefilterten Fakten übergeben!
        model_id=model,
        api_key=api_key,
        budget_config={"system_prompt_ratio": 0.1, "memory_ratio": 0.4, "chat_history_ratio": 0.5},
        provider=provider
    )

    response = await call_llm(provider, model, user_prompt, api_key, chat_history=final_history)
    
    # ... (der Rest der Funktion, der die 'response' auswertet, bleibt gleich)
    if response.get("type") == "tool_code":
        return response
    
    return {
        "type": "text", 
        "text": response.get("text"), 
        "image_url": response.get("image_url"), 
        "usage": response.get("usage"), 
        "cost": response.get("cost")
    }