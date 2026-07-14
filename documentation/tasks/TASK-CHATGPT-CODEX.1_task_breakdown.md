# TASK BREAKDOWN - TASK-CHATGPT-CODEX.1

## Bound Inputs

- Source Spec: `documentation/SPEC/CHATGPT_OAUTH_PROVIDER_FEATURE_SPEC.md`
- Parent Task File: `documentation/tasks/TASK-CHATGPT-CODEX-PROVIDER.md`
- Backlog Item: `N/A`
- Target Task: `TASK-CHATGPT-CODEX.1` only
- Target Subtask: `N/A`

## Source Of Truth

- The approved Feature Spec defines the product, security, privacy, account-isolation, and no-fallback boundaries.
- The parent task defines the official Codex access boundary as the first dependency for Tasks `.2` through `.4`.
- Historical `documentation/tasks/TASK-CHATGPT-OAUTH*` artifacts are stale evidence of a rejected direct-token design and are forbidden as implementation inputs.
- The OpenRouter result is counter-review material only. Codex remains the local authority and final writer.

## Decision

`TASK DESIGN COMPLETE`

- Exactly one target is released: `TASK-CHATGPT-CODEX.1`.
- Execution model: `5.6 Sol`, high reasoning.
- Readiness: ready for one `janus-preimplementation-check`; no implementation, test execution, live login, or code change is released here.

## Refined Goal

Provide one Janus-owned lifecycle boundary around the officially supported Codex App Server managed-account surface. Janus must be able to start the bundled official runtime lazily, keep its account state isolated from other local Codex/ChatGPT clients, expose only non-secret account/workspace/session state, and stop the process cleanly. Janus must not own, parse, export, log, or refresh OAuth secrets.

## Atomic Scope

In scope:

- resolve the official runtime from a Janus-packaged location in development and packaged Electron builds;
- pass a Janus-specific runtime home and keyring-only credential policy to the backend boundary;
- own one lazy App Server subprocess with request correlation, bounded timeouts, cancellation, crash state, retry, and graceful shutdown;
- support only the managed account lifecycle needed by later UI work: initialize, account read, login start, login cancel, account logout, and account/workspace state notifications;
- return stable, non-secret internal state objects for later API/UI consumers;
- redact subprocess output, protocol errors, and status diagnostics;
- fail closed if the official runtime, isolated OS-protected store, or supported protocol is unavailable.

Explicitly parked:

- `backend/llm_providers/runtime_llm.py`, Codex response transport, and `model/list` consumption remain in `TASK-CHATGPT-CODEX.3`;
- API endpoints, Settings UI, provider visibility, account-switch UI, and retry UI remain in `TASK-CHATGPT-CODEX.2`;
- chat continuity, first-send privacy notice, usage-limit presentation, and send blocking remain in `TASK-CHATGPT-CODEX.4`;
- no existing API-key provider or keyring namespace is changed.

The parent task's placeholder-resolution step is refined to mean that this slice publishes the lifecycle contract consumed by `.3`; the existing `openai-codex` runtime placeholder is not removed in `.1`.

## Files

Implementation allowlist for precheck validation:

- `backend/llm_providers/codex_app_server.py` - new JSON-RPC process/client lifecycle and non-secret account-state boundary.
- `backend/main.py` - construct and close the lifecycle owner through the existing FastAPI lifespan.
- `main.electron.cjs` - resolve the packaged official runtime and isolated Janus runtime-home paths, then pass only those paths/policy flags to the backend process.
- `scripts/run-backend-dev.cjs` - provide the equivalent explicit development runtime path without falling back to `PATH`.
- `package.json` - pin the official runtime package/resource and include it in Electron packaging.
- `package-lock.json` - lock the exact official runtime dependency and integrity metadata.
- `backend/tests/test_codex_app_server.py` - new fixture-driven process/protocol, isolation, lifecycle, and redaction tests.
- `tests/electron/codex-runtime-boundary.test.cjs` - new development/packaged path and environment-boundary tests.

Read-only dependencies unless precheck proves a minimal edit is mandatory:

- `backend/utils/redaction.py`
- `janus_backend.spec`

Any additional product file, router, transport, frontend file, general config file, or API-key path requires a new gate; it is not implicitly authorized.

## Required Protocol Boundary

