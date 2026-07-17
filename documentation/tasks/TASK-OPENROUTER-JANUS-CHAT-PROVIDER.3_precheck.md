# PRE-IMPLEMENTATION CHECK - TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3

PRE-CHECK RESULT
PRE-CHECK PASSED

## Pre-Check Identity

- Target Task: `TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3`
- Target Subtask: N/A
- Task: `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3_task_breakdown.md`
- Spec: `documentation/SPEC/OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md`
- Decision Summary: `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3_decision_summary.md`
- Backlog Item: N/A WITH REASON - compiled Feature Spec task
- Mode: `SINGLE_TASK_PRECHECK`
- Assigned Model: `5.6 Sol`
- Assigned Intelligence: high
- Risk: HIGH
- Artifact Identity Check: PASS - exactly one open target task, one Spec, one locked delta decision, and the matching canonical precheck path are bound.
- Implementation Started: NO
- Product Tests Executed: NO
- Live Provider/Credential Action: NO
- Git Action: NO

## Prior Blocker Resolution

### `OPENROUTER_RUNTIME_ELIGIBILITY_AUTHORITY_UNSCOPED`

RESOLVED.

- `backend/services/openrouter_credential_authority.py` is bound as the sole Janus-owned owner of keyring account constants, metadata schema/version, exact-key fingerprinting, metadata parsing, eligibility interpretation, capability construction, and allowed state transitions.
- `backend/api/routers/system.py` is the existing Settings consumer and must move its Task `.2` private helpers into that owner rather than copy them.
- Runtime eligibility receives only an immutable reader. Missing/malformed/version-mismatched/stale/mismatched/`INVALID`/`UNVERIFIED` state fails before catalog/model resolution and before transport.
- The Task forbids private-router imports, duplicated interpreters, user-editable authority, and any second path that can establish or preserve stale `VALID`.

### `OPENROUTER_AUTH_REJECTION_STATE_TRANSITION_CONTRACT_CONFLICT`

RESOLVED.

- The locked Decision Summary preserves Spec line 112: one unambiguous authenticated upstream rejection of the supplied request credential immediately changes only that exact bound key from `VALID` to `INVALID`.
- Eligibility remains read-only. The dedicated OpenRouter gateway alone receives a separate authority-owned invalidate-only capability; it never receives the Settings mutation capability.
- The reader returns an authority-issued, non-loggable opaque exact-key binding handle for the authorized request. Invalidation accepts only that handle.
- The authority performs one compare-and-transition, serialized with Settings save/replace/delete, and rechecks the current raw-key fingerprint plus metadata binding. A replacement, mismatch, stale handle, malformed state, or non-`VALID` state causes no write.
- The capability can perform only exact-current-key `VALID` to `INVALID`. It cannot grant, set, preserve, upgrade, restore, transfer, or delete `VALID`; cannot delete or return credentials; cannot target another key/provider; and cannot perform another state transition.
- The dedicated service has a safe typed seam: only an explicit SDK authentication-rejection type such as `openai.AuthenticationError`, mapped without message matching from the authenticated upstream unauthorized response, may produce the internal invalidation trigger. Rate-limit, timeout, connection, provider, model, malformed-response, stream, ambiguous auth-like, and other technical failures remain non-triggers and state-neutral.
- The gateway invokes invalidation exactly once with the request handle before returning the terminal current-turn error. The provider call is not retried or replayed, and no model/provider/credential fallback or tool rerun follows.

## Remaining Gate Review

