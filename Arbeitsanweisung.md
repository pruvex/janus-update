AGENTIC HANDLUNGSPLAN:
Dein Ziel: Den Chat funktionsfähig machen, indem die Platzhalter-URL im LLM-Gateway durch die echte OpenAI-API-Endpunkt-URL ersetzt wird.
Relevante PHASE_X.md: PHASE_2_KERNFUNKTIONALITAET.md
Der Plan:
Stufe 1: Validierung des Ausgangszustands
Führe python health_check.py aus.
Stufe 2: Planung & Recherche
Planung: Plane die Bearbeitung der Datei backend/llm_gateway.py.
Die Zeile, die die URL https://api.mockllm.dev/v1/chat/completions enthält, muss durch die korrekte OpenAI-API-URL ersetzt werden: https://api.openai.com/v1/chat/completions.
Ebenso muss der payload (die Daten, die an die API gesendet werden) an das Format von OpenAI angepasst werden. OpenAI erwartet ein messages-Array und ein model. Wir werden das Modell vorerst hartcodieren (z.B. auf gpt-3.5-turbo).
Stufe 3: Implementierung & Arbeits-Logbuch
Verwende das replace-Tool, um in backend/llm_gateway.py die Platzhalter-URL durch die echte OpenAI-URL zu ersetzen.
Verwende edit_file, um den payload-Teil in derselben Datei so zu ändern, dass er dem OpenAI-Format entspricht (z.B. payload = {"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": prompt}]}).
Dokumentiere die Anbindung an die Live-API im AGENT_WORK_LOG.md.
Stufe 4: Dynamische Verifizierung (Funktionstest)
Manueller Test-Auftrag: Dies ist der finale Funktionstest für Phase 2.
Ihre Anweisung: Starten Sie das System wie gewohnt mit npm start aus dem frontend-Verzeichnis.
Testen Sie den finalen, vollständigen Zyklus:
Stellen Sie sicher, dass Ihr OpenAI-API-Key in den Einstellungen gespeichert ist.
Wählen Sie im Chat "OpenAI" aus.
Senden Sie eine Nachricht wie "Hallo, Welt!".
Erwartetes Ergebnis: Diesmal darf kein Fehler erscheinen. Stattdessen sollten Sie nach einem kurzen Moment eine echte Antwort von ChatGPT im Chatfenster sehen.
Stufe 5: Aufräumen & Finale Validierung
Ich warte auf Ihre Bestätigung, dass Sie eine echte KI-Antwort erhalten haben.
Führe python health_check.py aus.
Stufe 6: Archivierung & Meilenstein-Commit (KRITISCHE STUFE)
Führe git add . aus.
Erstelle den Commit: git commit -m "milestone(Phase-2): Connect gateway to live OpenAI API and finalize core chat".
Stufe 7: Dokumentation aktualisieren
Markiere alle Aufgaben in PHASE_2_KERNFUNKTIONALITAET.md als erledigt (- [x]).
Stufe 8: Vorbereitung für die Zukunft (Phase 3)
Erstelle die neue Datei PHASE_3_FILESYSTEM_AGENT.md und befülle sie.
Erstelle einen neuen Git-Branch für die erste Aufgabe von Phase 3.
Erfolgs-Kriterien:
Eine im Chat-UI gesendete Nachricht resultiert in einer echten, nicht-gemockten Antwort der OpenAI-API, die im Chat-UI angezeigt wird.