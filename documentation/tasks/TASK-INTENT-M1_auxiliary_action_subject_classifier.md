TASK-INTENT-M1
- Source Spec: `documentation/Cursor specs/INTENT_ENGINE_HERMES_INSPIRED_UPGRADE_PLAN.md`
- Backlog Item: `N/A`
- Feature: Intent Phase 1 Auxiliary Action/Subject Classifier
- Generated At: 2026-07-07

## Generated Tasks

### TASK-INTENT-M1.1 Build the auxiliary classifier contract, provider wrapper, and focused unit coverage
- Ziel:
  - Fuehre den neuen Auxiliary Action/Subject Classifier als klaren lokalen Contract mit konfigurierbarer Provider-Anbindung und deterministischer Testoberflaeche ein.
- Scope:
  - Nur neuer Classifier-Service, Flag-/Config-Wiring, Ergebnis-Schema und fokussierte Unit-Tests fuer den Classifier-Contract.
  - Keine Integration in `detect_all_intents()` und keine Aenderung bestehender Merge-Regeln in dieser Slice.
- Files:
  - `backend/services/orchestrator/intent_aux_classifier.py`
  - `backend/services/orchestrator/intent_config.py`
  - `backend/data/schemas_intent.py`
  - `backend/tests/test_intent_aux_classifier.py`
  - `backend/tests/test_intent_action_subject_mapping.py`
- Steps:
  1. Definiere den `ActionSubjectResult`-Contract gemaess Spec `§5.4` mit den erlaubten `action`-, `subject`-, `confidence`-, `evidence`- und `source`-Feldern.
  2. Implementiere einen gekapselten Auxiliary-Classifier-Service mit Provider-Auswahl, JSON-Parsing, fail-closed Validation und Regex-/disabled-Fallback.
  3. Fuehre die M1-Flags und Basis-Konfigurationswerte in `intent_config.py` ein, ohne das bestehende Verhalten bei Flag `off` zu veraendern.
  4. Ergaenze fokussierte Tests fuer Schema-Validation, erfolgreiche Klassifikation, ungueltige Antworten, Provider-Fehler und disabled/offline Fallback.
- Acceptance Criteria:
  - Der Auxiliary-Classifier liefert nur valide `ActionSubjectResult`-Objekte oder faellt deterministisch auf den Legacy-/Regex-Pfad zurueck.
  - Flag `off` fuehrt nicht zu einer veraenderten externen Intent-Entscheidung.
  - Provider-/Parsing-Fehler oeffnen keine neue unkontrollierte Route und erzeugen keinen Crash im Intent-Pfad.
  - Die neue Contract-Oberflaeche ist ueber Unit-Tests lokal pruefbar, ohne Live-Provider zu benoetigen.
- Tests:
  - `python -m pytest backend/tests/test_intent_aux_classifier.py -q`
  - `python -m pytest backend/tests/test_intent_action_subject_mapping.py -q`
  - `python -m py_compile backend/services/orchestrator/intent_aux_classifier.py backend/services/orchestrator/intent_config.py backend/data/schemas_intent.py`
- Model: 5.4
- Reason:
  - Die erste M1-Slice sollte die neue Classifier-Vertragsflaeche isoliert verankern, bevor der laufende Intent-Pfad integriert wird.
- Closeout:
  - Final Audit PASS ist in `documentation/tasks/TASK-INTENT-M1.1_final_audit.md` dokumentiert. Der erste M1-I1-Slice ist damit task-scharf abgeschlossen: der Auxiliary Action/Subject Classifier besitzt jetzt einen fail-closed `ActionSubjectResult`-Contract, eine gebundene Default-Provider-Wrapper-Schicht ueber `llm_gateway.call_llm`, M1-Flag-/Config-Wiring und fokussierte Unit-Tests. `detect_all_intents()`-Integration, Benchmark-Uplift, Staging-Enablement und Memory A/B bleiben bewusst offen fuer `TASK-INTENT-M1.2` und `TASK-INTENT-M1.3`.

### TASK-INTENT-M1.2 Integrate the auxiliary classifier into detect_all_intents with merge rules and flag-off parity
- Ziel:
  - Integriere den Auxiliary-Classifier in den bestehenden Intent-Pfad, sodass Action/Subject gemerged werden koennen, ohne Legacy-Verhalten bei Flag `off` zu brechen.
- Scope:
  - Nur `detect_all_intents()`-Integration, Merge-Regeln, Circuit-Breaker/Fallback-Verhalten und Regressionen gegen bestehende Intent-Pfade.
  - Keine Benchmark-Zielerreichung oder Staging-Freigabe in dieser Slice.
- Files:
  - `backend/services/orchestrator/intent_engine.py`
  - `backend/services/orchestrator/intent_aux_classifier.py`
  - `backend/services/orchestrator/intent_config.py`
  - `backend/tests/test_calendar_routing_fix.py`
  - `backend/tests/test_intent_aux_classifier.py`
  - `backend/tests/test_intent_action_subject_mapping.py`
- Steps:
  1. Fuehre den Auxiliary-Layer gemaess Spec `§5.6` in `detect_all_intents()` ein und halte Safety-Veto sowie Legacy-Fallback intakt.
  2. Implementiere die Merge-Regeln fuer hohe, mittlere und niedrige Confidence inklusive `clarify`-Pfad bei Aux-vs-Legacy-Konflikt.
  3. Integriere den Circuit-Breaker fuer wiederholte Aux-Fehler mit deterministischem Regex-Fallback.
  4. Ergaenze Regressionen fuer Contact/Pet/Recall sowie fuer bestehende Calendar-/Shopping-/Weather-/Routing-Pfade bei Flag `off` und Flag `on`.
