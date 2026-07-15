# AUDIT_PACKAGE

Generated: 2026-07-15 15:38:20 UTC

## Goal

Independently audit TASK-CHATGPT-DEVICE-CODE-PROVIDER.2 Settings/API-key presentation for official ChatGPT device-code lifecycle, preserving Task .1 isolation and production default-deny.

## Scope Rules

- Audit the provided package and changed artifacts only.
- Do not rely on development chat history.
- Verify cost, caching, skill quality, safety scope, and validation evidence.
- On re-audit, review the blocker delta first before widening scope.
- If scoped paths were provided, treat them as the audit diff boundary.

## Bound Audit Inputs

- Spec: APPROVED: documentation/SPEC/CHATGPT_OFFICIAL_DEVICE_CODE_PROVIDER_REDESIGN_FEATURE_SPEC.md
- Task File: documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.2_task_breakdown.md
- Backlog Item: N/A WITH REASON - No backlog marker provided.
- Pre-Implementation Check: documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.2_precheck.md
- Manual Janus Evidence: PASS: Account-free user observation recorded in TASK-CHATGPT-DEVICE-CODE-PROVIDER.2_execution_result.md: masked openai/gemini keys; ChatGPT Codex card unavailable; secure storage no-fallback explanation; sign-in unavailable; no login or account action.
- Pipeline Completion Status: Task .1 final audit PASS; Task .2 precheck PASS; Task .2.2 runner-only execution PASS; Task .2 automated validation PASS (API 11/11, headed E2E 8/8); Task .2 manual Settings validation PASS.

## Backlog Item

```text
N/A WITH REASON - No backlog source or marker provided.
```

## Task Acceptance Scope

```text
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
```

## Pre-Implementation Check

```text
# PRE-IMPLEMENTATION CHECK - TASK-CHATGPT-DEVICE-CODE-PROVIDER.2

PRE-CHECK RESULT
PRE-CHECK PASSED

```text
legacy handoff start
NEXT: janus-executioner
Target Task: TASK-CHATGPT-DEVICE-CODE-PROVIDER.2
Target Subtask: N/A
Task: documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.md
Spec: documentation/SPEC/CHATGPT_OFFICIAL_DEVICE_CODE_PROVIDER_REDESIGN_FEATURE_SPEC.md
Backlog Item: N/A
Assigned Model: 5.6 Terra
Assigned Intelligence: high
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- Task .1 Final Audit PASS is the binding credential-isolation, redaction, Janus-only logout, and production-default-deny foundation.
- The confirmed Task .2 changeset boundary contains exactly the three modified Settings/API files and two new test files named below; frontend/css/settings.css remains in scope although currently unchanged.
- Task .2 is one bounded Settings/API slice. It does not select a provider/model, send chat content, change credential persistence, or activate production.
Affected Files:
- backend/api/routers/system.py
- frontend/index.html
- frontend/js/settings.js
- frontend/css/settings.css
- backend/tests/test_codex_connection_settings_api.py
- tests/e2e/codex-connection-settings.spec.js
Evidence Focus:
- Expose only non-sensitive lifecycle states and actions through the Settings/API contract.
- Keep verification URL and user code transient in the dedicated login path; exclude them from public state, generic errors, logs, telemetry, snapshots, and secret-bearing URLs.
- Preserve the old Janus connection until a replacement login confirms connected; cancel or failure leaves it usable.
- Disabled secure persistence blocks UI initiation without cleartext, session-only, API-key, shared-session, or credential-import fallback.
- Janus-only logout and error language leave API-key providers and external Codex/ChatGPT sessions unchanged.
Scope-Regel:
- Implement only TASK-CHATGPT-DEVICE-CODE-PROVIDER.2 within the six listed files. No provider/model dropdown, model verification, chat transport, context transfer, privacy acknowledgement, credential-store change, direct OAuth, API-key fallback, production activation, release, or live account action.
- If the existing Task .1 non-sensitive lifecycle contract cannot support the Settings/API requirements, stop execution and return BLOCKED; do not alter backend/llm_providers/codex_app_server.py or widen scope.
Automated Evidence Gate:
- python -m pytest backend/tests/test_codex_connection_settings_api.py -q
- python -m py_compile backend/api/routers/system.py
- node --check frontend/js/settings.js
- npx playwright test <runner> --headed --workers=1 --reporter=list
- npx playwright test tests/e2e/codex-connection-settings.spec.js --headed --workers=1 --reporter=list
- git diff --check -- backend/api/routers/system.py frontend/index.html frontend/js/settings.js frontend/css/settings.css backend/tests/test_codex_connection_settings_api.py tests/e2e/codex-connection-settings.spec.js
Artifact Identity Check:
- PASS: Task, Target Task, Backlog Item, Spec, Task .2 breakdown, and operator-confirmed five-file changeset boundary verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. No TestSpec or generated test-plan artifact is in scope; route any later TestSpec change to janus-test-pipeline.
Keep Context:
- documentation/SPEC/CHATGPT_OFFICIAL_DEVICE_CODE_PROVIDER_REDESIGN_FEATURE_SPEC.md
- documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.md
- documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.2_task_breakdown.md
- documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_final_audit.md
- six affected files and the automated evidence commands
Drop Context:
- prior blocked ownership check, Task .1 development history, unrelated dirty worktree paths, Tasks .3 through .5, release and Git history
Completion Rule:
- End with PASS, BLOCKED, NEEDS_INFO, or HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.
legacy handoff end
```

## NEXT STEP

Recommended Skill: janus-executioner
Recommended Model: 5.6 Terra
Recommended Intelligence: high
User Action: Reply `ok` to start janus-executioner for Task .2 only; no live account action is authorized by this precheck.
```

