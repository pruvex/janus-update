Arbeitsauftrag 3: Implementierung des "Gold Standard Switch" in main.py
AGENTIC HANDLUNGSPLAN:
Dein Ziel: Die zentrale Anwendungslogik in main.py komplett umbauen. Die alte, heuristische Intent-Erkennung wird durch einen modernen, Tool-gesteuerten Ansatz ersetzt, der vom llm_gateway orchestriert wird.
Relevante PHASE_X.md: REFAKTORING_PLANalt.md (Block 8)
Der Plan:
Stufe 1: Validierung des Ausgangszustands
Führe python health_check.py aus.
Validiere die Existenz von backend/main.py.
Stufe 2: Planung & Recherche
Der Plan ist, die Datei backend/main.py vollständig mit einer neuen, sauberen Version zu überschreiben, da die Änderungen zu umfangreich für replace sind.
Stufe 3: Implementierung & Arbeits-Logbuch
Überschreibe den Inhalt von backend/main.py mit dem vollständigen, refaktorisierten Code aus dem vorherigen Vorschlag. Nutze write_file (ohne append=True).
Dokumentiere im AGENT_WORK_LOG.md: "Aktion: backend/main.py vollständig überschrieben. Grund: Implementierung des 'Gold Standard Switch'. Die alte Logik (_classify_intent, match intent:) wurde entfernt und durch einen zentralen reason_and_respond-Aufruf mit anschließender Tool-Dispatch-Logik ersetzt."
Stufe 4: Dynamische Verifizierung (Funktionstest)
Der Test besteht darin, zu prüfen, ob der FastAPI-Server nach den Änderungen noch startet. Dies ist ein kritischer Integrationstest.
Führe aus mit run_shell_command: uvicorn backend.main:app --host 127.0.0.1 --port 8002 --timeout-keep-alive 5.
Erwartetes Ergebnis: Der Befehl sollte nach 5 Sekunden ohne Absturz oder Syntaxfehler beenden. Ein Fehler deutet auf ein Problem in der neuen main.py hin.
Stufe 5: Aufräumen & Finale Validierung
Führe python health_check.py erneut aus.
Stufe 6: Archivierung & Lockfile-Garantie (KRITISCHE STUFE)
Führe git add . aus.
Führe git commit -m "refactor(agent)!: Implement Gold Standard Switch in main.py" mit run_shell_command aus. (Das ! markiert einen Breaking Change).
Stufe 7: Dokumentation aktualisieren
Aktualisiere REFAKTORING_PLANalt.md. Setze (Erledigt) hinter die Aktion "Anpassung des /api/chat-Endpunkts, um die neue Tool-Routing-Logik zu nutzen".
Stufe 8: Vorbereitung für die Zukunft
Erstelle einen neuen Git-Branch. Nutze run_shell_command: git checkout -b "test/implement-pytest-infrastructure".
Erfolgs-Kriterien:
backend/main.py enthält die neue, Tool-basierte Logik.
Die alten Intent-Funktionen sind entfernt.
Der Uvicorn-Server startet erfolgreich.
Finale Erfolgsmeldung:
Arbeitsauftrag 3 erfolgreich abgeschlossen. Der Kern der Anwendung wurde auf den Gold-Standard-Switch umgestellt. Das Backend ist nun logisch refaktorisiert. Nächster Schritt: Testinfrastruktur aufbauen.