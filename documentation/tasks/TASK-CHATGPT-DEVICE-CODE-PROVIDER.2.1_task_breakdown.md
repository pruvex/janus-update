# TASK BREAKDOWN - TASK-CHATGPT-DEVICE-CODE-PROVIDER.2.1

## Source Identity

- **Spec:** `documentation/SPEC/CHATGPT_OFFICIAL_DEVICE_CODE_PROVIDER_REDESIGN_FEATURE_SPEC.md`
- **Task File:** `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.md`
- **Parent Task:** `TASK-CHATGPT-DEVICE-CODE-PROVIDER.2`
- **Backlog Item:** N/A WITH REASON - a bound follow-up for the incomplete compiled Feature Spec task
- **Prior Gate:** `TASK-CHATGPT-DEVICE-CODE-PROVIDER.1` Final Audit PASS; secure Janus-only credential foundation remains binding
- **Failure Source:** `E2E_REPLACEMENT_LIFECYCLE_PENDING_STUCK` in `documentation/tasks/TASK-BACKLOG-131-SETTINGS-NAVIGATION_debug_result.md`

## Selected Target

- **Target Task:** `TASK-CHATGPT-DEVICE-CODE-PROVIDER.2.1`
- **Target Subtask:** N/A
- **Mode:** SINGLE_TASK_PRECHECK
- **Goal:** Refresh the already-approved public Janus connection state after managed Device-Code login so the Settings card leaves the pending state only when the existing lifecycle reports a confirmed terminal state.

## Scope

- Use the existing non-sensitive `GET /api/codex-connection` contract after a managed login start to refresh the visible Settings card.
- Keep the refresh bounded to the active in-memory login and stop it on cancel, failure, unavailable/disconnected state, or confirmed connected state.
- Render only the existing public lifecycle state; retain one-time verification values only in the existing matching in-memory pending-login UI path.
- Reuse the existing replacement-account E2E scenario to prove the queued connected state reaches `Abmelden` only after public confirmation.

## Files

- `frontend/js/settings.js`
- `tests/e2e/codex-connection-settings.spec.js` (bound regression runner; edit only if the precheck proves an assertion or mock transition needs a minimal correction)

## Explicit Exclusions

- No change to `backend/llm_providers/codex_app_server.py`, secure persistence, keyring, API router, Device-Code protocol, URL validation, code display/redaction rules, credential import, API-key behavior, provider/model selection, chat transport, privacy acknowledgement, production activation, release, live account action, or Git action.
- No change to BACKLOG-131 navigation behavior except using its corrected Settings entry path as existing regression evidence.
- No background refresh that survives renderer teardown, persists login data, logs lifecycle payloads, or bypasses the public connection endpoint.

## Acceptance Criteria

1. After managed login start, Settings refreshes only the existing public connection status for the matching active in-memory login.
2. The refresh stops and clears transient instructions when cancel, failure, unavailable/disconnected, or confirmed connected state is rendered.
3. A successful mocked replacement displays the second account with `Abmelden` and `Konto wechseln`; the previous Janus account remains intact until that confirmed state.
4. One-time verification values, login identifiers, tokens, stored credentials, private account identifiers, and secret-bearing URLs remain absent from generic state, errors, logs, telemetry, snapshots, and evidence.
5. Existing API-key Settings behavior, Task `.1` credential isolation/redaction/two-account evidence, provider/model non-selection, and production default-deny remain unchanged.

## Tests

- `node --check frontend/js/settings.js`
- `python -m pytest backend/tests/test_codex_connection_settings_api.py -q`
- `npx playwright test tests/e2e/codex-connection-settings.spec.js --headed --workers=1 --reporter=list`
- Scoped `git diff --check` for the two bound files
- Mocked lifecycle responses only; no live login, refresh, logout, account switching, credential inspection, or two-account action is authorized.

## Risks And Precheck Gates

- Preserve the Task `.1` transient-value rule: a refresh may consume only public connection state and must not persist or re-expose one-time Device-Code values.
- Ensure a later or stale refresh cannot overwrite a newer active login/card state.
- Block precheck if a public-state refresh would require a private lifecycle endpoint, credential-store change, provider/model decision, or production-policy change.

## Execution Model

- **Model:** `5.6 Terra`
- **Intelligence:** high
- **Reason:** Bounded asynchronous renderer lifecycle behavior on the final-audited credential-isolation foundation.

## Decision

TASK DESIGN COMPLETE

```text
@janus-preimplementation-check
Spec: documentation/SPEC/CHATGPT_OFFICIAL_DEVICE_CODE_PROVIDER_REDESIGN_FEATURE_SPEC.md
Task: documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.md
Backlog Item: N/A
Target Task: TASK-CHATGPT-DEVICE-CODE-PROVIDER.2.1
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.6 Terra
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```
