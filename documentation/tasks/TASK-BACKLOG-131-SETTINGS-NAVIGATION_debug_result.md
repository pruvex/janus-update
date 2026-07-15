SKILL 5 DEBUG RESULT: OUT OF SCOPE

Iteration: 1

Progress-Validierung: Failure Code `E2E_REPLACEMENT_LIFECYCLE_PENDING_STUCK`; Evidence geaendert ggü. N-1: N/A; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN.

## Bound Failure Slice

- Target Task: `TASK-BACKLOG-131-SETTINGS-NAVIGATION`
- Backlog Item: `BACKLOG-131`
- Spec: N/A WITH REASON - bounded Backlog navigation correction.
- Expected: after the mocked replacement login reaches the connected public state, the Settings card replaces `Anmeldung abbrechen` with `Abmelden` and `Konto wechseln`.
- Actual: the second account identity renders, but its card remains `connecting/login_pending`; the full headed runner times out waiting for `Abmelden` after four preceding scenarios pass.
- New evidence: the E2E route supplies `nextStatusState` only on `GET /api/codex-connection`. `frontend/js/settings.js` renders the `POST /login` response as connecting and opens the verification URL, but does not call `refreshCodexConnectionCard()` or otherwise poll the public status after that action. The queued connected response is therefore never consumed.
- Changed product files during debug iteration 1: none.
- Security boundary: all lifecycle responses are mocked; no live Device-Code, account, credential, token, provider, production, or Git action occurred.

Root Cause: `E2E_REPLACEMENT_LIFECYCLE_PENDING_STUCK`. The Settings renderer lacks a bounded public-state refresh after a managed replacement login starts. This is a Task `.2` renderer-lifecycle gap, not a remaining BACKLOG-131 navigation defect.

Fix Summary: no fix is applied in `janus-debug`. The identified correction belongs in `frontend/js/settings.js`, which is outside the passed BACKLOG-131 precheck. The existing Task `.2` scope owns that renderer file, but it needs a newly released, explicit follow-up target before execution.

Auto-Verification:
- Status: PASS
- Evidence: targeted `WHAT_I_LEARNED` search preserved the Task `.1` isolation tripwire; static correlation of the E2E queued GET state with the renderer's POST-only login path is deterministic and does not require a live account.

Artifact Identity Check: PASS

Final Feature Suite: N/A WITH REASON - BACKLOG-131 navigation validation is partially demonstrated, but the shared Task `.2` E2E suite is still blocked by an out-of-scope renderer-lifecycle gap.

Changed Files:

- `documentation/tasks/TASK-BACKLOG-131-SETTINGS-NAVIGATION_debug_result.md`
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/SKILL_USAGE_LOG.md`

NEXT_STEP
Target Skill: janus-task-breakdown
Canonical State: HANDOFF
Required Artifacts: Task `.2` breakdown and passed precheck; BACKLOG-131 execution result and this debug result; `frontend/js/settings.js`; `tests/e2e/codex-connection-settings.spec.js`.
Evidence Paths: `documentation/tasks/TASK-BACKLOG-131-SETTINGS-NAVIGATION_execution_result.md`; this debug result; `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.2_execution_result.md`; `test-results/tests-e2e-codex-connection-8aef9-es-it-only-after-completion-janus-chromium/error-context.md`.
Failure Code: E2E_REPLACEMENT_LIFECYCLE_PENDING_STUCK
Changed Files: debug documentation only.
Decision: release one bounded Task `.2` follow-up for a cancellable, public-state-only refresh after managed replacement login, then retest the existing headed runner.
Reason: the only identified product correction is in Task `.2` renderer scope, not the BACKLOG-131 navigation scope; a fresh target prevents silent scope expansion and preserves Task `.1` security boundaries.
Recommended Model: 5.6 Terra
Recommended Intelligence: high
Next User Action: reply `ok` to run `janus-task-breakdown` for exactly one Task `.2` renderer-refresh follow-up; do not rerun the full suite or modify settings code before that handoff exists.
