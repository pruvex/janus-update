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

### Block 1: API Key Management
*   **Inhalt:** Verantwortlich für das sichere Speichern, Abrufen und Validieren von API-Schlüsseln für verschiedene Dienste (LLMs, Bildgenerierung etc.).
*   **Zugehörige Dateien:** `backend/key_manager.py`
*   **Interagiert mit:** LLM Gateway, Chat-Operationen & Routing (indirekt), Kostenkontrolle (indirekt, falls Schlüssel für Kostenberechnung relevant sind).

### Block 2: Datenbank & Persistenz
*   **Inhalt:** Kapselt alle Datenbankoperationen (CRUD) und das Datenbankschema. Stellt eine saubere Schnittstelle für andere Backend-Dienste bereit.
*   **Zugehörige Dateien:** `backend/database.py`, `backend/crud.py`, `backend/schemas.py`
*   **Interagiert mit:** Kontext-Management, Speicher & Wissensmanagement, Chat-Operationen & Routing (für Chat-Historie).

### Block 3: Kostenkontrolle
*   **Inhalt:** Berechnet und verfolgt die Kosten basierend auf der Nutzung von LLMs und anderen Diensten.
*   **Zugehörige Dateien:** `backend/cost_calculator.py`
*   **Interagiert mit:** LLM Gateway, Chat-Operationen & Routing (direkt oder indirekt über LLM Gateway).

### Block 4: LLM Gateway
*   **Inhalt:** Abstrahiert die Kommunikation mit verschiedenen Large Language Models (LLMs). Wählt den passenden LLM-Anbieter basierend auf Konfiguration oder Anfrage.
*   **Zugehörige Dateien:** `backend/llm_gateway.py`, `backend/model_catalog.json`, `backend/download_model.py`
*   **Interagiert mit:** API Key Management, Kostenkontrolle, Chat-Operationen & Routing, Kontext-Management (empfängt Kontext), Speicher & Wissensmanagement (für RAG), Bildgenerierung.
*   **Hinweis zur Bildgenerierung:** LLM-Toolaufrufe (z.B. `image.generate`) werden erkannt und an den dedizierten Bildgenerierungsdienst delegiert, sodass Kostenlogik und Speicherung vereinheitlicht sind.
*   **Refactoring-Details:**
    *   **`model_catalog.json`:** Aktualisiert, um `image_generation_model` für Textmodelle zu integrieren und `gemini-2.5-flash-image-preview` als primäres Bildgenerierungsmodell für Gemini-Textmodelle festzulegen. Modellnamen wurden auf '2.5' korrigiert.
    *   **`llm_gateway.py`:**
        *   Erkennung von Bildgenerierungs-Keywords im Benutzer-Prompt implementiert.
        *   `_call_gemini_image_generation_api` wird nun mit dem korrekten Prompt aufgerufen.
        *   Die Verwendung von `genai.Client()` wurde zugunsten von `genai.GenerativeModel` rückgängig gemacht, um Kompatibilitätsprobleme zu beheben.
        *   Sichergestellt, dass die Textantwort leer ist, wenn ein Bild generiert wird, um Frontend-Anzeigefehler zu vermeiden.
    *   **`backend/main.py`:** Angepasst, um die `image_url` von Gemini-Modellen korrekt zu verarbeiten und direkt an das Frontend weiterzuleiten, ohne unnötige Download-Versuche.
    *   **`backend/memory_extractor.py`:** Korrigiert, um den Benutzertext korrekt an das LLM für die Faktenextraktion zu übergeben, wodurch die vorherige Fehlinterpretation des Prompts behoben wurde.
    *   **`frontend/js/chat.js`:** Aktualisiert, um Bilder korrekt anzuzeigen und leere Textknoten zu vermeiden, die bei der Bildgenerierung entstanden sind.

### Block 5: Kontext-Management (Erledigt) (Erledigt) (Erledigt) (Erledigt) (Erledigt)
*   **Inhalt:** Verwaltet den Gesprächskontext für laufende Chats. Dies beinhaltet das Speichern und Abrufen von Nachrichtenhistorien und die Vorbereitung des Kontexts für LLM-Anfragen. Beinhaltet auch die Logik für "Cross-Chat Context" (Kontext, der über einzelne Chats hinausgeht).
*   **Zugehörige Dateien:** `backend/context_manager.py`
*   **Interagiert mit:** Datenbank & Persistenz, LLM Gateway, Chat-Operationen & Routing.
*   **Refactoring-Details:**
    *   **`backend/context_manager.py`:** Die `_summarize_chat_segment` Funktion wurde angepasst, um den vom Benutzer ausgewählten Provider und das Modell für die Zusammenfassung zu verwenden, anstatt hartkodiert OpenAI zu nutzen.
    *   **`backend/memory_extractor.py`:** Die `extract_and_save_fact` Funktion wurde erweitert, um auch für erfolgreich generierte Bilder einen Speichereintrag zu erstellen. Dabei wird der ursprüngliche Benutzer-Prompt als Grundlage für den Fakt verwendet, auch wenn keine Textantwort vom LLM vorliegt.

