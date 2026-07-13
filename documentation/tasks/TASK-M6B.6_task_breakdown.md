# TASK BREAKDOWN - TASK-M6B.6

TASK BREAKDOWN RESULT
- Spec: `documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md` (Phase-B T-B6).
- Task File: `documentation/tasks/TASK-M6_transport_phase_b.md`.
- Target Task: `TASK-M6B.6`.
- Decision: TASK DESIGN COMPLETE.
- Source Of Truth: T-B6 requires flag-gated gateway-to-transport delegation. `TASK-M6B.6_decision_summary.md` locks the normal Gemini tool-loop only; engine-owned and drill-down paths stay outside the first Gemini rollout.
- Files:
  - `backend/services/llm_gateway.py`
  - `backend/llm_providers/gemini/gateway.py`
  - `backend/tests/test_transport_layer_gemini_gateway.py` (new focused regression)
  - existing Gemini tool-loop runner regression selected by precheck
- Tests:
  - flag absent/false preserves direct Gemini silo dispatch and injects no transport;
  - flag true for direct `gemini` creates `GeminiNativeTransport` from the existing gateway service and injects it only into `_run_simple_tool_loop`;
  - normal legacy and runner tool-loop paths use transport send/history seams while retaining grounding, model policy, and cost attribution callbacks;
  - engine-owned and drill-down paths receive no transport; no direct `google` gateway route is introduced.
- Execution Model: `5.6 Terra/high`.
- Readiness: one direct provider, one normal-loop seam, explicit flag-off behavior, concrete exclusions, and hermetic regression surface. The current router has no direct `google` silo, so the resolved Google family is not activated in this slice.
- Next Skill: `janus-preimplementation-check`.
- Model Recommendation: `5.6 Terra/high`.

```text
@janus-preimplementation-check
Spec: documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
Task: documentation/tasks/TASK-M6_transport_phase_b.md
Backlog Item: N/A
Target Task: TASK-M6B.6
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.6 Terra
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```
