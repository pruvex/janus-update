AGENTIC HANDlungsplan: Implementierung des Gemini-Kosten-Trackings
Dein Ziel: Die _call_gemini_api-Funktion in backend/llm_gateway.py so erweitern, dass sie die Token-Nutzung (usage) und die daraus resultierenden Kosten (cost) aus der Gemini-API-Antwort extrahiert und zurückgibt.
Relevante FEATURE_X.md: FEATURE_KOSTENKONTROLLE.md
Der Plan:
Stufe 1: Validierung des Ausgangszustands
An den CLI-Agenten: git status. Bestätige, dass wir uns auf dem Branch dev/kosten-gemini-tracking-1 befinden.
Stufe 2: Implementierung der Kostenextraktion
An den CLI-Agenten: Lese die Datei backend/llm_gateway.py.
An den CLI-Agenten (Ankerpunkt-Strategie): Finde die Funktion async def _call_gemini_api(...).
Ersetze den gesamten Block dieser Funktion.
Mit dem folgenden, erweiterten Block:
code
Python
async def _call_gemini_api(api_key, prompt, model_name):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    
    try:
        response = await model.generate_content_async(prompt)
        
        # --- NEUE LOGIK ZUR KOSTENEXTRAKTION ---
        
        # Hole die Nutzungsdaten aus der Antwort
        usage_metadata = response.usage_metadata
        input_tokens = usage_metadata.prompt_token_count
        output_tokens = usage_metadata.candidates_token_count
        
        # Hole die Kosten pro Token aus unserem Katalog
        # (Dieser Schritt setzt voraus, dass eine Funktion zum Laden des Katalogs existiert)
        model_info = get_model_from_catalog(model_name) # Annahme: diese Hilfsfunktion existiert
        cost_per_input = model_info.get('cost_per_token_input', 0)
        cost_per_output = model_info.get('cost_per_token_output', 0)
        
        # Berechne die Gesamtkosten
        total_cost = (input_tokens / 1_000_000 * cost_per_input) + (output_tokens / 1_000_000 * cost_per_output)
        
        # Erstelle das Rückgabeobjekt
        return {
            "text": response.text,
            "usage": {
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
            },
            "cost": {
                "total_cost": round(total_cost, 6)
            }
        }
        # --- ENDE DER NEUEN LOGIK ---

    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        # Stelle sicher, dass auch im Fehlerfall ein konsistentes Format zurückgegeben wird
        return {"text": f"An error occurred with the Gemini API: {e}", "usage": None, "cost": None}
An den CLI-Agenten: Da die get_model_from_catalog-Funktion noch nicht existiert, füge sie am Anfang der Datei llm_gateway.py hinzu:
code
Python
import json
import os

def get_model_from_catalog(model_id):
    catalog_path = os.path.join(os.path.dirname(__file__), 'model_catalog.json')
    with open(catalog_path, 'r') as f:
        catalog = json.load(f)
    for model in catalog:
        if model['id'] == model_id:
            return model
    return {}
An den CLI-Agenten: Dokumentiere im AGENT_WORK_LOG.md: "Kosten- und Nutzungsdaten-Extraktion für Gemini in llm_gateway.py implementiert."
Stufe 3: Implementierungs-Abschluss & Übergabe zur Verifizierung
[KRITISCHER SCHRITT] Alle Änderungen sind implementiert. KEIN COMMIT.
Ich übergebe die Kontrolle an Sie.
Bitte testen Sie jetzt das Gemini-Modell:
Starten Sie die App (npm run start-dev).
Wählen Sie ein Gemini-Modell aus.
Führen Sie einen Chat durch.
Funktioniert der Chat noch?
Überprüfen Sie die Backend-Logs: Gibt es Fehler?
Prüfen Sie die Datenbank (optional, aber gut): Wird ein neuer Kosteneintrag für den Gemini-Chat in der costs.db-Datei erstellt?
Ich warte auf Ihr explizites 'success'-Signal.
Stufe 4 & 5: Abschluss (Nach 'success'-Signal)
(Nach 'success') Der Agent wird den Fortschritt committen (feat(backend): Implement cost and usage tracking for Gemini models) und einen neuen Branch dev/kosten-gemini-tracking-2 erstellen.