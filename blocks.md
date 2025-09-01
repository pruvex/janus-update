# Dokumentation der Refactoring-Blöcke

## Block 1: API Key Management

### Zweck
Dieser Block ist verantwortlich für das sichere und flexible Management von API-Schlüsseln, die von verschiedenen Diensten (z.B. Large Language Models) innerhalb der Anwendung benötigt werden. Ziel ist es, API-Schlüssel nicht direkt im Code oder in leicht zugänglichen Konfigurationsdateien zu speichern, sondern über Umgebungsvariablen oder `.env`-Dateien zu laden.

### Implementierung (Offen)

### Interaktionen
Dieser Block wird von anderen Blöcken, insbesondere dem `LLM Gateway` und `Chat-Operationen & Routing`, genutzt, um auf die benötigten API-Schlüssel zuzugreifen.

### Tests
Unit-Tests vorhanden in `backend/test_key_manager.py` (Laden aus Env/.env, unbekannte Provider, fehlende Variablen).

### Definition of Done
*   **Settings vorhanden:** Zentrale `Settings` mit `SecretStr` und `.env`-Support.
*   **Funktional:** `get_api_key()` nutzt `Settings` und unterstützt relevante Provider.
*   **Sicherheit:** `.env` ist in `.gitignore` enthalten.
*   **Tests grün:** Unit-Tests decken Kernpfade ab.

## Hinweis: Capability-Registry (Tools)
Kurzreferenz für Blöcke 4 und 8.

* **Quelle:** `backend/model_catalog.json` enthält pro Modell `tools[]` (name, version, input_schema, output_schema?, rate_limits, cost_key, security, notes).
* **API:** `backend/tool_registry.py` stellt bereit: `get_tools_for_model(model_id)`, `get_tool(model_id, tool_name)`.
* **Validierung:** Pydantic-Modelle in `backend/schemas.py` (ToolSpec usw.) und JSON-Schema-Checks für Inputs/Outputs.
* **Nutzung:**
  * Block 4 (`backend/llm_gateway.py`): Adapter führt Tools aus (`execute_tool(...)`).
  * Block 8 (Routing): Wählt passende Tools je Intent/Modell basierend auf der Registry.

## Block 2: Datenbank & Persistenz

### Zweck
Dieser Block kapselt alle Datenbankoperationen (CRUD) und das Datenbankschema. Er stellt eine saubere und einheitliche Schnittstelle für andere Backend-Dienste bereit, die Daten speichern oder abrufen müssen. Das Hauptziel dieses Refactorings ist die Verbesserung der Modularität und Wartbarkeit durch eine striktere Trennung der Zuständigkeiten innerhalb der Datenbank-bezogenen Logik.

### Implementierung (Erledigt)
Die bestehenden SQLAlchemy-Modelle und -Verbindungen werden genutzt, und die ehemals zentrale `crud.py` wurde aufgeteilt in spezialisierte Module.

*   **Verwendete Technologien:** Python, SQLAlchemy, SQLite, Pydantic.
*   **Schlüsselkomponenten:**
    *   `backend/database.py`: Definiert SQLAlchemy-Modelle und Datenbankverbindungen.
    *   `backend/schemas.py`: Definiert Pydantic-Modelle für Datenvalidierung und Serialisierung.
    *   `backend/crud.py` (refaktorisiert): Enthält CRUD-Operationen für Chats und Nachrichten (create/get/update/delete, Summaries, Archive-Toggle).
    *   `backend/image_manager.py`: Enthält Logik für Bildspeicherung/-migration (z.B. `save_image_from_url`, `migrate_image_paths`).
    *   `backend/memory_manager.py`: Enthält Logik für Gedächtnis-Snippets/Einbettungen (z.B. `save_memory_snippet`, `find_similar_memory_snippet`).

