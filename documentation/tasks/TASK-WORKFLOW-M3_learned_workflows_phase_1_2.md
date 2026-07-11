TASK-WORKFLOW-M3
- Source Spec: `documentation/Cursor specs/LEARNED_WORKFLOWS_SPEC.md`
- Backlog Item: `N/A`
- Feature: Learned Workflows MVP Phase 1+2
- Generated At: 2026-07-08

## Generated Tasks

### TASK-WORKFLOW-M3.1 Implement Workflow Phase 1+2 as one bounded store-and-detector slice
- Ziel:
  - Fuehre den Routine-Store und den Workflow-Detector als einen gebundenen MVP-Foundation-Slice ein, damit Janus erfolgreiche Multi-Step-Ablaufspuren strukturiert speichern und fuer spaetere Offer-/Runner-Phasen sauber erkennen kann.
- Scope:
  - Datenmodell, Store/Schema, Fingerprint-/Registry-Validierung, Step-Trace-Extraktion und Offer-Candidate-Detection fuer Learned Workflows.
  - Nur M3 Phase 1 und Phase 2 aus der Workflow-Spec; kein proaktives Offer, kein Routine-Runner, keine Routinen-UI, keine Memory-V2-Aenderung ausser erlaubten Placeholder-/Binding-Vorbereitungen im Datenmodell.
  - `ROUTINES_ENABLED` bleibt default `false`.
- Files:
  - `backend/data/models.py`
  - `backend/data/database.py`
  - `backend/services/workflow/routine_store.py`
  - `backend/services/workflow/routine_schema.py`
  - `backend/services/workflow/workflow_detector.py`
  - `backend/services/workflow/step_trace_extractor.py`
  - `backend/services/capability_registry.py` (nur falls fuer Registry-Validierung minimal benoetigt)
  - `backend/tests/test_routine_store.py`
  - `backend/tests/test_workflow_detector.py`
  - direkt betroffene bestehende Workflow-/Orchestrator-Regressionen, falls fuer echte KPI-Trace-Fixtures noetig
- Steps:
  1. Ergaenze das Routine-Datenmodell inklusive `user_routines` und `user_routine_offer_log` mit dediziertem JSON-Step-Schema, Fingerprint und User-Scope.
  2. Implementiere `routine_store.py` und `routine_schema.py` mit CRUD-Grundlagen, Registry-Validierung, Fingerprint-Dedup und sicherem Umgang mit Trigger-/Step-Daten.
  3. Implementiere `step_trace_extractor.py` und `workflow_detector.py`, um aus bestehenden Tool-/KPI-Spuren erfolgreiche Multi-Step-Ablaeufe in deterministische Routine-Steps und Offer-Kandidaten zu ueberfuehren.
  4. Ergaenze fokussierte Tests fuer Store-CRUD, Registry-Validation, Dedup, Step-Reihenfolge, Failed-Step-Ignorierung und Offer-Candidate-Reject-Gruende.
- Acceptance Criteria:
  - `user_routines` und `user_routine_offer_log` existieren mit user-gebundener Abfrage, Fingerprint-Dedup und validierbarem Step-Schema.
  - Unbekannte `skill_id`s werden beim Speichern deterministisch abgewiesen.
  - Der Detector extrahiert aus erfolgreichen Multi-Step-Spuren die korrekte Step-Reihenfolge und ignoriert fehlgeschlagene Steps.
  - `is_offer_candidate` bildet die positiven/negativen Gate-Regeln aus der Spec fuer Phase 2 verlässlich ab, ohne schon Offer-Text oder Intent-Patterns einzufuehren.
  - `ROUTINES_ENABLED` bleibt default `false`; kein proaktives Offer, kein Runner, keine UI.
- Tests:
  - `python -m pytest backend/tests/test_routine_store.py -v`
  - `python -m pytest backend/tests/test_workflow_detector.py -v`
  - `python -m py_compile backend/services/workflow/routine_store.py backend/services/workflow/routine_schema.py backend/services/workflow/workflow_detector.py backend/services/workflow/step_trace_extractor.py`
- Model: 5.4
- Reason:
  - Die Roadmap definiert M3 Phase 1+2 explizit als ersten Workflow-MVP-Slice. Store und Detector bilden zusammen einen kleinen, zusammenhaengenden Foundation-Block, ohne schon in Offer-, Runner- oder UI-Logik zu kippen.
- Closeout:
  - Final Audit PASS ist in `documentation/tasks/TASK-WORKFLOW-M3.1_final_audit.md` dokumentiert. Der erste Workflow-MVP-Foundation-Slice ist damit task-scharf abgeschlossen: `user_routines` und `user_routine_offer_log` sind im Datenmodell verankert, `RoutineStore` validiert gegen echte `CapabilityRegistry`-Skills und dedupliziert ueber Step-Fingerprints, und der Detector extrahiert erfolgreiche Multi-Step-Spuren jetzt deterministisch in Routine-Steps und bounded Offer-Kandidaten.
  - Die lokale Evidenz umfasst `pytest backend/tests/test_routine_store.py` PASS, `pytest backend/tests/test_workflow_detector.py` PASS, `py_compile` PASS sowie einen assist-only OpenRouter-Precheck-Review als zusaetzliche bounded Evidence (`WF-PRECHECK-WORKFLOW-M3.1-OR-2026-07-08-001`, PASS, echte Kosten `0.000094010`), waehrend die produktive Acceptance Authority lokal bei Codex blieb.
  - M3 Phase 3 (proaktives Offer), Phase 4 (Runner) und Phase 5 (UI) bleiben bewusst offen und duerfen aus diesem PASS nicht impliziert werden.
