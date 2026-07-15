# TASK BREAKDOWN - TASK-CHATGPT-DEVICE-CODE-PROVIDER.2.2

## Source Identity

- **Spec:** `documentation/SPEC/CHATGPT_OFFICIAL_DEVICE_CODE_PROVIDER_REDESIGN_FEATURE_SPEC.md`
- **Task File:** `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.md`
- **Parent Task:** `TASK-CHATGPT-DEVICE-CODE-PROVIDER.2`
- **Backlog Item:** N/A WITH REASON - deterministic E2E follow-up for the incomplete compiled Feature Spec task
- **Prior Gates:** Task `.1` Final Audit PASS; BACKLOG-131 navigation correction reaches the Settings surface; Task `.2.1` precheck correctly blocked its contradicted renderer premise
- **Failure Source:** `E2E_REPLACEMENT_LIFECYCLE_PENDING_STUCK` and `TASK-CHATGPT-DEVICE-CODE-PROVIDER.2.1_precheck.md`

## Selected Target

- **Target Task:** `TASK-CHATGPT-DEVICE-CODE-PROVIDER.2.2`
- **Target Subtask:** N/A
- **Mode:** SINGLE_TASK_PRECHECK
- **Goal:** Correct the mocked replacement-account state sequencing so the existing post-action public-status refresh consumes the simulated connected state after the login POST, not before it.

## Scope

- In the existing intercepted E2E lifecycle mock, represent the replacement completion state separately from the next generic status response.
- Queue that connected replacement state only after the login POST has set and returned the expected pending state.
- Keep the existing renderer action flow, public-state refresh, account-switch assertions, redaction checks, external-open stubs, and no-live-account discipline unchanged.

## Files

- `tests/e2e/codex-connection-settings.spec.js`

## Explicit Exclusions

- No change to `frontend/js/settings.js`, `frontend/js/app.js`, HTML, CSS, backend API/lifecycle, Device-Code protocol, credential/keyring persistence, provider/model selection, chat transport, privacy, production, release, live account action, or Git action.
- No TestSpec, generated TestPlan, or TestResult artifact change.

## Acceptance Criteria

1. The generic pre-action `GET /api/codex-connection` cannot consume the replacement completion state.
2. The mocked login POST first returns the expected matching pending state, then makes exactly one connected replacement state available to the existing post-action public refresh.
3. The existing replacement scenario observes `second@example.com`, `Abmelden`, and no early Janus logout; its logout assertion remains valid.
4. The complete headed Task `.2` E2E suite passes with mocked responses only.
5. The runner does not emit or depend on credentials, tokens, private account data beyond existing non-secret fixtures, or live account activity; Task `.1` isolation/redaction and production default-deny remain unchanged.

## Tests

- `node --check tests/e2e/codex-connection-settings.spec.js`
- `python -m pytest backend/tests/test_codex_connection_settings_api.py -q`
- `npx playwright test tests/e2e/codex-connection-settings.spec.js --headed --workers=1 --reporter=list`
- Scoped `git diff --check` for the bound E2E runner

## Risks And Precheck Gates

- Preserve actual renderer timing: the mock must match the existing action listener's pre-action GET, login POST, and post-action refresh order rather than bypassing it.
- Preserve all redaction and atomic-switch assertions; a passing test must not be obtained by skipping the pending or logout transition.
- Block precheck if a runner-only correction cannot simulate the existing public-state order without product-code or contract changes.

## Execution Model

- **Model:** `5.6 Terra`
- **Intelligence:** high
- **Reason:** Small deterministic E2E lifecycle-sequencing correction with security-sensitive regression assertions.

## Decision

TASK DESIGN COMPLETE

```text
@janus-preimplementation-check
Spec: documentation/SPEC/CHATGPT_OFFICIAL_DEVICE_CODE_PROVIDER_REDESIGN_FEATURE_SPEC.md
Task: documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.md
Backlog Item: N/A
Target Task: TASK-CHATGPT-DEVICE-CODE-PROVIDER.2.2
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.6 Terra
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```
