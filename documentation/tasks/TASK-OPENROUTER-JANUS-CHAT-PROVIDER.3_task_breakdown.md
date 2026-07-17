# TASK BREAKDOWN - TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3

## Source Identity

- **Spec:** `documentation/SPEC/OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md`
- **Task File:** `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.md`
- **Backlog Item:** N/A WITH REASON - compiled Feature Spec task
- **Prior Gates:** `janus-spec-review` APPROVED; Tasks `.1` and `.2` Final Audit PASS; Task `.3` first precheck blocker `OPENROUTER_RUNTIME_ELIGIBILITY_AUTHORITY_UNSCOPED` resolved by the shared authority-owner refinement; rerun precheck blocked with `OPENROUTER_AUTH_REJECTION_STATE_TRANSITION_CONTRACT_CONFLICT`; the locked Decision Summary preserves Spec line 112 and authorizes only an authority-owned exact-key-safe invalidate-only path; parent feature remains `PARTIAL IMPLEMENTATION (2/6)`
- **Blocked Precheck:** `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3_precheck.md`

## Selected Target

- **Target Task:** `TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3`
- **Target Subtask:** N/A
- **Mode:** SINGLE_TASK_PRECHECK
- **Goal:** Add one isolated, fail-closed OpenRouter chat path through the existing OpenAI-compatible transport while Janus retains full control of redaction, necessary context, skills, canonical tools, permissions, confirmations, and tool execution, with exact-model enforcement and zero Janus retry, replay, model fallback, or provider fallback.

## Scope

- Add `backend/services/openrouter_credential_authority.py` as the single Janus-owned owner of the OpenRouter keyring accounts, metadata schema/version, exact-key fingerprint calculation, metadata parsing, eligibility-state interpretation, and all allowed validation-state transitions. Move the existing Task `.2` private interpretation from `backend/api/routers/system.py` into this owner; do not copy it.
- Expose three capability-separated consumers/contracts from that owner: a Settings-only mutation capability used by `backend/api/routers/system.py`; an immutable runtime eligibility reader passed to the dedicated OpenRouter gateway; and a separate invalidate-only capability available exclusively to that dedicated OpenRouter gateway. The reader may return an eligible credential plus a non-loggable opaque exact-key binding handle only when the currently stored exact key is bound to metadata state `VALID`; it remains read-only and has no state-mutation method.
- The invalidate-only capability accepts only the authority-issued binding handle for the authorized request and can perform exactly one transition: the same exact currently stored key from `VALID` to `INVALID`. The authority must compare the handle against the current raw-key fingerprint and current metadata inside one authority-owned compare-and-transition boundary that is serialized with Settings save, replace, and delete mutations. A missing, malformed, stale, mismatched, replaced, non-`VALID`, or differently bound current value produces no write. The capability cannot set, grant, preserve, upgrade, restore, transfer, or delete `VALID`; cannot delete or return a credential; cannot select another key/provider; and cannot perform any other metadata transition.
- Add a dedicated OpenRouter provider service and gateway. The service uses only the OpenRouter key and `https://openrouter.ai/api/v1`; it must not reuse the native OpenAI service, credential, retry decorator, client, gateway, or model routing.
- Before catalog/model resolution and before every external transmission, the dedicated gateway must read the current credential through the shared read-only authority. Missing raw key, missing/malformed/version-mismatched metadata, stale or mismatched exact-key fingerprint, `INVALID`, or `UNVERIFIED` ends the current turn fail closed before catalog access and transmits zero requests. Only after that pass may the gateway retain the authority-issued binding handle, require the selected exact model in the filtered Task `.1` certified catalog, and transmit that same exact ID.
- Reuse the existing OpenAI-compatible transport protocol and shared tool-loop machinery only where their behavior satisfies the OpenRouter contract. Keep the provider identity `openrouter` throughout transport, tool mapping, silo context, kill-switch checks, orchestration, errors, and tests.
- Use the same Janus-controlled redaction, necessary conversation context, selected skill/tool definitions, canonical tool-name mapping, `ToolExecutor`, permission rules, and confirmation rules as other external API-key providers.
- Pin the user-selected exact certified model for every text request, tool round, synthesis round, and stream continuation. Disable MoA resolution, model overrides, helper-provider switching, auth fallback, model fallback, and provider fallback for OpenRouter.
- Make every OpenRouter layer single-attempt: SDK/client automatic retries disabled, no tenacity retry wrapper, no gateway key-refresh retry, no stream replay, no duplicate transmission after partial output, and no tool rerun after a provider/transport/model failure.
- Validate upstream `response.model` against the exact selected model before treating text, tool calls, synthesis, or stream completion as success. Missing or mismatched identity ends the current turn fail closed.
- Contain non-secret auth, provider, model, transport, and stream failures to the current turn. The dedicated OpenRouter service must classify a typed authenticated-request rejection only when the authenticated upstream response unambiguously rejects the supplied credential as unauthorized; raw exception text, malformed responses, ambiguous auth-like errors, network/timeout/rate-limit/provider/model/stream failures, and all other technical failures cannot produce that classification. Only this typed rejection lets the dedicated gateway invoke the invalidate-only capability exactly once with the binding handle captured for that request, before returning the terminal current-turn error. No rejection or invalidation path may retry, replay, duplicate the transmission, switch model/provider/credential, or repeat an executed tool. All non-trigger failures leave credential metadata unchanged.
- Preserve existing OpenAI, Gemini, Ollama, and ChatGPT behavior.

