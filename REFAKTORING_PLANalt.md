# Refactoring-Plan für das Janus-Projekt

## 1. Audit-Zusammenfassung

Das Janus-Projekt ist eine Full-Stack-Anwendung mit einem Python-Backend (FastAPI) und einem JavaScript-Frontend (Electron/Vite). Es integriert verschiedene KI-Funktionalitäten wie LLM-Interaktion, Kontext- und Speicherverwaltung, Kostenkontrolle und Bildgenerierung. Die aktuelle Struktur ist funktional, aber aufgrund des Wachstums ist ein Refactoring notwendig, um die Modularität, Testbarkeit und Wartbarkeit zu verbessern.

**Gefundene Schlüsselkomponenten:**
*   **Backend (Python):**
    *   `main.py`: Haupt-API-Endpunkte.
    *   `llm_gateway.py`: Abstraktion für verschiedene LLM-Anbieter.
    *   `context_manager.py`: Verwaltung des Gesprächskontexts.
    *   `memory_extractor.py`, `vector_service.py`, `chat_summarizer.py`: Komponenten für Langzeitgedächtnis und Wissensmanagement.
    *   `key_manager.py`: Verwaltung von API-Schlüsseln.
    *   `database.py`, `crud.py`, `schemas.py`: Datenbank-Interaktion (SQLite).
    *   `cost_calculator.py`: Berechnung und Verfolgung von Kosten.
    *   `download_model.py`: Modell-Download-Logik.
    *   `health_check.py`: System-Gesundheitsprüfung.
*   **Frontend (JavaScript):**
    *   `app.js`, `chat-manager.js`, `chat.js`, `settings.js`, `cost-visualizer.js`: Hauptlogik für UI, Chat-Interaktion und Einstellungen.
    *   `main.electron.js`: Electron-Hauptprozess.
*   **Tests:** Vorhandene Tests in `backend/` und `waechter/`.

## 2. Identifizierte Thematische Blöcke und Interaktionen

Die Refaktorierung wird in thematische Blöcke unterteilt, um eine klare Trennung der Verantwortlichkeiten zu schaffen und die Entwicklung schrittweise voranzutreiben.

### Block 1: API Key Management (Audit: Code implementiert, Tests & Doku ausstehend)
*   **Inhalt:** Verantwortlich für das sichere Speichern, Abrufen und Validieren von API-Schlüsseln für verschiedene Dienste (LLMs, Bildgenerierung etc.).
*   **Zugehörige Dateien:** `backend/key_manager.py`
*   **Interagiert mit:** LLM Gateway, Chat-Operationen & Routing (indirekt), Kostenkontrolle (indirekt, falls Schlüssel für Kostenberechnung relevant sind).
*   **Audit-Status:**
    *   `pydantic-settings` in `requirements.in`: ✅
    *   `Settings`-Klasse in `key_manager.py`: ✅
    *   `get_api_key` angepasst: ✅
    *   `config.json`-Abhängigkeit entfernt: ✅
    *   `.env` in `.gitignore`: ✅
    *   Dokumentation aktualisieren: ❌
    *   Unit-Tests schreiben: ❌

### Block 2: Datenbank & Persistenz (Audit: Code implementiert, Tests ausstehend)
*   **Inhalt:** Kapselt alle Datenbankoperationen (CRUD) und das Datenbankschema. Stellt eine saubere Schnittstelle für andere Backend-Dienste bereit.
*   **Zugehörige Dateien:** `backend/database.py`, `backend/crud.py`, `backend/schemas.py`
*   **Interagiert mit:** Kontext-Management, Speicher & Wissensmanagement, Chat-Operationen & Routing (für Chat-Historie).
*   **Audit-Status:**
    *   `crud.py` refaktorisieren (Bild- und Memory-Funktionen verschoben): ✅
    *   Importe aktualisiert: ✅
    *   Unit-Tests schreiben: ❌

### Block 3: Kostenkontrolle (Audit: Code implementiert)
*   **Inhalt:** Berechnet und verfolgt die Kosten basierend auf der Nutzung von LLMs und anderen Diensten.
*   **Zugehörige Dateien:** `backend/cost_calculator.py`
*   **Interagiert mit:** LLM Gateway, Chat-Operationen & Routing (direkt oder indirekt über LLM Gateway).
*   **Audit-Status:**
    *   `cost_calculator.py` refaktorisieren (reine Berechnungsfunktion): ✅
    *   `llm_gateway.py` angepasst (`_calculate_and_log_cost`): ✅
    *   Unit-Tests aktualisiert (`test_cost_calculator.py` auf pytest): ✅

