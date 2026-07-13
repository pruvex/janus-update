# TASK BREAKDOWN - TASK-M6C.2

TASK BREAKDOWN RESULT
- Spec: `documentation/SPEC/Spec Done/M6C2_response_postprocessor_extraction.md`.
- Task File: `documentation/tasks/TASK-M6C.2_response_postprocessors.md`.
- Target Task: `TASK-M6C.2`.
- Decision: TASK DESIGN COMPLETE.
- Source Of Truth: the C2 Spec and the user's locked Option A assign invocation ownership to `backend/services/llm_gateway.py:reason_and_respond` after the selected silo response returns.

## Bound Live Seam

- `backend/services/llm_gateway.py:reason_and_respond` is the shared provider router and currently returns the selected silo response directly.
- `backend/llm_providers/openai/gateway.py` performs release-list link repair only inside its `tool_results` synthesis branch, after gateway-owned quality guards.
- `backend/llm_providers/gemini/gateway.py` preserves Gemini metadata on the returned result; its comments name a later orchestrator renderer, but no consumed caller of the advertised final-render method was found in the bound response path.
- The user selected `llm_gateway.reason_and_respond` as the central owner. This resolves the only task-breakdown ambiguity while preserving the approved full OpenAI-plus-Gemini scope.

## Precheck-Ready Scope

- Files:
  - `backend/llm_providers/shared/response_postprocessors.py` (new)
  - `backend/services/llm_gateway.py`
  - `backend/llm_providers/openai/gateway.py`
  - `backend/llm_providers/gemini/gateway.py`
  - `backend/tests/test_response_postprocessors.py` (new)
  - Existing focused OpenAI/Gemini response regressions selected by precheck only after import and call-site verification.
- Tests:
  - Hermetic shared-boundary behavior for OpenAI release-list links, Gemini grounding/link rendering, missing metadata, and unregistered provider families.
  - Regression checks that gateway-owned quality, cost, and synthesis behavior remain outside the new registry.
  - Syntax and scoped diff checks.
- Risks:
  - The router must receive and preserve the response context needed by the existing provider-specific behaviors.
  - Engine-owned/drill-down and streaming paths remain excluded unless they already traverse the bound central return seam.

## Acceptance Criteria

- OpenAI release-list link output remains visible after central post-processing.
- Gemini grounding and link output remains visible after central post-processing.
- Missing optional metadata and unregistered provider families leave responses unchanged without rendering failure.
- No Websearch policy, provider fallback, model policy, transport enablement, tool execution, streaming, persistence, or unrelated provider-branch behavior changes.
- Focused regressions remain hermetic and require no provider credentials or network access.

```text
@janus-preimplementation-check
Spec: documentation/SPEC/Spec Done/M6C2_response_postprocessor_extraction.md
Task: documentation/tasks/TASK-M6C.2_response_postprocessors.md
Backlog Item: N/A
Target Task: TASK-M6C.2
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.6 Terra
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```

NEXT STEP
Recommended Skill: `janus-preimplementation-check`
Recommended Model: `5.6 Terra`
Recommended Intelligence: `high`
Required User Decision: select Option A or Option B, then regenerate/review the C2 delta Spec before compiling a precheck handoff.
Resolved User Decision: Option A selected. `backend/services/llm_gateway.py:reason_and_respond` owns the central post-response invocation; the C2 delta Spec and task artifact were regenerated and review-validated.
