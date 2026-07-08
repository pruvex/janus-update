# AUDIT_PACKAGE

Generated: 2026-07-08 14:25:54 UTC

## Goal

Final audit package for TASK-MEM-M1.1 bounded Memory Phase A+B hot-layer-cap plus on-demand injection slice.

## Scope Rules

- Audit the provided package and changed artifacts only.
- Do not rely on development chat history.
- Verify cost, caching, skill quality, safety scope, and validation evidence.
- On re-audit, review the blocker delta first before widening scope.
- If scoped paths were provided, treat them as the audit diff boundary.

## Bound Audit Inputs

- Spec: documentation/Cursor specs/MEMORY_HERMES_INSPIRED_UPGRADE_PLAN.md
- Task File: documentation/tasks/TASK-MEM-M1_memory_phase_ab_hot_layer_caps_and_on_demand_injection.md
- Backlog Item: N/A WITH REASON - No backlog marker provided.
- Pre-Implementation Check: documentation/tasks/TASK-MEM-M1.1_preimplementation_check.md
- Manual Janus Evidence: PRESENT - PASS on 2026-07-08 for GPT and Gemini: weather with personal-scope hint preserved and nut-allergy guidance remained safe.
- Pipeline Completion Status: remaining tasks none; implementation complete yes

## Backlog Item

```text
N/A WITH REASON - No backlog source or marker provided.
```

## Task Acceptance Scope

```text
TASK-MEM-M1
- Source Spec: `documentation/Cursor specs/MEMORY_HERMES_INSPIRED_UPGRADE_PLAN.md`
- Backlog Item: `N/A`
- Feature: Memory Phase A+B Hot-Layer-Caps and On-Demand Injection
- Generated At: 2026-07-08

## Generated Tasks

### TASK-MEM-M1.1 Implement Memory Phase A+B as one bounded guarded retrieval slice
- Ziel:
  - Fuehre Hot-Layer-Caps und On-Demand Memory Injection als einen kleinen, sicheren Memory-V2-Produktionsslice ein, ohne Session-Search, Frozen Core, Intent M2 oder Provider-Transport zu beruehren.
- Scope:
  - Nur Core-Cap-Logik, On-Demand-Gating fuer allgemeine Memory-Injection, benoetigte Observability/Config-Wiring und fokussierte Regressionen fuer die Retrieval-/Orchestrator-Pfade.
  - Kein Session-Search, kein Frozen Core, keine Export-API, keine neuen Provider-/Transportpfade, keine Recall-gap-Implementierung fuer Intent M1.
- Files:
  - `backend/services/memory/retrieval_service.py`
  - `backend/services/memory_budget.py`
  - `backend/services/memory_observability.py`
  - `backend/services/chat_orchestrator.py`
  - `backend/services/orchestrator/intent_engine.py` (nur wenn ein bestehendes Intent-Signal minimal wiederverwendet werden muss)
  - `backend/tests/test_memory_hot_layer_cap.py`
  - `backend/tests/test_memory_on_demand_injection.py`
  - bestehende fokussierte Memory-Regressionen, falls direkt betroffen
- Steps:
  1. Fuehre Flag-gesteuerte Hot-Layer-Caps fuer Core-Memory-Slots ein, inklusive Protected-Tags fuer Health/Medical und einer klaren Drop-Metrik.
  2. Extrahiere ein kleines `should_inject_memory(...)`-Gate fuer personal/recall-nahe Queries und binde es vor der allgemeinen Retrieval-Injection ein.
  3. Halte Health-Injector und bestehende Safety-/Medical-Pfade ausserhalb des neuen allgemeinen Injection-Gates.
  4. Ergaenze fokussierte Unit-/Regressionstests fuer Cap-Verhalten, Protected-Core-Fakten, Flag-off-Paritaet und Wetter-vs-personal Grenzfaelle.
- Acceptance Criteria:
  - `core_always`-Slots bleiben bei aktivem Flag innerhalb des konfigurierten Budgets; Protected Health/Medical-Slots werden nicht verdraengt.
  - Allgemeine Queries wie Wetter/externen Kontext ziehen bei aktivem On-Demand-Flag keine unnoetige Memory-Injection.
  - Personal-/Recall-nahe Queries und Wohnort-/Personen-Hinweise aktivieren Memory weiterhin korrekt.
  - Health-/Medical-Schutzpfade bleiben unveraendert aktiv.
  - Beide Flags defaulten auf `false`, und Flag-`off` behaelt das bisherige Verhalten bei.
- Tests:
  - `python -m pytest backend/tests/test_memory_hot_layer_cap.py -v`
  - `python -m pytest backend/tests/test_memory_on_demand_injection.py -v`
  - `python -m pytest backend/tests/test_memory_diamond.py backend/tests/test_memory_regression.py backend/tests/test_memory_tools.py backend/tests/test_memory_retrieval_relevance_priority.py -q`
  - `python -m py_compile backend/services/memory/retrieval_service.py backend/services/memory_budget.py backend/services/memory_observability.py backend/services/chat_orchestrator.py`
- Model: 5.4
- Reason:
  - Die Roadmap erlaubt MA/MB parallel zu M1, und beide Aenderungen bilden einen kleinen zusammenhaengenden Retrieval-/Injection-Sicherheitsblock, der ohne Session-Search oder Intent-M2-Entscheidungen ausgeliefert werden kann.
```