## Files

- `backend/services/openrouter_credential_authority.py` (new; single metadata/fingerprint/transition authority with capability-separated Settings writer, runtime eligibility reader, and exact-key-safe invalidate-only capability)
- `backend/api/routers/system.py` (existing Settings consumer; private Task `.2` authority helpers move to the shared owner)
- `backend/llm_providers/openrouter/__init__.py` (new)
- `backend/llm_providers/openrouter/service.py` (new)
- `backend/llm_providers/openrouter/gateway.py` (new; read-only eligibility consumer plus exclusive caller of the separate authority-owned invalidate-only capability)
- `backend/llm_providers/runtime_llm.py`
- `backend/llm_providers/transports/openai_compat.py`
- `backend/llm_providers/shared/tool_call_adapter.py`
- `backend/llm_providers/shared/response_postprocessors.py`
- `backend/services/llm_gateway.py`
- `backend/services/chat_orchestrator.py`
- `backend/services/llm_silo_context.py`
- `backend/services/ops_kill_switches.py`
- `backend/services/orchestrator/execution_engine.py`
- `backend/tests/test_openrouter_credential_authority.py` (new)
- `backend/tests/test_openrouter_key_settings_api.py` (existing Task `.2` regression against the moved shared authority)
- `backend/tests/test_openrouter_provider.py` (new)
- `backend/tests/test_provider_parity.py`
- `backend/tests/test_provider_auth_fallback.py`
- `backend/tests/test_runtime_llm.py`
- `backend/tests/test_ops_kill_switches.py`
- `backend/tests/test_streaming_tool_loop_runner.py`

The shared credential-authority owner, its existing Settings consumer/regression, and the three runtime service additions with focused tests refine the compiled source-task file list only where the blocked prechecks, locked Decision Summary, and existing repository seams prove they are required: one exact-key eligibility and transition authority, an exclusive invalidate-only authenticated-rejection path, provider-silo isolation, the global cloud-provider kill switch, and streaming/no-fallback orchestration. They add no behavior beyond the approved Spec and locked decision.

## Explicit Exclusions

