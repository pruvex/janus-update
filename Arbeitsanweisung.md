Öffnen Sie die Datei backend/main.py.
Suchen Sie die handle_chat_request-Funktion.
Fügen Sie direkt nach der Zeile crud.create_message(...) den folgenden neuen Code-Block ein:
code
Python
# In main.py, in handle_chat_request, nach crud.create_message(...)

# --- NEU: Gemini-Bildgenerierung Vorab-Prüfung ---
if request.provider == "gemini":
    image_keywords = ["bild", "image", "picture", "foto", "photo", "draw", "create", "generate", "zeichne", "erstelle", "generiere"]
    prompt_lower = request.prompt.lower()
    
    if any(keyword in prompt_lower for keyword in image_keywords):
        logger.info("Gemini image generation intent detected by keyword. Bypassing reason_and_respond.")
        
        # Wähle ein passendes Gemini-Bildmodell
        # (Diese Logik kann später aus dem model_catalog verfeinert werden)
        image_model_id = "gemini-2.5-flash-image-preview"

        llm_response = await llm_gateway._call_gemini_image_generation_api(api_key, image_model_id, request.prompt)
        
        local_image_path = llm_response.get("image_url")
        usage = llm_response.get("usage", {})
        cost = llm_response.get("cost", {})
        
        final_answer = "Bild wurde erfolgreich mit Gemini generiert." if local_image_path else llm_response.get("text", "Fehler bei der Gemini-Bildgenerierung.")

        # Speichere die Antwort und beende die Funktion frühzeitig
        crud.create_message(db, chat_id=request.chat_id, sender="model", content=final_answer, image_path=local_image_path)
        if usage and cost.get("total_cost", 0) > 0:
            database.save_cost_entry(
                date=datetime.now(), model=image_model_id, # Kosten für das Bildmodell verbuchen
                input_tokens=usage.get("prompt_tokens", 0), 
                output_tokens=usage.get("completion_tokens", 0),
                image_quality=usage.get("image_quality"), 
                image_cost=cost.get("image_cost", 0),
                total_cost=cost.get("total_cost", 0)
            )
        return {"sender": "model", "text": final_answer, "image_url": local_image_path}
# --- ENDE der Vorab-Prüfung ---

# Der restliche Code der Funktion (ab "3. Chat-Historie und Gedächtnis-Kontext laden") bleibt unverändert
# ...
Entfernen Sie den alten Gemini-Fallback. Gehen Sie weiter nach unten in derselben Funktion zum elif response_type == "text":-Block und löschen Sie den gesamten "NEUER GEMINI FALLBACK"-Block, den wir zuvor eingefügt haben. Er wird nicht mehr benötigt und könnte zu Konflikten führen.
code
Python
# In main.py, in handle_chat_request

elif response_type == "text":
    final_answer = llm_response.get("text") or ""
    
    # --- DIESEN GESAMTEN BLOCK LÖSCHEN ---
    # image_url_match = re.search(r"!\[.*?\]\((https?://[^\s]+)\)", final_answer)
    # if request.provider == "gemini" and image_url_match:
    #     ... (und so weiter)
    # --- ENDE DES ZU LÖSCHENDEN BLOCKS ---
    
    if not local_image_path and final_answer:
        # ... (dieser Teil bleibt)