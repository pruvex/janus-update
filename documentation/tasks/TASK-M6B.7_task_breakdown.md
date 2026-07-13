# TASK BREAKDOWN - TASK-M6B.7

TASK BREAKDOWN RESULT
- Spec: `documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md` (Phase-B T-B6).
- Task File: `documentation/tasks/TASK-M6_transport_phase_b.md`.
- Target Task: `TASK-M6B.7`.
- Decision: TASK DESIGN COMPLETE.
- Source Of Truth: T-B6 requires flag-gated gateway-to-transport delegation. `TASK-M6B.7_decision_summary.md` locks direct Ollama gateway request/synthesis only; Atomic/AgentRuntime/engine execution remains outside the rollout.
- Files:
  - `backend/services/llm_gateway.py`
  - `backend/llm_providers/ollama/gateway.py`
  - `backend/tests/test_transport_layer_ollama_gateway.py` (new focused regression)
  - `backend/tests/llm_providers/test_ollama_gateway.py` and `backend/tests/test_agent_factory_runtime.py` (existing bounded regressions selected by precheck)
- Tests:
  - flag absent/false preserves direct Ollama silo dispatch and injects no transport;
  - flag true for direct `ollama` constructs `OllamaLocalTransport` from the existing gateway service and injects it only into the gateway;
  - initial tool-capable and synthesis provider requests use the injected transport while tool filtering, forced-tool forwarding, budget guard, and response behavior stay gateway-owned;
  - Atomic/AgentRuntime path receives no transport and existing weather execution regression remains unchanged;
  - OpenAI and Gemini paths remain isolated.
- Execution Model: `5.6 Terra/high`.
- Readiness: one direct provider, one existing request seam, explicit flag-off behavior, and concrete Atomic exclusion with hermetic regression coverage.
- Next Skill: `janus-preimplementation-check`.
- Model Recommendation: `5.6 Terra/high`.

```text
@janus-preimplementation-check
Spec: documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
Task: documentation/tasks/TASK-M6_transport_phase_b.md
Backlog Item: N/A
Target Task: TASK-M6B.7
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.6 Terra
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```
