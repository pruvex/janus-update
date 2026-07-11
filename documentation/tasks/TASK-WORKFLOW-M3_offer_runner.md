TASK-WORKFLOW-M3
- Source Spec: documentation/Cursor specs/LEARNED_WORKFLOWS_SPEC.md
- Backlog Item: N/A
- Feature: Learned Workflows Phase 3+4
- Generated At: 2026-07-08

## Generated Tasks

### TASK-WORKFLOW-M3.2 Proaktives Offer und Save-Dialog
- Ziel:
  - Nach erfolgreichem Multi-Step-Workflow ein bounded Routine-Offer erzeugen und explizite Save-/Decline-Antworten verarbeiten, ohne autonome Speicherung oder Runner-Ausfuehrung.
- Scope:
  - Offer-Gate-Ergebnis aus dem bestehenden Workflow-Detector konsumieren.
  - Proaktiven Offer-Text nur dann an die Antwort anhaengen, wenn die Guards aus der Spec greifen.
  - Explizite Save-/Decline-Intents fuer den Offer-Dialog erkennen.
  - Speicherung nur nach explizitem User-`Ja` oder explizitem Save-Request erlauben.
  - Session-Cooldown und Fingerprint-Denylist fuer abgelehnte Offers lokal persistieren.
  - Keine Routine-Ausfuehrung, keine UI, kein Transport, kein OAuth, kein Produkt-OpenRouter.
- Files:
  - backend/services/workflow/workflow_offer_service.py
  - backend/services/orchestrator/intent_engine.py
  - backend/services/orchestrator/response_finalizer.py
  - backend/tests/test_workflow_offer_service.py
  - backend/tests/test_routine_intent_patterns.py
- Steps:
  - Offer-Entscheidung und Offer-Text-Generierung in einen dedizierten Workflow-Service extrahieren.
  - Intent-Patterns fuer Save-Confirm, Save-Request und Decline bounded in der Intent-Engine ergaenzen.
  - Response-Finalizer nur minimal anbinden, damit Offers nach erfolgreichem Multi-Step-Erfolg angehaengt werden koennen.
  - Persistente Offer-Logs und Save-Flows ueber den bestehenden Routine-Store integrieren.
- Acceptance Criteria:
  - Nach Multi-Step-Erfolg erscheint ein Offer-Text nur dann, wenn Gate und Feature-Flags passen.
  - `Ja` oder expliziter Save-Request speichert eine Routine, `Nein` speichert nicht und setzt Session-Cooldown.
  - `Nicht mehr fragen` blockiert denselben Fingerprint fuer weitere Offers.
  - `ROUTINES_PROACTIVE_OFFER_ENABLED=false` unterdrueckt Offers, explizite Save-Requests funktionieren weiter.
  - Maximal ein Offer pro Session, sofern der Cooldown aktiv ist.
- Tests:
  - python -m pytest backend/tests/test_workflow_offer_service.py -v
  - python -m pytest backend/tests/test_routine_intent_patterns.py -v
  - python -m py_compile backend/services/workflow/workflow_offer_service.py backend/services/orchestrator/intent_engine.py backend/services/orchestrator/response_finalizer.py
- Model: 5.4
- Reason:
  - Produktiver Backend-Slice mit mehreren betroffenen Dateien, aber noch klar bounded vor Runner und UI.

### TASK-WORKFLOW-M3.3 Routine-Runner und Placeholder-Aufloesung
- Ziel:
  - Gespeicherte Routinen ueber Trigger-Phrasen ausfuehren, Placeholder aus Memory aufloesen und Step-Ergebnisse sicher aggregieren.
- Scope:
  - Trigger-Matching gegen gespeicherte `trigger_phrases`.
  - Sequenzielle Runner-Ausfuehrung ueber bestehenden Tool-Executor.
  - Placeholder-Resolver fuer bounded User-Kontext wie `{{user.city}}`.
  - Policy-Stop pro Step mit klarer Fehlerrueckmeldung.
  - `run_count` und `last_run_at` aktualisieren.
  - Kein UI, kein neuer Transportpfad, kein Produkt-OpenRouter, keine Delegation-/Gate-Arbeit.
- Files:
  - backend/services/workflow/routine_runner.py
  - backend/services/workflow/placeholder_resolver.py
  - backend/services/orchestrator/intent_engine.py
  - backend/tests/test_routine_runner.py
  - backend/tests/test_routine_placeholder_resolver.py
- Steps:
  - Placeholder-Aufloesung fuer Routine-Step-Argumente implementieren.
  - Runner bauen, der Steps geordnet ausfuehrt und Policy-Blocks fail-closed behandelt.
  - Trigger-Erkennung mit der Intent-Engine verbinden.
  - Aggregierte Antwort und Run-Metadaten sauber zurueckgeben.
