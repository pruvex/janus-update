# AUDIT_PACKAGE

Generated: 2026-07-08 14:56:10 UTC

## Goal

Final audit package for TASK-INTENT-M2.1 confidence-based intent routing and ambiguity softening.

## Scope Rules

- Audit the provided package and changed artifacts only.
- Do not rely on development chat history.
- Verify cost, caching, skill quality, safety scope, and validation evidence.
- On re-audit, review the blocker delta first before widening scope.
- If scoped paths were provided, treat them as the audit diff boundary.

## Bound Audit Inputs

- Spec: documentation/Cursor specs/INTENT_ENGINE_HERMES_INSPIRED_UPGRADE_PLAN.md section 6 / Roadmap M2
- Task File: documentation/tasks/TASK-INTENT-M2_confidence_routing_and_regex_freeze.md
- Backlog Item: N/A WITH REASON - No backlog marker provided.
- Pre-Implementation Check: documentation/tasks/TASK-INTENT-M2.1_preimplementation_check.md
- Manual Janus Evidence: N/A WITH REASON - routing/benchmark hardening slice; bound acceptance is deterministic pytest plus benchmark proof, no separate manual product walkthrough required.
- Pipeline Completion Status: TASK-INTENT-M2.1 implementation complete yes; validation complete yes; remaining tasks none for this slice; M2.2 remains separate.

## Backlog Item

```text
N/A WITH REASON - No backlog source or marker provided.
```

## Task Acceptance Scope