### Block 4: LLM Gateway (Audit: Code implementiert)
*   **Inhalt:** Abstrahiert die Kommunikation mit verschiedenen Large Language Models (LLMs). Wählt den passenden LLM-Anbieter basierend auf Konfiguration oder Anfrage.
*   **Zugehörige Dateien:** `backend/llm_gateway.py`, `backend/model_catalog.json`, `backend/download_model.py`
*   **Interagiert mit:** API Key Management, Kostenkontrolle, Chat-Operationen & Routing, Kontext-Management (empfängt Kontext), Speicher & Wissensmanagement (für RAG), Bildgenerierung.
*   **Hinweis zur Bildgenerierung:** LLM-Toolaufrufe (z.B. `image.generate`) werden erkannt und an den dedizierten Bildgenerierungsdienst delegiert, sodass Kostenlogik und Speicherung vereinheitlicht sind.
*   **Refactoring-Details:**
    *   `model_catalog.json` aktualisiert: ✅
    *   `llm_gateway.py` (Bildgenerierungs-Keywords, `_call_gemini_image_generation_api`, `genai.GenerativeModel`, leere Textantwort bei Bildgenerierung): ✅
    *   `backend/main.py` (Verarbeitung `image_url` von Gemini): ✅
    *   `backend/memory_extractor.py` (Benutzertext korrekt an LLM für Faktenextraktion): ✅

### Block 5: Kontext-Management (Erledigt) (Erledigt) (Erledigt) (Erledigt) (Erledigt) (Audit: Code implementiert)
*   **Inhalt:** Verwaltet den Gesprächskontext für laufende Chats. Dies beinhaltet das Speichern und Abrufen von Nachrichtenhistorien und die Vorbereitung des Kontexts für LLM-Anfragen. Beinhaltet auch die Logik für "Cross-Chat Context" (Kontext, der über einzelne Chats hinausgeht).
*   **Zugehörige Dateien:** `backend/context_manager.py`
*   **Interagiert mit:** Datenbank & Persistenz, LLM Gateway, Chat-Operationen & Routing.
*   **Refactoring-Details:**
    *   `backend/context_manager.py` (`_summarize_chat_segment` angepasst): ✅
    *   `backend/memory_extractor.py` (`extract_and_save_fact` erweitert für Bilder): ✅

### Block 6: Speicher & Wissensmanagement (Erledigt) (Erledigt) (Erledigt) (Erledigt) (Audit: Code implementiert)
*   **Inhalt:** Implementiert Langzeitgedächtnis-Funktionen, einschließlich Textzusammenfassung, Vektorisierung und semantischer Suche.
*   **Zugehörige Dateien:** `backend/memory_extractor.py`, `backend/vector_service.py`, `backend/chat_summarizer.py`
*   **Interagiert mit:** Datenbank & Persistenz, LLM Gateway (für RAG-Anfragen), Kontext-Management (für die Integration von Gedächtnisinhalten in den Kontext).
*   **Audit-Status:** Komponenten sind vorhanden und scheinen funktional.

### Block 7: Bildgenerierung (Service) (Audit: Code implementiert)
*   **Inhalt:** Einheitlicher Dienst zur Bildgenerierung mit zwei Pfaden: (A) Delegation von LLM-Toolaufrufen und (B) direkte Nutzung von Bildmodellen (z.B. DALL·E 3, Gemini Imagen). Beinhaltet Endpunkte, Schemas, Kostenkalkulation und Speicherung.
*   **Zugehörige Dateien:** Endpunkte in `backend/main.py`; Service-Logik (`backend/image_manager.py`), Schemas in `backend/schemas.py`, Kosten in `backend/cost_calculator.py`, Storage unter `backend/static/images/`.
*   **Interagiert mit:** LLM Gateway (Delegation von Toolcalls), Kostenkontrolle, Datenbank & Persistenz, Frontend.
*   **Audit-Status:**
    *   Endpoints in `backend/main.py` (image generation logic): ✅
    *   Service-Logik (`backend/image_manager.py`): ✅
    *   Schemas in `backend/schemas.py` (`GenerateImageToolArgs`): ✅
    *   Costs in `backend/cost_calculator.py` (image cost calculation): ✅
    *   Storage under `backend/static/images/`: ✅

