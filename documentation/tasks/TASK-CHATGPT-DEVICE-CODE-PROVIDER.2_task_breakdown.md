# TASK BREAKDOWN - TASK-CHATGPT-DEVICE-CODE-PROVIDER.2

## Source Identity

- **Spec:** `documentation/SPEC/CHATGPT_OFFICIAL_DEVICE_CODE_PROVIDER_REDESIGN_FEATURE_SPEC.md`
- **Task File:** `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.md`
- **Backlog Item:** N/A WITH REASON - compiled Feature Spec task
- **Prior Gate:** `TASK-CHATGPT-DEVICE-CODE-PROVIDER.1` Final Audit PASS; secure Janus-only credential foundation is binding

## Selected Target

- **Target Task:** `TASK-CHATGPT-DEVICE-CODE-PROVIDER.2`
- **Target Subtask:** N/A
- **Mode:** SINGLE_TASK_PRECHECK
- **Goal:** Expose the already-isolated official device-code lifecycle through the existing Settings surface and non-sensitive API contract, including atomic one-account switching, without enabling provider selection, model availability, chat transport, or production.

## Scope

- Add non-sensitive Settings/API lifecycle states and actions: disconnected, login pending, connected, error, cancel, retry, Janus-only logout, and account switch.
- Display the official verification location and one-time user code only in the dedicated active-login UI path; do not persist either value or place it in public status snapshots, generic errors, logs, telemetry, evidence, or browser URLs containing secrets.
- Preserve a connected Janus account until a replacement login completes successfully; cancel or failure leaves that existing Janus connection usable.
- Make unavailable secure persistence visibly disabled with a non-sensitive reason and no cleartext, session-only, API-key, shared-session, or credential-import fallback.
- Keep Janus-only logout and all error language explicitly bounded to the Janus connection; API-key providers and external Codex/ChatGPT clients remain untouched.

## Files

- `backend/api/routers/system.py`
- `frontend/index.html`
- `frontend/js/settings.js`
- `frontend/css/settings.css`
- `backend/tests/test_codex_connection_settings_api.py`
- `tests/e2e/codex-connection-settings.spec.js`

## Explicit Exclusions

- No change to `backend/llm_providers/codex_app_server.py` or the Task `.1` credential boundary unless precheck proves the existing non-sensitive lifecycle contract is insufficient; that condition is a BLOCKED precheck result, not permission to widen scope.
- No ChatGPT provider/model dropdown visibility, model verification, chat transport, context transfer, privacy acknowledgement, provider fallback, production activation, release, or live two-account/account action.
- No direct OAuth client, token exchange, private backend endpoint, credential import, plaintext persistence, session-only fallback, or API-key fallback.

## Acceptance Criteria

1. Settings displays and operates each specified non-sensitive connection state and only Janus-scoped actions.
2. A first-login cancel or error leaves no partially connected Janus state.
3. A replacement-login cancel or error preserves the prior Janus connection unchanged and usable.
4. A successful replacement login replaces the prior Janus connection only after confirmed completion.
5. Janus logout and user-visible error text state and enforce that only the Janus connection changes.
6. If secure persistence is unavailable, login is disabled with a non-sensitive explanation and no fallback path.
7. Device codes, tokens, stored credentials, private account identifiers, and secret-bearing URLs are absent from public status, generic API errors, logs, telemetry, test snapshots, and evidence.
8. Existing API-key Settings behavior remains unchanged.
9. ChatGPT remains unavailable as a selectable provider and production remains default-deny after this task.

## Tests

- `python -m pytest backend/tests/test_codex_connection_settings_api.py -q` for state/action contracts, redaction, disabled persistence, first-login cleanup, atomic account-switch preservation, Janus-only logout, and API-key regression.
- `npx playwright test tests/e2e/codex-connection-settings.spec.js --headed --workers=1 --reporter=list` for disconnected, pending login, cancel, connected, retry, logout, successful switch, failed/cancelled switch, and disabled-persistence behavior.
- JavaScript syntax check for `frontend/js/settings.js` and scoped `git diff --check` over the six bound files.
- Test doubles only for device-code lifecycle responses; no live login, refresh, logout, account switching, credential inspection, or two-account action is authorized in this task.

## Risks And Precheck Gates

- Preserve the Task `.1` rule that verification values are transient and never become a generic public status field.
- Confirm system-router responses expose only the already-approved non-sensitive lifecycle contract and cannot trigger a second parallel login.
- Confirm the atomic switch action cannot remove the old Janus session before the new session reaches confirmed connected state.
- Confirm disabled secure persistence blocks UI initiation before any lifecycle side effect.
- Block precheck if fulfilling the Settings contract requires a new provider/model/chat or credential-storage decision, changes a Task `.1` security boundary, or cannot prove API-key non-interference.

## Execution Model

- **Model:** `5.6 Terra`
- **Intelligence:** high
- **Reason:** Multi-surface Settings/API implementation on a security-sensitive, but final-audited, isolation foundation.

## Decision

TASK DESIGN COMPLETE

```text
@janus-preimplementation-check
Spec: documentation/SPEC/CHATGPT_OFFICIAL_DEVICE_CODE_PROVIDER_REDESIGN_FEATURE_SPEC.md
Task: documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.md
Backlog Item: N/A
Target Task: TASK-CHATGPT-DEVICE-CODE-PROVIDER.2
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.6 Terra
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```
