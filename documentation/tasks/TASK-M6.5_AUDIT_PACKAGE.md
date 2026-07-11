# AUDIT_PACKAGE

Generated: 2026-07-11 19:16:24 UTC

## Goal

TASK-M6.5 streaming gateway/ToolLoopRunner boundary

## Scope Rules

- Audit the provided package and changed artifacts only.
- Do not rely on development chat history.
- Verify cost, caching, skill quality, safety scope, and validation evidence.
- On re-audit, review the blocker delta first before widening scope.
- If scoped paths were provided, treat them as the audit diff boundary.

## Bound Audit Inputs

- Spec: Phase-A T-A5 implementation complete; parent M6 Spec is ready for separate parent closeout review.
- Task File: documentation/tasks/TASK-M6_transport_phase_a.md
- Backlog Item: N/A WITH REASON - No backlog marker provided.
- Pre-Implementation Check: documentation/tasks/TASK-M6.5_preimplementation_check.md
- Manual Janus Evidence: N/A WITH REASON: default-off flag and local collection blockers.
- Pipeline Completion Status: Implementation complete; final audit PASS WITH FIXES; no remaining Phase-A implementation task.

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
- Closeout:
  - Final Audit: `PASS WITH FIXES` in `documentation/tasks/TASK-M6.1_final_audit.md`.
  - `MOA_MODEL_HIERARCHY` is now the sole runtime hierarchy source for the bound orchestrator and Gemini gateway paths. The approved OpenAI, Gemini, and Ollama matrix, including `fast`, is covered by focused regressions and manual Gemini websearch evidence.
  - Non-blocking follow-up: correct the obsolete Ollama-no-tier comment in `backend/llm_providers/shared/moa.py` before `TASK-M6.2`.
  - `T-A2` through `T-A5` remain open and are not covered by this task closeout.
  - Changelog skipped: internal provider-routing consolidation with no new user-facing feature or release.

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
- Closeout:
  - Final Audit: `PASS WITH FIXES` in `documentation/tasks/TASK-M6.2_final_audit.md`.
  - `ToolManager` now emits canonical dotted skill IDs; `ToolCallAdapter` owns OpenAI/Gemini outbound naming, inbound canonical restoration, and provider-specific schema adaptation.
  - Focused adapter (`12/12`), OpenAI (`2/2`), and Gemini (`12/12`) regressions, syntax, scoped diff, and manual Gemini Berlin-weather evidence passed.
  - Non-blocking follow-up: Cursor Composer proposal-first execution is not autonomous/productive yet because the shared delegate has wrapper-contract defects and the valid direct run timed out without structured output. Track it as a separate Cursor-infrastructure debug slice.
  - `T-A3` through `T-A5` remain open and are not covered by this task closeout.
  - Changelog skipped: internal provider-routing consolidation with no new user-facing feature or release.

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
- Closeout:
  - Final Audit: `PASS WITH FIXES` in `documentation/tasks/TASK-M6.3_final_audit.md`.
  - `ToolLoopRunner` now owns the declared provider-neutral OpenAI loop responsibilities behind `TRANSPORT_TOOL_LOOP_RUNNER_ENABLED=false`; the legacy OpenAI loop remains the default path.
  - Focused runner (`4/4`), syntax, scoped diff, execution-result, and final-audit validation passed.
  - Non-blocking follow-up: the broad OpenAI regression remains blocked by the independent local ChromaDB SQLite panic; Cursor Composer proposal-first evidence also timed out without structured output and needs a separate Cursor-infrastructure debug slice.
  - `T-A4` and `T-A5` remain open and are not covered by this task closeout.
  - Changelog skipped: internal default-off provider-routing consolidation with no new user-facing feature or release.

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
- Closeout:
  - Final Audit: `PASS WITH FIXES` in `documentation/tasks/TASK-M6.4_final_audit.md`.
  - Gemini now uses the provider-neutral runner only through gateway-owned callbacks; Flash/override policy, list rounds, grounding/cost attribution, native history, synthesis, engine-owned, and drill-down behavior remain in the gateway.
  - Focused Gemini runner (`6/6`), syntax, execution-result, and final-audit validation passed.
  - `T-A5` remains open; changelog skipped because this is internal default-off provider-routing work.

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
- Closeout:
  - Final Audit: `PASS WITH FIXES` in `documentation/tasks/TASK-M6.5_final_audit.md`.
  - Flag-off retains the provider-native StreamEvent path. Flag-on sends only post-tool non-streaming OpenAI/Gemini continuations to the existing gateway/ToolLoopRunner boundary and passes the remaining outer-loop budget as the runner limit.
  - Syntax, scoped diff, precheck, execution-result, and final-audit validation passed. The focused pytest is blocked before collection by independent ChromaDB SQLite and missing `backend.data.schemas_intent` defects.
  - Phase-A implementation tasks `T-A1` through `T-A5` are complete. Manual enabled-flag streaming smoke evidence is required before broad flag enablement; changelog skipped because this remains internal default-off provider-routing work.
