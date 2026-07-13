# AUDIT_PACKAGE

Generated: 2026-07-11 13:41:47 UTC

## Goal

Final audit TASK-M6.1 single-source MoA model hierarchy consolidation

## Scope Rules

- Audit the provided package and changed artifacts only.
- Do not rely on development chat history.
- Verify cost, caching, skill quality, safety scope, and validation evidence.
- On re-audit, review the blocker delta first before widening scope.
- If scoped paths were provided, treat them as the audit diff boundary.

## Bound Audit Inputs

- Spec: documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md - APPROVED Phase A T-A1 mapping; TASK-M6.1 implementation complete; later M6 tasks remain out of scope.
- Task File: documentation/tasks/TASK-M6_transport_phase_a.md
- Backlog Item: N/A WITH REASON - No backlog marker provided.
- Pre-Implementation Check: documentation/tasks/TASK-M6.1_preimplementation_check.md
- Manual Janus Evidence: PRESENT
- Pipeline Completion Status: TASK-M6.1 implementation complete; later Phase-A tasks T-A2 through T-A5 remain intentionally out of scope; manual Gemini websearch evidence present.

## Backlog Item

```text
N/A WITH REASON - No backlog source or marker provided.
```

## Task Acceptance Scope

```text
TASK-M6
- Source Spec: `documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md`
- Backlog Item: `N/A`
- Feature: Epic 4 Provider Transport Refactor, Phase A Consolidation
- Generated At: 2026-07-11

## Generated Tasks

### TASK-M6.1 Unify the model hierarchy as the single MoA source
- Ziel:
  - Make `MOA_MODEL_HIERARCHY` in `backend/llm_providers/shared/moa.py` the only model-tier source and remove the duplicate `ChatOrchestrator.MODEL_HIERARCHY` use.
- Scope:
  - Spec Section 3.4 and Phase A `T-A1` only. Migrate the bound imports and add a drift regression. No transport class, runtime resolver, OAuth, OpenRouter product path, or feature-flag flip.
- Files:
  - `backend/llm_providers/shared/moa.py`
  - `backend/services/chat_orchestrator.py`
  - `backend/llm_providers/gemini/gateway.py`
  - `backend/tests/test_model_hierarchy_single_source.py`
- Steps:
  1. Identify and remove the duplicate hierarchy definition from the orchestrator path.
  2. Migrate the bound consumers to the shared MoA hierarchy without changing tier semantics.
  3. Add a regression that fails if a second runtime model hierarchy is introduced.
- Acceptance Criteria:
  - `MOA_MODEL_HIERARCHY` is the only runtime model-hierarchy source for the bound paths.
  - OpenAI and Gemini bound consumers preserve their existing tier lookup behavior.
  - The new drift test passes.
- Tests:
  - `python -m pytest backend/tests/test_model_hierarchy_single_source.py -q`
  - focused existing hierarchy/gateway regressions selected by precheck
  - `python -m py_compile backend/llm_providers/shared/moa.py backend/services/chat_orchestrator.py backend/llm_providers/gemini/gateway.py`
- Model: 5.6 Terra
- Reason:
  - The Spec names this as the first bounded Phase-A consolidation seam; it removes drift before shared loop extraction changes behavior.

### TASK-M6.2 Introduce the transport-boundary ToolCallAdapter
- Ziel:
  - Add the canonical-to-transport tool-call adapter defined in Spec Section 2.4 and Phase A `T-A2`.
- Scope:
  - Adapter and directly bound tool-definition/service seams only. Keep canonical skill IDs in the ToolManager and normalize provider names only at the transport boundary.
- Files:
  - `backend/llm_providers/shared/tool_call_adapter.py`
  - `backend/services/tool_manager.py`
  - `backend/llm_providers/openai/service.py`
  - `backend/llm_providers/shared/utils.py`
  - focused adapter/tool-call tests
- Steps:
  1. Define canonical outbound and inbound adaptation for skill IDs and LLM names.
  2. Move dot/underscore and Gemini schema normalization into the adapter boundary.
  3. Cover canonical ID preservation and provider-specific conversion with focused tests.
- Acceptance Criteria:
  - ToolManager emits canonical skill IDs.
  - Provider-specific tool naming is confined to the adapter boundary.
  - Inbound calls normalize back to canonical skill IDs.
- Tests:
  - focused adapter and existing prevalidation regressions selected by precheck
  - `python -m py_compile backend/llm_providers/shared/tool_call_adapter.py backend/services/tool_manager.py backend/llm_providers/openai/service.py backend/llm_providers/shared/utils.py`
- Model: 5.6 Terra
- Reason:
  - This is the explicit next Phase-A seam after hierarchy consolidation and stays transport-boundary only.

### TASK-M6.3 Extract the OpenAI ToolLoopRunner behind a default-off flag
- Ziel:
  - Extract the provider-neutral OpenAI tool loop into `ToolLoopRunner` without changing default production behavior.
- Scope:
  - Spec Section 3.3 and Phase A `T-A3` only. Preserve OpenAI behavior behind `TRANSPORT_TOOL_LOOP_RUNNER_ENABLED=false`; no Gemini migration in this task.
- Files:
  - `backend/llm_providers/shared/tool_loop_runner.py`
  - `backend/llm_providers/openai/gateway.py`
  - focused OpenAI gateway and runner tests
- Steps:
  1. Extract the explicit provider-neutral loop responsibilities named in the Spec.
  2. Keep provider-specific prompt compilation and synthesis outside the runner.
  3. Add default-off and flag-on regression coverage for the OpenAI path.
- Acceptance Criteria:
  - The default flag preserves the existing OpenAI path.
  - The enabled path routes the declared loop responsibilities through `ToolLoopRunner`.
  - Focused OpenAI gateway regressions pass.
- Tests:
  - focused OpenAI gateway/runner regressions selected by precheck
  - `python -m py_compile backend/llm_providers/shared/tool_loop_runner.py backend/llm_providers/openai/gateway.py`
- Model: 5.6 Terra
- Reason:
  - The Spec explicitly stages OpenAI extraction before Gemini migration to keep behavior risk bounded.

### TASK-M6.4 Migrate the Gemini gateway to the shared ToolLoopRunner
- Ziel:
  - Route the Gemini gateway through the shared runner while preserving its native proto, schema, and history behavior.
- Scope:
  - Phase A `T-A4` only, after the OpenAI runner extraction is validated. No transport-layer classes or provider expansion.
- Files:
  - `backend/llm_providers/gemini/gateway.py`
  - `backend/llm_providers/shared/tool_loop_runner.py`
  - focused Gemini gateway and parity regressions
- Steps:
  1. Replace duplicated Gemini loop control with the shared runner integration.
  2. Keep Gemini-specific bridge and schema behavior in its gateway/service boundary.
  3. Add focused parity and regression coverage.
- Acceptance Criteria:
  - Gemini uses `ToolLoopRunner` for the declared loop responsibilities.
  - Gemini-specific proto/history behavior remains intact.
  - Focused Gemini regressions pass.
- Tests:
  - focused Gemini gateway and existing calendar routing regressions selected by precheck
  - `python -m py_compile backend/llm_providers/gemini/gateway.py backend/llm_providers/shared/tool_loop_runner.py`
- Model: 5.6 Terra
- Reason:
  - This follows the explicit Spec migration order and must remain separate from OpenAI extraction for diagnosis.

### TASK-M6.5 Route streaming through the gateway and ToolLoopRunner path
- Ziel:
  - Remove the declared direct streaming bypass from `execution_engine.py` while preserving provider behavior behind the Phase-A flag boundary.
- Scope:
  - Phase A `T-A5` only, after the shared runner is proven for OpenAI and Gemini. No Phase-B transport resolver or websearch decoupling.
- Files:
  - `backend/services/orchestrator/execution_engine.py`
  - bound gateway/runner files as required
  - focused streaming regressions
- Steps:
  1. Identify the direct provider streaming bypass named in the Spec.
  2. Route it through the gateway/runner path without changing the default-off flag behavior.
  3. Cover streaming and non-streaming path consistency.
- Acceptance Criteria:
  - Streaming no longer bypasses the bound gateway/runner path when Phase A is enabled.
  - Default-off behavior remains unchanged.
  - Focused streaming regressions pass.
- Tests:
  - focused streaming and gateway regressions selected by precheck
  - `python -m py_compile backend/services/orchestrator/execution_engine.py`
- Model: 5.6 Terra
- Reason:
  - The Spec explicitly places streaming migration last in Phase A because it depends on the shared runner path.
```

