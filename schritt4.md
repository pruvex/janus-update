# 🚀 Global Memory – Aktueller Stand und Implementierungsdetails

Dieses Dokument fasst den aktuellen Stand der Implementierung des Global Memory zusammen, basierend auf den ursprünglichen Plänen und den tatsächlich umgesetzten Schritten.

## ✅ Umgesetzte Funktionalitäten

### 1. Datenbankschema-Erweiterung
*   **Tabelle `memory`:** Eine neue Tabelle `memory` wurde in `backend/database.py` definiert, um extrahierte Wissensbausteine zu speichern.
    *   Felder: `id`, `chat_id` (Herkunft des Eintrags), `snippet` (der eigentliche Wissensbaustein), `embedding_json` (Vektor-Embedding als JSON-String), `created_at`.
*   **`embedding_json` Feld:** Das `Memory`-Modell in `backend/database.py` wurde um das Feld `embedding_json = Column(Text, nullable=True)` erweitert, um Vektor-Embeddings zu speichern.
*   **Datenbank-Migration:** Die `chat_history.db` muss manuell gelöscht werden, damit das Schema mit der neuen Spalte korrekt neu erstellt wird.

### 2. Vektor-Logik (Reines Python)
*   **`backend/vector_service.py`:** Ein neues Modul wurde erstellt, das die gesamte Logik für die Erstellung von Embeddings und die semantische Ähnlichkeitssuche kapselt.
    *   **`SentenceTransformer('all-MiniLM-L6-v2')`:** Wird zum Generieren von Embeddings verwendet. Das Modell wird einmal geladen und wiederverwendet.
    *   **`generate_embedding(text: str)`:** Generiert einen Vektor-Embedding für einen gegebenen Text und speichert ihn als JSON-String.
    *   **`find_similar_snippets(query_text: str, memories: list, top_k: int = 3, threshold: float = 0.1)`:** Findet die semantisch ähnlichsten Erinnerungen an einen Suchtext basierend auf Kosinus-Ähnlichkeit. Der `threshold` wurde auf 0.1 gesetzt, um eine breitere Abdeckung zu ermöglichen.

### 3. CRUD-Operationen für Memory
*   **`backend/crud.py`:** Wurde angepasst, um die Vektor-Logik zu nutzen.
    *   **`save_memory_snippet(db, chat_id, snippet_text)`:** Generiert jetzt das Embedding des `snippet_text` mittels `vector_service.generate_embedding` und speichert es im `embedding_json`-Feld.
    *   **`find_similar_memory_snippet(db, text)`:** Ersetzt die alte `memory_snippet_exists`-Funktion. Diese Funktion lädt alle Memories und verwendet `vector_service.find_similar_snippets` (mit `top_k=1` und `threshold=0.95`) um semantisch ähnliche Fakten zu finden. Dies dient primär dem Duplicate-Check und der Konfliktlösung.
    *   **`update_memory_snippet(db, memory_id, new_snippet)`:** Eine neue Funktion zum Aktualisieren eines bestehenden Memory-Eintrags, inklusive Neuberechnung des Embeddings.
    *   **`get_all_memories(db)`:** Eine neue Funktion, die alle gespeicherten Memory-Snippets aus der Datenbank abruft.

### 4. Memory-Intelligenz-Schicht
*   **`backend/memory_extractor.py`:**
    *   **`resolve_fact_conflict(db, old_fact, new_fact, api_key)`:** Eine neue asynchrone Funktion, die ein LLM befragt, ob ein `new_fact` eine Korrektur oder Aktualisierung eines `old_fact` darstellt.
    *   **`extract_and_save_fact(db, chat_id, text_block, api_key)`:** Diese Funktion wurde erweitert, um Konflikte zu lösen.
        *   Sie nutzt `crud.find_similar_memory_snippet` um ähnliche Fakten zu finden.
        *   Wenn ein sehr ähnlicher Fakt gefunden wird (Kosinus-Ähnlichkeit > 0.95), wird er als Duplikat ignoriert.
        *   Wenn ein mäßig ähnlicher Fakt gefunden wird, wird `resolve_fact_conflict` aufgerufen, um zu prüfen, ob es sich um eine Korrektur handelt. Bei einer Korrektur wird der alte Fakt mittels `crud.update_memory_snippet` aktualisiert.
        *   Andernfalls wird der Fakt als neuer Eintrag gespeichert.

