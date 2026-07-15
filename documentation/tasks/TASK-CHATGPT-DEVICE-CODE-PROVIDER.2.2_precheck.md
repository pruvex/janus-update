# PRE-IMPLEMENTATION CHECK - TASK-CHATGPT-DEVICE-CODE-PROVIDER.2.2

PRE-CHECK RESULT
PRE-CHECK PASSED

```text
legacy handoff start
NEXT: janus-executioner
Target Task: TASK-CHATGPT-DEVICE-CODE-PROVIDER.2.2
Target Subtask: N/A
Task: documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.2.2_task_breakdown.md
Spec: documentation/SPEC/CHATGPT_OFFICIAL_DEVICE_CODE_PROVIDER_REDESIGN_FEATURE_SPEC.md
Backlog Item: N/A
Assigned Model: 5.6 Terra
Assigned Intelligence: high
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The existing Settings action handler already performs the authoritative public-state refresh after the managed login POST; the runner alone queues the simulated replacement connected state too early.
- The correction is exactly one mocked E2E sequencing change. It does not alter renderer, API, Device-Code, credential, provider, account, or production behavior.
Affected Files:
- tests/e2e/codex-connection-settings.spec.js
Evidence Focus:
- Preserve the real action order: pre-action GET, login POST returning pending, then post-action GET returning the queued connected replacement state.
- Preserve pending, cancel, failure, redaction, atomic-switch, Janus-only logout, API-key, provider/model non-selection, and production-default-deny assertions.
- node --check tests/e2e/codex-connection-settings.spec.js
- python -m pytest backend/tests/test_codex_connection_settings_api.py -q
- npx playwright test tests/e2e/codex-connection-settings.spec.js --headed --workers=1 --reporter=list
- git diff --check -- tests/e2e/codex-connection-settings.spec.js
Scope-Regel:
- Implement only TASK-CHATGPT-DEVICE-CODE-PROVIDER.2.2 in the bound E2E runner. No renderer, backend, lifecycle, credential, provider/model, chat, privacy, production, live-account, release, or Git action.
- Do not bypass the existing public refresh or relax assertions; correct only mock-state availability after the pending login POST.
Automated Evidence Gate:
- node --check tests/e2e/codex-connection-settings.spec.js
- python -m pytest backend/tests/test_codex_connection_settings_api.py -q
- npx playwright test <runner> --headed --workers=1 --reporter=list
- npx playwright test tests/e2e/codex-connection-settings.spec.js --headed --workers=1 --reporter=list
- git diff --check -- tests/e2e/codex-connection-settings.spec.js
Artifact Identity Check:
- PASS: Target Task, Task `.2` source, Spec, `.2.2` breakdown, pre-action GET/post-action GET mock order, and exact runner path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. No TestSpec change is in scope; preserve the existing bound mocked E2E assertions.
Keep Context:
- `.2.2` breakdown and this precheck
- settings action ordering as read-only seam evidence
- bound E2E runner
Drop Context:
- blocked `.2.1` renderer premise
- BACKLOG-131 navigation implementation history
- unrelated feature tasks and account history
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
User Action: Reply `ok` to execute only TASK-CHATGPT-DEVICE-CODE-PROVIDER.2.2; no live account or Git action is authorized.
