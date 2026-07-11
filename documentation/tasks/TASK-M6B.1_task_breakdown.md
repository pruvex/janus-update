# TASK BREAKDOWN - TASK-M6B.1

## Binding Sources
- Spec: `documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md` (Sections 2.2, 2.4, 3.1, 3.3 and Phase-B `T-B1`/`T-B2`).
- Parent Task: `documentation/tasks/TASK-M6_transport_phase_b.md`.
- Backlog Item: `N/A` - approved spec-driven infrastructure slice.

## Released Target
- Target Task: `TASK-M6B.1`.
- Title: Establish the BaseTransport contract and OpenAI-compatible vertical slice.
- Execution Model: `5.6 Terra`, `high`; later code execution is `Cursor-first` with Codex review of the bounded diff and evidence.
- Readiness: `PRECHECK_READY`.

## Atomic Scope
- Create the minimal abstract `BaseTransport` contract for the Spec-declared non-streaming `send`, tool-normalization, and `prepare_history_for_second_call` seams.
- Create `OpenAICompatTransport` as the first concrete API-family adapter. It delegates request execution and history construction to the existing `OpenAIServiceProvider`; it does not duplicate service request compilation, response-cost accounting, or streaming.
- Keep canonical skill IDs until the existing OpenAI ToolCallAdapter boundary and keep `TRANSPORT_LAYER_ENABLED=false`. No caller, resolver, gateway, runner, or feature-flag integration is allowed in this task.

## Files
- `backend/llm_providers/shared/base_transport.py` (new).
- `backend/llm_providers/transports/__init__.py` (new).
- `backend/llm_providers/transports/openai_compat.py` (new).
- `backend/tests/test_base_transport.py` (new).
- `backend/tests/test_openai_compat_transport.py` (new).

## Explicit Exclusions
- No modification to `backend/llm_providers/openai/service.py`, `backend/llm_providers/openai/gateway.py`, `backend/llm_providers/shared/tool_loop_runner.py`, `backend/services/llm_gateway.py`, or `backend/services/orchestrator/execution_engine.py`.
- No `runtime_llm.resolve()`, gateway selection/delegation, OpenRouter endpoint, Gemini/Ollama transport, OAuth, Websearch, streaming migration, cost-model change, or `TRANSPORT_LAYER_ENABLED` flip.
- No network call, API key, staging smoke, commit, push, release, or broad test-suite execution.

## Acceptance Criteria
- `BaseTransport` exposes and enforces the three declared contract seams.
- `OpenAICompatTransport` implements all contract seams and delegates non-streaming request/history behavior to an injected existing OpenAI service seam.
- Existing OpenAI tool normalization is used at the transport boundary; canonical IDs are not globally rewritten.
- Existing production behavior is unchanged because no existing caller is rerouted and the Phase-B flag remains default-off.
- The two focused tests are hermetic: they use a fake/mocked service, require no credentials, and make no external request.

## Tests
- `python -m pytest --noconftest backend/tests/test_base_transport.py backend/tests/test_openai_compat_transport.py -q`.
- `python -m py_compile backend/llm_providers/shared/base_transport.py backend/llm_providers/transports/__init__.py backend/llm_providers/transports/openai_compat.py`.
- Precheck selects only directly relevant existing OpenAI service/ToolCallAdapter regressions; unrelated ChromaDB-dependent suites are out of scope.

## Risks and Evidence Focus
- Risk: the new abstraction could accidentally duplicate or bypass OpenAI service responsibilities. Mitigation: injected fake-service tests assert exact delegation and untouched response pass-through.
- Risk: tool-name normalization could migrate out of its existing boundary. Mitigation: focused regression asserts use of the existing adapter behavior rather than a new global normalization rule.
- Risk: scope expansion into live routing. Mitigation: static review/diff check against the explicit exclusion list and no flag consumer changes.

## Next Skill
`janus-preimplementation-check`

```text
@janus-preimplementation-check
Spec: documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
Task: documentation/tasks/TASK-M6_transport_phase_b.md
Backlog Item: N/A
Target Task: TASK-M6B.1
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.6 Terra
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```