```text
TASK-INTENT-M2
- Source Spec: `documentation/Cursor specs/INTENT_ENGINE_HERMES_INSPIRED_UPGRADE_PLAN.md`
- Backlog Item: `N/A`
- Feature: Intent Phase 2 Confidence Routing and Regex Freeze
- Generated At: 2026-07-08

## Generated Tasks

### TASK-INTENT-M2.1 Implement confidence-based intent routing and soften ambiguity hard-blocks
- Ziel:
  - Ersetze den harten Ambiguity-Block fuer mittlere Intent-Sicherheit durch ein kontrolliertes Confidence-Routing, damit Contact/Pet-Facts und Recall-Pfade nicht unnoetig mit `disable_tools=True` abgewuergt werden.
- Scope:
  - Nur Confidence-Routing in Intent-/Dispatcher-Pfad, die direkt benoetigten Tests und die gebundene Evidenz fuer Ambiguity-FP-Reduktion gegen die bestehende M0/M1-Benchmark-Basis.
  - Kein Entity-First-Routing, kein neuer Auxiliary-Classifier-Scope, kein Transport, kein Workflow-Offer und kein Regex-Freeze-Schreibschutz in dieser Slice.
- Files:
  - `backend/services/orchestrator/execution_dispatcher.py`
  - `backend/services/orchestrator/intent_engine.py`
  - `backend/tests/test_intent_confidence_routing.py`
  - `backend/tests/test_calendar_routing_fix.py`
  - `backend/tests/test_intent_benchmark.py`
  - bestehende gezielte Intent-/Routing-Regressionen, falls direkt betroffen
- Steps:
  1. Fuehre einen klaren Confidence-Pfad fuer hohe, mittlere und niedrige Intent-Sicherheit ein, der echte Mehrdeutigkeit weiter blockiert, mittlere Sicherheit aber nicht mehr pauschal in `disable_tools=True` umkippen laesst.
  2. Halte Safety-, Medical-, Consent- und Personal-Recall-Web-Guards unveraendert bindend, auch wenn der neue Confidence-Pfad aktiv ist.
  3. Ergaenze fokussierte Regressionen fuer Contact/Pet/Recall-Faelle, die bisher an Ambiguity-False-Positives haengen, sowie Guardrail-Tests fuer bestehende Calendar-/Weather-/Shopping-Pfade.
  4. Beweise die Ambiguity-FP-Verbesserung ueber den Benchmark-/Test-Pfad gegen die vorhandene M0-Baseline und den M1-Classifier-Stand.
- Acceptance Criteria:
  - Ambiguity False Positives sinken messbar im Rahmen der M2-Zielsetzung (`-30%` bis `-50%`) oder ein belastbarer Blocker ist dokumentiert.
  - Contact/Pet-Fact- und Recall-Faelle mit hoher bzw. ausreichender Sicherheit werden nicht mehr unnoetig durch `disable_tools=True` blockiert.
  - `test_calendar_routing_fix.py` bleibt vollstaendig gruen.
  - Safety-/Medical-/Consent- und Personal-Recall-Web-Guards bleiben unveraendert wirksam.
- Tests:
  - `python -m pytest backend/tests/test_intent_confidence_routing.py -q`
  - `python -m pytest backend/tests/test_calendar_routing_fix.py backend/tests/test_intent_benchmark.py -q`
  - `python -m py_compile backend/services/orchestrator/execution_dispatcher.py backend/services/orchestrator/intent_engine.py`
  - `python -m backend.scripts.run_intent_benchmark --mode m2-proof --output documentation/test-runs/TASK-INTENT-M2.1_confidence_routing_2026-07-08.md`
- Model: 5.4
- Reason:
  - M2 I2 ist der naechste offene produktive Roadmap-Slice und bleibt als klarer Routing-/Guardrail-Block klein genug fuer den normalen 5.4-Workhorse-Pfad.

### TASK-INTENT-M2.2 Implement regex freeze guardrails and deprecate new fact-telling pattern growth
- Ziel:
  - Friere weiteres Regex-Wachstum kontrolliert ein und verankere den Prozesspfad, dass neue sprachliche Varianten kuenftig ueber Classifier-/Benchmark-Faelle statt neue Pattern-Listen gelöst werden.
- Scope:
  - Nur Regex-Freeze-Schalter, Kommentare/Tripwires, CI-/Test-Guardrails und direkt benoetigte Deprecation-Hinweise fuer den bestehenden Fact-Telling-/Search-Pattern-Pfad.
  - Keine neue Intent-Logik ausserhalb der Freeze- und Deprecation-Grenzen.
- Files:
  - `backend/services/orchestrator/intent_engine.py`
  - `backend/utils/intent_classifier.py`
  - `backend/tests/test_intent_regex_freeze.py`
  - ggf. kleine validator-/guardrail-nahe Testdateien, falls direkt betroffen
- Steps:
  1. Verankere den Regex-Freeze-Hinweis und die fail-closed Guardrails fuer neue `_FACT_TELLING_PATTERNS`-/aehnliche Pattern-Erweiterungen.
  2. Markiere den alten Search-/Regex-Hilfspfad sauber als deprecation-only, ohne das bestehende Laufzeitverhalten bei deaktivierten Flags zu brechen.
  3. Ergaenze fokussierte Tests, die den Freeze-/Tripwire-Pfad und die weiterhin erlaubten Bugfix-Grenzen klar absichern.
- Acceptance Criteria:
  - Neue Pattern-Wachstumsfaelle werden ueber den Freeze-Pfad sichtbar unterbunden oder eindeutig markiert.
  - Der bestehende Intent-Pfad bleibt bei deaktivierten Freeze-/M2-Flags kompatibel.
  - Die neue Guardrail-Oberflaeche ist lokal testbar und dokumentiert, ohne Produktlogik ausserhalb des Freeze-Scopes zu veraendern.
- Tests:
  - `python -m pytest backend/tests/test_intent_regex_freeze.py -q`
  - `python -m py_compile backend/services/orchestrator/intent_engine.py backend/utils/intent_classifier.py`
- Model: 5.4
- Reason:
  - I3 bleibt laut Spec optional und sollte erst nach dem Confidence-Routing-Kern als separater kleiner Follow-up-Slice freigegeben werden.
```

## Pre-Implementation Check

