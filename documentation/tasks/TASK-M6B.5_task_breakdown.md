# TASK BREAKDOWN - TASK-M6B.5

TASK BREAKDOWN RESULT
- Spec: `documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md` (Phase-B T-B6, Phase-B exit, feature-flag rule).
- Task File: `documentation/tasks/TASK-M6_transport_phase_b.md`.
- Target Task: `TASK-M6B.5`.
- Decision: TASK DESIGN COMPLETE.
- Source Of Truth: T-B6 says `Gateways -> Transport-Delegation` and Phase-B exit requires `llm_gateway.reason_and_respond()` to use transport plus runner behind `TRANSPORT_LAYER_ENABLED=false`.
- Decision Summary: `documentation/tasks/TASK-M6B.5_decision_summary.md` (OpenAI-compatible family selected; current implementation slice is the existing direct `openai` path only because `openrouter` has no live gateway silo yet).
- Files: `backend/services/llm_gateway.py`; `backend/llm_providers/openai/gateway.py`; `backend/tests/test_transport_layer_openai_gateway.py` (new focused flag-on/flag-off regression); update `backend/tests/test_runtime_llm.py` only if the existing resolver test needs the flag boundary asserted.
- Tests: hermetic tests must prove (1) absent/false flag keeps `llm_gateway.reason_and_respond()` on the unmodified silo call, (2) true flag constructs `OpenAICompatTransport` from the existing OpenAI gateway service and passes it only to the direct OpenAI gateway path, and (3) Gemini/Google/Ollama/OpenRouter never receive the new transport argument. Existing OpenAI tool-loop runner regression remains selected by precheck.
- Execution Model: `5.6 Terra/high`.
- Readiness: precheck-ready. The locked adapter seam is gateway-owned: `llm_gateway.reason_and_respond()` preserves access policy and skill selection, creates `OpenAICompatTransport` from the selected `OpenAIGateway.service` only for resolved `openai_compat` with a true flag, and forwards it as an optional dependency. `OpenAIGateway` alone replaces its existing service-level requests and second-call-history callback with that injected transport; it retains all current orchestration, runner, policy, synthesis, response shaping, and cost persistence.
- Scope Rules: no provider-specific branch removal; no OpenRouter/Gemini/Google/Ollama/Codex enablement; no change when flag is absent/false; no service request construction duplication; no streaming or Websearch work.
- Next Skill: `janus-preimplementation-check`.
- Model Recommendation: `5.6 Terra/high`.

```text
@janus-preimplementation-check
Spec: documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
Task: documentation/tasks/TASK-M6_transport_phase_b.md
Backlog Item: N/A
Target Task: TASK-M6B.5
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.6 Terra
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```