### Refactoring-Details (durchgeführt vor diesem Projektstart):
*   Die Aufteilung der `crud.py` in `backend/crud.py`, `backend/image_manager.py` und `backend/memory_manager.py` wurde bereits vor Beginn dieses Refactoring-Projekts vorgenommen.
*   Die entsprechenden Importe in `backend/main.py` und anderen betroffenen Dateien waren bereits aktualisiert.
*   Umfassende Unit-Tests für die refaktorisierten Module waren bereits vorhanden.

### Interaktionen
Dieser Block ist eine fundamentale Schicht, die von vielen anderen Backend-Blöcken genutzt wird, insbesondere vom Kontext-Management, Speicher & Wissensmanagement und Chat-Operationen & Routing, um Daten zu persistieren und abzurufen.

### Tests
Unit-Tests vorhanden für `backend/crud.py`, `backend/image_manager.py` und `backend/memory_manager.py` (siehe `backend/test_crud.py`, `backend/test_image_manager.py`, `backend/test_memory_manager.py`).

### Definition of Done
*   **Trennung:** Chat/Message-CRUD in `backend/crud.py`, Bilder in `backend/image_manager.py`, Memory in `backend/memory_manager.py`.
*   **Schnittstellen stabil:** Funktionen werden von aufrufenden Schichten verwendet (z.B. `create_message`, `save_image_from_url`, `save_memory_snippet`).
*   **Migration bedacht:** Bildpfad-Migration (`migrate_image_paths`) vorhanden, Pfade auf App-Datenverzeichnis beschränkt.
*   **Tests grün:** Unit-Tests für die drei Module bestehen.

## Block 3: Kostenkontrolle

### Zweck
Dieser Block ist dafür verantwortlich, die Kosten zu berechnen und zu verfolgen, die durch die Nutzung von LLMs und anderen Diensten entstehen. Er soll eine unabhängige Utility-Funktion darstellen, die von anderen Teilen des Backends genutzt werden kann, um die Kosten transparent zu halten und Budgetgrenzen zu überwachen.

### Implementierung (Erledigt)
Die Kernlogik zur Kostenberechnung ist in `backend/cost_calculator.py` implementiert.

*   **Verwendete Technologien:** Python.
*   **Schlüsselkomponenten:**
    *   `backend/cost_calculator.py`: Enthält die Funktion `calculate_cost`, die die Kosten basierend auf Modell-ID und Nutzungsdaten berechnet. Die Preisinformationen werden aus `model_catalog.json` geladen.
    *   `backend/llm_gateway.py`: Eine private Hilfsfunktion `_calculate_and_log_cost` wurde hinzugefügt, um die Kostenberechnung zu zentralisieren und das Logging der Nutzungsdaten zu übernehmen.

### Interaktionen
Dieser Block interagiert hauptsächlich mit dem `LLM Gateway`, das die Kosten für jede LLM-Interaktion berechnet und protokolliert.

### Tests
Unit-Tests vorhanden in `backend/test_cost_calculator.py`.

### Definition of Done
*   **Unabhängigkeit:** `cost_calculator.py` ist eine eigenständige Utility-Funktion ohne direkte Abhängigkeiten zu anderen Modulen außer `model_catalog.json`.n*   **Zentralisierte Berechnung:** Die Kostenberechnung ist in `calculate_cost` gekapselt.
*   **Logging:** Die Kosten und Nutzungsdaten werden zentral über `_calculate_and_log_cost` im `llm_gateway.py` protokolliert.
*   **Tests grün:** Unit-Tests für `cost_calculator.py` bestehen.

## Block 4: LLM Gateway

### Zweck
Dieser Block abstrahiert die Kommunikation mit verschiedenen Large Language Models (LLMs). Er wählt den passenden LLM-Anbieter basierend auf Konfiguration oder Anfrage und delegiert Aufgaben wie Textgenerierung, Tool-Aufrufe und Bildgenerierung an die entsprechenden Modelle.

### Implementierung (Erledigt)
Die Hauptlogik ist in `backend/llm_gateway.py` implementiert.

