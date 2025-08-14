# FEATURE_KOSTENKONTROLLE.md - Implementierung der Kostenkontrolle

## Gesamtstrategie:
Das Ziel ist es, eine umfassende Kostenverfolgung und -visualisierung zu implementieren, ohne die derzeit stabile Kernfunktionalität zu beeinträchtigen. Dies wird durch die Erweiterung bestehender Komponenten und das Hinzufügen neuer Komponenten erreicht.

## 1. Backend-Erweiterungen:

*   **1.1. Kostenberechnung und Datenextraktion (llm_gateway.py):**
    *   **Aktueller Zustand:** `_call_dalle_api` und `_call_openai_api` (für Bildgenerierung) geben bereits `usage`- und `cost`-Daten zurück. `_call_gemini_api` tut dies derzeit **nicht**.
    *   **Vorgeschlagene Änderung:** `_call_gemini_api` muss angepasst werden, um `usage` (z.B. `input_tokens`, `output_tokens`) und `cost` (z.B. `total_cost`) aus der Gemini-API-Antwort zu extrahieren und zurückzugeben. Dies erfordert das Parsen des Preismodells und der Antwortstruktur der Gemini-API. Falls die Gemini-API keine direkten Token-Zahlen liefert, müssen diese basierend auf der Prompt-/Antwortlänge geschätzt werden.
    *   **Nicht-destruktiver Aspekt:** Dies erweitert den Rückgabewert von `_call_gemini_api`, ohne dessen Kernfunktionalität zu ändern.

*   **1.2. Kostenspeicherung (main.py & database.py):**
    *   **Aktueller Zustand:** Der `chat`-Endpunkt von `main.py` ruft bereits `save_cost_entry` mit `usage`- und `cost`-Daten aus der `llm_gateway`-Antwort auf. `database.py` enthält `save_cost_entry` und `get_costs_for_month`.
    *   **Vorgeschlagene Änderung:** Für den grundlegenden Speichermechanismus sind hier keine Änderungen erforderlich, da dieser bereits implementiert ist und funktioniert. Dies ist ein starker Punkt für die Nicht-Beeinträchtigung.
    *   **Erweiterung (optional, für die Zukunft):** Bei Bedarf kann eine detailliertere Kostenaufschlüsselung in `database.py` hinzugefügt werden (z.B. Kosten pro Modell, tägliche Kostenübersichten). Für den Moment ist das bestehende Schema ausreichend.

*   **1.3. API-Endpunkte zur Kostenabfrage (main.py):**
    *   **Aktueller Zustand:** Die Endpunkte `get_costs_dashboard` und `get_costs_details` fehlen derzeit in `main.py` (aufgrund des `git reset`).
    *   **Vorgeschlagene Änderung:** Diese API-Endpunkte müssen in `main.py` wieder hinzugefügt werden.
        *   `/api/costs/dashboard`: Gibt eine Zusammenfassung zurück (z.B. Kosten des aktuellen Monats, Budget). Dies fragt `database.py` mit `get_costs_for_month`.
        *   `/api/costs/details`: Gibt eine detaillierte Liste der Kosteneinträge zurück. Dies erfordert eine neue Funktion in `database.py` (z.B. `get_all_cost_entries` oder `get_cost_entries_by_date_range`).
    *   **Nicht-destruktiver Aspekt:** Dies sind neue Endpunkte, die die bestehende Funktionalität nicht beeinträchtigen.

*   **1.4. Modell-Kosten-Mapping (backend/model_catalog.json & main.py/llm_gateway.py):**
    *   **Aktueller Zustand:** `model_catalog.json` enthält bereits `cost_per_image`, `cost_per_token_input`, `cost_per_token_output`.
    *   **Vorgeschlagene Änderung:** Eine Hilfsfunktion (z.B. in `main.py` oder einem neuen Modul `cost_calculator.py`) implementieren, die `model_catalog.json` verwendet, um die `total_cost` basierend auf `input_tokens`, `output_tokens` oder `image_cost` vom LLM-Gateway zu berechnen. Diese Berechnung sollte *vor* dem Aufruf von `save_cost_entry` erfolgen.
    *   **Non-Destructive Aspect:** This centralizes cost calculation and makes it easily configurable via `model_catalog.json`.

## 2. Frontend-Erweiterungen:

*   **2.1. Kostenanzeige (frontend/js/cost-visualizer.js oder neues Modul):**
    *   **Aktueller Zustand:** `frontend/js/cost-visualizer.js` ist missing.
    *   **Vorgeschlagene Änderung:** Recreate `frontend/js/cost-visualizer.js` (oder ein neues Modul wie `cost_display.js`). This module will:
        *   Fetch data from `/api/costs/dashboard` and `/api/costs/details`.
        *   Display the current month's cost and budget.
        *   Display a detailed list of transactions (model, date, tokens/image, cost).
        *   Integrate this into the main UI (z.B. a sidebar, a dedicated tab, or a modal).
    *   **Nicht-destruktiver Aspekt:** Dies fügt neue UI-Elemente hinzu, ohne die bestehende Chat-Funktionalität zu ändern.

*   **2.2. UI-Integration:**
    *   **Vorgeschlagene Änderung:** `index.html` oder `main.js` anpassen, um das Kostenvisualisierungsmodul einzubinden und zu initialisieren. Dies könnte das Hinzufügen eines neuen Buttons oder Abschnitts beinhalten, um die Anzeige der Kostendaten auszulösen.
    *   **Nicht-destruktiver Aspekt:** Minimale Änderungen an der bestehenden UI-Struktur.

## 3. Teststrategie (entscheidend für nicht-destruktive Implementierung):

*   **Unit-Tests:** Unit-Tests für neue Funktionen (z.B. Kostenberechnungs-Helfer, neue Datenbankfunktionen) schreiben.
*   **Integrationstests:** Die neuen API-Endpunkte (`/api/costs/dashboard`, `/api/costs/details`) testen.
*   **End-to-End-Tests:** Überprüfen, ob die Kostendaten nach Chat-Interaktionen korrekt in der UI angezeigt werden.
*   **Regressionstests:** Sicherstellen, dass die bestehende Chat-Funktionalität (Text, DALL-E, Schlüsselverwaltung) unbeeinträchtigt bleibt.

## 4. Phasenweise Einführung (optional, für größere Projekte):
*   Kostenverfolgung in Phasen implementieren (z.B. zuerst Backend-Berechnung und -Speicherung, dann grundlegende Anzeige, dann detaillierte Visualisierung).
