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

### Block 8: Erweiterte Chat-Funktionalitäten und Speicherverwaltung
- [x]  **Implementierung der Chat-Historie:** Speicherung und Abruf vergangener Konversationen.
- [x]  **Kontext-Management:** Sicherstellung, dass der KI-Agent den Konversationskontext über mehrere Runden hinweg beibehält.
- [ ]  **Speicher-Optimierung:** Effiziente Verwaltung des Speichers, um Leistungseinbußen bei langen Konversationen zu vermeiden.
- [x]  **Bildgenerierung in Chats:** Integration der Bildgenerierungsfunktion direkt in den Chat-Workflow.
- [ ]  **Testen der erweiterten Chat-Funktionen:** Umfassende Tests für alle neuen Chat-Funktionalitäten.

#### Intelligente Entscheidungslogik (Überblick)
1. **Modell- und Fähigkeits-Ermittlung**
   - Aktuell ausgewähltes Modell aus dem Frontend-Status ermitteln (`frontend/js/chat-manager.js`).
   - Fähigkeiten/Tools des Modells aus einer Registry lesen (siehe „Capability-Registry“).
2. **Intent/Task-Erkennung**
   - Basierend auf User-Input (und optional NLU-Heuristiken) bestimmen: Chat-Antwort, Tool-Aufruf, Dateioperation, Bildgenerierung, Memory-Operation.
3. **Kontext-Entscheidung**
   - Prüfen, ob zusätzlicher Kontext benötigt wird (z.B. relevante Memory-Snippets via `backend/context_manager.py`/`backend/memory_extractor.py`).
   - Policy: Context beifügen, wenn Relevanzscore > Schwelle; ansonsten minimal halten.
4. **Tool-/Service-Routing**
   - Wenn Task durch ein Modell-Tool abbildbar ist und verfügbar: Toolcall via `backend/llm_gateway.py` ausführen.
   - Bildgenerierung: Toolcalls → Bildgenerierungsdienst (Block 7); direkte Bildmodelle → Bildendpunkte.
5. **Dateioperationen**
   - Datei-bezogene Intents (z.B. Datei anlegen, speichern) über dedizierte, abgesicherte Backend-Operationen (z.B. `backend/main.py` Endpunkte) ausführen.
6. **Pass-through Chat**
   - Falls keine Tools/Services passen: Anfrage als reinen Chat an das Textmodell weiterreichen.
7. **Kosten/Limit-Checks**
   - Vor Ausführung Kosten/Token-Budgets prüfen (`backend/cost_calculator.py`), ggfs. Warnung/Abbruch.
8. **Fallbacks & Retries**
   - Bei Provider-/Modellfehlern definierte Fallbacks (z.B. alternatives Modell derselben Providerfamilie) und begrenzte Retries.

#### Capability-Registry
* Quelle: `backend/model_catalog.json` + Adapter in `backend/llm_gateway.py`/Provider-spezifisch.
* Enthält: unterstützte Tools, Max-Kontext, Tokenlimits, unterstützte Medientypen, Bildfähigkeiten (falls vorhanden).
* Wird im Routing abgefragt, um festzustellen, ob das gewählte Modell die gewünschte Aufgabe direkt unterstützt.

#### Kontext- und Memory-Policy
* Entscheidungskriterien: Relevanzscore, Konversationslänge, Nutzerpräferenzen.
* Operationen: Memory-Snippets abrufen/hinzufügen/zusammenfassen (siehe `backend/chat_summarizer.py`, `backend/memory_extractor.py`).
* Governance: Max-Context-Size, PII-Filter, Redundanzvermeidung.

#### Dateioperationen
* Zulässige Operationen whitelisten (Create, Update, Append) und Pfade einschränken.
* Logging/Auditing aller Dateiaktionen (für Nachvollziehbarkeit).

#### Observability & Telemetrie
* Strukturierte Logs (Start/Ende, Entscheidungspfade, Fehler, Kosten) mit Korrelation-ID.
* Metriken: Erfolgsrate pro Intent, Tool-Usage, Latenzen, Kosten pro Anfrage.

#### Definition of Done (Block 8)
* Entscheidungsbaum implementiert und modular getestet (Unit-Tests + Integrationstests gegen `backend/llm_gateway.py`, Block 7 Service, Kontext-Manager).
* Capability-Registry eingebunden und im Routing durchgängig genutzt.
* Kosten-/Budget-Checks vor Ausführung integriert.
* Fallbacks/Retry-Strategien vorhanden, Telemetrie/Logs vollständig.
* Frontend- und Backend-Schnittstellen stabil dokumentiert.

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