- Use the official App Server JSON-RPC lifecycle and managed login surface; do not implement browser OAuth directly.
- Correlate request IDs deterministically and treat notifications separately from responses.
- Translate protocol data into an allowlisted internal account-state object containing only connection state, non-secret account identifier, workspace identifier/display data, retry reason, and capability flags required by later tasks.
- Never expose access tokens, refresh tokens, authorization headers, raw credential objects, credential-store contents, or unredacted process output.
- Keep provider calls and model enumeration outside this task.

## Acceptance Criteria

- Given an available Janus-packaged official runtime, the first lifecycle request starts exactly one App Server process and later requests reuse it.
- Given a packaged build or development run, runtime resolution uses only the explicit Janus-managed path; another `codex` executable on `PATH` is never selected silently.
- Given a Janus session, the process receives a Janus-specific runtime home and an enforced OS-keyring credential policy with no credential-file fallback.
- Given managed login/account/logout protocol messages, Janus returns only the allowlisted non-secret account/workspace/session state.
- Given login cancellation or failure, the previously published connection state remains unchanged and a retryable non-secret error is returned.
- Given Janus logout, only the isolated Janus account session is removed; other local Codex/ChatGPT clients are not targeted.
- Given process crash, timeout, unsupported protocol, missing runtime, or unavailable safe storage, the boundary becomes unavailable and fails closed without API-key, provider, model, external-session, file-store, or `PATH` fallback.
- Given backend shutdown, the owned App Server process and pending requests are terminated deterministically without affecting unrelated processes.
- Given any diagnostic, exception, stdout/stderr event, or state object, credential-shaped values are absent or redacted.
- Existing API-key providers and the `openai-codex` transport placeholder remain behaviorally unchanged in this slice.

## Tests

Precheck must bind tests without executing them:

- fixture-driven JSON-RPC initialization, request/response correlation, notification handling, malformed-message rejection, and bounded timeout behavior;
- lazy start, single-process reuse, explicit retry after crash, login cancel, logout, pending-request cleanup, and graceful shutdown;
- non-secret account/workspace state allowlist and token/authorization/credential redaction for protocol errors plus stdout/stderr;
- Janus-specific runtime-home and keyring-only environment/configuration contract;
- missing safe store, unsupported protocol, unavailable packaged runtime, and invalid runtime-path failures;
- negative test proving a system/PATH Codex installation is not used;
- negative test proving Janus logout addresses only the owned isolated process/session;
- Electron development and packaged path resolution plus backend environment forwarding;
- regression assertion that existing API-key provider configuration and `runtime_llm.py` behavior are untouched.

No live account, token, browser login, network call, product runtime test, or release build belongs to precheck. Live and packaged evidence must be defined later by TestSpec/TestPlan after implementation.

## Mandatory Precheck Proofs

Precheck must block unless all of these can be evidenced from current official contracts and repository state:

- the selected official Codex distribution may be bundled and pinned by Janus for the target Windows package;
- the managed App Server login surface still owns secret persistence and refresh;
- the selected configuration can force OS-protected storage without credential-file fallback;
- the Janus-specific runtime home/credential namespace is actually isolated from other Codex/ChatGPT clients;
- the exact executable/resource path is available in both development and packaged Electron modes;
- the existing redaction helper is sufficient or one tightly bounded extension is explicitly added to the allowlist.

Failure of any proof is `PRE_CHECK_BLOCKED`, not permission to invent a fallback.

## Dependencies And Rollback

- `.2` may consume only the non-secret lifecycle/state contract after `.1` passes implementation validation.
- `.3` may consume the same owned process for model discovery and provider transport after a separate task-breakdown/precheck gate.
- `.4` remains blocked until `.2` and `.3` provide their UI/send-state contracts.
- Rollback removes the new App Server boundary, its lifespan hook, runtime resource/path wiring, dependency lock entry, and focused tests. Existing API-key providers, chats, settings, and `runtime_llm.py` remain untouched.

## Open Risks For Precheck

- official runtime redistribution and platform package layout must be verified rather than assumed;
- OS-keyring storage may still share a vendor credential namespace unless the official runtime provides a truly isolated instance boundary;
- subprocess protocol/version drift needs a fail-closed compatibility gate;
- this slice crosses Electron packaging and Python lifecycle ownership, so partial implementation is not releasable.

## Next Skill Handoff

```text
@janus-preimplementation-check
Spec: documentation/SPEC/CHATGPT_OAUTH_PROVIDER_FEATURE_SPEC.md
Task: documentation/tasks/TASK-CHATGPT-CODEX.1_task_breakdown.md
Backlog Item: N/A
Target Task: TASK-CHATGPT-CODEX.1
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.6 Sol
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```