## Pre-Implementation Check

```text
PRE-CHECK RESULT
PRE-CHECK PASSED

legacy handoff start
NEXT: janus-executioner
Target Task: TASK-M6.1
Target Subtask: N/A
Task: documentation/tasks/TASK-M6_transport_phase_a.md
Spec: documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
Backlog Item: N/A
Assigned Model: 5.6 Terra
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound scope is atomic: Phase A T-A1 only consolidates the existing model hierarchy into `MOA_MODEL_HIERARCHY` and adds a drift regression.
- The approved Spec mapping preserves active behavior: OpenAI `balanced=gpt-5.4-mini`, Gemini `vision=gemini-3-flash-preview` and `logic=gemini-3-pro-preview`, plus the current Ollama tiers including `fast`.
- Repository scan found exactly two hierarchy definitions. Existing MoA readers in debug and execution-dispatch paths do not introduce additional definitions.
- Risk is HIGH because model-tier selection and provider fallback are central behavior, but the scope is bounded by the approved verbatim mapping, default behavior preservation, and a dedicated drift regression.
Affected Files:
- backend/llm_providers/shared/moa.py
- backend/services/chat_orchestrator.py
- backend/llm_providers/gemini/gateway.py
- backend/tests/test_model_hierarchy_single_source.py
- backend/tests/test_moa_routing.py
Evidence Focus:
- python -m pytest backend/tests/test_model_hierarchy_single_source.py -q
- python -m pytest backend/tests/test_moa_routing.py -q
- python -m pytest backend/tests/test_calendar_routing_fix.py -q
- python -m py_compile backend/llm_providers/shared/moa.py backend/services/chat_orchestrator.py backend/llm_providers/gemini/gateway.py
- git diff --check -- backend/llm_providers/shared/moa.py backend/services/chat_orchestrator.py backend/llm_providers/gemini/gateway.py backend/tests/test_model_hierarchy_single_source.py documentation/tasks/TASK-M6_transport_phase_a.md documentation/tasks/TASK-M6.1_task_breakdown.md documentation/tasks/TASK-M6.1_preimplementation_check.md
Scope-Regel:
- Implement only TASK-M6.1. Preserve the approved mapping exactly; no ToolCallAdapter, ToolLoopRunner, streaming, transport class, OAuth, OpenRouter, websearch, feature-flag, or provider-policy expansion.
Automated Evidence Gate:
- python -m pytest backend/tests/test_model_hierarchy_single_source.py -q
- python -m pytest backend/tests/test_moa_routing.py -q
- python -m pytest backend/tests/test_calendar_routing_fix.py -q
- python -m py_compile backend/llm_providers/shared/moa.py backend/services/chat_orchestrator.py backend/llm_providers/gemini/gateway.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, task-breakdown handoff, and approved Spec review metadata verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
- documentation/tasks/TASK-M6_transport_phase_a.md
- documentation/tasks/TASK-M6.1_task_breakdown.md
- backend/llm_providers/shared/moa.py
- backend/services/chat_orchestrator.py
- backend/llm_providers/gemini/gateway.py
- backend/tests/test_moa_routing.py
Drop Context:
- Phase-A tasks T-A2 through T-A5
- Phase-B/C transport work
- OAuth, OpenRouter, websearch, and unrelated mixed-worktree history
Completion Rule:
- End with PASS, BLOCKED, or HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.
legacy handoff end

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.6 Terra
Recommended Intelligence: medium
Reason: The approved mapping removes the only architecture ambiguity. TASK-M6.1 is now a bounded high-risk consolidation with concrete consumers, explicit exclusions, and focused regression gates.
User Action: Say `ok` to start implementation of TASK-M6.1 in the clean M6 worktree.
```