```text
PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-INTENT-M2.1
Target Subtask: N/A
Task: documentation/tasks/TASK-INTENT-M2_confidence_routing_and_regex_freeze.md
Spec: documentation/Cursor specs/INTENT_ENGINE_HERMES_INSPIRED_UPGRADE_PLAN.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: soften the ambiguity hard-block through confidence-based routing on top of the sealed M1 auxiliary-classifier baseline, while preserving all current safety, medical, consent, and personal-recall-web guards.
- Artifact identity is consistent across Intent Spec section 6, Roadmap section 4 M2, the compiled task artifact `documentation/tasks/TASK-INTENT-M2_confidence_routing_and_regex_freeze.md`, the released handoff `documentation/tasks/TASK-INTENT-M2.1_task_breakdown.md`, and the checked-in benchmark baseline `documentation/test-runs/INTENT_BENCHMARK_BASELINE.md`.
- The affected file cluster is concrete and intentionally bounded to the intent-engine and execution-dispatcher routing seam, a new focused confidence-routing test surface, the existing calendar and benchmark regression surfaces, and the evidence artifact needed for the M2 proof run.
- Risk is MEDIUM because this slice changes live intent-routing behavior and ambiguity handling on the product path, but it stays bounded behind explicit acceptance gates and must not widen into Regex-Freeze, Entity-First routing, Memory follow-up work, Transport, OAuth, OpenRouter, or delegation hardening.
Affected Files:
- backend/services/orchestrator/execution_dispatcher.py
- backend/services/orchestrator/intent_engine.py
- backend/tests/test_intent_confidence_routing.py
- backend/tests/test_calendar_routing_fix.py
- backend/tests/test_intent_benchmark.py
- documentation/test-runs/TASK-INTENT-M2.1_confidence_routing_2026-07-08.md
Evidence Focus:
- python -m pytest backend/tests/test_intent_confidence_routing.py -q
- python -m pytest backend/tests/test_calendar_routing_fix.py backend/tests/test_intent_benchmark.py -q
- python -m py_compile backend/services/orchestrator/execution_dispatcher.py backend/services/orchestrator/intent_engine.py
- python -m backend.scripts.run_intent_benchmark --mode m2-proof --output documentation/test-runs/TASK-INTENT-M2.1_confidence_routing_2026-07-08.md
- git diff --check -- backend/services/orchestrator/execution_dispatcher.py backend/services/orchestrator/intent_engine.py backend/tests/test_intent_confidence_routing.py backend/tests/test_calendar_routing_fix.py backend/tests/test_intent_benchmark.py documentation/tasks/TASK-INTENT-M2_confidence_routing_and_regex_freeze.md documentation/tasks/TASK-INTENT-M2.1_task_breakdown.md documentation/tasks/TASK-INTENT-M2.1_preimplementation_check.md documentation/ai/CURRENT_STATE.md documentation/codex/SKILL_USAGE_LOG.md
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest backend/tests/test_intent_confidence_routing.py -q
- python -m pytest backend/tests/test_calendar_routing_fix.py backend/tests/test_intent_benchmark.py -q
- python -m py_compile backend/services/orchestrator/execution_dispatcher.py backend/services/orchestrator/intent_engine.py
- python -m backend.scripts.run_intent_benchmark --mode m2-proof --output documentation/test-runs/TASK-INTENT-M2.1_confidence_routing_2026-07-08.md
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/Cursor specs/INTENT_ENGINE_HERMES_INSPIRED_UPGRADE_PLAN.md
- documentation/Cursor specs/ROADMAP_EPIC_ORDER.md
- documentation/tasks/TASK-INTENT-M2_confidence_routing_and_regex_freeze.md
- documentation/tasks/TASK-INTENT-M2.1_task_breakdown.md
- documentation/test-runs/INTENT_BENCHMARK_BASELINE.md
- backend/services/orchestrator/execution_dispatcher.py
- backend/services/orchestrator/intent_engine.py
Drop Context:
- sealed M1 implementation details beyond the already-delivered auxiliary-classifier surface
- TASK-INTENT-M2.2 regex-freeze follow-up
- Memory A/B, Session-Search, Transport, OAuth, OpenRouter, and delegation hardening work
- unrelated dirty worktree changes
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The M2 I2 slice is now precheck-ready as one bounded confidence-routing block with explicit benchmark, regression, and safety evidence gates.
User Action: Say `ok` to start implementation of `TASK-INTENT-M2.1` with the bound scope and evidence gate above.
```

