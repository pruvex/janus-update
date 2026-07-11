# TASK BREAKDOWN - TASK-M6.3

## Binding Sources
- Spec: `documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md` (Section 3.3 and Phase A `T-A3`)
- Parent Task: `documentation/tasks/TASK-M6_transport_phase_a.md`
- Backlog Item: `N/A` - roadmap/spec-driven infrastructure slice
- Prior Slices: `TASK-M6.1` and `TASK-M6.2` are checkpointed; their model-hierarchy and ToolCallAdapter boundaries are unchanged.

## Released Target
- Target Task: `TASK-M6.3`
- Title: Extract the OpenAI ToolLoopRunner behind a default-off flag
- Execution Model: `5.6 Terra`, `medium`
- Readiness: `PRECHECK_READY`

## Cursor Review Evidence
- Operator choice: Cursor API (`4`), model `gpt-5.4-mini-medium`.
- Workflow: `WF-M6.3-TASK-BREAKDOWN-2026-07-11-001`.
- Result: `CURSOR_WORKER_DRY_RUN_READY`; the shared assist-only lane currently plans the bounded worker but does not permit a live Cursor task-breakdown call.
- Authority: Codex reviewed the actual source and writes this authoritative handoff locally. No Cursor output is treated as a requirements or implementation decision.

## Atomic Scope
- Add `backend/llm_providers/shared/tool_loop_runner.py` for only the provider-neutral responsibilities explicitly named in Spec Section 3.3: MoA model resolution, tool-call prevalidation, the bounded round loop, tool execution, history preparation, and configurable max-round behavior.
- Refactor `backend/llm_providers/openai/gateway.py` so its existing `_run_full_tool_loop` remains the default path while `TRANSPORT_TOOL_LOOP_RUNNER_ENABLED=false` preserves the current behavior exactly.
- When the flag is enabled, route only the declared OpenAI loop responsibilities through `ToolLoopRunner`; retain OpenAI prompt compilation, forced-tool fallback construction, response synthesis, link repair, routing guards, and cost persistence in the gateway or existing provider seams.
- Add focused tests proving flag-off parity and flag-on runner routing for a deterministic OpenAI tool-call round.

## Files
- `backend/llm_providers/shared/tool_loop_runner.py` (new)
- `backend/llm_providers/openai/gateway.py`
- `backend/tests/test_openai_tool_loop_runner.py` (new)
- `backend/tests/test_backlog_007_tool_routing_performance.py`

## Explicit Exclusions
- No Gemini gateway migration, Gemini proto/history change, or Gemini parity work; those belong to `TASK-M6.4`.
- No streaming path or `execution_engine.py` change; that belongs to `TASK-M6.5`.
- No new transport classes, runtime resolver, OAuth, OpenRouter product behavior, websearch-policy change, ToolCallAdapter change, provider-policy change, or MoA hierarchy change.
- No default-on flag, shadow-mode rollout, release, or user-facing behavioral change.
- Do not broaden the runner beyond the existing OpenAI loop; provider-specific synthesis and forced-tool fallback policy remain outside the shared runner.

## Acceptance Criteria
- `TRANSPORT_TOOL_LOOP_RUNNER_ENABLED` defaults to `false`, and the OpenAI gateway retains the existing loop implementation when it is disabled.
- With the flag enabled, the OpenAI tool-call round uses `ToolLoopRunner` for model selection, prevalidation, bounded iteration, execution, and second-call history preparation.
- OpenAI-specific prompt compilation, forced-tool fallback construction, synthesis, routing guards, link repair, and cost persistence remain outside `ToolLoopRunner`.
- A deterministic one-tool OpenAI regression has equivalent visible response and tool-result behavior for flag-off and flag-on execution.
- The runner has no Gemini imports or Gemini-specific behavior.

## Tests
- `python -m pytest --noconftest backend/tests/test_openai_tool_loop_runner.py -q`
- `python -m pytest --noconftest backend/tests/test_backlog_007_tool_routing_performance.py -q`
- focused existing OpenAI gateway regression selected by precheck
- `python -m py_compile backend/llm_providers/shared/tool_loop_runner.py backend/llm_providers/openai/gateway.py`

## Risks
- Extracting a loop seam can accidentally move forced-tool fallback, MoA synthesis, cost accumulation, or history semantics into the provider-neutral layer; the precheck must bind a responsibility matrix before implementation.
- The flag must be directly testable in-process and default to disabled; precheck must select the narrowest existing configuration seam without creating a global configuration migration.
- The current local ChromaDB SQLite panic can block normal pytest collection, so precheck must confirm focused suites can run with `--noconftest` or document an environment blocker.

## Next Skill
`janus-preimplementation-check`

```text
@janus-preimplementation-check
Spec: documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
Task: documentation/tasks/TASK-M6_transport_phase_a.md
Backlog Item: N/A
Target Task: TASK-M6.3
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.6 Terra
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```