## Changed Files

```text
M backend/llm_providers/gemini/gateway.py
 M backend/llm_providers/shared/moa.py
 M backend/services/chat_orchestrator.py
 M backend/tests/test_moa_routing.py
?? backend/tests/test_model_hierarchy_single_source.py
?? documentation/tasks/TASK-M6.1_execution_result.md
```

## Artifact Inventory

```text
FILE C:\KI\Janus-M6-Transport-Prep\documentation\Cursor specs\PROVIDER_TRANSPORT_REFACTOR_SPEC.md (21279 bytes)
FILE C:\KI\Janus-M6-Transport-Prep\documentation\tasks\TASK-M6.1_task_breakdown.md (2418 bytes)
FILE C:\KI\Janus-M6-Transport-Prep\documentation\tasks\TASK-M6.1_execution_result.md (3977 bytes)
```

## Diff Summary

```text
backend/llm_providers/gemini/gateway.py |  4 ++--
 backend/llm_providers/shared/moa.py     | 15 +++++++++----
 backend/services/chat_orchestrator.py   | 40 +++++++++------------------------
 backend/tests/test_moa_routing.py       | 13 +++++------
 4 files changed, 29 insertions(+), 43 deletions(-)
```

## Validation

```text
TASK EXECUTION RESULT
Canonical State: HANDOFF
Target Task: TASK-M6.1

Changed Files:
- backend/llm_providers/shared/moa.py
- backend/services/chat_orchestrator.py
- backend/llm_providers/gemini/gateway.py
- backend/tests/test_moa_routing.py
- backend/tests/test_model_hierarchy_single_source.py
- documentation/tasks/TASK-M6.1_execution_result.md
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md

Executed Checks:
- `python -m pytest --noconftest backend/tests/test_model_hierarchy_single_source.py -q`: PASS, 3 tests
- `python -m pytest --noconftest backend/tests/test_moa_routing.py -q`: PASS, 13 tests
- `python -m py_compile backend/llm_providers/shared/moa.py backend/services/chat_orchestrator.py backend/llm_providers/gemini/gateway.py`: PASS
- `git diff --check -- backend/llm_providers/shared/moa.py backend/services/chat_orchestrator.py backend/llm_providers/gemini/gateway.py backend/tests/test_moa_routing.py backend/tests/test_model_hierarchy_single_source.py`: PASS
- `rg -n 'MODEL_HIERARCHY\\s*=' backend/llm_providers backend/services/chat_orchestrator.py`: PASS, only `MOA_MODEL_HIERARCHY` remains
- `rg -n 'ChatOrchestrator\\.MODEL_HIERARCHY|self\\.MODEL_HIERARCHY' backend/llm_providers backend/services/chat_orchestrator.py`: PASS, no matches
- `python -m pytest backend/tests/test_model_hierarchy_single_source.py -q`: BLOCKED before collection by the pre-existing ChromaDB SQLite panic in `backend/tests/conftest.py`
- `python -m pytest backend/tests/test_moa_routing.py -q`: BLOCKED before collection by the same pre-existing ChromaDB SQLite panic
- `python -m pytest backend/tests/test_calendar_routing_fix.py -q`: BLOCKED before collection by the same pre-existing ChromaDB SQLite panic

Implementation Notes:
- `MOA_MODEL_HIERARCHY` is the sole runtime hierarchy source for the orchestrator and Gemini gateway.
- The approved active OpenAI, Gemini, and Ollama mappings were preserved verbatim, including Ollama `fast` and `MOA` support for that tier.
- The new AST and source-level regression prevents a new orchestrator hierarchy definition or a Gemini dependency back to `ChatOrchestrator.MODEL_HIERARCHY`.

Manual Janus Validation Gate:
- Status: PASS
- Test Example: Start Janus from the clean M6 worktree with Gemini configured, then ask `Suche aktuelle Nachrichten zu Berlin.`
- Expected Result: The request completes normally through the Gemini websearch path without an import/circular-dependency failure or an unintended provider fallback.
- If Failed: route to `janus-debug` with the backend log excerpt.
- If Passed: route to `janus-final-audit`.
- Actual PASS Evidence: On `2026-07-11 15:34 +02:00`, Gemini returned a current Berlin news briefing with five curated source entries (ZEIT, Deutschlandfunk, n-tv, and Tagesschau) and the expected RSS/websearch-fallback explanation. No import error, circular dependency, provider fallback, or degraded error response occurred.

NEXT_STEP
Target Skill: janus-final-audit after manual validation passes
Canonical State: HANDOFF
Required Artifacts:
- documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
- documentation/tasks/TASK-M6_transport_phase_a.md
- documentation/tasks/TASK-M6.1_task_breakdown.md
- documentation/tasks/TASK-M6.1_preimplementation_check.md
- documentation/tasks/TASK-M6.1_execution_result.md
Evidence Paths:
- backend/llm_providers/shared/moa.py
- backend/services/chat_orchestrator.py
- backend/llm_providers/gemini/gateway.py
- backend/tests/test_model_hierarchy_single_source.py
- backend/tests/test_moa_routing.py
Failure Code: ENVIRONMENT_CHROMADB_SQLITE_PANIC for full pytest collection only
Decision: HANDOFF
Reason: The bounded source consolidation, isolated regression evidence, and manual Gemini websearch validation pass. Normal pytest collection remains independently blocked by the local ChromaDB SQLite panic.
Recommended Model: 5.6 Terra
Recommended Intelligence: high
Next User Action: Review the final audit result.
```

