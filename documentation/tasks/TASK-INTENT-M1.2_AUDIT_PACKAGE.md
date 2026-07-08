# AUDIT_PACKAGE

Generated: 2026-07-08 12:15:24 UTC

## Goal

Final review package for TASK-INTENT-M1.2 auxiliary classifier integration and post-debug recall parity

## Scope Rules

- Audit the provided package and changed artifacts only.
- Do not rely on development chat history.
- Verify cost, caching, skill quality, safety scope, and validation evidence.
- On re-audit, review the blocker delta first before widening scope.
- If scoped paths were provided, treat them as the audit diff boundary.

## Bound Audit Inputs

- Spec: documentation/Cursor specs/INTENT_ENGINE_HERMES_INSPIRED_UPGRADE_PLAN.md §5.6
- Task File: documentation/tasks/TASK-INTENT-M1_auxiliary_action_subject_classifier.md
- Backlog Item: N/A WITH REASON - No backlog marker provided.
- Pre-Implementation Check: documentation/tasks/TASK-INTENT-M1.2_preimplementation_check.md
- Manual Janus Evidence: PRESENT - 2026-07-08 live retest PASS on GPT and Gemini for 'Was weisst du ueber Chris?' after DB cleanup and provider-path fallback fix.
- Pipeline Completion Status: remaining tasks none; implementation complete yes

## Backlog Item

```text
N/A WITH REASON - No backlog source or marker provided.
```

## Task Acceptance Scope

```text
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
```

## Pre-Implementation Check

```text
PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-INTENT-M1.2
Target Subtask: N/A
Task: documentation/tasks/TASK-INTENT-M1_auxiliary_action_subject_classifier.md
Spec: documentation/Cursor specs/INTENT_ENGINE_HERMES_INSPIRED_UPGRADE_PLAN.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: integrate the already-delivered auxiliary classifier into `detect_all_intents()`, apply the spec merge rules, preserve the safety veto, and add bounded regressions without claiming any benchmark uplift yet.
- Artifact identity is consistent across the source spec section 5.6, the compiled task artifact `documentation/tasks/TASK-INTENT-M1_auxiliary_action_subject_classifier.md`, and the released handoff `documentation/tasks/TASK-INTENT-M1.2_task_breakdown.md`.
- The affected file cluster is concrete and intentionally limited to the live intent engine, the already-created classifier/config files, and focused regression surfaces for calendar and action-subject coverage.
- Risk is MEDIUM because this slice touches the live intent routing seam, but the boundary is tight: no benchmark-proof work, no staging flag flip, no Memory A/B scope, and no transport/provider-product refactor.
Affected Files:
- backend/services/orchestrator/intent_engine.py
- backend/services/orchestrator/intent_aux_classifier.py
- backend/services/orchestrator/intent_config.py
- backend/tests/test_calendar_routing_fix.py
- backend/tests/test_intent_aux_classifier.py
- backend/tests/test_intent_action_subject_mapping.py
Evidence Focus:
- python -m pytest backend/tests/test_intent_aux_classifier.py backend/tests/test_intent_action_subject_mapping.py -q
- python -m pytest backend/tests/test_calendar_routing_fix.py -q
- python -m py_compile backend/services/orchestrator/intent_engine.py backend/services/orchestrator/intent_aux_classifier.py backend/services/orchestrator/intent_config.py
- git diff --check -- backend/services/orchestrator/intent_engine.py backend/services/orchestrator/intent_aux_classifier.py backend/services/orchestrator/intent_config.py backend/tests/test_calendar_routing_fix.py backend/tests/test_intent_aux_classifier.py backend/tests/test_intent_action_subject_mapping.py documentation/tasks/TASK-INTENT-M1.2_preimplementation_check.md documentation/tasks/TASK-INTENT-M1.2_task_breakdown.md documentation/tasks/TASK-INTENT-M1_auxiliary_action_subject_classifier.md
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest backend/tests/test_intent_aux_classifier.py backend/tests/test_intent_action_subject_mapping.py -q
- python -m pytest backend/tests/test_calendar_routing_fix.py -q
- python -m py_compile backend/services/orchestrator/intent_engine.py backend/services/orchestrator/intent_aux_classifier.py backend/services/orchestrator/intent_config.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/Cursor specs/INTENT_ENGINE_HERMES_INSPIRED_UPGRADE_PLAN.md
- documentation/tasks/TASK-INTENT-M1_auxiliary_action_subject_classifier.md
- documentation/tasks/TASK-INTENT-M1.2_task_breakdown.md
- documentation/test-runs/INTENT_BENCHMARK_BASELINE.md
- backend/services/orchestrator/intent_engine.py
- backend/services/orchestrator/intent_aux_classifier.py
Drop Context:
- sealed TASK-INTENT-M1.1 implementation details beyond the delivered contract surface
- later TASK-INTENT-M1.3 benchmark uplift and staged enablement work
- Memory A/B roadmap work
- delegation, transport, OAuth, and OpenRouter roadmap work
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
User Action: Say `ok` to start implementation of `TASK-INTENT-M1.2` with the bound scope and evidence gate above.
```