## Changed Files

```text
M backend/api/routers/system.py
 M frontend/index.html
 M frontend/js/app.js
 M frontend/js/settings.js
?? backend/tests/test_codex_connection_settings_api.py
?? documentation/tasks/TASK-BACKLOG-131-SETTINGS-NAVIGATION_execution_result.md
?? documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.2.2_execution_result.md
?? documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.2_execution_result.md
?? tests/e2e/codex-connection-settings.spec.js
```

## Artifact Inventory

```text
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-CHATGPT-DEVICE-CODE-PROVIDER.2_execution_result.md (7104 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-CHATGPT-DEVICE-CODE-PROVIDER.2.2_execution_result.md (3250 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-BACKLOG-131-SETTINGS-NAVIGATION_execution_result.md (3727 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-CHATGPT-DEVICE-CODE-PROVIDER.2_debug_result.md (4105 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-BACKLOG-131-SETTINGS-NAVIGATION_debug_result.md (3816 bytes)
FILE C:\KI\Janus-Projekt\backend\tests\test_codex_connection_settings_api.py (11617 bytes)
FILE C:\KI\Janus-Projekt\tests\e2e\codex-connection-settings.spec.js (13180 bytes)
```

## Diff Summary

```text
backend/api/routers/system.py | 139 +++++++++++++++++-
 frontend/index.html           |  22 +++
 frontend/js/app.js            |  40 ++---
 frontend/js/settings.js       | 332 +++++++++++++++++++++++++++++++++++++++++-
 4 files changed, 505 insertions(+), 28 deletions(-)
```

## Validation