*   **Verwendete Technologien:** Python, `openai` Bibliothek, `google.generativeai` Bibliothek.
*   **Schlüsselkomponenten:**
    *   `backend/llm_gateway.py`: Enthält Funktionen wie `call_llm`, `_call_openai_api`, `_call_gemini_api`, `_call_gemini_image_generation_api`, `generate_image_tool`, `reason_and_respond`.
    *   `backend/model_catalog.json`: Definiert die verfügbaren LLM-Modelle, deren Typen (Text/Bild), Kosten und spezifische Bildgenerierungsmodelle.

### Refactoring-Details (durchgeführt in diesem Projekt):
*   **`model_catalog.json`:** Aktualisiert, um `image_generation_model` für Textmodelle zu integrieren und `gemini-2.5-flash-image-preview` als primäres Bildgenerierungsmodell für Gemini-Textmodelle festzulegen. Modellnamen wurden auf '2.5' korrigiert.
*   **`llm_gateway.py`:**
    *   Erkennung von Bildgenerierungs-Keywords im Benutzer-Prompt implementiert.
    *   `_call_gemini_image_generation_api` wird nun mit dem korrekten Prompt aufgerufen.
    *   Die Verwendung von `genai.Client()` wurde zugunsten von `genai.GenerativeModel` rückgängig gemacht, um Kompatibilitätsprobleme zu beheben.
    *   Sichergestellt, dass die Textantwort leer ist, wenn ein Bild generiert wird, um Frontend-Anzeigefehler zu vermeiden.
*   **`backend/main.py`:** Angepasst, um die `image_url` von Gemini-Modellen korrekt zu verarbeiten und direkt an das Frontend weiterzuleiten, ohne unnötige Download-Versuche.
*   **`backend/memory_extractor.py`:** Korrigiert, um den Benutzertext korrekt an das LLM für die Faktenextraktion zu übergeben, wodurch die vorherige Fehlinterpretation des Prompts behoben wurde.
*   **`frontend/js/chat.js`:** Aktualisiert, um Bilder korrekt anzuzeigen und leere Textknoten zu vermeiden, die bei der Bildgenerierung entstanden sind.

### Interaktionen
Dieser Block interagiert mit dem `API Key Management` (für API-Schlüssel), der `Kostenkontrolle` (für Nutzungsdaten), dem `Kontext-Management` (für die Vorbereitung des Prompts) und der `Bildgenerierung` (für die Delegation von Bildanfragen).

### Tests
Unit-Tests vorhanden in `backend/test_llm_gateway.py`.

### Definition of Done
*   **Abstraktion:** Einheitliche Schnittstelle für verschiedene LLM-Anbieter.
*   **Modell-Routing:** Korrekte Auswahl des LLM-Modells basierend auf Konfiguration und Anfrage.
*   **Tool-Delegation:** Erkennung und Delegation von Tool-Aufrufen (insbesondere Bildgenerierung) an spezialisierte Funktionen.
*   **Kostenintegration:** Nutzungsdaten werden korrekt an die Kostenkontrolle übergeben.
*   **Tests grün:** Unit-Tests für `llm_gateway.py` bestehen.

## Block 5: Kontext-Management

### Zweck
Dieser Block verwaltet den Gesprächskontext für laufende Chats. Dies beinhaltet das Speichern und Abrufen von Nachrichtenhistorien und die Vorbereitung des Kontexts für LLM-Anfragen. Beinhaltet auch die Logik für "Cross-Chat Context" (Kontext, der über einzelne Chats hinausgeht).

### Implementierung (Erledigt)
Die Hauptlogik ist in `backend/context_manager.py` implementiert.

*   **Verwendete Technologien:** Python, `tiktoken` Bibliothek.
*   **Schlüsselkomponenten:**
    *   `backend/context_manager.py`: Enthält die `ContextManager` Klasse mit Funktionen wie `count_tokens`, `_summarize_chat_segment`, `build_final_context`.

