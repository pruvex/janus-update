# AUDIT PACKAGE

## Scope
- Target Task: `TASK-INTENT-M1.1`
- Parent Task: `documentation/tasks/TASK-INTENT-M1_auxiliary_action_subject_classifier.md`
- Spec: `documentation/Cursor specs/INTENT_ENGINE_HERMES_INSPIRED_UPGRADE_PLAN.md`
- Backlog Item: `N/A`
- Precheck: `documentation/tasks/TASK-INTENT-M1.1_preimplementation_check.md`
- Execution Result: `documentation/tasks/TASK-INTENT-M1.1_execution_result.md`

## Bound Goal
- Introduce the auxiliary action/subject classifier contract, bounded provider/config wrapper, and focused unit coverage.
- Do not integrate into `detect_all_intents()`.
- Do not widen into benchmark uplift, Memory A/B, transport, OAuth, or product OpenRouter work.

## Changed Files
- `backend/services/orchestrator/intent_aux_classifier.py`
- `backend/services/orchestrator/intent_config.py`
- `backend/data/schemas_intent.py`
- `backend/tests/test_intent_aux_classifier.py`
- `backend/tests/test_intent_action_subject_mapping.py`

## Diff Summary
- Added or refined the `ActionSubjectResult` contract and fail-closed payload validation surface in `schemas_intent.py`.
- Completed the bounded auxiliary classifier module with regex fallback, circuit breaker, legacy-flag mapping, provider JSON parsing, and a default `llm_gateway` wrapper that is still isolated from the live intent engine.
- Kept the config surface explicit and flag-controlled in `intent_config.py`.
- Added focused tests for contract validation, provider output parsing, fallback behavior, circuit breaking, and action/subject compatibility mapping.

## Validation Commands And Results
- `python -m pytest backend/tests/test_intent_aux_classifier.py -q`
  - PASS (`13 passed`)
- `python -m pytest backend/tests/test_intent_action_subject_mapping.py -q`
  - PASS (`8 passed`)
- `python -m py_compile backend/services/orchestrator/intent_aux_classifier.py backend/services/orchestrator/intent_config.py backend/data/schemas_intent.py`
  - PASS
- `git diff --check -- backend/services/orchestrator/intent_aux_classifier.py backend/services/orchestrator/intent_config.py backend/data/schemas_intent.py backend/tests/test_intent_aux_classifier.py backend/tests/test_intent_action_subject_mapping.py documentation/tasks/TASK-INTENT-M1.1_execution_result.md documentation/tasks/TASK-INTENT-M1.1_AUDIT_PACKAGE.md documentation/ai/CURRENT_STATE.md documentation/codex/SKILL_USAGE_LOG.md`
  - PASS

## Evidence Paths
- `backend/services/orchestrator/intent_aux_classifier.py`
- `backend/services/orchestrator/intent_config.py`
- `backend/data/schemas_intent.py`
- `backend/tests/test_intent_aux_classifier.py`
- `backend/tests/test_intent_action_subject_mapping.py`
- `documentation/tasks/TASK-INTENT-M1.1_execution_result.md`
- `documentation/test-runs/INTENT_BENCHMARK_BASELINE.md`

## Manual Janus Evidence
- Status: `N/A WITH REASON`
- Reason: the auxiliary classifier is not yet integrated into the live `detect_all_intents()` path in M1.1, so this slice does not change observable Janus runtime behavior by itself.

## Pipeline Completion Status
- Remaining tasks none: `no`
- Bound target task complete: `yes`
- Implementation complete for this slice: `yes`
- Validation-only run: `no`
- Remaining roadmap work explicitly out of scope for this audit:
  - `TASK-INTENT-M1.2`
  - `TASK-INTENT-M1.3`

## Risks And Open Issues
- The slice is intentionally unwired; real intent-routing impact is still deferred to M1.2 and benchmark proof to M1.3.
- Live delegation evidence for this same slice showed Composer timeout and API transport-only failure; that is execution-lane evidence, not a blocker for the local Codex implementation itself.
- No live provider call was exercised as part of the local M1.1 test evidence; the provider wrapper is covered through focused unit-level seams and fail-closed behavior.

## Audit Delta Note
- This package is current for the local Codex implementation path after the bounded Cursor runs were retained as evidence only and not used for final code delivery.