## Changed Files

```text
M backend/services/orchestrator/execution_engine.py
 M backend/services/orchestrator/intent_engine.py
 M backend/tests/integration/test_pet_recall_chat_path.py
 M backend/tests/test_calendar_routing_fix.py
 M backend/tests/test_provider_auth_fallback.py
?? backend/services/orchestrator/intent_aux_classifier.py
?? backend/services/orchestrator/intent_config.py
?? backend/tests/test_intent_action_subject_mapping.py
?? backend/tests/test_intent_aux_classifier.py
?? documentation/tasks/TASK-INTENT-M1.2_execution_result.md
?? documentation/tasks/TASK-INTENT-M1.2_validation_summary.md
?? documentation/test-runs/TASK-INTENT-M1.2_debug_gemini_contact_recall_fallback_2026-07-08.md
?? documentation/test-runs/TASK-INTENT-M1.2_debug_live_db_contamination_cleanup_2026-07-08.md
```

## Artifact Inventory

```text
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-INTENT-M1.2_execution_result.md (5247 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-INTENT-M1.2_validation_summary.md (2163 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-INTENT-M1.2_preimplementation_check.md (4292 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-INTENT-M1.2_task_breakdown.md (2864 bytes)
FILE C:\KI\Janus-Projekt\documentation\test-runs\INTENT_BENCHMARK_BASELINE.md (5340 bytes)
FILE C:\KI\Janus-Projekt\documentation\test-runs\TASK-INTENT-M1.2_debug_live_db_contamination_cleanup_2026-07-08.md (3851 bytes)
FILE C:\KI\Janus-Projekt\documentation\test-runs\TASK-INTENT-M1.2_debug_gemini_contact_recall_fallback_2026-07-08.md (3892 bytes)
FILE C:\KI\Janus-Projekt\backend\services\orchestrator\intent_engine.py (91183 bytes)
FILE C:\KI\Janus-Projekt\backend\services\orchestrator\intent_aux_classifier.py (15188 bytes)
FILE C:\KI\Janus-Projekt\backend\services\orchestrator\intent_config.py (1466 bytes)
FILE C:\KI\Janus-Projekt\backend\services\orchestrator\execution_engine.py (205937 bytes)
FILE C:\KI\Janus-Projekt\backend\tests\test_calendar_routing_fix.py (18696 bytes)
FILE C:\KI\Janus-Projekt\backend\tests\test_intent_aux_classifier.py (5748 bytes)
FILE C:\KI\Janus-Projekt\backend\tests\test_intent_action_subject_mapping.py (2485 bytes)
FILE C:\KI\Janus-Projekt\backend\tests\test_provider_auth_fallback.py (8771 bytes)
FILE C:\KI\Janus-Projekt\backend\tests\integration\test_pet_recall_chat_path.py (8969 bytes)
```