## Pre-Implementation Check

```text
PRE-CHECK RESULT
PRE-CHECK PASSED

NEXT: janus-executioner
Target Task: TASK-MEM-M1.1
Target Subtask: N/A
Task: documentation/tasks/TASK-MEM-M1_memory_phase_ab_hot_layer_caps_and_on_demand_injection.md
Spec: documentation/Cursor specs/MEMORY_HERMES_INSPIRED_UPGRADE_PLAN.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: implement Memory Phase A Hot-Layer-Caps and Phase B On-Demand Memory Injection as one guarded retrieval slice with explicit flag-off parity, protected health slots, and no Session-Search/Frozen-Core expansion.
- Artifact identity is consistent across the Memory spec sections 4 and 5, the roadmap M1 Memory A+B entry, the compiled task artifact `documentation/tasks/TASK-MEM-M1_memory_phase_ab_hot_layer_caps_and_on_demand_injection.md`, and the released handoff `documentation/tasks/TASK-MEM-M1.1_task_breakdown.md`.
- The affected file cluster is concrete and intentionally bounded to memory retrieval/injection services, config/observability support, and focused memory regression tests.
- Risk is MEDIUM because this slice changes live memory-injection behavior and core-slot budgeting, but it remains bounded by feature flags and explicit medical/health safety constraints.
Affected Files:
- backend/services/memory/retrieval_service.py
- backend/services/memory_budget.py
- backend/services/memory_observability.py
- backend/services/chat_orchestrator.py
- backend/services/orchestrator/intent_engine.py
- backend/tests/test_memory_hot_layer_cap.py
- backend/tests/test_memory_on_demand_injection.py
- backend/tests/test_memory_diamond.py
- backend/tests/test_memory_regression.py
- backend/tests/test_memory_tools.py
- backend/tests/test_memory_retrieval_relevance_priority.py
Evidence Focus:
- python -m pytest backend/tests/test_memory_hot_layer_cap.py -v
- python -m pytest backend/tests/test_memory_on_demand_injection.py -v
- python -m pytest backend/tests/test_memory_diamond.py backend/tests/test_memory_regression.py backend/tests/test_memory_tools.py backend/tests/test_memory_retrieval_relevance_priority.py -q
- python -m py_compile backend/services/memory/retrieval_service.py backend/services/memory_budget.py backend/services/memory_observability.py backend/services/chat_orchestrator.py
- git diff --check -- backend/services/memory/retrieval_service.py backend/services/memory_budget.py backend/services/memory_observability.py backend/services/chat_orchestrator.py backend/services/orchestrator/intent_engine.py backend/tests/test_memory_hot_layer_cap.py backend/tests/test_memory_on_demand_injection.py documentation/tasks/TASK-MEM-M1_memory_phase_ab_hot_layer_caps_and_on_demand_injection.md documentation/tasks/TASK-MEM-M1.1_task_breakdown.md documentation/tasks/TASK-MEM-M1.1_preimplementation_check.md documentation/ai/CURRENT_STATE.md documentation/codex/SKILL_USAGE_LOG.md
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest backend/tests/test_memory_hot_layer_cap.py -v
- python -m pytest backend/tests/test_memory_on_demand_injection.py -v
- python -m pytest backend/tests/test_memory_diamond.py backend/tests/test_memory_regression.py backend/tests/test_memory_tools.py backend/tests/test_memory_retrieval_relevance_priority.py -q
- python -m py_compile backend/services/memory/retrieval_service.py backend/services/memory_budget.py backend/services/memory_observability.py backend/services/chat_orchestrator.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/Cursor specs/MEMORY_HERMES_INSPIRED_UPGRADE_PLAN.md
- documentation/Cursor specs/ROADMAP_EPIC_ORDER.md
- documentation/tasks/TASK-MEM-M1_memory_phase_ab_hot_layer_caps_and_on_demand_injection.md
- documentation/tasks/TASK-MEM-M1.1_task_breakdown.md
- backend/services/memory/retrieval_service.py
- backend/services/chat_orchestrator.py
Drop Context:
- sealed Intent M1 implementation details except the explicit Recall caveat
- Session-Search, Frozen Core, and USER.md export phases
- Transport, OAuth, OpenRouter, and delegation hardening work
- unrelated dirty worktree changes
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The MA/MB slice is now precheck-ready as one bounded memory retrieval/injection hardening block with explicit flag, health-safety, and regression evidence gates.
User Action: Say `ok` to start implementation of `TASK-MEM-M1.1` with the bound scope and evidence gate above.
```

