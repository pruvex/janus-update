# TASK BREAKDOWN - TASK-CHATGPT-DEVICE-CODE-PROVIDER.4

## Source Identity

- **Spec:** `documentation/SPEC/CHATGPT_OFFICIAL_DEVICE_CODE_PROVIDER_REDESIGN_FEATURE_SPEC.md`
- **Spec Review:** APPROVED, 2026-07-16, complexity `78`, risk `HIGH`
- **Task File:** `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.md`
- **Backlog Item:** N/A WITH REASON - compiled Feature Spec task
- **Prior Gates:** Tasks `.1`, `.2`, and `.3` Final Audit PASS; production remains default-deny

## Selected Target

- **Target Task:** `TASK-CHATGPT-DEVICE-CODE-PROVIDER.4`
- **Target Subtask:** N/A WITH REASON - the approved Spec requires one provider-parity slice whose protocol, gateway, orchestration, privacy, tool, streaming, and cancellation boundaries must be validated together
- **Mode:** SINGLE_TASK_PRECHECK
- **Goal:** Add a per-turn ephemeral ChatGPT App-Server transport that behaves as a Janus provider, exposes only Janus-controlled skills/tools, blocks all Codex-native actions, enforces privacy acknowledgement before any externalization, and remains production default-deny through Task `.5`.

## Bound Scope

- Verify the expected experimental App-Server client-tool contract at runtime before making ChatGPT usable; missing, changed, or unverifiable support is complete fail-closed unavailability with no degraded text-only mode.
- Bind the official App-Server thread/start, turn/start, text/event stream, client-tool call/response, turn completion, and turn interruption lifecycle to a new transport adapter owned by the existing transport layer.
- Add an isolated ChatGPT gateway silo to the existing gateway router and runtime resolution pattern without an API key, OpenAI fallback, shared credentials, or mutation of another provider.
- Use a new ephemeral App-Server conversation for every Janus turn. Janus remains the only conversation source and no Codex thread identifier or parallel history is persisted.
- Offer only the tool definitions already selected and allowed by Janus. Execute accepted client-tool calls only through the existing `ToolExecutor`, permission, confirmation, and redaction boundaries.
- Translate only agent text and Janus-controlled tool status into the existing stream. Any Codex-native shell, file, approval, MCP, app, web, subagent, or other action must be impossible before execution and must fail only the current turn closed.
- Require current verified-model eligibility from Task `.3` and a backend-verifiable acknowledgement of the current privacy-information version before any App-Server thread, turn, context, tool payload, or retry is externalized.
- Update the visible privacy information and version to name current message, required history, Janus/skill instructions, required tool inputs, and tool results.
- Preserve draft, history, provider/model selection, Janus login, and all other providers on privacy rejection, close, user cancellation, contract drift, tool failure, or transport failure. No automatic retry, double send, or provider fallback.
- Keep production resolution default-deny. Only explicitly injected test evidence may activate the path in bounded tests; Task `.5` remains the sole production activation gate.

## Bound Files

### App-Server And Transport Ownership

- `backend/llm_providers/codex_app_server.py`
- `backend/llm_providers/transports/codex_app_server.py` (new)
- `backend/llm_providers/chatgpt/gateway.py` (new)
- `backend/llm_providers/runtime_llm.py`
- `backend/services/llm_gateway.py`

### Orchestration, Request, And UI Ownership

- `backend/services/chat_orchestrator.py`
- `backend/data/schemas.py`
- `frontend/index.html`
- `frontend/js/chat.js`
- `frontend/js/beta-privacy-notice.js`
- `documentation/beta/BETA_PRIVACY_NOTICE.md`

### Test Ownership

- `backend/tests/test_codex_app_server.py`
- `backend/tests/test_context_privacy_externalization_boundary.py`
- `backend/tests/test_provider_parity.py`
- `backend/tests/test_provider_auth_fallback.py`
- `tests/e2e/codex-connection-settings.spec.js`

No additional product file may be added during execution unless precheck first blocks and routes the source artifact back through task recompilation.

## Explicit Exclusions