## Diff Summary

```text
backend/services/orchestrator/execution_engine.py  |  22 +-
 backend/services/orchestrator/intent_engine.py     | 177 ++++++++++++++-
 .../tests/integration/test_pet_recall_chat_path.py | 122 ++++++++++-
 backend/tests/test_calendar_routing_fix.py         | 238 +++++++++++++++++++++
 backend/tests/test_provider_auth_fallback.py       |  26 +++
 5 files changed, 577 insertions(+), 8 deletions(-)
```

## Validation

```text
TASK-INTENT-M1.2 VALIDATION SUMMARY

Automated checks:
- `python -m pytest backend/tests/test_intent_aux_classifier.py backend/tests/test_intent_action_subject_mapping.py -q`: PASS
- `python -m pytest backend/tests/test_calendar_routing_fix.py -q`: PASS
- `python -m py_compile backend/services/orchestrator/intent_engine.py backend/services/orchestrator/intent_aux_classifier.py backend/services/orchestrator/intent_config.py`: PASS
- `python -m pytest backend/tests/test_provider_auth_fallback.py backend/tests/integration/test_pet_recall_chat_path.py -q`: PASS (`12 passed`)
- `python -m py_compile backend/services/orchestrator/execution_engine.py`: PASS
- `git diff --check -- backend/services/orchestrator/intent_engine.py backend/services/orchestrator/intent_aux_classifier.py backend/services/orchestrator/intent_config.py backend/services/orchestrator/execution_engine.py backend/tests/test_calendar_routing_fix.py backend/tests/test_intent_aux_classifier.py backend/tests/test_intent_action_subject_mapping.py backend/tests/test_provider_auth_fallback.py backend/tests/integration/test_pet_recall_chat_path.py documentation/tasks/TASK-INTENT-M1.2_execution_result.md documentation/test-runs/TASK-INTENT-M1.2_debug_live_db_contamination_cleanup_2026-07-08.md documentation/test-runs/TASK-INTENT-M1.2_debug_gemini_contact_recall_fallback_2026-07-08.md documentation/ai/CURRENT_STATE.md documentation/codex/SKILL_USAGE_LOG.md`: PASS

Manual Janus evidence:
- Initial manual failure on `2026-07-08` was invalidated because the local live DB contained unsupported Chris appearance/style facts.
- Live DB cleanup completed and documented in `documentation/test-runs/TASK-INTENT-M1.2_debug_live_db_contamination_cleanup_2026-07-08.md`.
- Provider-path fix completed and documented in `documentation/test-runs/TASK-INTENT-M1.2_debug_gemini_contact_recall_fallback_2026-07-08.md`.
- Final manual retest on `2026-07-08`:
  - GPT `Was weisst du ueber Chris?`: PASS, only local preference/interest facts.
  - Gemini `Was weisst du ueber Chris?`: PASS, only local preference/interest facts.

Result:
- M1.2 validation evidence is complete and ready for final audit.
```

## Notes

No additional notes provided.

## Risks

Medium bounded risk: live intent routing seam changed, but feature flag default-off parity, focused regressions, startup regression fix, live DB contamination cleanup, and Gemini recall fallback hardening are all evidenced. Known local vector-model dependency warning appeared during integration tests but did not affect the targeted recall path.

## Open Issues

No blocking open issues inside TASK-INTENT-M1.2 scope. Wider repo worktree remains dirty outside this slice.

## Re-Audit Delta

No re-audit delta provided.

## Final Audit Handoff

```text
NEW_CHAT_HANDOFF
NEXT: janus-final-audit
MODEL: 5.5/high
PASS: C:\KI\Janus-Projekt\documentation\tasks\TASK-INTENT-M1.2_AUDIT_PACKAGE.md
ASK: Lade nur dieses Paket im neuen Chat und starte dann den Final Audit.
DROP: dev chat history
```

For bounded same-thread re-audits after a local blocker fix, `5.4/high` is acceptable when the package stays compact and the risk did not escalate.