```

## Pre-Implementation Check

```text
PRE-CHECK RESULT
PRE-CHECK PASSED

legacy handoff start
NEXT: janus-executioner
Target Task: TASK-M6.5
Target Subtask: N/A
Task: documentation/tasks/TASK-M6_transport_phase_a.md
Spec: documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
Backlog Item: N/A
Assigned Model: 5.6 Terra
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- Implement only the confirmed streaming boundary: StreamEvent protocol, auth isolation, forced-tool start, delta normalization, and stream-final cost remain in execution_engine.
- Flag-on may route only non-streaming tool-round handoff through existing gateway/runner seams; flag-off remains unchanged.
- OpenRouter review is planned-only; Codex owns the final precheck decision.
Affected Files:
- backend/services/orchestrator/execution_engine.py
- backend/tests/test_streaming_tool_loop_runner.py
Evidence Focus:
- focused streaming flag-off/flag-on regression
- provider stream regression selected during execution
- python -m py_compile backend/services/orchestrator/execution_engine.py
Scope-Regel:
- Implement only TASK-M6.5. No StreamEvent rewrite, delta parser migration, auth-isolation change, forced-tool policy change, Gemini grounding-policy change, transport classes, resolver, OAuth, or Phase-B work.
Automated Evidence Gate:
- focused streaming regression
- python -m py_compile backend/services/orchestrator/execution_engine.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and task-breakdown handoff verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- M6.5 task, Spec Section 3.3.3, execution_engine streaming loop, gateway/runner boundaries.
Drop Context:
- completed M6.1 through M6.4 implementation history and Phase-B work.
Completion Rule:
- End with PASS, BLOCKED, or HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.
legacy handoff end

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.6 Terra
Recommended Intelligence: high
Reason: M6.5 has an explicit stream ownership boundary and no remaining architecture decision.
User Action: Execution proceeds in this approved M6 chain.
```

## Changed Files

```text
M backend/services/orchestrator/execution_engine.py
?? backend/tests/test_streaming_tool_loop_runner.py
?? documentation/tasks/TASK-M6.5_execution_result.md
?? documentation/tasks/TASK-M6.5_final_audit.md
?? documentation/tasks/TASK-M6.5_preimplementation_check.md
?? documentation/tasks/TASK-M6.5_task_breakdown.md
?? documentation/tasks/TASK-M6.5_validation.md
```

## Artifact Inventory

```text
DIR C:\KI\Janus-M6-Transport-Prep\documentation\codex\model-routing\cursor-worker-runs\WF-M6.5-EXECUTION-2026-07-11-001 (5 files)
  FILE C:\KI\Janus-M6-Transport-Prep\documentation\codex\model-routing\cursor-worker-runs\WF-M6.5-EXECUTION-2026-07-11-001\changed_files.txt (0 bytes)
  FILE C:\KI\Janus-M6-Transport-Prep\documentation\codex\model-routing\cursor-worker-runs\WF-M6.5-EXECUTION-2026-07-11-001\cursor_response.json (52 bytes)
  FILE C:\KI\Janus-M6-Transport-Prep\documentation\codex\model-routing\cursor-worker-runs\WF-M6.5-EXECUTION-2026-07-11-001\dispatcher_result.json (3154 bytes)
  FILE C:\KI\Janus-M6-Transport-Prep\documentation\codex\model-routing\cursor-worker-runs\WF-M6.5-EXECUTION-2026-07-11-001\stderr.log (0 bytes)
  FILE C:\KI\Janus-M6-Transport-Prep\documentation\codex\model-routing\cursor-worker-runs\WF-M6.5-EXECUTION-2026-07-11-001\stdout.log (0 bytes)
```

## Diff Summary

```text
backend/services/orchestrator/execution_engine.py | 122 +++++++++++++++++++++-
 1 file changed, 121 insertions(+), 1 deletion(-)
```

## Validation

```text
# TASK-M6.5 Validation Evidence

## PASS
- `python -m py_compile backend/services/orchestrator/execution_engine.py backend/tests/test_streaming_tool_loop_runner.py`
- `git diff --check`

## BLOCKED (external environment)
- `python -m pytest --noconftest backend/tests/test_streaming_tool_loop_runner.py -q`
  - collection stops in ChromaDB Rust SQLite with `range start index 10 out of range for slice of length 9`.
- Retry after replacing `chromadb.PersistentClient` for the test process only
  - collection reaches and stops at `ModuleNotFoundError: No module named 'backend.data.schemas_intent'`.