### Block 6: Speicher & Wissensmanagement (Erledigt) (Erledigt) (Erledigt) (Erledigt)
*   **Inhalt:** Implementiert Langzeitgedächtnis-Funktionen, einschließlich Textzusammenfassung, Vektorisierung und semantischer Suche.
*   **Zugehörige Dateien:** `backend/memory_extractor.py`, `backend/vector_service.py`, `backend/chat_summarizer.py`
*   **Interagiert mit:** Datenbank & Persistenz, LLM Gateway (für RAG-Anfragen), Kontext-Management (für die Integration von Gedächtnisinhalten in den Kontext).

### Block 7: Bildgenerierung (Service)
*   **Inhalt:** Einheitlicher Dienst zur Bildgenerierung mit zwei Pfaden: (A) Delegation von LLM-Toolaufrufen und (B) direkte Nutzung von Bildmodellen (z.B. DALL·E 3, Gemini Imagen). Beinhaltet Endpunkte, Schemas, Kostenkalkulation und Speicherung.
*   **Zugehörige Dateien:** Endpunkte in `backend/main.py`; Service-Logik (z.B. `backend/image_service.py`), Schemas in `backend/schemas.py`, Kosten in `backend/cost_calculator.py`, Storage unter `backend/static/images/`.
*   **Interagiert mit:** LLM Gateway (Delegation von Toolcalls), Kostenkontrolle, Datenbank & Persistenz, Frontend.

### Block 8: Chat-Operationen & Routing (Der "Switch") - Goldstandard-Implementierung (Erledigt)
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
1.  **Tool-Definitionen (Pydantic-Modelle):**
    *   Erstellung von Pydantic-Modellen für alle Tools (z.B. `ImageGenerationTool`, `MemoryRetrievalTool`, `CrossChatMemoryTool`).
    *   Diese Modelle werden `name`, `description` und `parameters` (unter Verwendung von Pydantic für das Schema) enthalten.
    *   **Aktion:** Neue Pydantic-Modelle in `backend/schemas.py` definieren. (Erledigt) (Erledigt)
2.  **Tool-Register (`backend/tool_registry.py`):**
    *   Formalisierung eines Tool-Registers, das Tool-Namen ihren Python-Funktionen und Pydantic-Schemata zuordnet.
    *   Dieses Register wird die Metadaten der Tools (Beschreibung, Parameter) für das LLM bereitstellen und die Mapping-Logik für die Ausführung enthalten.
    *   **Aktion:** Neue Datei `backend/tool_registry.py` erstellen und die Tool-Definitionen dort zentralisieren. (Erledigt) (Erledigt)
3.  **LLM-Tool-Calling-Integration (`backend/llm_gateway.py`):**
    *   Modifizierung von `llm_gateway.py`, um dem LLM die verfügbaren Tool-Definitionen (aus dem neuen Tool-Register) bei einem Chat-Completion-Aufruf zu präsentieren.
    *   Verarbeitung der LLM-Antwort, um festzustellen, ob ein Tool-Aufruf vorgeschlagen wurde.
    *   **Aktion:** `_call_gemini_api` und `_call_openai_api` anpassen, um Tool-Definitionen zu übergeben und Tool-Aufrufe zu verarbeiten. (Erledigt) (Erledigt)
4.  **Dynamischer Tool-Dispatcher (`backend/llm_gateway.py` oder neue Utility):**
    *   Erstellung einer Funktion (z.B. `execute_tool_call`), die den Tool-Namen und die Argumente aus der LLM-Antwort entgegennimmt.
    *   Dynamisches Nachschlagen der entsprechenden Python-Funktion im Tool-Register.
    *   Validierung der Argumente gegen das Pydantic-Schema des Tools.
    *   Ausführung der Tool-Funktion.
    *   Behandlung von Tool-spezifischen Fehlern und Rückgabe strukturierter Ergebnisse.
    *   **Aktion:** Implementierung der Dispatch-Logik, vorzugsweise in `llm_gateway.py` oder einer neuen, dedizierten Utility-Datei. (Erledigt)