## Notes

TASK EXECUTION RESULT
Canonical State: HANDOFF
Target Task: TASK-M6.1

Changed Files:
- backend/llm_providers/shared/moa.py
- backend/services/chat_orchestrator.py
- backend/llm_providers/gemini/gateway.py
- backend/tests/test_moa_routing.py
- backend/tests/test_model_hierarchy_single_source.py
- documentation/tasks/TASK-M6.1_execution_result.md
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md

Executed Checks:
- `python -m pytest --noconftest backend/tests/test_model_hierarchy_single_source.py -q`: PASS, 3 tests
- `python -m pytest --noconftest backend/tests/test_moa_routing.py -q`: PASS, 13 tests
- `python -m py_compile backend/llm_providers/shared/moa.py backend/services/chat_orchestrator.py backend/llm_providers/gemini/gateway.py`: PASS
- `git diff --check -- backend/llm_providers/shared/moa.py backend/services/chat_orchestrator.py backend/llm_providers/gemini/gateway.py backend/tests/test_moa_routing.py backend/tests/test_model_hierarchy_single_source.py`: PASS
- `rg -n 'MODEL_HIERARCHY\\s*=' backend/llm_providers backend/services/chat_orchestrator.py`: PASS, only `MOA_MODEL_HIERARCHY` remains
- `rg -n 'ChatOrchestrator\\.MODEL_HIERARCHY|self\\.MODEL_HIERARCHY' backend/llm_providers backend/services/chat_orchestrator.py`: PASS, no matches
- `python -m pytest backend/tests/test_model_hierarchy_single_source.py -q`: BLOCKED before collection by the pre-existing ChromaDB SQLite panic in `backend/tests/conftest.py`
- `python -m pytest backend/tests/test_moa_routing.py -q`: BLOCKED before collection by the same pre-existing ChromaDB SQLite panic
- `python -m pytest backend/tests/test_calendar_routing_fix.py -q`: BLOCKED before collection by the same pre-existing ChromaDB SQLite panic

