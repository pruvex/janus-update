# SPEC COMPILATION RESULT - TASK-M6C.3

Canonical State: BLOCKED

- Spec: `documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md` (Phase-C T-C3).
- Task File: `N/A`.
- Generated Tasks: none.
- Execution Models: `5.6 Terra/high` after a decision-locked C3 scope.
- Validation: parent T-C3 wording and live provider-branch scan reviewed; no deterministic allowlist can be derived.
- Next Skill: `janus-feature-design`.
- Model Recommendation: `5.6 Terra/high`.

## Blocking Decision

T-C3 names only “Tote Provider-Branches entfernen” in “Orchestrator, `execution_engine`”. The live scan exposes materially different branch classes:

- `backend/services/orchestrator/execution_engine.py:_async_iter_llm_stream` directly constructs OpenAI, Gemini, and Ollama services for provider-native streaming.
- `backend/services/orchestrator/execution_dispatcher.py:_reason_and_respond_with_provider_fixes` owns Gemini-only chat-history normalization before the central gateway.
- `backend/services/llm_gateway.py` contains live provider selection, transport injection, image-generation fallback, and simple internal generation branches.

Removing any one of these branches changes a different runtime contract (streaming, history normalization, fallback, or internal generation). The parent Spec does not identify which branches are dead after Phase A/B, whether streaming is in scope, or the required safe replacement/seam. A C3 execution task would therefore invent an architecture decision.

## Required Decision

- Option A: C3 starts with one read-only dead-branch inventory and reachability proof; code removal is deferred to follow-up subtasks.
- Option B: C3 is limited to a named non-streaming branch cluster after the user selects it; streaming stays excluded.
- Option C: C3 includes the execution-engine streaming branches and requires an explicit parity/replacement design before any deletion.

Keep Context:
- `documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md` Phase-C T-C3
- `documentation/tasks/TASK-M6_transport_phase_c.md`
- C2 final-audit result and current provider-router seam

Drop Context:
- completed Phase-A/B and C1/C2 implementation detail
- T-C4 parity-test design