### 5. Haupt-API-Integration
*   **`backend/main.py` (`/api/chat` Route):**
    *   **Chat-Erstellung:** Wenn `request.chat_id` `None` ist (neuer Chat), wird automatisch ein neuer Chat in der Datenbank erstellt und die `chat_id` zugewiesen.
    *   **Query Expansion:** Vor der Gedächtnissuche wird die Benutzeranfrage (`request.prompt`) mittels eines LLM (`expand_query` Funktion) erweitert, um verwandte Konzepte oder alternative Formulierungen zu finden. Dies soll die Trefferquote bei indirekten Fragen erhöhen.
    *   **Vektor-basierter Retrieval:** Die Gedächtnissuche verwendet jetzt `crud.get_all_memories` und `vector_service.find_similar_snippets` mit den erweiterten Suchanfragen, um relevante `memory_snippets` zu finden.
    *   **Hintergrundaufgabe:** `memory_extractor.extract_and_save_fact` wird weiterhin als asynchrone Hintergrundaufgabe gestartet, um die Faktenextraktion nicht-blockierend durchzuführen.

### 6. Test-Infrastruktur
*   **`waechter/conftest.py`:** Eine zentrale Datei für Pytest-Fixtures (`db_session`) wurde erstellt, um die Wiederverwendung und Wartbarkeit zu verbessern.
*   **`waechter/test_memory_crud.py`:** Bereinigt und testet die CRUD-Operationen für Memory.
*   **`waechter/test_memory_extractor.py`:** Testet die Extraktions- und Konfliktlösungslogik.
*   **`waechter/test_chat_endpoint.py`:** Aktualisiert, um die mehrfachen LLM-Aufrufe (Hauptantwort und Hintergrund-Extraktion) korrekt zu mocken und zu überprüfen.

## ⚠️ Bekannte Probleme und Einschränkungen

*   **Asynchrone Tests:** Die asynchronen Tests in `waechter/test_memory_extractor.py` werden aufgrund hartnäckiger Umgebungsprobleme (insbesondere mit `pytest-asyncio` und der Python-Umgebung) derzeit übersprungen. Dies stellt eine Lücke in der Testabdeckung dar, die idealerweise behoben werden sollte.
*   **Inferenz-Robustheit:** Obwohl die Query Expansion implementiert wurde, kann das System immer noch Schwierigkeiten haben, komplexe inferentielle Fragen (z. B. "wer ist meine Mutter?" wenn nur "Frau des Vaters" gespeichert ist) zuverlässig zu beantworten. Dies erfordert möglicherweise weitere Verfeinerungen im Prompt-Engineering oder eine dedizierte Inferenzschicht.
*   **Datenbankgröße (`chat_history.db`):** Die SQLite-Datenbankdatei kann im Laufe der Zeit anwachsen und Speicherplatz nicht freigeben, selbst nach dem Löschen von Daten. Dies ist ein bekanntes Verhalten von SQLite.
    *   **Lösung:** Manuelles Ausführen des `VACUUM;` Befehls in einem SQLite-Browser, um den Speicherplatz zurückzugewinnen.
*   **FAISS-Integration:** Der ursprüngliche Plan zur Integration von FAISS für die Vektor-Suche wurde aufgrund unlösbarer Umgebungsprobleme verworfen. Die aktuelle Implementierung basiert auf einer reinen Python-Lösung (`sentence-transformers`).

---
*Letzte Aktualisierung: 2025-08-23*
