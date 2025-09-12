## Zyklus: LTM-Integration und LRU-Logik

**Stufe 3: Implementierung & Arbeits-Logbuch**

*   **WAS:** `get_all_searchable_memories`-Funktion zu `backend/memory_manager.py` hinzugefügt.
*   **WARUM:** Um eine kombinierte Liste von STM- und LTM-Einträgen für die Vektorsuche bereitzustellen.

*   **WAS:** `handle_chat_request` in `backend/main.py` modifiziert.
*   **WARUM:** Die Suche wurde auf das gesamte Gedächtnis (STM + LTM) erweitert. LTM-Treffer werden nun ins STM befördert.

*   **WAS:** "Touch"-Logik in `handle_chat_request` in `backend/main.py` hinzugefügt.
*   **WARUM:** Um den Zeitstempel von verwendeten STM-Einträgen zu aktualisieren und sie so vor der Archivierung zu schützen (LRU-Logik).