## Changed Files

```text
M backend/scripts/run_intent_benchmark.py
 M backend/services/orchestrator/execution_dispatcher.py
 M backend/services/orchestrator/intent_engine.py
 M backend/tests/test_intent_benchmark.py
?? backend/tests/test_intent_confidence_routing.py
?? documentation/tasks/TASK-INTENT-M2.1_execution_result.md
?? documentation/test-runs/TASK-INTENT-M2.1_confidence_routing_2026-07-08.md
```

## Artifact Inventory

```text
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-INTENT-M2.1_task_breakdown.md (2960 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-INTENT-M2.1_preimplementation_check.md (5000 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-INTENT-M2.1_execution_result.md (4051 bytes)
FILE C:\KI\Janus-Projekt\documentation\test-runs\TASK-INTENT-M2.1_confidence_routing_2026-07-08.md (1208 bytes)
```

## OpenRouter Evidence Pre-Review

```text
Workflow: WF-INTENT-M2.1-OR-TRIAGE-REVIEW-2026-07-08-001
Path: documentation/codex/model-routing/bounded-dispatch-runs/WF-INTENT-M2.1-OR-TRIAGE-REVIEW-2026-07-08-001/delegated_result.md
Validation Summary: documentation/codex/model-routing/bounded-dispatch-runs/WF-INTENT-M2.1-OR-TRIAGE-REVIEW-2026-07-08-001/validation_summary.json
Selected OR Model: qwen/qwen3-coder-30b-a3b-instruct
Actual OR Cost: 0.00014553
Delegated Result Status: PASS
Delegated Primary Outcome: no_blocking_issue
Delegated Classification: NOT_REPRODUCIBLE
Delegated Suggested Routing: janus-final-audit
Codex Authority Boundary: OR review is assist-only evidence; Codex remains final audit and acceptance owner.
```

## Diff Summary

```text
backend/scripts/run_intent_benchmark.py            |  71 +++++++-
 .../services/orchestrator/execution_dispatcher.py  | 181 ++++++++++++++-------
 backend/services/orchestrator/intent_engine.py     |  49 +++++-
 backend/tests/test_intent_benchmark.py             |  24 +++
 4 files changed, 263 insertions(+), 62 deletions(-)
```

## Validation

