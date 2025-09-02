Schritt 1: Den context_manager umbauen
Wir entfernen den Memory-Teil aus dem System-Prompt.
Öffnen Sie backend/context_manager.py.
Passen Sie den system_prompt an. Machen Sie ihn wieder einfacher und allgemeiner.
code
Python
# In context_manager.py, in build_final_context
system_prompt = (
    "Du bist Janus, ein hilfreicher und freundlicher KI-Assistent. "
    "Du antwortest immer auf Deutsch."
)
Schritt 2: Die Injektion in llm_gateway.py durchführen
Hier passiert die eigentliche Magie. Wir modifizieren die reason_and_respond-Funktion so, dass sie den Gedächtnis-Kontext direkt vor den user_prompt setzt.
Öffnen Sie backend/llm_gateway.py.
Suchen Sie die reason_and_respond-Funktion.
Modifizieren Sie den Anfang der Funktion und den Aufruf von build_final_context.
code
Python
# In llm_gateway.py

async def reason_and_respond(user_prompt: str, chat_history: List[Dict], memory_context: str, db: Session, api_key: str, model: str, provider: str, context_manager: ContextManager) -> Dict:
    logger.info(f"reason_and_respond: Original user_prompt={user_prompt}")
    logger.info(f"reason_and_respond: Received memory_context={memory_context}")

    # --- HIER IST DIE NEUE LOGIK (DIREKTE INJEKTION) ---
    final_user_prompt = user_prompt
    if memory_context:
        # Wir bauen den Kontext direkt in den Prompt des Benutzers ein.
        # Das ist die stärkste Form des Prompt Engineering.
        injection_prompt = (
            "Verwende die folgenden Informationen aus deinem Gedächtnis, um die Frage zu beantworten. "
            "Diese Informationen sind Fakten und haben absolute Priorität:\n"
            "--- GEDÄCHTNIS ---\n"
            f"{memory_context}\n"
            "--- FRAGE ---\n"
            f"{user_prompt}"
        )
        final_user_prompt = injection_prompt
        logger.info(f"reason_and_respond: Injected memory into prompt. New prompt length: {len(final_user_prompt)}")

    # Der 'memory_context' wird jetzt leer übergeben, da er bereits im Prompt ist.
    final_history = await context_manager.build_final_context(
        user_prompt=final_user_prompt, # Wir übergeben den modifizierten Prompt
        chat_history=chat_history,
        memory_context="", # WICHTIG: Hier leer lassen!
        model_id=model,
        api_key=api_key,
        # Budget anpassen, da der Prompt jetzt länger ist
        budget_config={"system_prompt_ratio": 0.05, "memory_ratio": 0.0, "chat_history_ratio": 0.95},
        provider=provider
    )

    response = await call_llm(provider, model, final_user_prompt, api_key, chat_history=final_history)

    # ... (der Rest der Funktion bleibt gleich)