## Changed Files

```text
M backend/services/chat_orchestrator.py
 M backend/services/memory/retrieval_service.py
 M backend/services/memory_budget.py
 M backend/services/memory_observability.py
 M documentation/ai/CURRENT_STATE.md
 M documentation/codex/SKILL_USAGE_LOG.md
?? backend/tests/test_memory_hot_layer_cap.py
?? backend/tests/test_memory_on_demand_injection.py
?? documentation/tasks/TASK-MEM-M1.1_execution_result.md
```

## Artifact Inventory

```text
FILE C:\KI\Janus-Projekt\backend\services\memory\retrieval_service.py (41913 bytes)
FILE C:\KI\Janus-Projekt\backend\services\memory_budget.py (25067 bytes)
FILE C:\KI\Janus-Projekt\backend\services\memory_observability.py (2991 bytes)
FILE C:\KI\Janus-Projekt\backend\services\chat_orchestrator.py (275466 bytes)
FILE C:\KI\Janus-Projekt\backend\tests\test_memory_hot_layer_cap.py (2465 bytes)
FILE C:\KI\Janus-Projekt\backend\tests\test_memory_on_demand_injection.py (3520 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-MEM-M1.1_execution_result.md (5332 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-MEM-M1.1_preimplementation_check.md (5039 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-MEM-M1.1_task_breakdown.md (2540 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-MEM-M1_memory_phase_ab_hot_layer_caps_and_on_demand_injection.md (3249 bytes)
```

## Diff Summary

```text
backend/services/chat_orchestrator.py        |  38 ++-
 backend/services/memory/retrieval_service.py | 345 ++++++++++++++++++++++++---
 backend/services/memory_budget.py            |  70 +++++-
 backend/services/memory_observability.py     |   2 +
 documentation/ai/CURRENT_STATE.md            | 172 +++++++++++++
 documentation/codex/SKILL_USAGE_LOG.md       |   5 +
 6 files changed, 588 insertions(+), 44 deletions(-)
```

## Validation

```text
Validation evidence not provided.
```

## Notes

TASK EXECUTION RESULT
Canonical State: NEEDS_INFO
Target Task: TASK-MEM-M1.1
Changed Files:
- backend/services/memory/retrieval_service.py
- backend/services/memory_budget.py
- backend/services/memory_observability.py
- backend/services/chat_orchestrator.py
- backend/tests/test_memory_hot_layer_cap.py
- backend/tests/test_memory_on_demand_injection.py
- documentation/tasks/TASK-MEM-M1.1_execution_result.md
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md
Executed Checks:
- `python -m py_compile backend/services/memory/retrieval_service.py backend/services/memory_budget.py backend/services/memory_observability.py backend/services/chat_orchestrator.py`
- `python -m pytest backend/tests/test_memory_hot_layer_cap.py -v`
- `python -m pytest backend/tests/test_memory_on_demand_injection.py -v`
- `python -m pytest backend/tests/test_memory_hot_layer_cap.py -v backend/tests/test_memory_on_demand_injection.py -v backend/tests/test_memory_diamond.py backend/tests/test_memory_regression.py backend/tests/test_memory_tools.py backend/tests/test_memory_retrieval_relevance_priority.py -q`
- `git diff --check -- backend/services/memory/retrieval_service.py backend/services/memory_budget.py backend/services/memory_observability.py backend/services/chat_orchestrator.py backend/tests/test_memory_hot_layer_cap.py backend/tests/test_memory_on_demand_injection.py backend/tests/test_memory_diamond.py backend/tests/test_memory_regression.py backend/tests/test_memory_tools.py backend/tests/test_memory_retrieval_relevance_priority.py documentation/ai/CURRENT_STATE.md documentation/codex/SKILL_USAGE_LOG.md`
Auto-Verification:
- Status: PASS
- Evidence:
  - `retrieve_diamond_slots()` now supports a bounded `include_general_memory=False` path so generic/external queries can skip general retrieval while the health injector still runs.
  - `should_inject_memory(...)` now keeps personal-scope queries such as `wo ich wohne` eligible for retrieval while blocking generic weather/external-context requests.
  - High-priority memory slots are now tiered more explicitly (`core_always` vs. `core_identity`) so the bounded hot-layer cap can run on the always-on core slice instead of the full memory pool.
  - `select_slots_by_budget()` now applies the Phase-A hot-layer cap behind `MEMORY_HOT_LAYER_CAP_ENABLED`, preserves protected `health`/`medical` slots, and records `slots_dropped_core_cap`.
  - `format_memory_context()` now renders `health_mandatory` slots explicitly instead of letting that safety tier disappear from the formatted context block.
  - Focused new suites passed for protected core-cap behavior, weather-vs-personal gating, and health-only retrieval without query-embedding dependency; the bound legacy memory regression block stayed green (`68 passed`).