Implementation Notes:
- `MOA_MODEL_HIERARCHY` is the sole runtime hierarchy source for the orchestrator and Gemini gateway.
- The approved active OpenAI, Gemini, and Ollama mappings were preserved verbatim, including Ollama `fast` and `MOA` support for that tier.
- The new AST and source-level regression prevents a new orchestrator hierarchy definition or a Gemini dependency back to `ChatOrchestrator.MODEL_HIERARCHY`.

Manual Janus Validation Gate:
- Status: PASS
- Test Example: Start Janus from the clean M6 worktree with Gemini configured, then ask `Suche aktuelle Nachrichten zu Berlin.`
- Expected Result: The request completes normally through the Gemini websearch path without an import/circular-dependency failure or an unintended provider fallback.
- If Failed: route to `janus-debug` with the backend log excerpt.
- If Passed: route to `janus-final-audit`.
- Actual PASS Evidence: On `2026-07-11 15:34 +02:00`, Gemini returned a current Berlin news briefing with five curated source entries (ZEIT, Deutschlandfunk, n-tv, and Tagesschau) and the expected RSS/websearch-fallback explanation. No import error, circular dependency, provider fallback, or degraded error response occurred.

NEXT_STEP
Target Skill: janus-final-audit after manual validation passes
Canonical State: HANDOFF
Required Artifacts:
- documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
- documentation/tasks/TASK-M6_transport_phase_a.md
- documentation/tasks/TASK-M6.1_task_breakdown.md
- documentation/tasks/TASK-M6.1_preimplementation_check.md
- documentation/tasks/TASK-M6.1_execution_result.md
Evidence Paths:
- backend/llm_providers/shared/moa.py
- backend/services/chat_orchestrator.py
- backend/llm_providers/gemini/gateway.py
- backend/tests/test_model_hierarchy_single_source.py
- backend/tests/test_moa_routing.py
Failure Code: ENVIRONMENT_CHROMADB_SQLITE_PANIC for full pytest collection only
Decision: HANDOFF
Reason: The bounded source consolidation, isolated regression evidence, and manual Gemini websearch validation pass. Normal pytest collection remains independently blocked by the local ChromaDB SQLite panic.
Recommended Model: 5.6 Terra
Recommended Intelligence: high
Next User Action: Review the final audit result.

## Risks

Provider-routing change; full pytest collection is environment-blocked by the local ChromaDB SQLite panic.

## Open Issues

Non-blocking: remove the obsolete Ollama-no-tiers comment in backend/llm_providers/shared/moa.py before the next M6 implementation task. Full pytest collection requires independent local ChromaDB environment repair.

## Re-Audit Delta

No re-audit delta provided.

## Final Audit Handoff

```text
NEW_CHAT_HANDOFF
NEXT: final-skill-audit
MODEL: 5.6 Sol/high if runtime-supported; otherwise 5.6 Terra/high
PASS: C:\KI\Janus-M6-Transport-Prep\documentation\tasks\TASK-M6.1_AUDIT_PACKAGE.md
ASK: Lade nur dieses Paket im neuen Chat und starte dann den Final Audit.
DROP: dev chat history
```

Use `5.6 Sol/high` when the current Codex run can start it; if Codex reports `gpt-5.6-sol` is unsupported for the active ChatGPT account, use `5.6 Terra/high` and record `SOL_UNAVAILABLE_FOR_CHATGPT_CODEX_ACCOUNT`.

For bounded same-thread re-audits after a local blocker fix, `5.6 Terra/high` is acceptable when the package stays compact and the risk did not escalate.