- Scope and files: PASS - the new authority/service/gateway/test files and every existing Settings, gateway, orchestration, silo, kill-switch, transport, tool, and regression seam required by the Task are explicitly named. Existing schemas and the filtered Task `.1` catalog are reusable without modification.
- Exact model: PASS - every initial, tool, synthesis, and stream round is bound to the user-selected exact certified model; `MODEL_OVERRIDE`, MoA, helper-provider switching, aliases, and fallback are explicitly forbidden for OpenRouter.
- Upstream identity: PASS - `response.model` is required before text or tool calls are accepted. The dedicated service can propagate the top-level non-stream response identity and validate each stream chunk identity before emitting its content; missing or mismatched identity is a terminal model error.
- SDK retry: PASS - the Task requires a dedicated service, `AsyncOpenAI(max_retries=0)`, no native OpenAI tenacity decorator, and one service attempt.
- Gateway and stream retry: PASS - OpenRouter must bypass the existing two-attempt key-refresh loop, stream replay, duplicate transmission, fallback summaries that mask provider failure, and any post-tool rerun.
- Provider silo: PASS - `backend/services/llm_silo_context.py`, `backend/services/llm_gateway.py`, `backend/services/chat_orchestrator.py`, and `backend/services/orchestrator/execution_engine.py` are bound to make `openrouter` an independent cloud silo and prevent helper escape.
- Cloud kill switch: PASS - `backend/services/ops_kill_switches.py` and its focused tests are bound to add `openrouter` before transport and to retain non-secret dry-run evidence.
- Tool, permission, and confirmation parity: PASS - the common adapter, `ToolLoopRunner`, and central `ToolExecutor` remain the authorities. Exact response identity must pass before provider-formatted tool calls reach execution; allowlisting, policy decisions, permission denial, and confirmation requirements remain local and cannot be bypassed.
- Provider and credential isolation: PASS - the service is bound to only the OpenRouter key, provider identity, exact base URL, and filtered certified catalog. Native OpenAI and every other credential remain unavailable as fallback.
- Production safety: PASS - the certification registry remains intentionally empty, so Task `.3` cannot make a production OpenRouter model eligible.
- Regression evidence: PASS - binary authority, gateway, Settings, provider parity/fallback, runtime resolution, kill-switch, streaming, existing-provider, syntax, secret/leak, and headed Settings regression evidence are mandatory in execution.
- Open product decisions: NONE.
- Open architecture decisions: NONE. Concrete class shape, synchronization primitive, typed internal error representation, and test fixture mechanics remain bounded implementation choices inside the named files and binary contracts.

## Execution Risk Controls

- Use sentinel credentials only. Never read a real credential, log raw keys, expose fingerprints/binding handles, or make a live OpenRouter request.
- Hold exact-key compare-and-transition semantics across every authority-owned Settings mutation; deterministic interleaving tests must prove an old request cannot invalidate a replacement.
- Treat only the explicit typed authentication rejection as the trigger. Exception-message parsing or broad `APIStatusError`/HTTP-family matching is not acceptable.
- Validate `response.model` before emitting text, accepting tool calls, executing a tool, or accepting stream completion.
- Count every authorized provider round. Each must have exactly one attempt, including auth rejection and post-tool synthesis failure.
- Preserve existing OpenAI, Gemini, Ollama, and ChatGPT behavior, including their existing retry behavior where applicable.
- Preserve unrelated dirty-worktree content. Any later Git checkpoint remains a separate `janus-git-governance` step requiring explicit user approval.

## Validation

- Task/Spec/Decision identity and single-target scope: PASS
- Shared authority-owner and read-only eligibility scope: PASS
- Authority-owned invalidate-only contract: PASS
- Exact-key binding and TOCTOU-safe compare-and-transition: PASS
- Typed trigger and technical-error non-trigger boundary: PASS
- Exact model and `response.model` enforcement: PASS
- SDK/gateway/stream zero-retry and no replay/fallback: PASS
- Provider silo and cloud kill switch: PASS
- Tool/permission/confirmation parity: PASS
- Concrete affected-file and regression-evidence boundary: PASS
- Product tests or live-provider checks during precheck: NOT RUN by rule

## Execution Handoff

