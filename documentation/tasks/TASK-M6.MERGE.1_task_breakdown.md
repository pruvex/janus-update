# TASK BREAKDOWN - TASK-M6.MERGE.1

## Bound Inputs

- Source Spec: `documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md`.
- Task File: `documentation/tasks/TASK-M6_MASTER_INTEGRATION.md`.
- Supporting Evidence: `documentation/tasks/TASK-M6_AGGREGATE_FINAL_AUDIT.md`; `documentation/tasks/CURSOR_M6_TOTAL_REVIEW_HANDOFF.md`; `documentation/ai/CURRENT_STATE.md`.
- Target Task: `TASK-M6.MERGE.1` only.

## Source Of Truth And Scope

- The approved M6 Spec and aggregate final audit define the M6 behavior that must survive integration.
- Current `master` is the source of truth for its newer non-M6 behavior.
- The failed merge command is the sole failure slice: `git merge --no-ff codex/m6-transport-prep` from current `master`.
- Exactly nine conflicting files are in scope. No global `ours`/`theirs` choice, new provider feature, C3 deletion, release work, or unrelated Ollama worktree change is authorized.

## File And Test Readiness

- Concrete conflict files: `CHANGELOG.md`; `PROJECT_STATE.md`; `WHAT_I_LEARNED.md`; `backend/data/schemas_intent.py`; `backend/tests/test_agent_factory_runtime.py`; `documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md`; `documentation/ai/CURRENT_STATE.md`; `documentation/codex/SKILL_USAGE_LOG.md`; `documentation/codex/model-routing/cursor_delegation_log.jsonl`.
- Required precheck must inspect merge base, master, and M6 sides for each conflict hunk before an execution allowlist is released.
- Required validation is the task-bound `schemas_intent.py` compile, agent-factory test, focused M6 regression matrix, conflict-marker scan, and scoped diff check. Precheck may narrow exact pytest selectors but may not remove provider-boundary, tool-ID, postprocessor, transport, or Websearch coverage.

## Decision

`TASK DESIGN COMPLETE`

- Target: `TASK-M6.MERGE.1` is one atomic integration task.
- Execution model: `5.6 Terra/high`.
- Readiness: ready for one `janus-preimplementation-check`; no implementation is released by this document.

```text
@janus-preimplementation-check
Spec: documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
Task: documentation/tasks/TASK-M6_MASTER_INTEGRATION.md
Backlog Item: N/A
Target Task: TASK-M6.MERGE.1
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.6 Terra
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```
