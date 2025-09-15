### PHASE 5: Erweiterte Agenten-Fähigkeiten
*Ziel: Janus mit fortgeschrittenen, agentenhaften Fähigkeiten ausstatten.*

- [ ] **[JANUS] Filesystem-Agent (Backend & Frontend):** Den vollständigen Filesystem-Agenten implementieren.
- [ ] **[WÄCHTER] Filesystem-Agent testen:** Umfassende Tests für die Backend-Logik des Filesystem-Agenten schreiben, insbesondere für die Sicherheits-Sandbox.
- [ ] **[JANUS] Bilderzeugung & Anzeige:** Die Funktionalität zur Bilderzeugung implementieren und im Frontend darstellen.
- [ ] **[WÄCHTER] Bilderzeugung testen:** Die Anbindung an die Bild-API und die Tool-Nutzung durch das LLM testen.
- [ ] **[JANUS] Vorbereitung für Agenten-Erstellung:** Die Architektur für benutzerdefinierte Agenten vorbereiten. (Architektur-Aufgabe, verifiziert durch Code-Review)
- [ ] **[GIT] Meilenstein-Commit:** Die ersten erweiterten Agenten-Fähigkeiten als stabilen Meilenstein committen.
- [x] **[JANUS] Websearch-Tool implementieren:** Ein Tool zur Durchführung von Websuchen über GPTs integriertes web.search Tool implementieren.
- [x] **[JANUS] Prompt für Kreativen Schreiber aktualisiert:** Der Prompt für die Persönlichkeit "Kreativer Schreiber" wurde aktualisiert, um die Rolle und Prinzipien zu präzisieren.
- [x] **[JANUS] Creative Writer Pipeline implementiert:** Eine Pipeline für kreatives Schreiben wurde implementiert, die Ideen-, Entwurfs- und Endfassungsphasen umfasst.
- [x] **[JANUS] Creative Writer Pipeline in Backend integriert:** Die Logik in `backend/main.py` wurde angepasst, um die `creative_writer` Pipeline aufzurufen, wenn die Persönlichkeit "Kreativer Schreiber" aktiv ist.
- [x] **[JANUS] Behebung des ImportError in der Creative Writer Pipeline:** Der `ImportError` in der Creative Writer Pipeline wurde behoben, indem `simple_llm_generate_content` in `backend/llm_gateway.py` hinzugefügt und die Aufrufe in `backend/creative_writer.py` und `backend/main.py` angepasst wurden.
- [x] **[JANUS] Behebung des AttributeError in der Creative Writer Pipeline:** Der `AttributeError` in der Creative Writer Pipeline wurde behoben, indem alle Zugriffe auf `.text` in `backend/creative_writer.py` in `.get('text', '')` geändert wurden.
- [x] **[JANUS] Behebung des UnboundLocalError in handle_chat_request:** Der `llm_response` wurde in `backend/main.py` initialisiert, um `UnboundLocalError` zu verhindern.
- [x] **[JANUS] Logging in Creative Writer Pipeline hinzugefügt:** Detaillierte Logging-Statements wurden in `backend/creative_writer.py` hinzugefügt, um die Fehlersuche bei der Inhaltserzeugung zu erleichtern.
- [x] **[JANUS] Dynamische Stil-Extraktion für Creative Writer:** Die `handle_chat_request` Funktion in `backend/main.py` extrahiert nun dynamisch den kreativen Stil aus dem Benutzer-Prompt und übergibt ihn an die `creative_writer` Pipeline.
- [x] **[JANUS] Logging für final_answer in main.py hinzugefügt:** Ein Logging-Statement wurde in `backend/main.py` hinzugefügt, um den Wert von `final_answer` vor der Überprüfung zu protokollieren.