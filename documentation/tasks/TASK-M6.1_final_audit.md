# FINAL AUDIT - TASK-M6.1 single MoA model hierarchy

FINAL AUDIT RESULT: PASS WITH FIXES

Audit Model To Use: 5.6 Terra/high

Canonical State: PASS

## Audit Scope

- Spec: `documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md`, Section 3.4 and approved Phase-A migration decision only.
- Task: `documentation/tasks/TASK-M6_transport_phase_a.md`, `TASK-M6.1` only.
- Backlog Item: N/A WITH REASON - this infrastructure epic is bound by the M6 Spec and task artifact.
- TestSpec/TestRun: N/A WITH REASON - the precheck selected focused backend regressions; no separate TestSpec/TestRun exists for this bounded implementation task.
- Changed Files: `backend/llm_providers/shared/moa.py`, `backend/services/chat_orchestrator.py`, `backend/llm_providers/gemini/gateway.py`, `backend/tests/test_moa_routing.py`, `backend/tests/test_model_hierarchy_single_source.py`, and the bound M6.1 evidence artifacts.

## Runtime Note

- Provider-routing work normally requires `5.6 Sol/high` when runtime-supported.
- This audit used `5.6 Terra/high` because the active ChatGPT Codex account cannot start Sol.
- Failure code for the model fallback: `SOL_UNAVAILABLE_FOR_CHATGPT_CODEX_ACCOUNT`.

## Testmatrix

- `python -m pytest --noconftest backend/tests/test_model_hierarchy_single_source.py -q`: PASS, 3 tests.
- `python -m pytest --noconftest backend/tests/test_moa_routing.py -q`: PASS, 13 tests.
- `python -m py_compile backend/llm_providers/shared/moa.py backend/services/chat_orchestrator.py backend/llm_providers/gemini/gateway.py`: PASS.
- Scoped `git diff --check`: PASS.
- Runtime hierarchy-definition scan: PASS - `MOA_MODEL_HIERARCHY` is the only definition in the bound paths.
- Stale `ChatOrchestrator.MODEL_HIERARCHY` and `self.MODEL_HIERARCHY` consumer scan: PASS - no matches.
- Manual Janus evidence: PASS - Gemini answered `Suche aktuelle Nachrichten zu Berlin.` on `2026-07-11 15:34 +02:00` with five curated current-news entries and the expected RSS/websearch-fallback explanation, without import, circular-dependency, provider-fallback, or degraded error output.
- Regular pytest collection including `backend/tests/test_calendar_routing_fix.py`: N/A WITH REASON - collection is independently blocked before tests run by the local ChromaDB SQLite panic in `backend/tests/conftest.py`. The isolated target tests cover the changed hierarchy contract directly.

## Findings

- P3, non-blocking: `backend/llm_providers/shared/moa.py` still contains the obsolete comment that Ollama has no tier hierarchy. The approved mapping now defines Ollama tiers. This cannot affect runtime behavior, but the comment must be removed or corrected before `TASK-M6.2` to prevent future maintenance drift.

## Residual Risks

- Full project pytest collection remains unavailable until the independent local ChromaDB SQLite environment panic is repaired.
- The current M6 worktree is local and uncommitted. No remote, including `origin/codex-sync`, contains this newest state.
- The parent M6 transport Spec remains in progress because Phase-A tasks `T-A2` through `T-A5` are deliberately separate and unimplemented. This audit closes `TASK-M6.1` only.

NEXT_STEP
Target Skill: janus-documentation-update
Canonical State: HANDOFF
Required Artifacts: `documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md`, `documentation/tasks/TASK-M6_transport_phase_a.md`, `documentation/tasks/TASK-M6.1_task_breakdown.md`, `documentation/tasks/TASK-M6.1_preimplementation_check.md`, `documentation/tasks/TASK-M6.1_execution_result.md`, `documentation/tasks/TASK-M6.1_AUDIT_PACKAGE.md`, `documentation/tasks/TASK-M6.1_final_audit.md`
Evidence Paths: `backend/llm_providers/shared/moa.py`, `backend/services/chat_orchestrator.py`, `backend/llm_providers/gemini/gateway.py`, `backend/tests/test_model_hierarchy_single_source.py`, `backend/tests/test_moa_routing.py`, `documentation/tasks/TASK-M6.1_AUDIT_PACKAGE.md`
Failure Code: N/A
Changed Files: `backend/llm_providers/shared/moa.py`, `backend/services/chat_orchestrator.py`, `backend/llm_providers/gemini/gateway.py`, `backend/tests/test_moa_routing.py`, `backend/tests/test_model_hierarchy_single_source.py`, and bound M6.1 evidence artifacts
Decision: HANDOFF
Reason: FINAL AUDIT RESULT PASS WITH FIXES; documentation sync is required. The single P3 source-comment correction is non-blocking but must be completed before the next M6 implementation task.
Recommended Model: 5.6 Terra
Recommended Intelligence: medium
Next User Action: Say `ok` to start janus-documentation-update for `TASK-M6.1`.