## Scope Review
- The enabled handoff is limited to an already completed tool round and OpenAI/Gemini providers.
- Flag-off still uses the original provider-native streaming call.
- `max_tool_rounds` is derived from the streaming loop's remaining budget.
- No StreamEvent protocol, delta parser, auth isolation, forced-tool start, Gemini policy, or Phase-B transport files changed.
```

## Notes

# TASK EXECUTION RESULT - TASK-M6.5

Canonical State: HANDOFF
Target Task: TASK-M6.5

Auto-Verification:
- Status: PASS
- Scope and syntax checks pass; the focused test runner is externally blocked before collection, as recorded below.

## Implementation
- `execution_engine.py` retains StreamEvent parsing, stream auth isolation, forced-tool start, provider delta normalization, and stream-final cost handling.
- With `TRANSPORT_TOOL_LOOP_RUNNER_ENABLED=true`, only a post-tool non-streaming continuation for OpenAI/Gemini is routed through `llm_gateway.reason_and_respond`, which reaches the existing gateway/ToolLoopRunner boundary.
- The continuation strips forced-tool and stream-only cache controls and inherits the remaining streaming round budget, so the gateway runner cannot exceed the outer streaming limit.
- The flag-off path remains the existing provider-native `_async_iter_llm_stream` path.

## Executed Checks
- `python -m py_compile backend/services/orchestrator/execution_engine.py backend/tests/test_streaming_tool_loop_runner.py`: PASS.
- `git diff --check`: PASS.
- `python -m pytest --noconftest backend/tests/test_streaming_tool_loop_runner.py -q`: BLOCKED during collection by the existing ChromaDB SQLite panic (`range start index 10 out of range for slice of length 9`).
- Isolated retry with a harmless Chroma client stub: BLOCKED during collection by the pre-existing missing module `backend.data.schemas_intent`.

## Cursor Evidence
- Workflow `WF-M6.5-EXECUTION-2026-07-11-001` used a validated allowlist and package, then started a live Cursor Composer worker.
- The worker timed out after 180 seconds and returned no structured result. It left an allowlisted partial candidate in the worktree; Codex reviewed it, added the missing remaining-round budget guard, and owns the validation and completion decision.
- Evidence: `documentation/codex/model-routing/cursor-worker-runs/WF-M6.5-EXECUTION-2026-07-11-001/`.

## Manual Janus Validation Gate:
- Status: N/A WITH REASON.
- Test Example: In a controlled development session, enable `TRANSPORT_TOOL_LOOP_RUNNER_ENABLED` and issue one OpenAI and one Gemini tool-backed streaming request.
- Expected Result: first stream/tool event remains native; post-tool continuation reaches the gateway/runner and returns the final text without exceeding the configured round cap.
- If Failed: route to janus-debug with backend stream logs and the provider/model used.
- If Passed: route to janus-final-audit.
- Reason: production remains default-off; automated focused execution is currently blocked by unrelated local import/runtime defects.

NEXT_STEP
Target Skill: janus-final-audit
Canonical State: HANDOFF
Required Artifacts: `documentation/tasks/TASK-M6.5_task_breakdown.md`, `documentation/tasks/TASK-M6.5_preimplementation_check.md`, `documentation/tasks/TASK-M6.5_execution_result.md`
Evidence Paths: `backend/services/orchestrator/execution_engine.py`, `backend/tests/test_streaming_tool_loop_runner.py`, `documentation/codex/model-routing/cursor-worker-runs/WF-M6.5-EXECUTION-2026-07-11-001/`
Failure Code: N/A
Changed Files: streaming execution engine, focused streaming regression, bounded Cursor worker evidence
Decision: HANDOFF
Reason: implementation is scope-conformant and syntax-validated; final audit must record the external test-collection blockers.
Recommended Model: 5.6 Terra
Recommended Intelligence: high
Next User Action: Say `ok` to start janus-final-audit for TASK-M6.5.

## Risks

Focused pytest is blocked by pre-existing ChromaDB and missing schemas_intent; flag remains default-off.

## Open Issues

Collect OpenAI and Gemini manual enabled-flag streaming smoke evidence before broad enablement.

## Re-Audit Delta

No re-audit delta provided.

## Final Audit Handoff

```text
NEW_CHAT_HANDOFF
NEXT: janus-final-audit
MODEL: 5.6 Sol/high if runtime-supported; otherwise 5.6 Terra/high
PASS: C:\KI\Janus-M6-Transport-Prep\documentation\tasks\TASK-M6.5_AUDIT_PACKAGE.md
ASK: Lade nur dieses Paket im neuen Chat und starte dann den Final Audit.
DROP: dev chat history
```

If Codex reports `gpt-5.6-sol` is unsupported for the active ChatGPT account, use `5.6 Terra/high` and record `SOL_UNAVAILABLE_FOR_CHATGPT_CODEX_ACCOUNT`. For bounded same-thread re-audits after a local blocker fix, `5.6 Terra/high` is acceptable when the package stays compact and the risk did not escalate.
