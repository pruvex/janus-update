# BACKLOG HANDOFF - BACKLOG-131

## HANDOFF_SCOPE

- Backlog Item: `BACKLOG-131`
- Target Task: `TASK-BACKLOG-131-SETTINGS-NAVIGATION`
- Entry Point: `PRE_IMPLEMENTATION_VERIFICATION`
- Required Next Skill: `janus-preimplementation-check`
- Required Artifact: this handoff
- Evidence Paths:
  - `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.2_debug_result.md`
  - `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.2_execution_result.md`
  - `test-results/tests-e2e-codex-connection-aed8d-thout-mutating-API-key-form-janus-chromium/error-context.md`
  - `frontend/js/app.js`
- Dropped Context: unrelated backlog items, old DONE history, Task `.1` implementation history, device-code account actions, provider/model selection, API-key management, transport, and release work.

## Bound Problem

`frontend/js/app.js` first binds `#settings-btn` to the stateful Settings transition, then a delayed legacy block clones the same button and replaces that listener with `forceOpenSettings()`. The replacement does not synchronize `appState.currentView` or dispatch `show-settings`, and it invokes `initializeApp()` again. After the delay, the visible Settings button can therefore leave the application in the Chat surface and the API-key section is unavailable to the bound headed E2E suite.

## Goal

Restore one durable, state-consistent Settings navigation path for the visible sidebar button without changing the Task `.1` credential boundary or the Task `.2` Device-Code lifecycle contract.

## Bound Scope For Precheck

- Inspect `frontend/js/app.js` navigation initialization and determine the narrowest safe removal, consolidation, or synchronization of the duplicate Settings-button binding.
- Candidate product file: `frontend/js/app.js`.
- Candidate validation file: `tests/e2e/codex-connection-settings.spec.js`; precheck may name one additional focused navigation test only if required to prove the general button behavior.
- Re-run the full bound Task `.2` mocked headed E2E suite after the navigation correction, plus the focused Settings/API contract checks already bound to Task `.2`.

## Explicitly Out Of Scope

- Device-Code/OAuth flows, token or credential persistence, keyring storage, public API response shapes, renderer Device-Code presentation, account switching, API-key providers, provider/model selection, chat transport, privacy acknowledgement, production activation, release, and live account actions.
- Broad navigation redesign, unrelated emergency navigation helpers, or changes to the Task `.1` final-audit record.

## Acceptance Gate

- After application initialization, the visible `#settings-btn` has one state-consistent navigation path that reaches Settings and the API-key section.
- The correction does not trigger a second application initialization solely to open Settings.
- `tests/e2e/codex-connection-settings.spec.js` passes headed with its mocked lifecycle responses and no DOM/timing workaround.
- Task `.1` credential isolation, redaction, two-account non-interference evidence, API-key behavior, provider/model non-selection, and production default-deny remain unchanged.

## Next Skill Copy Prompt

```text
@[/SKILL 3 - PRE-IMPLEMENTATION VERIFICATION]
Target Task: TASK-BACKLOG-131-SETTINGS-NAVIGATION
Task: documentation/tasks/backlog_BACKLOG-131_settings_handler_navigation.md
Backlog Item: BACKLOG-131
```

Keep Context:
- `BACKLOG-131`
- this handoff
- `TASK-CHATGPT-DEVICE-CODE-PROVIDER.2_debug_result.md`

Drop Context:
- unrelated READY items
- old DONE history
- broad backlog narrative