### Block 8: Chat-Operationen & Routing (Der "Switch") - Goldstandard-Implementierung (Audit: Abgeschlossen)
*   **Inhalt:** Die zentrale Logik, die eingehende Benutzeranfragen verarbeitet. Sie identifiziert die Art der Anfrage (reiner Chat, Tool-Aufruf, Dateiop, Bilderstellung, Memory-Operation etc.) und leitet sie an den entsprechenden Backend-Dienst weiter. Dies ist der "Switch"-Mechanismus.
*   **Zugehörige Dateien:** `backend/main.py` (primär), `backend/llm_gateway.py`, `backend/tool_registry.py` (neu), `backend/schemas.py` (Erweiterung), `frontend/js/app.js`, `frontend/js/chat-manager.js` (Frontend-Teil der Interaktion).
*   **Interagiert mit:** Allen anderen Backend-Blöcken (API Key Management, LLM Gateway, Kontext-Management, Speicher & Wissensmanagement, Kostenkontrolle, Datenbank & Persistenz, Bildgenerierung).
*   **Hinweis zur Bildgenerierung:** Routing trennt explizit zwischen LLM-Tool-basierten Bildanforderungen (→ Bildgenerierungsdienst) und direkten Bildmodell-Requests (→ Bildgenerierungsendpunkte).

#### Ziel
Implementierung eines robusten, LLM-gesteuerten "Intelligenten Switches" für das Routing von Benutzeranfragen an die entsprechenden Backend-Dienste (LLM-Chat, Tool-Aufrufe, Memory-Operationen, Bilderzeugung usw.) basierend auf der Intent-Klassifizierung, weg von heuristischem Keyword-Matching.

#### Schlüsselprinzipien
*   **LLM-basierte Intent-Klassifizierung/Tool-Calling:** Nutzung der Fähigkeit des LLM, Benutzerabsichten zu identifizieren und Tool-Aufrufe vorzuschlagen.
*   **Strukturierte Tool-Definitionen:** Definition aller aufrufbaren Tools mit klaren Beschreibungen und Pydantic-Schemata.
*   **Zentraler Dispatcher:** Erstellung einer dedizierten Komponente für dynamisches Tool-Dispatching.
*   **Robuste Fehlerbehandlung:** Implementierung umfassender Fehlerbehandlung, Wiederholungen und Fallbacks.
*   **Skalierbarkeit & Modularität:** Sicherstellung, dass das Design skalierbar und modular für zukünftige Tool-Erweiterungen ist.

#### Schritte zur Umsetzung des Goldstandards
1.  **Tool-Definitionen (Pydantic-Modelle):** ✅
    *   **Aktion:** Neue Pydantic-Modelle in `backend/schemas.py` definieren.
2.  **Tool-Register (`backend/tool_registry.py`):** ✅
    *   **Aktion:** Neue Datei `backend/tool_registry.py` erstellen und die Tool-Definitionen dort zentralisieren.
3.  **LLM-Tool-Calling-Integration (`backend/llm_gateway.py`):** ✅
    *   **Aktion:** `_call_gemini_api` und `_call_openai_api` anpassen, um Tool-Definitionen zu übergeben und Tool-Aufrufe zu verarbeiten.
4.  **Dynamischer Tool-Dispatcher (`backend/llm_gateway.py` oder neue Utility):** ✅
    *   **Aktion:** Implementierung der Dispatch-Logik, vorzugsweise in `llm_gateway.py` oder einer neuen, dedizierten Utility-Datei.
5.  **Refaktorierung von `main.py` (`/api/chat`-Endpunkt):** ✅
    *   **Aktion:** Anpassung des `/api/chat`-Endpunkts, um die neue Tool-Routing-Logik zu nutzen.
6.  **Verbesserung der Fehlerbehandlung:** ❌
    *   **Aktion:** Implementierung von `backoff` oder ähnlichen Bibliotheken für externe Aufrufe; Anpassung der Fehlerantworten.
7.  **Initialisierung von `vector_service.model`:** ✅
    *   **Aktion:** Überprüfung und Anpassung der Initialisierungslogik für `vector_service.model`.
8.  **Umfassendes Testen:** ❌ (Partiell)
    *   **Aktion:** Erstellung neuer Testdateien und Aktualisierung bestehender Tests.
    *   **Audit-Details:** `test_llm_gateway.py` fehlt. `waechter/test_main_api.py` ist vorhanden, aber die Tests müssen umfassender sein, um die neue Routing-Logik vollständig abzudecken.

