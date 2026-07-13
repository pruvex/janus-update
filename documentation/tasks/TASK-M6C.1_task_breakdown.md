# TASK BREAKDOWN - TASK-M6C.1

TASK BREAKDOWN RESULT
- Spec: `documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md` (Phase-C T-C1).
- Task File: `documentation/tasks/TASK-M6_transport_phase_c.md`.
- Target Task: `TASK-M6C.1`.
- Decision: TASK DESIGN COMPLETE.
- Source Of Truth: Phase-C `T-C1` requires Websearch to be decoupled from `tool_executor`; Exit C requires Websearch without provider coercion in the executor; the approved flag table defines `TRANSPORT_WEBSEARCH_DECOUPLED=false` as the Phase-C rollout guard. Source review confirms the live `system.websearch` path is `ToolExecutor -> backend.tool_registry:websearch_wrapper -> backend.services.websearch.websearch:execute_websearch_service`.
- Files:
  - `backend/services/tool_executor.py`
  - `backend/tool_registry.py`
  - `backend/tests/test_backlog_007_tool_routing_performance.py`
  - `backend/tests/tools/test_websearch.py`
- Acceptance Criteria:
  - With `TRANSPORT_WEBSEARCH_DECOUPLED` absent or `false`, the existing executor-owned Websearch behavior remains preserved.
  - With the flag true, Websearch-specific provider/model coercion is no longer owned by `ToolExecutor`; `websearch_wrapper` receives the existing request context and owns that policy.
  - The focused regressions preserve provider/model compatibility and cross-provider safety without changing gateways, transports, schemas, or unrelated tools.
- Tests:
  - flag absent/false preserves the existing `system.websearch` executor behavior;
  - flag true proves that the executor no longer applies Websearch-specific provider/model coercion;
  - `websearch_wrapper` receives the context needed to retain provider/model compatibility and cross-provider safety behavior;
  - OpenAI and Gemini Websearch compatibility regressions remain hermetic and no network credentials are used;
  - syntax and scoped-diff checks cover only the approved file cluster.
- Execution Model: `5.6 Terra/high`.
- Readiness: one approved Phase-C table entry, the verified executor-to-ToolRegistry Websearch seam, default-off rollout protection, concrete tests, and no dependency on T-C2 through T-C4.
- Next Skill: `janus-preimplementation-check`.
- Model Recommendation: `5.6 Terra/high`.

```text
@janus-preimplementation-check
Spec: documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
Task: documentation/tasks/TASK-M6_transport_phase_c.md
Backlog Item: N/A
Target Task: TASK-M6C.1
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.6 Terra
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```