- Acceptance Criteria:
  - Eine gespeicherte Routine wird ueber passende Trigger-Phrase gefunden und ausgefuehrt.
  - Placeholder wie `{{user.city}}` werden aus Memory-Kontext aufgeloest.
  - Ein Policy-Block beendet die Restausfuehrung und erklaert den Abbruch.
  - Unbekannte Routine fuehrt zu einer klaren Nicht-Gefunden-Antwort.
  - Save-zu-Execute-Roundtrip ist in Integration abgedeckt.
- Tests:
  - python -m pytest backend/tests/test_routine_runner.py -v
  - python -m pytest backend/tests/test_routine_placeholder_resolver.py -v
  - python -m py_compile backend/services/workflow/routine_runner.py backend/services/workflow/placeholder_resolver.py backend/services/orchestrator/intent_engine.py
- Model: 5.4
- Reason:
  - Multi-file Backend-Slice mit Tool-Execution- und Memory-Anbindung, deshalb klar Codex-owned.

### TASK-WORKFLOW-M3.4 Semantische Routine-Wiedererkennung
- Ziel:
  - Eine gespeicherte Routine beim naechsten semantisch passenden natuerlichen User-Wunsch erkennen und ausfuehren, ohne dass der User den generierten Routinenamen oder eine Magic Phrase kennen muss.
- Scope:
  - Backend-only Erweiterung des bestehenden Routine-Runner-Pfads.
  - Matching zuerst weiterhin gegen explizite `trigger_phrases`, danach bounded semantisch gegen die gespeicherte Step-Signatur und die natuerliche User-Anfrage.
  - Fuer das MVP mindestens den realen Kalender-plus-Wetter-Fall absichern: `calendar.list_events` + `system.weather` muss bei einer spaeteren Anfrage wie `Was steht heute in meinem Kalender und wie wird das Wetter in Koeln?` die gespeicherte Routine finden.
  - Runner-Antwort muss transparent sagen, dass eine passende gespeicherte Routine genutzt wurde.
  - Keine autonome Ausfuehrung ohne User-Anfrage; keine UI, kein neuer Transportpfad, kein OAuth, kein Produkt-OpenRouter, keine Delegation-Haertung.
- Files:
  - backend/services/workflow/routine_runner.py
  - backend/services/orchestrator/intent_engine.py
  - backend/services/chat_orchestrator.py
  - backend/tests/test_routine_runner.py
  - backend/tests/test_workflow_offer_service.py
- Steps:
  - Natuerliche Anfrage in eine bounded Skill-Signatur normalisieren.
  - Gespeicherte Routinen anhand `steps_json`/Step-Fingerprint gegen diese Signatur matchen, wenn kein expliziter Trigger passt.
  - Matched-Trigger/Match-Art im Runner-Ergebnis so setzen, dass Debugging und User-Feedback unterscheidbar bleiben.
  - Erfolgsantwort um einen kurzen Hinweis ergaenzen, dass die passende gespeicherte Routine genutzt wurde.
- Acceptance Criteria:
  - Nach Save einer Kalender-plus-Wetter-Routine fuehrt eine spaetere semantisch gleiche natuerliche Anfrage die Routine aus, ohne den Routinenamen zu nennen.
  - Ein direkter Routinename/Trigger funktioniert weiterhin.
  - Unpassende natuerliche Anfragen fuehren nicht zu Routine-Ausfuehrung.
  - Die Antwort nennt transparent, dass eine gespeicherte Routine genutzt wurde.
- Tests:
  - python -m pytest backend/tests/test_routine_runner.py -v
  - python -m pytest backend/tests/test_workflow_offer_service.py -v
  - python -m py_compile backend/services/workflow/routine_runner.py backend/services/orchestrator/intent_engine.py backend/services/chat_orchestrator.py
- Model: 5.4
- Reason:
  - Produktrelevanter Backend-UX-Slice mit bestehendem Runner/Intent-Code, write-capable und gut fuer Cursor Composer als bounded Workhorse geeignet.

## Completion Metadata

- **TASK-WORKFLOW-M3.4 Status:** DONE
- **Final Audit:** `documentation/tasks/TASK-WORKFLOW-M3.4_final_audit.md` (PASS)
- **Audit Package:** `documentation/tasks/TASK-WORKFLOW-M3.4_AUDIT_PACKAGE.md`
- **Validation:** focused routine/offer/chat-finalize pytest PASS (`40 passed`); Python compile PASS; scoped diff check PASS; manual GPT and Gemini evidence PASS.
- **Scope Note:** M3 closes the bounded workflow execution roadmap scope. Optional routine-management UI and silent routine learning remain separate future work.
