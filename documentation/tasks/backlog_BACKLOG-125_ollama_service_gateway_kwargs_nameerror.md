# Selected Backlog Handoff - BACKLOG-125

## Binding
- Backlog Item: `BACKLOG-125 - Ollama-Service bricht lokale Antworten durch undefiniertes gateway_kwargs ab`.
- Entry Point: `PRE_IMPLEMENTATION_VERIFICATION`.
- Source Evidence: `documentation/tasks/TASK-M6B.3_debug_result.md`, local untracked `documentation/logs/janus_backend.log`, and `backend/llm_providers/ollama/service.py:203,223`.

## Handoff Scope
- Correct only the existing undefined `gateway_kwargs` reference in the bounded Ollama-service response path.
- Add one focused hermetic service regression covering the failed normal response path; precheck must bind the exact test file and mock seam.
- Re-run the default-off local-Ollama weather smoke after automated evidence passes.

## Explicit Exclusions
- No `OllamaLocalTransport` integration, resolver/gateway refactor, feature-flag consumer or flip, endpoint/model-node policy, capability cache, native-tool fallback, retry-policy redesign, streaming change, provider fallback, credential change, Git action, or M6B.3 scope expansion.

## Acceptance Focus
- The reproduced normal Ollama response path no longer raises `NameError` or the resulting atomic-agent fallback.
- The focused regression fails on the old undefined-variable behavior and passes after the bounded correction.
- With `TRANSPORT_LAYER_ENABLED=false`, the manual local-Ollama weather smoke returns the normal weather answer.

## HANDOFF_SCOPE
- Backlog Item: BACKLOG-125
- Entry Point: PRE_IMPLEMENTATION_VERIFICATION
- Required Artifact: this selected handoff
- Required Next Skill: janus-preimplementation-check
- Evidence Paths: `documentation/tasks/TASK-M6B.3_debug_result.md`; `backend/llm_providers/ollama/service.py:203,223`; local `documentation/logs/janus_backend.log`
- Dropped Context: M6B.3 transport implementation details, later M6 Phase-B work, unrelated open Backlog items, and broad backlog history

## Next Skill Copy Prompts

```text
@[/SKILL 3 - PRE-IMPLEMENTATION VERIFICATION]
Target Task: BACKLOG-125
Task: documentation/tasks/backlog_BACKLOG-125_ollama_service_gateway_kwargs_nameerror.md
Backlog Item: BACKLOG-125
```