```text
legacy handoff start
NEXT: janus-executioner
Target Task: TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3
Target Subtask: N/A
Task: documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3_task_breakdown.md
Spec: documentation/SPEC/OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md
Backlog Item: N/A
Assigned Model: 5.6 Sol
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- Implement the single isolated OpenRouter chat/tool path, including the shared credential authority, read-only eligibility, exclusive invalidate-only authenticated-rejection capability, exact-key/TOCTOU protection, exact-model identity, zero retry/replay/fallback, silo, kill-switch, and tool/permission parity contracts.
- Only a typed unambiguous authenticated rejection of the supplied request credential may invoke invalidation; all technical and ambiguous failures remain state-neutral.
Affected Files:
- backend/services/openrouter_credential_authority.py
- backend/api/routers/system.py
- backend/llm_providers/openrouter/__init__.py
- backend/llm_providers/openrouter/service.py
- backend/llm_providers/openrouter/gateway.py
- backend/llm_providers/runtime_llm.py
- backend/llm_providers/transports/openai_compat.py
- backend/llm_providers/shared/tool_call_adapter.py
- backend/llm_providers/shared/response_postprocessors.py
- backend/services/llm_gateway.py
- backend/services/chat_orchestrator.py
- backend/services/llm_silo_context.py
- backend/services/ops_kill_switches.py
- backend/services/orchestrator/execution_engine.py
- backend/tests/test_openrouter_credential_authority.py
- backend/tests/test_openrouter_key_settings_api.py
- backend/tests/test_openrouter_provider.py
- backend/tests/test_provider_parity.py
- backend/tests/test_provider_auth_fallback.py
- backend/tests/test_runtime_llm.py
- backend/tests/test_ops_kill_switches.py
- backend/tests/test_streaming_tool_loop_runner.py
- tests/e2e/openrouter-settings.spec.js (evidence-only unchanged headed regression runner)
Evidence Focus:
- Authority tests: sole interpreter, immutable eligibility, capability minimality, exact matching VALID-to-INVALID, idempotence, non-trigger no-write, provider/key isolation, and deterministic replacement interleaving.
- Gateway/service tests: typed auth trigger once, every non-trigger zero times, exact request/response model, no pre-identity tool execution, one provider attempt, no replay/fallback/tool rerun, no secret/binding leakage.
- Settings regressions: complete Task .2 lifecycle after helper migration, runtime INVALID visibility, replacement isolation, and only successful Settings validation establishing VALID.
- Silo, kill-switch, tool adapter, ToolExecutor permission/confirmation, runtime resolution, provider-fallback, streaming, and existing-provider regression assertions.
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
- Do not populate the certification registry, add UI/DeepDive/release work, access real credentials, or make live provider calls.
Automated Evidence Gate:
- python -m pytest -q backend/tests/test_openrouter_credential_authority.py backend/tests/test_openrouter_key_settings_api.py backend/tests/test_openrouter_provider.py
- python -m pytest -q backend/tests/test_provider_parity.py backend/tests/test_provider_auth_fallback.py backend/tests/test_runtime_llm.py backend/tests/test_ops_kill_switches.py backend/tests/test_streaming_tool_loop_runner.py
- python -m pytest -q backend/tests/test_openai_compat_transport.py backend/tests/test_transport_layer_openai_gateway.py backend/tests/test_transport_layer_gemini_gateway.py backend/tests/test_transport_layer_ollama_gateway.py
- python -m py_compile backend/services/openrouter_credential_authority.py backend/api/routers/system.py backend/llm_providers/openrouter/__init__.py backend/llm_providers/openrouter/service.py backend/llm_providers/openrouter/gateway.py backend/llm_providers/runtime_llm.py backend/llm_providers/transports/openai_compat.py backend/llm_providers/shared/tool_call_adapter.py backend/llm_providers/shared/response_postprocessors.py backend/services/llm_gateway.py backend/services/chat_orchestrator.py backend/services/llm_silo_context.py backend/services/ops_kill_switches.py backend/services/orchestrator/execution_engine.py
- node --check tests/e2e/openrouter-settings.spec.js
- Required runner form: npx playwright test <runner> --headed --workers=1 --reporter=list
- npx playwright test tests/e2e/openrouter-settings.spec.js --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, Decision Summary, prior blocker identity, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md
- documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3_decision_summary.md
- documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3_task_breakdown.md
- documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3_precheck.md
- named affected files and evidence commands only
Drop Context:
- superseded blocked-precheck prose
- old refinement conversation
- unrelated Tasks .4 through .6, backlog, audit, release, and Git history
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths. Stop before final audit, documentation closeout, Git, release, or production activation.
Expected Output:
- Implementation result, executed checks, affected files, residual risks, and exact next-skill handoff.
legacy handoff end
```

## NEXT STEP

Recommended Skill: janus-executioner

Recommended Model: `5.6 Sol`

Recommended Intelligence: high

User Action: Execute exactly `TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3` from this canonical PASS artifact; do not broaden scope or perform live-provider, credential, Git, release, or production actions.