- No Settings or chat picker UI, provider/model selection persistence, disabled-selection retention, privacy-copy change, DeepDive field, cost persistence, database migration, conformance runner, candidate model, registry population, release, publish, or production activation.
- No real OpenRouter key, live OpenRouter request, external transmission, or credential-bearing manual test. All Task `.3` validation uses mocked clients and sentinel secrets that must not appear in output.
- No automatic retry, stream replay, duplicate transmission, OpenAI credential reuse, cross-provider credential lookup, provider switch, model switch, MoA selection, `MODEL_OVERRIDE`, or uncertified model alias such as `latest`.
- No generic rewrite of existing provider gateways, transport architecture, tool executor, permissions, confirmations, or streaming protocol.
- No direct import of API-router-private Task `.2` helpers and no duplicated, user-editable, stale, or independently grantable `VALID` authority.
- No runtime import or possession of the Settings mutation capability. The eligibility reader remains read-only; the dedicated OpenRouter gateway receives only the separate invalidate-only capability and cannot set, grant, preserve, upgrade, restore, transfer, delete, or perform any transition other than exact-current-key `VALID` to `INVALID` after a typed unambiguous authenticated-request rejection.
- No changes to Tasks `.4`, `.5`, or `.6`; the production certification registry stays intentionally empty.

## Acceptance Criteria

1. OpenRouter uses only its own service, gateway, key, provider identity, and base URL. Native OpenAI service/client/credential and every other provider credential remain untouched and cannot act as fallback.
2. One shared authority is the sole interpreter of Task `.2` metadata and exact-key fingerprint binding and the sole validation-state transition owner. Settings, runtime eligibility, and runtime invalidation consume separate capabilities; the eligibility reader is read-only, while only the dedicated OpenRouter gateway can receive the invalidate-only capability. Before catalog/model resolution and transmission, missing/malformed/version-mismatched/stale/mismatched/`INVALID`/`UNVERIFIED` state fails closed with zero catalog-authorized calls and zero external requests. After credential eligibility passes, the selected exact model must be present in the filtered certified catalog and the same ID must be sent.
3. OpenRouter uses the same Janus redaction, necessary context boundary, selected skill/tool definitions, canonical tool mapping, `ToolExecutor`, permissions, and confirmations. Permission denial or missing confirmation remains local and cannot be bypassed by provider-formatted tool calls.
4. Every OpenRouter text, tool, synthesis, and stream round remains pinned to the user-selected exact certified model. No MoA, helper provider, override, model fallback, provider fallback, or credential fallback is possible.
5. Exactly one provider attempt is made for each authorized round: client retries are zero, no tenacity retry applies, gateway key-refresh retry is bypassed, failed streams are not replayed, and executed tools are not rerun after provider failure.
6. `response.model` is required and exactly equals the selected model before text, tool calls, synthesis, or stream completion is accepted. Missing or mismatched identity ends only the current turn as a non-secret model error.
7. Auth, provider, model, transport, malformed-response, and stream failures remain current-turn failures, reveal no key, binding handle, fingerprint, or private provider payload, and never convert partial output into a successful completed turn. Only a typed, unambiguous authenticated upstream rejection of the request credential is an invalidation trigger; message matching, ambiguous auth-like errors, and every technical failure are non-triggers.
8. For the trigger in criterion 7, the dedicated gateway invokes the authority-owned invalidate-only capability exactly once with the request's opaque binding handle before returning the terminal error. The authority changes only the same exact currently stored key from `VALID` to `INVALID` through a compare-and-transition serialized with Settings save/replace/delete. If the key or binding changed before invalidation, no state changes. The capability cannot set, grant, preserve, upgrade, restore, transfer, or delete `VALID`, cannot delete credentials, and cannot perform any other transition. Network, timeout, rate-limit, provider, model, malformed-response, stream, and other technical failures leave metadata unchanged. The current turn has no retry, replay, duplicate transmission, model/provider/credential fallback, or tool rerun.
9. OpenRouter is an independent cloud-provider silo and is covered by the global cloud-provider kill switch; no OpenRouter helper call may escape into another provider silo.
10. Existing OpenAI, Gemini, Ollama, and ChatGPT paths retain their current behavior, including their current retry behavior where applicable. The empty certification registry keeps production OpenRouter unusable after this task.

## Tests

