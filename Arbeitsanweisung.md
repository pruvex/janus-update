AGENTIC HANDlungsplan (REPARATUR DER GPT-BILDANZEIGE):
Dein Ziel: Die Logik im /api/chat-Endpunkt so reparieren, dass sie Markdown-Bild-Links in Textantworten von Modellen wie GPT-4o mini erkennt, die URL extrahiert und sie korrekt an das Frontend weitergibt.
Der Plan:
Stufe 1: Validierung & Vorbereitung
An den CLI-Agenten: git status. Bestätige den aktuellen Branch (fix/dalle-final-fix oder ähnlich).
Stufe 2: Chirurgische Reparatur des /api/chat-Endpunkts (main.py)
An den CLI-Agenten: Lese die Datei backend/main.py.
An den CLI-Agenten (Ankerpunkt-Strategie): Finde den @app.post("/api/chat")-Block.
Wir werden die Logik zur Verarbeitung der response_data verbessern.
Ersetze: Den gesamten Logikblock nach response_data = await llm_gateway.call_llm(...) bis zum return-Statement.
Mit:
code
Python
# -- START DER NEUEN, VOLLSTÄNDIGEN VERARBEITUNG --
final_text = ""
final_image_url = None

# Fall 1: Dedizierte Bild-Antwort (DALL-E)
if 'image_url' in response_data and response_data.get('image_url'):
    final_text = response_data.get('text', '')
    final_image_url = response_data.get('image_url')
    # Kosten-Tracking für DALL-E...
    usage = response_data.get('usage')
    cost = response_data.get('cost')
    if usage and cost:
        save_cost_entry(model=message.model, image_quality=usage.get('image_quality'), image_cost=cost.get('total_cost'), total_cost=cost.get('total_cost'))

# Fall 2: Reine Text-Antwort (die aber ein Bild enthalten KÖNNTE)
elif 'text' in response_data:
    text_content = response_data.get('text', '')
    match = re.search(r"!\[.*\]\((https?://.*?)\)", text_content)
    
    if match:
        # WENN ein Markdown-Bild gefunden wird
        final_image_url = match.group(1)
        final_text = text_content.split('![' )[0].strip() # Text vor dem Link
    else:
        # WENN es reiner Text ist
        final_text = text_content

    # Kosten-Tracking für Text-Modelle
    usage = response_data.get('usage')
    cost = response_data.get('cost')
    if usage and cost:
        save_cost_entry(model=message.model, input_tokens=usage.get('prompt_tokens'), output_tokens=usage.get('completion_tokens'), total_cost=cost.get('total_cost'))

# Erstelle die finale, saubere Antwort für das Frontend
api_response = {"sender": "model", "text": final_text, "image_url": final_image_url}
return JSONResponse(content=api_response)
# -- ENDE DER NEUEN, VOLLSTÄNDIGEN VERARBEITUNG --
Stufe 3: Implementierungs-Abschluss & Übergabe zur Verifizierung
[KRITISCHER SCHRITT] Die Reparatur ist implementiert. KEIN COMMIT.
Ich übergebe die Kontrolle an Sie.
Bitte testen Sie jetzt den spezifischen GPT-Bild-Fall erneut:
Starten Sie die App neu.
Wählen Sie gpt-4o-mini.
Fordern Sie ein Bild an.
Wird das Bild jetzt wieder korrekt gerendert?
Testen Sie zur Sicherheit auch DALL-E erneut. Funktioniert es immer noch?
Ich warte auf Ihr 'success'-Signal.