- No Device-Code login, refresh, logout, account switch, credential-persistence redesign, credential import, or reopening of Tasks `.1`-`.3`.
- No Task `.5` release evidence, production activation, real-account message, live tool action, publish, build, or release work.
- No permanent or resumed Codex thread, Codex-owned history, second agent UI, Codex skill/tool use, shell, file edit, approval, MCP, app, web search, subagent, computer action, or hidden background action.
- No prompt-only security claim, event hiding, post-execution rejection, or treating an ignored Codex action as a successful turn.
- No text-only degraded fallback when client-tool compatibility or the hard native-action guard is unavailable.
- No API key, OpenAI-compatible transport, API-key-provider fallback, automatic retry, duplicate content externalization, or provider auto-switch.
- No static, cached, last-known, imported, or unverified ChatGPT model eligibility.
- No unbounded conversation export or context archive beyond the existing redacted Janus turn context.

## Binary Acceptance Criteria

1. ChatGPT resolves to the test-bound transport only when connection, current model verification, privacy acknowledgement, experimental client-tool compatibility, and the hard native-action guard are all valid.
2. Missing, drifted, or unverifiable client-tool support makes ChatGPT fully unavailable and cannot activate a reduced text-only path.
3. Each Janus turn creates one ephemeral App-Server conversation, streams the permitted text/tool status, supports interruption, and persists no Codex thread identifier or second history.
4. Only the required redacted Janus turn context is sent, and the active provider remains visibly ChatGPT throughout the turn and after completion/failure.
5. Only Janus-selected and allowed tool definitions cross the client-tool boundary; calls execute through the existing `ToolExecutor` and existing permission/confirmation rules, and only redacted results return.
6. Unknown, unselected, malformed, duplicate, late, or disallowed client-tool calls fail the current turn closed without execution, retry, fallback, or mutation of another provider.
7. Codex-native shell, file, approval, MCP, app, web, subagent, or other actions cannot execute. Any attempted native-action event fails the current turn with a non-sensitive error and is never reported as success.
8. Without a backend-verifiable acknowledgement of the exact current privacy-information version, no App-Server thread/turn starts and no message, history, skill instruction, tool input, tool result, or retry is externalized.
9. The visible privacy notice expressly covers current message, required history, Janus/skill instructions, required tool inputs, and tool results; unchanged acknowledgement is reused and a material version change requires renewed acknowledgement.
10. Rejection, close, cancellation, contract drift, tool failure, authentication/model failure, or transport failure preserves Janus history, draft, provider/model choice, login, and other provider connections, with no automatic retry or API-key fallback.
11. Task `.3` current-session verified-model-only selection and stale-selection self-healing remain enforced at the final pre-send boundary.
12. Product resolution remains default-deny after Task `.4`; test-only injection is isolated and Task `.5` remains the sole production activation gate.
13. Existing OpenAI, Gemini, Ollama, and other API-key-provider credentials, models, tool behavior, and provider switching remain unchanged.
14. Public errors, logs, stream events, snapshots, and evidence contain no tokens, device codes, credentials, private account identifiers, secret-bearing URLs, or unredacted tool content.

## Tests And Evidence Matrix

- `backend/tests/test_codex_app_server.py`: exact compatible contract, absent/drifted/unverifiable contract, ephemeral thread, text deltas, client-tool call/response, duplicate/late/unknown tool call, forbidden native action, interruption, protocol failure, crash, redaction, and production default-deny.
- `backend/tests/test_context_privacy_externalization_boundary.py`: backend gate precedes thread/start and all externalization; exact notice version, first acknowledgement, reuse, material version change, rejection/close, and disclosure content.
- `backend/tests/test_provider_parity.py`: gateway resolution, Janus tool-definition normalization, `ToolExecutor` permissions/confirmations, redacted results, streaming parity, tool status, and existing-provider non-regression.
- `backend/tests/test_provider_auth_fallback.py`: no API key dependency, no OpenAI/Gemini/Ollama credential read, no automatic fallback/retry/provider mutation, and test-only activation isolation.
- `tests/e2e/codex-connection-settings.spec.js`: headed provider switch in an existing chat, visible provider, blocked first send, acknowledgement and re-acknowledgement, retained draft, context continuation, Janus tool status, cancellation, transport error, and API-key-provider regression.
- Python compilation for all changed Python files, JavaScript syntax checks for changed frontend files, focused pytest files above, headed focused Playwright, and scoped `git diff --check`.
- Automated tests use fake App-Server/session/tool/privacy state only. No real account, external content submission, live Janus tool action, credential change, production activation, or Task `.5` evidence is permitted.