5.  **Refaktorierung von `main.py` (`/api/chat`-Endpunkt):**
    *   Entfernung der heuristischen Keyword-Prüfungen für die Bilderzeugung und das Cross-Chat-Memory.
    *   Integration der LLM-Tool-Calling- und dynamischen Dispatch-Logik.
    *   Die Funktion `reason_and_respond` in `llm_gateway.py` wird der primäre Orchestrator für diese Logik sein.
    *   **Aktion:** Anpassung des `/api/chat`-Endpunkts, um die neue Tool-Routing-Logik zu nutzen. (Erledigt)
6.  **Verbesserung der Fehlerbehandlung:**
    *   Implementierung von Wiederholungen (Retries) mit exponentiellem Backoff für externe API-Aufrufe (z.B. DALL-E, Gemini-Bilderzeugung).
    *   Verbesserung der benutzerseitigen Fehlermeldungen für Tool-Fehler.
    *   **Aktion:** Implementierung von `backoff` oder ähnlichen Bibliotheken für externe Aufrufe; Anpassung der Fehlerantworten. (Erledigt)
7.  **Initialisierung von `vector_service.model`:**
    *   Sicherstellung, dass das `vector_service.model` zuverlässig initialisiert und zugänglich ist, wo es benötigt wird (z.B. in `memory_extractor.py`). Dies könnte eine explizite Initialisierung beim Start oder eine Dependency Injection erfordern.
    *   **Aktion:** Überprüfung und Anpassung der Initialisierungslogik für `vector_service.model`. (Erledigt)
8.  **Umfassendes Testen:**
    *   Schreiben von Unit-Tests für die neuen Tool-Definitionen, das Tool-Register und den dynamischen Dispatcher.
    *   Aktualisierung bestehender Integrationstests (z.B. `test_llm_gateway.py`, `test_main_api.py`), um die neue Routing-Logik widerzuspiegeln.
    *   Hinzufügen spezifischer Tests für Fehlerbehandlung, Wiederholungen und Fallbacks.
    *   **Aktion:** Erstellung neuer Testdateien und Aktualisierung bestehender Tests. (Erledigt - `test_llm_gateway.py` ist grün, `test_main_api.py` hat noch Fehler, die mit In-Memory-DB behoben werden sollen)

#### Definition of Done (Block 8 - Goldstandard)
*   LLM-basierte Intent-Klassifizierung und Tool-Calling sind vollständig implementiert und ersetzen heuristische Keyword-Prüfungen.
*   Alle Tools sind mit Pydantic-Modellen definiert und in einem zentralen Register verwaltet.
*   Ein dynamischer Tool-Dispatcher ist vorhanden, der Tool-Aufrufe sicher und robust ausführt.
*   Die Fehlerbehandlung für Tool-Aufrufe ist umfassend, inklusive Retries und informativer Fehlermeldungen.
*   Die Initialisierung von `vector_service.model` ist robust und fehlerfrei.
*   Umfassende Unit- und Integrationstests für die neue Routing-Logik sind vorhanden und grün.
*   Die Frontend- und Backend-Schnittstellen sind stabil und dokumentiert.

### Block 9: Frontend-Interaktion
*   **Inhalt:** Die gesamte Benutzeroberfläche, die Benutzerinteraktionen verarbeitet, Eingaben sendet und Antworten anzeigt.
*   **Zugehörige Dateien:** `frontend/js/app.js`, `frontend/js/chat-manager.js`, `frontend/js/chat.js`, `frontend/js/settings.js`, `frontend/js/cost-visualizer.js`, `frontend/index.html`, `frontend/preload.js`, `frontend/css/settings.css`, `frontend/src/styles.css`, `main.electron.js`
*   **Interagiert mit:** Chat-Operationen & Routing (Backend-API), Bildgenerierung.
*   **Hinweis zur Bildgenerierung:** Separates "Bilderstellung"-Modal mit Auswahl der Bildmodelle und Parameter (Qualität, Größe, Ratio, Stil, etc.) sowie Live-Preisansicht.

### Block 10: System-Validierung (Health Check)
*   **Inhalt:** Ein eigenständiger Dienst zur Überprüfung der Systemgesundheit und der Verfügbarkeit kritischer Komponenten.
*   **Zugehörige Dateien:** `health_check.py`
*   **Interagiert mit:** Keine direkten Abhängigkeiten zu anderen Blöcken im Betrieb, dient der externen Überprüfung.

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