#### Definition of Done (Block 8 - Goldstandard)
*   LLM-basierte Intent-Klassifizierung und Tool-Calling sind vollständig implementiert und ersetzen heuristische Keyword-Prüfungen. ✅
*   Alle Tools sind mit Pydantic-Modellen definiert und in einem zentralen Register verwaltet. ✅
*   Ein dynamischer Tool-Dispatcher ist vorhanden, der Tool-Aufrufe sicher und robust ausführt. ✅
*   Die Fehlerbehandlung für Tool-Aufrufe ist umfassend, inklusive Retries und informativer Fehlermeldungen. ❌
*   Die Initialisierung von `vector_service.model` ist robust und fehlerfrei. ✅
*   Umfassende Unit- und Integrationstests für die neue Routing-Logik sind vorhanden und grün. ❌
*   Die Frontend- und Backend-Schnittstellen sind stabil und dokumentiert. (Manuelle Prüfung erforderlich)

### Block 9: Frontend-Interaktion (Audit: Code implementiert, UI-Audit ausstehend)
*   **Inhalt:** Die gesamte Benutzeroberfläche, die Benutzerinteraktionen verarbeitet, Eingaben sendet und Antworten anzeigt.
*   **Zugehörige Dateien:** `frontend/js/app.js`, `frontend/js/chat-manager.js`, `frontend/js/chat.js`, `frontend/js/settings.js`, `frontend/js/cost-visualizer.js`, `frontend/index.html`, `frontend/preload.js`, `frontend/css/settings.css`, `frontend/src/styles.css`, `main.electron.js`
*   **Interagiert mit:** Chat-Operationen & Routing (Backend-API), Bildgenerierung.
*   **Hinweis zur Bildgenerierung:** Separates "Bilderstellung"-Modal mit Auswahl der Bildmodelle und Parameter (Qualität, Größe, Ratio, Stil, etc.) sowie Live-Preisansicht.
*   **Audit-Status:**
    *   `frontend/js/chat.js` (Bildanzeige und leere Textknoten): ✅
    *   Gesamte UI: ❌ (Manuelle Prüfung erforderlich)

### Block 10: System-Validierung (Health Check) (Audit: Implementiert)
*   **Inhalt:** Ein eigenständiger Dienst zur Überprüfung der Systemgesundheit und der Verfügbarkeit kritischer Komponenten.
*   **Zugehörige Dateien:** `health_check.py`
*   **Interagiert mit:** Keine direkten Abhängigkeiten zu anderen Blöcken im Betrieb, dient der externen Überprüfung.
*   **Audit-Status:** ✅

## 3. Priorisierung der Refaktorierung

Die Blöcke werden in der folgenden Reihenfolge refaktorisiert, um Abhängigkeiten zu minimieren und eine stabile Basis zu schaffen:

1.  **API Key Management:**
    *   **Ziel:** Sichere und flexible Verwaltung von API-Schlüsseln über Umgebungsvariablen oder `.env`-Dateien.
    *   **Schritte:**
        1.  **Abhängigkeit hinzufügen:** `pydantic-settings` zur `backend/requirements.in` hinzufügen und installieren.
        2.  **`Settings`-Klasse erstellen:** Eine `Settings`-Klasse in `backend/key_manager.py` (oder einer neuen `config.py`) unter Verwendung von `pydantic_settings.BaseSettings` und `pydantic.SecretStr` definieren.
        3.  **`get_api_key` anpassen:** Die Funktion `get_api_key` so ändern, dass sie die Schlüssel aus der neuen `Settings`-Instanz abruft.
        4.  **`config.json`-Abhängigkeit entfernen:** Sicherstellen, dass `backend/key_manager.py` nicht mehr auf `config.json` zugreift.
        5.  **`.env` in `.gitignore`:** Überprüfen, ob `.env` in der `.gitignore`-Datei des Projekts aufgeführt ist.
        6.  **Dokumentation aktualisieren:** Anweisungen zur Bereitstellung von API-Schlüsseln über Umgebungsvariablen oder `.env`-Dateien hinzufügen.
        7.  **Unit-Tests schreiben:** Tests für die `Settings`-Klasse und die `get_api_key`-Funktion erstellen, um die korrekte und sichere Schlüsselverwaltung zu gewährleisten.