### Refactoring-Details (durchgeführt in diesem Projekt):
*   **`backend/context_manager.py`:** Die `_summarize_chat_segment` Funktion wurde angepasst, um den vom Benutzer ausgewählten Provider und das Modell für die Zusammenfassung zu verwenden, anstatt hartkodiert OpenAI zu nutzen.
*   **`backend/memory_extractor.py`:** Die `extract_and_save_fact` Funktion wurde erweitert, um auch für erfolgreich generierte Bilder einen Speichereintrag zu erstellen. Dabei wird der ursprüngliche Benutzer-Prompt als Grundlage für den Fakt verwendet, auch wenn keine Textantwort vom LLM vorliegt.

### Interaktionen
Dieser Block interagiert mit der `Datenbank & Persistenz` (für Chat-Historie), dem `LLM Gateway` (für LLM-Anfragen) und den `Chat-Operationen & Routing`.

### Tests
Unit-Tests vorhanden in `backend/test_context_manager.py`.

### Definition of Done
*   **Kontextverwaltung:** Der Gesprächskontext wird effizient verwaltet und für LLM-Anfragen vorbereitet.
*   **Zusammenfassung:** Ältere Chat-Segmente werden bei Bedarf zusammengefasst, um das Token-Budget einzuhalten.
*   **Cross-Chat Kontext:** Relevante Informationen aus anderen Chats können in den aktuellen Kontext integriert werden.
*   **Tests grün:** Unit-Tests für `context_manager.py` bestehen.

## Block 6: Speicher & Wissensmanagement

### Zweck
Dieser Block implementiert Langzeitgedächtnis-Funktionen, einschließlich Textzusammenfassung, Vektorisierung und semantischer Suche.

### Implementierung (Erledigt)
Die Hauptlogik ist in `backend/memory_extractor.py`, `backend/vector_service.py` und `backend/chat_summarizer.py` implementiert.

*   **Verwendete Technologien:** Python, `sentence-transformers` Bibliothek, `tiktoken` Bibliothek.
*   **Schlüsselkomponenten:**
    *   `backend/memory_extractor.py`: Extrahiert und speichert Fakten aus Textblöcken.
    *   `backend/vector_service.py`: Generiert Text-Embeddings und führt semantische Suchen durch.
    *   `backend/chat_summarizer.py`: Fasst Chat-Historien zusammen.

### Refactoring-Details (durchgeführt in diesem Projekt):
*   **`backend/memory_extractor.py`:**
    *   Der Import von `vector_service` wurde an den Dateianfang verschoben.
    *   Die Funktion `extract_and_save_fact` wurde angepasst, um `original_prompt` zu akzeptieren und einen Standard-Speichereintrag für erfolgreich generierte Bilder zu erstellen.
*   **`backend/vector_service.py`:**
    *   Code-Duplikation in `find_similar_snippets` und `find_similar_chat_summaries` wurde durch die Einführung einer neuen privaten Hilfsfunktion `_find_similar_items` reduziert.

### Interaktionen
Dieser Block interagiert eng mit der `Datenbank & Persistenz` (zum Speichern und Abrufen von Gedächtnisinhalten), dem `LLM Gateway` (für Retrieval Augmented Generation - RAG-Anfragen) und dem `Kontext-Management` (um Gedächtnisinhalte in den aktuellen Gesprächskontext zu integrieren).

### Tests
Unit-Tests vorhanden in `backend/test_memory_manager.py`, `backend/test_vector_service.py`, `backend/test_chat_summarizer.py`.

### Definition of Done
*   **Faktenextraktion:** Fakten werden korrekt aus Konversationen extrahiert und gespeichert.
*   **Vektorisierung:** Text-Embeddings werden zuverlässig generiert.
*   **Semantische Suche:** Ähnliche Inhalte können effektiv im Gedächtnis gefunden werden.
*   **Chat-Zusammenfassung:** Chat-Historien werden prägnant zusammengefasst.
*   **Tests grün:** Unit-Tests für die relevanten Module bestehen.
