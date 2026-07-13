# TASK BREAKDOWN - TASK-M6B.4

TASK BREAKDOWN RESULT
- Spec: `documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md` (Sections 2.2, 3.2, Phase-B T-B5).
- Task File: `documentation/tasks/TASK-M6_transport_phase_b.md`.
- Target Task: `TASK-M6B.4`.
- Decision: TASK DESIGN COMPLETE.
- Source Of Truth: Phase-B T-B5 maps provider/model to `api_mode`, credential/base-URL metadata, transport class, and model ID; no gateway delegation is allowed in this slice.
- Files:
  - `backend/llm_providers/runtime_llm.py` (new resolver module)
  - `backend/services/llm_gateway.py` (bounded registry seam only)
  - `backend/tests/test_runtime_llm.py` (new focused resolver regression)
- Tests:
  - deterministic mapping coverage for OpenAI/OpenRouter, Gemini, Ollama, and the declared unsupported Codex placeholder;
  - deterministic invalid/unknown-provider failure coverage;
  - syntax and scoped diff checks.
- Execution Model: `5.6 Terra/high`.
- Readiness: scope is one resolver/registry slice; provider runtime behavior, gateway delegation, feature-flag consumer changes, transport implementation changes, fallbacks, and websearch are excluded.
- Next Skill: `janus-preimplementation-check`.
- Model Recommendation: `5.6 Terra/high`.

```text
@janus-preimplementation-check
Spec: documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
Task: documentation/tasks/TASK-M6_transport_phase_b.md
Backlog Item: N/A
Target Task: TASK-M6B.4
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.6 Terra
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```
