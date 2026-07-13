# AUDIT PACKAGE - TASK-M6.3 ToolLoopRunner

## Goal

Audit the bounded Phase-A T-A3 extraction of the OpenAI tool loop into a default-off `ToolLoopRunner`.

## Bound Inputs

- Spec: `documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md` (Section 3.3 and Phase-A T-A3 only).
- Parent task: `documentation/tasks/TASK-M6_transport_phase_a.md` (`TASK-M6.3` only).
- Backlog Item: N/A WITH REASON - spec-driven infrastructure slice.
- Precheck: `documentation/tasks/TASK-M6.3_preimplementation_check.md` (`PRE-CHECK PASSED`).
- Execution result: `documentation/tasks/TASK-M6.3_execution_result.md` (focused evidence PASS; final-audit handoff).
- Manual Janus evidence: N/A WITH REASON - the feature flag defaults to false, so production behavior is unchanged; the flag-on extraction has deterministic focused evidence.
- Pipeline completion: `TASK-M6.3` implementation complete; parent M6 remains in progress because T-A4 and T-A5 are separate tasks.

## Scope Rules

- Audit only the OpenAI default-off runner slice.
- The runner may own MoA resolution, tool preparation, prevalidation, bounded rounds, execution, and history preparation.
- The OpenAI gateway retains forced-tool fallback construction, synthesis, routing guards, link repair, response shaping, and cost persistence.
- Gemini, streaming, transport classes, runtime resolver, OAuth, OpenRouter product behavior, ToolCallAdapter, provider policy, and MoA hierarchy are out of scope.

## Changed Files

- `backend/llm_providers/shared/tool_loop_runner.py` (new).
- `backend/llm_providers/openai/gateway.py`.
- `backend/tests/test_openai_tool_loop_runner.py` (new).
- `development/openrouter-skill-tests/janus-executioner/m6_3_tool_loop_runner_2026-07-11/`.
- `documentation/codex/model-routing/cursor-worker-runs/WF-M6.3-EXECUTION-GATE-2026-07-11-002/`.
- `documentation/codex/model-routing/cursor_delegation_log.jsonl`.
- `documentation/tasks/TASK-M6.3_task_breakdown.md`.
- `documentation/tasks/TASK-M6.3_preimplementation_check.md`.
- `documentation/tasks/TASK-M6.3_execution_result.md`.
- `documentation/tasks/TASK-M6.3_cursor_execution_probe_2026-07-11.md`.

## Diff And Boundary Summary

- `_run_full_tool_loop` dispatches to `_run_legacy_tool_loop` while the flag is false and to `_run_full_tool_loop_with_runner` only when enabled.
- `ToolLoopRunner` has no Gemini-specific imports or behavior.
- The runner defers the heavy shared-utility import until a real runner call, avoiding a new import-chain cost on the disabled dispatch path.
- The focused test proves false default, truthy flag recognition, deterministic one-tool runner behavior, and the gateway's explicit legacy-versus-runner dispatch structure.

## Validation

- `python -m pytest --noconftest backend/tests/test_openai_tool_loop_runner.py -q`: PASS, `4/4`.
- `python -m py_compile backend/llm_providers/shared/tool_loop_runner.py backend/llm_providers/openai/gateway.py`: PASS.
- `git diff --check`: PASS.
- `validate_execution_result.py documentation/tasks/TASK-M6.3_execution_result.md`: PASS.
- `python -m pytest --noconftest backend/tests/test_backlog_007_tool_routing_performance.py -q`: N/A WITH REASON - independent local ChromaDB SQLite panic before collection (`range start index 10 out of range for slice of length 9`).

## Cursor Evidence

- Shared gate `WF-M6.3-EXECUTION-GATE-2026-07-11-001`: `CURSOR_WORKER_OUTPUT_UNREADABLE` because the delegate passed unsupported `--cursor-pool auto_composer`.
- Direct valid worker `WF-M6.3-EXECUTION-GATE-2026-07-11-002`: package and allowlist PASS; Composer started, then `CURSOR_AGENT_TIMEOUT` after 180 seconds without structured output.
- The timed-out Composer left only allowlisted candidate changes. Codex reviewed the candidate, made bounded compatibility/testability corrections, and owns the listed validation.

## Risks And Open Issues

- P2 non-blocking: the broad existing OpenAI regression and full collection cannot run until the independent local ChromaDB SQLite panic is repaired.
- P2 non-blocking: Cursor is not yet an autonomous productive worker because the shared delegate has an argument-contract defect and Composer returns no structured result before timeout.
- Parent M6 Phase A is not complete: T-A4 (Gemini migration) and T-A5 (streaming path) remain open.

## Audit Decision Inputs

- No scope drift found in the runner/gateway/test diff.
- Manual Janus evidence is N/A with a concrete default-off reason.
- `PASS WITH FIXES` is appropriate only if the two P2 infrastructure limitations remain explicitly non-blocking for the reviewed M6.3 product slice.