- Acceptance Criteria:
  - Flag `off` behaelt das bestehende Verhalten des Intent-Pfads bei.
  - Safety-Veto und bestehende Calendar-/Weather-/Routing-Guardrails bleiben unveraendert wirksam.
  - Aux-Fehler, niedrige Confidence oder Konflikte fuehren nicht zu unkontrollierten neuen Routen.
  - `backend/tests/test_calendar_routing_fix.py` bleibt gruen.
- Tests:
  - `python -m pytest backend/tests/test_intent_aux_classifier.py backend/tests/test_intent_action_subject_mapping.py -q`
  - `python -m pytest backend/tests/test_calendar_routing_fix.py -q`
  - `python -m py_compile backend/services/orchestrator/intent_engine.py backend/services/orchestrator/intent_aux_classifier.py backend/services/orchestrator/intent_config.py`
- Model: 5.4
- Reason:
  - Diese Slice verbindet den neuen Classifier mit dem produktiven Intent-Pfad und ist der eigentliche Integrationskern von M1.
- Closeout:
  - Final Audit PASS ist in `documentation/tasks/TASK-INTENT-M1.2_final_audit.md` dokumentiert. Der zweite M1-I1-Slice ist damit task-scharf abgeschlossen: `detect_all_intents()` merged den Auxiliary-Classifier jetzt kontrolliert in den bestehenden Intent-Pfad, Flag-`off`-Paritaet und bestehende Guardrails bleiben erhalten, und der produktive Recall-Pfad wurde nach dem Debug-Hardening fuer Contact-Recall deterministisch lokal stabilisiert.
  - Die erste manuelle Fehlbeobachtung wurde als Live-DB-Kontamination isoliert und in `documentation/test-runs/TASK-INTENT-M1.2_debug_live_db_contamination_cleanup_2026-07-08.md` bereinigt; der anschliessende Gemini-spezifische Recall-Drift wurde in `documentation/test-runs/TASK-INTENT-M1.2_debug_gemini_contact_recall_fallback_2026-07-08.md` auf den Post-`memory.read`-Synthesepfad eingegrenzt und mit lokalem Fallback abgesichert.
  - M1 I1 bleibt bewusst offen, bis `TASK-INTENT-M1.3` den Benchmark-Uplift, die Latenz-Guardrails und das Staging-Enablement gegen die M0-Baseline belegt.

### TASK-INTENT-M1.3 Prove benchmark uplift, latency guardrails, and staged enablement for the auxiliary classifier
- Ziel:
  - Beweise den M1-Nutzen gegen die neue M0-Baseline und sichere Performance, Flag-Verhalten und Enablement-Nachweise fuer die erste Staging-Freigabe ab.
- Scope:
  - Nur Benchmark-Recheck, Latenz-/Telemetry-Nachweise, Flag-Enablement-Nachweise und die direkt benoetigten Tests/Dokumentationsartefakte fuer I1.
  - Keine neuen Intent-Features ausserhalb des Auxiliary-Classifier-Scope.
- Files:
  - `backend/scripts/run_intent_benchmark.py`
  - `backend/tests/test_intent_benchmark.py`
  - `backend/tests/test_intent_aux_classifier.py`
  - `backend/tests/test_calendar_routing_fix.py`
  - `documentation/test-runs/INTENT_BENCHMARK_BASELINE.md`
  - `documentation/test-runs/`
- Steps:
  1. Fuehre den Intent-Benchmark mit aktiviertem Auxiliary-Classifier erneut aus und vergleiche Contact/Pet/Recall explizit gegen die M0-Baseline.
  2. Ergaenze Nachweise fuer P95-Latenz des Classifiers und fuer identisches Verhalten bei Flag `off`.
  3. Halte fest, ob die I1-Exit-Kriterien aus Roadmap und Spec erreicht sind oder ob ein dokumentierter Blocker verbleibt.
  4. Lege die evidenzfaehigen Benchmark-/Test-/Latency-Artefakte fuer `janus-final-audit` und den Staging-Flip bereit.
- Acceptance Criteria:
  - Contact/Pet/Recall zeigen mindestens `+12 pp` gegen die M0-Baseline oder der Blocker ist sauber dokumentiert.
  - `backend/tests/test_calendar_routing_fix.py` bleibt gruen.
  - P95-Latenz des Auxiliary-Classifiers liegt unter `400 ms` oder ein belastbarer Blocker ist dokumentiert.
  - Flag `off` bleibt identisch zum Legacy-Verhalten.
- Tests:
  - `python -m pytest backend/tests/test_intent_benchmark.py backend/tests/test_intent_aux_classifier.py backend/tests/test_calendar_routing_fix.py -q`
  - `python -m backend.scripts.run_intent_benchmark --write-baseline`
  - targeted latency/telemetry check for the auxiliary classifier execution path
- Model: 5.4
- Reason:
  - Die dritte Slice schliesst M1 erst mit echter M0-vs-M1-Evidenz statt nur mit lokal gruener Implementierung.

@janus-task-breakdown
Spec: documentation/Cursor specs/INTENT_ENGINE_HERMES_INSPIRED_UPGRADE_PLAN.md
Task: documentation/tasks/TASK-INTENT-M1_auxiliary_action_subject_classifier.md
Backlog Item: N/A
Target Task: TASK-INTENT-M1.1
Mode: TASK_REFINEMENT
Execution Model: 5.4
Rules: USE_SPEC_AND_TASK_AS_SOURCE_OF_TRUTH_NO_IMPLEMENTATION_RELEASE_ONE_TARGET_TASK
Expected Output: TASK_REFINED_PLUS_PRECHECK_HANDOFF