2.  **Datenbank & Persistenz:**
    *   **Ziel:** Klare Trennung der Zuständigkeiten innerhalb der Datenbank- und CRUD-Operationen, um Modularität und Wartbarkeit zu verbessern.
    *   **Schritte:**
        1.  **`crud.py` refaktorisieren:**
            *   Bildverarbeitungsfunktionen (`save_image_from_url`, `migrate_image_paths`) in eine neue Datei `backend/image_manager.py` verschieben.
            *   Speicherbezogene CRUD-Funktionen (`save_memory_snippet`, `find_similar_memory_snippet`, `get_all_memories`, `update_memory_snippet`, `save_raw_memory`) in eine neue Datei `backend/memory_manager.py` verschieben. Dies beinhaltet auch das Verschieben des `vector_service`-Imports.
            *   Sicherstellen, dass `backend/crud.py` nur `Chat`- und `Message`-bezogene CRUD-Operationen enthält.
        2.  **Importe aktualisieren:** Importe in `backend/main.py` und anderen betroffenen Dateien an die neuen Speicherorte anpassen.
        3.  **Unit-Tests schreiben:** Umfassende Unit-Tests für die refaktorisierten `backend/crud.py`, `backend/image_manager.py` und `backend/memory_manager.py` erstellen, um die korrekte Funktionalität und Datenintegrität zu gewährleisten.

3.  **Kostenkontrolle:**
    *   **Ziel:** Eine weitgehend unabhängige Utility, die frühzeitig isoliert werden kann.
    *   **Schritte:**
        1.  **`cost_calculator.py` refaktorisieren:** Die Funktion `calculate_cost` wurde zu einer reinen Berechnungsfunktion ohne Logging-Seitenefekte umgestaltet.
        2.  **`llm_gateway.py` anpassen:** Eine neue private Hilfsfunktion `_calculate_and_log_cost` wurde in `llm_gateway.py` hinzugefügt, um die Kostenberechnung und das Logging zu zentralisieren.
        3.  **Unit-Tests aktualisieren:** Die Tests in `test_cost_calculator.py` wurden auf pytest umgestellt und an die neue Signatur von `calculate_cost` angepasst.

4.  **LLM Gateway:** Der Kern der KI-Interaktion, baut auf API Key Management auf.
5.  **Kontext-Management:** Baut auf Datenbank auf und ist für kohärente Gespräche unerlässlich.
6.  **Speicher & Wissensmanagement:** Baut auf Datenbank und Kontext auf.
7.  **Bildgenerierung (Service):** Vereinheitlicht Tool-basierte und direkte Bildgenerierung inkl. Kosten/Storage.
8.  **Chat-Operationen & Routing (Der "Switch"):** Integriert alle anderen Backend-Komponenten und ist der zentrale Einstiegspunkt für Benutzeranfragen.
9.  **Frontend-Interaktion:** Die UI-Schicht, die auf dem stabilen Backend aufbaut.
10. **System-Validierung (Health Check):** Kann jederzeit unabhängig getestet und verifiziert werden.

Jeder Block wird mit einem passenden Test versehen und sauber dokumentiert, bevor der nächste Block in Angriff genommen wird.

## 4. Jüngste Änderungen (Sitzung vom 02.09.2025)

- **Code-Audit und Korrekturen:**
  - **`backend/memory_manager.py`:** Die Import-Anweisungen wurden korrigiert, um `from . import database` zu verwenden und alle Vorkommen von `models.Memory` wurden auf `database.Memory` umgestellt, um die Konsistenz mit dem Rest des Backends herzustellen.
  - **`backend/main.py`:**
    - Der Parameter `top_k` im Aufruf von `vector_service.find_similar_snippets` wurde auf `10` erhöht, um die Relevanz der aus dem Gedächtnis abgerufenen Informationen zu verbessern.
    - Ein neuer API-Endpunkt `@app.get("/api/costs/summary-by-model")` wurde hinzugefügt, um eine Kostenübersicht nach Modell zu ermöglichen.
    - Die Dekoratoren für die Endpunkte zum Aktualisieren und Löschen von Chats wurden von `@router` auf `@app` korrigiert.
    - Der Aufruf der Funktion `get_costs_summary_by_model_for_current_month` wurde korrigiert, indem das unnötige `db`-Argument entfernt wurde.
costs_summary_by_model_for_current_month` wurde korrigiert, indem das unnötige `db`-Argument entfernt wurde.
