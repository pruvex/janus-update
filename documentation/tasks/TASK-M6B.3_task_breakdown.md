# TASK BREAKDOWN - TASK-M6B.3

## Binding Sources
- Spec: `documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md` (Sections 2.2, 2.4, 3.1 and Phase-B `T-B4`).
- Parent Task: `documentation/tasks/TASK-M6_transport_phase_b.md`.
- Backlog Item: `N/A` - approved spec-driven infrastructure slice.

## Released Target
- Target Task: `TASK-M6B.3`.
- Title: Add the Ollama-local transport as a 1:1 service wrapper.
- Execution Model: `5.6 Terra`, `high`; later code execution is Cursor-first with Codex review of the bounded diff and evidence.
- Readiness: `PRECHECK_READY`.

## Atomic Scope
- Add `OllamaLocalTransport` as one `BaseTransport` implementation over an injected existing `OllamaServiceProvider` seam.
- Delegate non-streaming `send`, tool normalization, and second-call history preparation to the existing Ollama service. Preserve its local endpoint selection, capability cache, native/non-native tool fallback, deadline/retry behavior, response normalization, and gateway policy by not transforming requests, responses, metadata, tool results, or history in the transport.
- Update the transport package export and add hermetic fake-service regressions. Keep `TRANSPORT_LAYER_ENABLED=false` and do not wire a caller.

## Files
- `backend/llm_providers/transports/ollama_local.py` (new).
- `backend/llm_providers/transports/__init__.py` (extend export only).
- `backend/tests/test_ollama_local_transport.py` (new).

## Explicit Exclusions
- No change to `backend/llm_providers/ollama/service.py`, `backend/llm_providers/ollama/gateway.py`, `backend/llm_providers/ollama/adapter.py`, `backend/llm_providers/ollama_service.py`, `backend/llm_providers/shared/tool_loop_runner.py`, `backend/llm_providers/shared/tool_call_adapter.py`, `backend/llm_providers/runtime_llm.py`, `backend/services/llm_gateway.py`, or `backend/services/orchestrator/execution_engine.py`.
- No local endpoint, model-node, capability-profile/cache, native-tool fallback, retry/deadline, streaming, structured response, image, provider fallback, resolver/gateway integration, flag consumer/flip, OpenRouter/OAuth/Gemini work, network call, Git action, or broad test-suite run.

## Acceptance Criteria
- `OllamaLocalTransport` implements every `BaseTransport` seam.
- `send` transparently delegates the existing Ollama service arguments and response; no request, response, metadata, tool-result, local endpoint, or capability reshaping is introduced in the wrapper.
- `normalize_tools` delegates to the existing Ollama service OpenAI-compatible conversion; canonical skill IDs remain at the existing boundary.
- `prepare_history_for_second_call` delegates unchanged to the existing Ollama service.
- Focused tests use a fake/mocked service, need no credentials, do not construct an OpenAI client, and make no network call.
- No existing runtime path is changed; the Phase-B flag remains default-off and unconsumed.

## Tests
- `python -m pytest --noconftest backend/tests/test_ollama_local_transport.py -q`.
- `python -m py_compile backend/llm_providers/transports/__init__.py backend/llm_providers/transports/ollama_local.py`.
- Precheck selects the directly relevant existing Ollama adapter regressions; unrelated ChromaDB-dependent suites are out of scope.

## Risks and Evidence Focus
- Risk: moving Ollama endpoint, capability, native-tool fallback, or response-normalization behavior into the wrapper. Mitigation: fake-service delegation tests assert exact pass-through and the transport remains a thin adapter only.
- Risk: tool conversion drifts from the existing local-service OpenAI-compatible boundary. Mitigation: focused regression proves the service conversion seam is called; no new sanitizer or capability policy is added.
- Risk: accidental live routing activation. Mitigation: static scope review excludes service, gateway, adapter, resolver, runner, and flag-consumer files.

## Next Skill
`janus-preimplementation-check`

```text
@janus-preimplementation-check
Spec: documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
Task: documentation/tasks/TASK-M6_transport_phase_b.md
Backlog Item: N/A
Target Task: TASK-M6B.3
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.6 Terra
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```