Manual Janus Validation Gate:
- Status: PASS
- Test Example: Starte Janus normal und teste nacheinander im Chat `Wie wird das Wetter in Berlin, wo ich wohne?` und danach `Ich habe eine Nussallergie, was soll ich beim Essen beachten?`
- Expected Result: Beim Wetter-Prompt darf Janus weiterhin den Wohnortbezug sinnvoll nutzen, statt die persönliche Memory-Schicht komplett zu verlieren. Beim Allergie-Prompt muss Janus weiterhin die Gesundheits-/Allergie-Information sicher berücksichtigen und darf sie nicht wegen On-Demand-Gating unterschlagen.
- Recorded Result: PASS am `2026-07-08` auf GPT und Gemini. Wetter mit Wohnortbezug blieb sinnvoll (`Wie wird das Wetter in Köln, wo ich wohne?`), und die Allergie-Antwort blieb sicher und alltagstauglich (`Ich habe eine Nussallergie, was soll ich beim Essen beachten?`) ohne erkennbaren Verlust der Health-/Medical-Schutzlogik.
- If Failed: route to janus-debug
- If Passed: route to janus-final-audit

NEXT_STEP
Target Skill: janus-final-audit
Canonical State: HANDOFF
Required Artifacts:
- documentation/Cursor specs/MEMORY_HERMES_INSPIRED_UPGRADE_PLAN.md
- documentation/tasks/TASK-MEM-M1_memory_phase_ab_hot_layer_caps_and_on_demand_injection.md
- documentation/tasks/TASK-MEM-M1.1_task_breakdown.md
- documentation/tasks/TASK-MEM-M1.1_preimplementation_check.md
- documentation/tasks/TASK-MEM-M1.1_execution_result.md
Audit Package:
- N/A until the Manual Janus Validation Gate is confirmed PASS
Evidence Paths:
- backend/services/memory/retrieval_service.py
- backend/services/memory_budget.py
- backend/services/memory_observability.py
- backend/services/chat_orchestrator.py
- backend/tests/test_memory_hot_layer_cap.py
- backend/tests/test_memory_on_demand_injection.py
Failure Code: N/A
Changed Files:
- backend/services/memory/retrieval_service.py
- backend/services/memory_budget.py
- backend/services/memory_observability.py
- backend/services/chat_orchestrator.py
- backend/tests/test_memory_hot_layer_cap.py
- backend/tests/test_memory_on_demand_injection.py
- documentation/tasks/TASK-MEM-M1.1_execution_result.md
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md
Decision: HANDOFF
Reason: The bounded Memory A+B slice is code-complete, locally green, and the required Manual Janus Validation Gate now passed on both GPT and Gemini.
Recommended Model: 5.4
Recommended Intelligence: medium
New Chat: no
Next User Action: Run the two manual Janus prompts above; if both behave as expected, route this artifact set to `janus-final-audit`.

## Risks

Known residual risk is limited to normal memory-runtime regression risk; local validation and manual Janus evidence are green. The separate local vector-model dependency warning (tokenizers>=0.21,<0.22) pre-existed this slice and did not block the bounded memory suites.

## Open Issues

No blocking open issues inside TASK-MEM-M1.1. Session-Search, Frozen Core, USER.md export, and later memory phases remain intentionally out of scope.

## Re-Audit Delta

No re-audit delta provided.

## Final Audit Handoff

```text
NEW_CHAT_HANDOFF
NEXT: janus-final-audit
MODEL: 5.5/high
PASS: C:\KI\Janus-Projekt\documentation\tasks\TASK-MEM-M1.1_AUDIT_PACKAGE.md
ASK: Lade nur dieses Paket im neuen Chat und starte dann den Final Audit.
DROP: dev chat history
```

For bounded same-thread re-audits after a local blocker fix, `5.4/high` is acceptable when the package stays compact and the risk did not escalate.