```text
Canonical State: HANDOFF
Target Task: TASK-INTENT-M2.1
Changed Files:
- backend/services/orchestrator/intent_engine.py
- backend/services/orchestrator/execution_dispatcher.py
- backend/scripts/run_intent_benchmark.py
- backend/tests/test_intent_confidence_routing.py
- backend/tests/test_intent_benchmark.py
- documentation/test-runs/TASK-INTENT-M2.1_confidence_routing_2026-07-08.md
- documentation/tasks/TASK-INTENT-M2.1_execution_result.md
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md
Executed Checks:
- `python -m pytest backend/tests/test_intent_confidence_routing.py -q`
- `python -m pytest backend/tests/test_calendar_routing_fix.py backend/tests/test_intent_benchmark.py -q`
- `python -m py_compile backend/services/orchestrator/execution_dispatcher.py backend/services/orchestrator/intent_engine.py backend/scripts/run_intent_benchmark.py`
- `python -m backend.scripts.run_intent_benchmark --mode m2-proof --output documentation/test-runs/TASK-INTENT-M2.1_confidence_routing_2026-07-08.md --write-baseline`
Auto-Verification:
- Status: PASS
- Evidence:
  - Intent detection now records bounded routing confidence from the auxiliary classifier and preserves the source for downstream ambiguity decisions.
  - Medium-confidence Contact/Pet/Recall and Calendar mutation paths can clear ambiguity without weakening the existing safety, weather, routing, realtime-search, or mail-query bypass boundaries.
  - Calendar read intents now stop carrying unnecessary ambiguity in the benchmark path when routing confidence is sufficient.
  - The benchmark CLI now supports `m2-proof` and writes the bound M2.1 evidence artifact locally.
  - The deterministic M2.1 proof improved the checked-in baseline from `81/110` (`73.6%`) to `91/110` (`82.7%`), including Calendar from `53.3%` to `66.7%`.
Manual Janus Validation Gate:
- Status: N/A WITH REASON
- Test Example: N/A - this slice is a routing/benchmark hardening block and the bound acceptance path is the deterministic pytest + benchmark evidence surface, not a separate manual product walkthrough.
- Expected Result: N/A - the required proof is the local M2 benchmark uplift plus unchanged guardrail regressions.
- If Failed: route to `janus-debug`
- If Passed: route to `janus-final-audit`

NEXT_STEP
Target Skill: janus-final-audit
Canonical State: HANDOFF
Required Artifacts:
- documentation/Cursor specs/INTENT_ENGINE_HERMES_INSPIRED_UPGRADE_PLAN.md
- documentation/tasks/TASK-INTENT-M2_confidence_routing_and_regex_freeze.md
- documentation/tasks/TASK-INTENT-M2.1_task_breakdown.md
- documentation/tasks/TASK-INTENT-M2.1_preimplementation_check.md
- documentation/tasks/TASK-INTENT-M2.1_execution_result.md
- documentation/test-runs/TASK-INTENT-M2.1_confidence_routing_2026-07-08.md
Evidence Paths:
- backend/services/orchestrator/intent_engine.py
- backend/services/orchestrator/execution_dispatcher.py
- backend/scripts/run_intent_benchmark.py
- backend/tests/test_intent_confidence_routing.py
- backend/tests/test_calendar_routing_fix.py
- backend/tests/test_intent_benchmark.py
Failure Code: N/A
Changed Files:
- backend/services/orchestrator/intent_engine.py
- backend/services/orchestrator/execution_dispatcher.py
- backend/scripts/run_intent_benchmark.py
- backend/tests/test_intent_confidence_routing.py
- backend/tests/test_intent_benchmark.py
- documentation/test-runs/TASK-INTENT-M2.1_confidence_routing_2026-07-08.md
- documentation/tasks/TASK-INTENT-M2.1_execution_result.md
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md
Decision: HANDOFF
Reason: `TASK-INTENT-M2.1` is now locally implemented with bounded confidence-routing logic, focused regression coverage, and a green deterministic benchmark proof that shows measurable ambiguity false-positive reduction without widening into M2.2 regex-freeze or other roadmap tracks.
Recommended Model: 5.5
Recommended Intelligence: high
New Chat: no
Next User Action: Continue with `janus-final-audit` for `TASK-INTENT-M2.1`, or explicitly redirect to another bounded slice.
```

## Notes

No additional notes provided.

## Risks

Medium product-routing risk bounded to intent confidence and ambiguity handling. Remaining deterministic Recall/Pet edge cases are documented as later-slice evidence, not M2.1 scope. Local benchmark command emits unrelated vector/skill-router startup warnings while completing successfully.

## Open Issues

No blocking M2.1 issue reported. TASK-INTENT-M2.2 regex-freeze and remaining Recall follow-up remain separate.

## Re-Audit Delta

No re-audit delta provided.

## Final Audit Handoff

```text
NEW_CHAT_HANDOFF
NEXT: final-skill-audit
MODEL: 5.5/high
PASS: C:\KI\Janus-Projekt\documentation\tasks\TASK-INTENT-M2.1_AUDIT_PACKAGE.md
ASK: Lade nur dieses Paket im neuen Chat und starte dann den Final Audit.
DROP: dev chat history
```

Change the model/reasoning to `5.5/high`, paste the block above into a fresh chat, write `ok`, and the final audit starts immediately.

For bounded same-thread re-audits after a local blocker fix, `5.4/high` is acceptable when the package stays compact and the risk did not escalate.
