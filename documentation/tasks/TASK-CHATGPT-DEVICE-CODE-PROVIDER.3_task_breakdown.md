# TASK BREAKDOWN - TASK-CHATGPT-DEVICE-CODE-PROVIDER.3

## Source Identity

- **Spec:** `documentation/SPEC/CHATGPT_OFFICIAL_DEVICE_CODE_PROVIDER_REDESIGN_FEATURE_SPEC.md`
- **Task File:** `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.md`
- **Backlog Item:** N/A WITH REASON - compiled Feature Spec task
- **Prior Gates:** Tasks `.1` and `.2` Final Audit PASS; `BACKLOG-131` Final Audit PASS and documentation closeout complete

## Selected Target

- **Target Task:** `TASK-CHATGPT-DEVICE-CODE-PROVIDER.3`
- **Target Subtask:** N/A
- **Mode:** SINGLE_TASK_PRECHECK
- **Goal:** Make ChatGPT selectable in the existing provider/model UI only when the active, Janus-owned session has at least one currently verified usable model, while preserving fail-closed behavior and all existing providers.

## Scope

- Derive non-sensitive ChatGPT model availability exclusively from the active Janus ChatGPT session; no static, cached, last-known, imported, or externally shared model list can grant selection.
- Expose only the current verification result through the existing system/model catalogue contracts.
- Render ChatGPT and its model options conditionally in the existing provider/model dropdown; show only currently verified usable models.
- Preserve the connected Janus account when verification is empty or fails, but make ChatGPT unavailable, hide unverified models, report the non-sensitive unavailable state, and offer non-destructive retry.
- Before the next attempted ChatGPT submission, reject a selected model whose verified availability has been lost and require a newly valid selection.
- Preserve API-key providers, their existing model options, settings behavior, and provider hierarchy unchanged.

## Files

- `backend/llm_providers/codex_app_server.py`
- `backend/api/routers/system.py`
- `backend/services/model_catalog.py`
- `frontend/index.html`
- `frontend/js/app.js`
- `frontend/js/chat.js`
- `frontend/js/settings.js`
- `backend/tests/test_codex_connection_settings_api.py`
- `backend/tests/test_model_hierarchy_single_source.py`
- `tests/e2e/codex-connection-settings.spec.js`

## Explicit Exclusions

- No Device-Code login, refresh, logout, account-switch, credential storage, credential import, shared credential, plaintext/session-only fallback, or changes to the Task `.1` isolation boundary.
- No ChatGPT chat transport, message/content transmission, conversation-context transfer, privacy acknowledgement, production activation, release, publish, or live account action.
- No static ChatGPT model catalogue, stale fallback list, API-key fallback, or alteration of another provider's availability/model selection.
- No Task `.4` or `.5` work.

## Acceptance Criteria

1. ChatGPT appears as selectable provider only with a valid Janus-owned connection and at least one currently verified usable model.
2. ChatGPT exposes only the models from the current successful verification result.
3. An empty, failed, expired, or absent verification keeps the Janus connection intact but makes ChatGPT unavailable and hides all ChatGPT models.
4. The unavailable state says `Modelle derzeit nicht verfügbar` (or approved equivalent), contains no secret or account detail, and offers a non-destructive retry.
5. A previously selected ChatGPT model that loses verified usability is rejected before the next ChatGPT submission and requires a fresh valid model selection.
6. Static, cached, last-known, imported, or stale models never create ChatGPT selection eligibility.
7. Existing API-key providers, their model lists, settings lifecycle, and hierarchy remain unchanged.
8. Credential values, device codes, tokens, private account identifiers, and secret-bearing URLs are absent from availability/status responses, UI errors, logs, telemetry, test snapshots, and evidence.
9. ChatGPT transport remains unimplemented and production remains default-deny.

## Tests

- `python -m pytest backend/tests/test_codex_connection_settings_api.py -q` for connected, empty, failed, retried, and non-sensitive model-verification state/API contracts.
- `python -m pytest backend/tests/test_model_hierarchy_single_source.py -q` for provider/model hierarchy, current-verification-only eligibility, and API-key provider regression.
- `npx playwright test tests/e2e/codex-connection-settings.spec.js --headed --workers=1 --reporter=list` for conditional ChatGPT visibility, verified-model-only options, unavailable/retry rendering, stale-selection loss, and existing provider regression.
- JavaScript syntax checks for `frontend/js/app.js`, `frontend/js/chat.js`, and `frontend/js/settings.js`, plus scoped `git diff --check` over the bound files.
- Test doubles only for session/model-verification results; no live login, refresh, account switch, model entitlement query against a real account, message submission, or two-account action is authorized.

## Risks And Precheck Gates

- Verify `frontend/js/app.js`, the existing provider/model-dropdown owner, receives only the current Janus-owned availability result and cannot read, import, or infer models from Codex Desktop, CLI, IDE, API-key settings, or stale cache.
- Verify failed/empty verification has no destructive lifecycle side effect and cannot leave ChatGPT selectable.
- Verify the selected-model loss gate blocks before any transport/content externalization; implementing transport is a Task `.4` boundary and must block this precheck if required.
- Verify retry remains non-destructive, concurrency-safe, and redacted.
- Block precheck if the required model source is undocumented/private, if a durable static fallback is required, if a Task `.1`/`.2` security boundary must change, or if API-key/provider non-interference cannot be tested.

## Execution Model

- **Model:** `5.6 Terra`
- **Intelligence:** high
- **Reason:** Provider/model integration across backend contracts and existing UI must preserve fail-closed, current-session-only eligibility without crossing into transport or privacy scope.

## Decision

TASK DESIGN COMPLETE

```text
@janus-preimplementation-check
Spec: documentation/SPEC/CHATGPT_OFFICIAL_DEVICE_CODE_PROVIDER_REDESIGN_FEATURE_SPEC.md
Task: documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.md
Backlog Item: N/A
Target Task: TASK-CHATGPT-DEVICE-CODE-PROVIDER.3
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.6 Terra
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```