- `backend/tests/test_openrouter_credential_authority.py`: prove the shared owner is the only metadata/fingerprint interpreter; missing raw key, absent/malformed/version-mismatched metadata, stale/mismatched fingerprint, `INVALID`, and `UNVERIFIED` all return ineligible, while only the same exact stored key bound to `VALID` returns an immutable runtime credential.
- `backend/tests/test_openrouter_credential_authority.py`: prove capability separation and minimality: the eligibility reader exposes no mutation method; the dedicated gateway cannot obtain the Settings capability; only the invalidate-only capability accepts the opaque request binding; it performs only matching-current-key `VALID` to `INVALID`, cannot create/grant/preserve/upgrade/restore/transfer `VALID`, cannot delete or return a credential, cannot affect another provider/key, and does no write for missing/malformed/stale/mismatched/replaced/non-`VALID` bindings.
- `backend/tests/test_openrouter_credential_authority.py`: deterministic interleaving/TOCTOU cases prove the compare-and-transition is serialized with Settings save/replace/delete and that a replacement between request authorization and rejection leaves the replacement key and its metadata unchanged; repeated same-rejection handling is idempotent at `INVALID`.
- `backend/tests/test_openrouter_key_settings_api.py`: rerun the complete Task `.2` lifecycle against the shared owner, including first save, replace, delete, same-key temporary-failure preservation, content-free validation rejection, stale-binding prevention, restart-safe read, provider isolation, and secret-free responses; add Settings regressions proving runtime invalidation is visible as `INVALID`, later replacement is not inherited or invalidated, and only a new successful Settings validation can establish `VALID`.
- `backend/tests/test_openrouter_provider.py`: mocked service/gateway/transport tests for base URL, provider identity, credential isolation, zero client retries, no tenacity wrapper, exact request model, exact `response.model`, text response, tool-call response, multi-round tool loop, and non-secret errors.
- `backend/tests/test_openrouter_provider.py`: ordering matrix proving the runtime reader is called before catalog/model resolution and zero transmission occurs for missing key, non-`VALID` exact-key state, stale/mismatched key binding, missing certification, hidden/non-exact model, alias model, cloud kill switch, and response-model mismatch.
- `backend/tests/test_openrouter_provider.py`: binary trigger/non-trigger matrix: only the typed unambiguous authenticated credential rejection invokes invalidate-only exactly once with the request binding; timeout, network, rate limit, provider error, model error, malformed response, ambiguous auth-like error, stream interruption, and post-tool synthesis failure invoke it zero times and preserve state.
- `backend/tests/test_openrouter_provider.py`: one-attempt and ordering counters prove authenticated rejection invalidates before the terminal current-turn error, while every failure path has no provider retry, replay, duplicate request, fallback, tool rerun, or second invalidation attempt and leaks no credential, binding handle, fingerprint, or private response.
- `backend/tests/test_provider_parity.py`: OpenRouter OpenAI-compatible canonical tool-name/schema roundtrip and parity through `ToolExecutor`, permission denial, confirmation requirement, selected skills/tools, and redacted necessary context.
- `backend/tests/test_provider_auth_fallback.py`: OpenRouter auth/provider/model failures cannot refresh from or fall back to another credential, model, or provider.
- `backend/tests/test_runtime_llm.py`: deterministic OpenRouter runtime resolution remains bound to `openai_compat`, provider credential `openrouter`, and the exact base URL.
- `backend/tests/test_ops_kill_switches.py`: the global cloud-provider kill switch blocks OpenRouter and its dry-run inventory remains non-secret.
- `backend/tests/test_streaming_tool_loop_runner.py`: OpenRouter stream/tool handoff preserves provider and exact model, makes no replay on interruption, and cannot route synthesis to another provider/model.
- Focused regression for existing provider silos, gateways, tool-call mapping, and orchestration behavior.
- Python compilation for all changed Python files, focused pytest for the listed tests, scoped secret/leak assertions, and scoped `git diff --check`.

## Risks And Precheck Gates