```text
# TASK EXECUTION RESULT - TASK-CHATGPT-DEVICE-CODE-PROVIDER.2

Canonical State: HANDOFF
Target Task: TASK-CHATGPT-DEVICE-CODE-PROVIDER.2

## Automated Retest Delta - 2026-07-15

- The delayed legacy Settings-handler overwrite was corrected separately under `TASK-BACKLOG-131-SETTINGS-NAVIGATION`.
- The remaining replacement state mismatch was runner-only: Task `.2.2` stages its mocked connected replacement state after the mocked login POST, allowing the existing post-action public refresh to observe it.
- The full headed mocked E2E gate now passes: `8 passed (53.2s)`. The focused API suite remains `11 passed`.
- No live account, credential, device-code, production, Git, or remote action was performed during these retests.

Auto-Verification:
- Status: PASS.
- Evidence: `python -m pytest backend/tests/test_codex_connection_settings_api.py -q` reports `11 passed`; `npx playwright test tests/e2e/codex-connection-settings.spec.js --headed --workers=1 --reporter=list` reports `8 passed (53.2s)`; syntax and scoped diff checks pass.
- Security boundary: The evidence continues to cover redacted public state, transient one-time presentation, API-key non-interference, atomic replacement/cancel/failure behavior, provider/model non-selection, and disabled persistence. Production remains default-deny.

## Manual Janus Validation Gate

- Status: PASS.
- Test Example: Start Janus, wait for normal startup, select `Einstellungen`, then `API Keys`. Do not select `Anmelden`, do not start a device-code flow, and do not use a live account.
- Expected: The Settings view remains visible; the API-key form and separate `ChatGPT über Codex` card are visible; no device code or credential is displayed without an active pending login; ChatGPT is not selectable as a general provider/model and production remains default-deny.
- If Failed: Capture the visible symptom only and route it to `janus-debug`; do not attempt account, credential, or production actions.
- If Passed: Build the compact Task `.2` audit package before requesting an independent final audit.
- Observed: `openai` and `gemini` API keys remain masked; `ChatGPT über Codex` reports unavailable; secure sign-in is disabled because Janus uses no alternative storage; the sign-in action is unavailable. No login or account action was initiated.

## Implemented Scope Pending E2E Gate

- The Settings/API start-login contract was changed from the stale callback-style `authorization_url` shape to the Task `.1` official device-code result: transient `verification_url`, `user_code`, `login_id`, and redacted public connection state.
- The Settings card renders the verification destination and one-time code only while the matching login remains pending in renderer memory. They are not added to the generic connection-state response, errors, logs, or browser URL.
- The renderer accepts only the fixed official `https://auth.openai.com/codex/device` URL without query, fragment, user-info, or non-default port; it rejects other response URLs before any browser-open attempt.
- `Konto wechseln` now starts the existing Task `.1` atomic lifecycle rather than logging out first. Task `.1` keeps the prior Janus state snapshot and restores it on cancel or start failure.
- When keyring-only isolated persistence is unavailable, Settings exposes a disabled non-fallback action with a non-sensitive explanation.
- API and Playwright test doubles cover public-state redaction, first-login cleanup, replacement cancel/failure preservation, mocked successful replacement, Janus-only logout, API-key non-interference, and disabled persistence.

## Changed Files

- `backend/api/routers/system.py`
- `frontend/index.html`
- `frontend/js/settings.js`
- `backend/tests/test_codex_connection_settings_api.py`
- `tests/e2e/codex-connection-settings.spec.js`
- `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.2_execution_result.md`
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/SKILL_USAGE_LOG.md`

`frontend/css/settings.css` remains within the bound scope and was not changed.

## Executed Checks

- Task `.2` precheck validator: PASS.
- Targeted `WHAT_I_LEARNED` search: PASS; the Task `.1` credential-isolation tripwire was applied.
- `python -m py_compile backend/api/routers/system.py`: PASS.
- `node --check frontend/js/settings.js`: PASS.
- `python -m pytest backend/tests/test_codex_connection_settings_api.py -q`: PASS, `11 passed`.
- Scoped `git diff --check` for tracked bound paths: PASS.
- `npx playwright test tests/e2e/codex-connection-settings.spec.js --headed --workers=1 --reporter=list`: BLOCKED. The rerouted helper now clicks the actual Settings button, but the first scenario cannot find `#api-key-section` after that click; seven later scenarios do not run. Read-only correlation shows a delayed `app.js` handler replacement routes the button to `forceOpenSettings()`, which neither updates `appState.currentView` nor dispatches `show-settings` before calling `initializeApp()`. No live account, credential, browser sign-in, or device-code action was performed.

