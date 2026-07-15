# PRE-IMPLEMENTATION CHECK - TASK-CHATGPT-DEVICE-CODE-PROVIDER.2.1

PRE-CHECK BLOCKED: SCOPE_MISMATCH

Target Task: `TASK-CHATGPT-DEVICE-CODE-PROVIDER.2.1`

Reason: The bound target assumes that `frontend/js/settings.js` lacks a public-state refresh after managed login. Current source evidence contradicts that premise: the existing action listener fetches current public state before dispatching the action, executes `handleCodexConnectionAction(...)`, then calls `await refreshCodexConnectionCard()` after the login POST. The E2E mock instead consumes `nextStatusState` in that pre-action GET, then the POST replaces its state with `connecting`; the post-action refresh correctly receives the still-pending mock state.

Required Correction To The Handoff: Do not edit `settings.js`. Refine exactly one runner-only target that schedules the mocked replacement connected state after the login POST rather than before the action-handler's pre-action GET. Preserve the existing renderer refresh, public-state-only contract, redaction, atomic account-switch assertions, API-key regression, provider/model non-selection, and production default-deny.

Evidence:

- `frontend/js/settings.js`: action listener obtains `currentPayload`, calls `handleCodexConnectionAction`, then `refreshCodexConnectionCard`.
- `tests/e2e/codex-connection-settings.spec.js`: `nextStatusState` is consumed on every mocked `GET /api/codex-connection`, while the replacement test assigns it immediately before clicking `Konto wechseln`.
- `documentation/tasks/TASK-BACKLOG-131-SETTINGS-NAVIGATION_debug_result.md`: original failure evidence.

NEXT: janus-task-breakdown
Blocked Target: `TASK-CHATGPT-DEVICE-CODE-PROVIDER.2.1`
Required Decision: release one runner-only replacement-state sequencing correction; no renderer, credential, provider, account, or production change.
