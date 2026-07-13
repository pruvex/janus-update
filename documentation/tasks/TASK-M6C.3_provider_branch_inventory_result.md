# PROVIDER-BRANCH REACHABILITY INVENTORY - TASK-M6C.3

Canonical State: PASS (read-only inventory); parent T-C3 deletion remains open.

## Scan Scope

- `backend/services/orchestrator/execution_engine.py:_async_iter_llm_stream`
- `backend/services/orchestrator/execution_dispatcher.py:_reason_and_respond_with_provider_fixes`
- `backend/services/llm_gateway.py:simple_llm_generate_content`

## Evidence

| Symbol | Static call / registration evidence | Classification | Deletion decision |
| --- | --- | --- | --- |
| `_async_iter_llm_stream` | Called by `execution_engine.py:3508`; covered by `backend/tests/test_streaming_tool_loop_runner.py`. | RETAINED | No deletion task. It owns active provider-native streaming. |
| `_reason_and_respond_with_provider_fixes` | Bound at `execution_dispatcher.py:1804` as `reason_and_respond_fn` for the active workflow gateway kwargs. | RETAINED | No deletion task. It owns active Gemini history normalization. |
| `simple_llm_generate_content` | Called by `agent_planner.py:111`, `project_service.py:51`, and `finance_tools.py:460`; agent-factory tests monkeypatch it. | RETAINED | No deletion task. It serves active internal generation. |

## Commands

- `rg -n "_async_iter_llm_stream\\(|_reason_and_respond_with_provider_fixes\\(|simple_llm_generate_content\\(" backend tests -g '*.py'`: PASS.
- `rg -n "_reason_and_respond_with_provider_fixes" . -g '*.py' -g '*.md' -g '*.json' -g '*.cjs'`: PASS; found active workflow registration at `execution_dispatcher.py:1804`.
- `rg -n "_async_iter_llm_stream|simple_llm_generate_content" backend/tests tests -g '*.py'`: PASS; found focused test evidence.
- `git diff --check`: PASS.

## Conclusion

No reviewed candidate is dead. This inventory grants no deletion authority and does not complete parent T-C3. Any further C3 work must begin with a new, separately bounded candidate inventory; T-C4 parity-test routing may proceed independently.

## Extended Scan

- The remaining provider branches in `execution_engine` are active streaming contracts: native service selection, provider-specific forced-tool normalization, Gemini history normalization, tool-call assembly, and grounding handling.
- The dispatcher’s Gemini normalization helper is actively registered into workflow gateway kwargs and is consumed before central gateway invocation.
- The remaining `llm_gateway` provider branches govern active transport injection, image fallback, and internal generation.

Extended conclusion: no safe deletion candidate is visible without redesigning active streaming or provider contracts. Parent T-C3 remains an explicit architecture-debt follow-up, not an executable cleanup slice.