- Verify the refined shared authority boundary exactly as bound: `backend/services/openrouter_credential_authority.py` owns the keyring account constants, metadata version/schema, fingerprint calculation, parsing, state interpretation, and capability construction; `backend/api/routers/system.py` consumes the Settings capability; the dedicated OpenRouter gateway consumes only the runtime reader. Precheck must block on any duplicate interpreter, private router import, user-editable authority, or second stale-`VALID` grant path.
- Verify capability separation structurally and with tests: runtime files must not import or receive the Settings mutation capability; the eligibility reader remains immutable; only the dedicated OpenRouter gateway receives the separate authority-owned invalidate-only capability. Precheck must block if any runtime caller can directly write/delete keyring data, grant/preserve/upgrade/restore/transfer `VALID`, invoke another status transition, or invalidate a key without the authority-issued request binding and typed authenticated-rejection evidence.
- Verify exact-key/TOCTOU safety: the authority's compare-and-transition must re-check current raw-key fingerprint and metadata binding and be serialized with Settings save/replace/delete. Precheck must require deterministic interleaving tests proving a replacement after request authorization cannot be invalidated by the old request and no check/write gap can target the replacement.
- Verify rejection classification and ordering: only an unambiguous authenticated upstream rejection of the supplied request credential may produce the typed invalidation trigger; no message matching or technical/ambiguous error may do so. The gateway invokes invalidate-only once before returning the terminal current-turn error, without provider retry, replay, duplicate transmission, fallback, tool rerun, or secret/binding leakage.
- Verify eligibility ordering: the runtime reader must reject missing/malformed/version-mismatched/stale/mismatched/`INVALID`/`UNVERIFIED` state before the filtered catalog is consulted, before model resolution, and before any SDK/client/transport construction or call.
- Prove that the filtered Task `.1` catalog is the sole runtime certification input and that the production-empty registry yields zero eligible models and zero transmission.
- Prove the dedicated OpenRouter service can configure the underlying SDK/client with automatic retries disabled and without inheriting the native OpenAI tenacity decorator or client defaults.
- Trace every OpenRouter call path through `llm_gateway`, `chat_orchestrator`, and streaming execution. The precheck must identify and eliminate the existing gateway two-attempt key-refresh loop, stream replay risk, model override/MoA resolution, and provider-switch/fallback branches specifically for OpenRouter without changing existing providers.
- Prove exact-model pinning across initial response, each tool round, synthesis, and streaming handoff, including validation of `response.model` before success or tool execution is accepted.
- Prove provider-silo and global cloud-kill-switch coverage before any transport call.
- Verify existing shared tool adapter behavior is OpenAI-compatible for `openrouter` without collapsing OpenRouter into the native `openai` credential or gateway.
- Verify failure ordering: no tool executes before eligibility and exact response identity are accepted; no already executed tool is repeated because a later provider round fails; partial stream output cannot become a successful completed turn.
- Verify all mocked error and leak tests use sentinel credentials only and inspect responses, logs, exceptions, captured request metadata, and test artifacts for secret exposure.
- Existing unrelated dirty-worktree paths remain out of scope and must be preserved.

## Execution Model

- **Model:** `5.6 Sol`
- **Intelligence:** high
- **Reason:** This task crosses an external credential boundary, exact-model security gate, tool execution permissions, provider-silo isolation, streaming, and strict no-retry/no-fallback semantics. If `gpt-5.6-sol` is unavailable for the ChatGPT Codex account, use `5.6 Terra` / high and record `SOL_UNAVAILABLE_FOR_CHATGPT_CODEX_ACCOUNT`.

## Decision

TASK DESIGN COMPLETE

```text
@janus-preimplementation-check
Spec: documentation/SPEC/OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md
Task: documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3_task_breakdown.md
Backlog Item: N/A
Target Task: TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.6 Sol
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```

## TASK IMPLEMENTATION METADATA

- **Implementation Status:** DONE
- **Completed:** 2026-07-17
- **Final Audit:** PASS
- **Automated Evidence:** `116` bound Python tests PASS; compile, JavaScript syntax, scoped diff/whitespace/credential checks PASS; direct complete/empty/incomplete/model/auth/technical stream matrix PASS
- **Headed Evidence:** exact OpenRouter Settings runner passed twice consecutively with `3 passed`
- **Manual Janus Evidence:** PASS - safe non-activation Settings/provider-selector observation without entering or saving an OpenRouter key
- **Audit Package:** `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3_AUDIT_PACKAGE.md`
- **Final Audit Path:** `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3_FINAL_AUDIT.md`
- **Production State:** DISABLED - certification registry remains intentionally empty