## Historical Blocker And Boundaries (Superseded)

- Failure code: `E2E_SETTINGS_HANDLER_REPLACEMENT_CONFLICT`.
- The one debug-rerouted stateful-helper correction was applied exactly as specified. Its immediate failure proves the assumed stable `#settings-btn` seam is superseded by a delayed legacy handler in the current application; this is not safe to mask with another test-only timing or DOM workaround.
- The full headed gate remains incomplete, so prior scenario evidence is insufficient to mark Task `.2` delivery-ready.
- Task `.1` lifecycle, credential persistence, provider/model selection, chat transport, privacy acknowledgement, production activation, and all live account activity remain untouched.
- Production remains default-deny. No provider becomes selectable through this task.

## NEXT_STEP

Target Skill: codex-audit-package-builder
Canonical State: HANDOFF
Required Artifacts: Task `.2` breakdown and passed precheck; this execution result; Task `.2.2` execution result; `TASK-BACKLOG-131-SETTINGS-NAVIGATION_execution_result.md`; `tests/e2e/codex-connection-settings.spec.js`; focused API-test evidence.
Evidence Paths: `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.2_execution_result.md`; `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.2.2_execution_result.md`.
Failure Code: none; MANUAL_SETTINGS_VALIDATION_PENDING resolved by the account-free Settings observation.
Changed Files: see scope list above.
Decision: build an artifact-only Task `.2` audit package, then request an independent final audit. Do not route directly to final audit before the package exists.
Reason: all scoped automated evidence and the bounded passive Settings presentation gate pass; secure storage remains default-deny without a fallback.
Recommended Model: 5.6 Terra
Recommended Intelligence: high
New Chat: no; retain the compact Task `.2` handoff only.
Next User Action: approve the compact Task `.2` audit-package build; it is read-only with respect to product, accounts, credentials, Git, remotes, and production.
```

## Notes

No additional notes provided.

## Risks

Credential/device-code values must remain transient and redacted; secure-storage absence must remain a disabled no-fallback state; provider/model selection and production must remain default-deny; account replacement must preserve the prior state on cancel/failure.

## Open Issues

No known Task .2 blocker. Independent final audit remains mandatory. BACKLOG-131 is a separately validated navigation prerequisite and remains governed by its own closeout.

## Re-Audit Delta

Primary blocker: E2E_SETTINGS_HANDLER_REPLACEMENT_CONFLICT; E2E_REPLACEMENT_LIFECYCLE_PENDING_STUCK

BACKLOG-131 corrected the delayed Settings-handler overwrite; Task .2.2 corrected only mocked replacement-state sequencing. Full headed E2E now passes 8/8 and focused API tests pass 11/11. Passive manual Settings observation confirms masked keys and unavailable no-fallback ChatGPT sign-in.

## Final Audit Handoff

```text
NEW_CHAT_HANDOFF
NEXT: final-skill-audit
MODEL: 5.6 Sol/high if runtime-supported; otherwise 5.6 Terra/high
PASS: C:\KI\Janus-Projekt\documentation\tasks\TASK-CHATGPT-DEVICE-CODE-PROVIDER.2_AUDIT_PACKAGE.md
ASK: Lade nur dieses Paket im neuen Chat und starte dann den Final Audit.
DROP: dev chat history
```

Use `5.6 Sol/high` when the current Codex run can start it; if Codex reports `gpt-5.6-sol` is unsupported for the active ChatGPT account, use `5.6 Terra/high` and record `SOL_UNAVAILABLE_FOR_CHATGPT_CODEX_ACCOUNT`.

For bounded same-thread re-audits after a local blocker fix, `5.6 Terra/high` is acceptable when the package stays compact and the risk did not escalate.
