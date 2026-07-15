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
