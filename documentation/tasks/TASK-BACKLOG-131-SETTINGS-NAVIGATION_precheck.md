# PRE-IMPLEMENTATION CHECK - TASK-BACKLOG-131-SETTINGS-NAVIGATION

PRE-CHECK RESULT
PRE-CHECK PASSED

```text
legacy handoff start
NEXT: janus-executioner
Target Task: TASK-BACKLOG-131-SETTINGS-NAVIGATION
Target Subtask: N/A
Task: documentation/tasks/backlog_BACKLOG-131_settings_handler_navigation.md
Spec: N/A WITH REASON - independent bounded Backlog BUG; no Feature Spec is required for this small navigation correction.
Backlog Item: BACKLOG-131
Assigned Model: 5.6 Terra
Assigned Intelligence: high
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound failure is deterministic: a 500-ms legacy listener replacement clones `#settings-btn`, removes the stateful listener, invokes `forceOpenSettings()`, and reinitializes the app without synchronized Settings state/event handling.
- The target is a small general-Settings navigation correction, separate from the blocked Task `.2` Device-Code presentation work. Task `.2` remains blocked until this task is validated and its headed suite can run green.
- Task `.1` secure credential isolation, redaction, two-account evidence, and production default-deny are binding regressions only; no lifecycle, credential, provider, or production behavior belongs to this task.
Affected Files:
- frontend/js/app.js
- tests/e2e/codex-connection-settings.spec.js
Evidence Focus:
- Preserve one state-consistent `#settings-btn` path after application initialization.
- Preserve the intended API-key Settings entry without a redundant initialization race.
- `node --check frontend/js/app.js`
- `node --check tests/e2e/codex-connection-settings.spec.js`
- `python -m pytest backend/tests/test_codex_connection_settings_api.py -q`
- `npx playwright test tests/e2e/codex-connection-settings.spec.js --headed --workers=1 --reporter=list`
- `git diff --check -- frontend/js/app.js tests/e2e/codex-connection-settings.spec.js`
Scope-Regel:
- Implement only TASK-BACKLOG-131-SETTINGS-NAVIGATION within the two affected files. No Device-Code/OAuth, credential/keyring, API-router, API-key, provider/model, chat transport, privacy, production, release, live-account, or Git action.
- Do not reintroduce a DOM/timing workaround in the E2E helper; correct the bounded application navigation defect and prove the existing mocked suite through the real Settings control.
Automated Evidence Gate:
- node --check frontend/js/app.js
- node --check tests/e2e/codex-connection-settings.spec.js
- python -m pytest backend/tests/test_codex_connection_settings_api.py -q
- npx playwright test <runner> --headed --workers=1 --reporter=list
- npx playwright test tests/e2e/codex-connection-settings.spec.js --headed --workers=1 --reporter=list
- git diff --check -- frontend/js/app.js tests/e2e/codex-connection-settings.spec.js
Artifact Identity Check:
- PASS: Target Task, Backlog Item, IN PROGRESS Backlog handoff path, and explicit no-Spec rationale verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. No TestSpec change is in scope; retain the existing mocked E2E as the bound regression runner.
Keep Context:
- BACKLOG-131 and its selected handoff
- frontend/js/app.js duplicate Settings-handler evidence
- tests/e2e/codex-connection-settings.spec.js and its headed failure context
Drop Context:
- unrelated Backlog history
- Task `.1` implementation details and live account history
- Task `.2` product changes beyond the bound regression runner
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.
legacy handoff end
```

## NEXT STEP

Recommended Skill: janus-executioner
Recommended Model: 5.6 Terra
Recommended Intelligence: high
User Action: Reply `ok` to execute only TASK-BACKLOG-131-SETTINGS-NAVIGATION; no live account or Git action is authorized.