## Mandatory Precheck Stop Gates

1. **Protocol Identity:** Bind the exact installed App-Server runtime identity and generated schema evidence for thread/start, turn/start, ephemeral conversation state, client-tool definitions, client-tool call/response, agent text deltas, turn completion, and turn interruption. Block on any unsupported or ambiguous field.
2. **Experimental Capability:** Prove the required experimental capability is explicitly negotiated and rejected fail-closed when absent. Block if compatibility is inferred only from a version string, prompt, or fixture.
3. **Hard Native-Action Non-Execution:** Identify and execute an account-free proof that every Codex-native action surface relevant to the installed runtime is disabled before execution. The proof must cover at least shell/command, file change, approvals, MCP/apps, web access, subagents, and any other generated native action type. Read-only sandbox alone, approval rejection after dispatch, prompt instructions, hidden notifications, or client-side ignoring are insufficient. If no officially supported hard-disable profile exists, precheck is `BLOCKED` and implementation must not begin.
4. **Provider/Gateway Ownership:** Confirm the new adapter and silo fit the existing `BaseTransport`/gateway/tool-loop contracts without routing ChatGPT through OpenAI or changing existing provider silos. Block if another product module is required but unbound.
5. **Tool Authority:** Confirm the existing Janus-selected tool definitions and `ToolExecutor` can be mapped to client tools and results without bypassing permissions, confirmations, duplicate-call protection, redaction, or tool-round limits.
6. **Backend Privacy Ordering:** Prove the backend can validate the exact current notice version before lifecycle readiness, thread/start, turn/start, tool registration, context construction for externalization, stream creation, or retry. Frontend-only acknowledgement is insufficient.
7. **Model Eligibility:** Preserve the Task `.3` active-session current-verification gate at final send time. Block any stale, static, cached, imported, or unverified eligibility path.
8. **Cancellation:** Prove frontend abort/disconnect reaches App-Server turn interruption and cannot leave a background turn or late tool call active.
9. **Default-Deny/Test Isolation:** Identify the existing production default-deny mechanism and a separate injectable test-only activation seam. Block if testability requires production activation or if Task `.4` could set release evidence.
10. **Privacy Text And Version:** Bind the exact visible notice source, durable notice document, acknowledgement key/version source, and version bump required by the expanded disclosure. Block if a new product/privacy decision is needed.
11. **Redaction:** Bind redaction for protocol errors, client-tool arguments/results, stream errors, logs, screenshots, and evidence before any test artifact is retained.
12. **Test Ownership:** Confirm all assertions belong to the bound source/task tests. Do not patch generated TestPlan/TestResult or invent an oracle outside the approved Spec.

## Execution Model

- **Model:** `5.6 Sol`
- **Intelligence:** high
- **Fallback:** `5.6 Terra/high` only if Sol is unavailable, with `SOL_UNAVAILABLE_FOR_CHATGPT_CODEX_ACCOUNT` recorded
- **Reason:** Security-critical experimental protocol, hard native-action non-execution, cross-layer gateway/tool/privacy integration, and production default-deny require the highest available review and execution reasoning.

## Decision

TASK DESIGN COMPLETE

```text
@janus-preimplementation-check
Spec: documentation/SPEC/CHATGPT_OFFICIAL_DEVICE_CODE_PROVIDER_REDESIGN_FEATURE_SPEC.md
Task: documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.md
Backlog Item: N/A
Target Task: TASK-CHATGPT-DEVICE-CODE-PROVIDER.4
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.6 Sol
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```
