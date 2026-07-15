# PRE-IMPLEMENTATION CHECK - TASK-CHATGPT-DEVICE-CODE-PROVIDER.3

PRE-CHECK RESULT
PRE-CHECK PASSED

```text
legacy handoff start
NEXT: janus-executioner
Target Task: TASK-CHATGPT-DEVICE-CODE-PROVIDER.3
Target Subtask: N/A
Task: documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.md
Spec: documentation/SPEC/CHATGPT_OFFICIAL_DEVICE_CODE_PROVIDER_REDESIGN_FEATURE_SPEC.md
Backlog Item: N/A
Assigned Model: 5.6 Terra
Assigned Intelligence: high
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- Tasks .1 and .2 Final Audit PASS provide the binding isolated credential, redaction, Settings lifecycle, atomic replacement, and production-default-deny foundation.
- The official Codex App Server public protocol includes `model/list`; the model source is therefore current-session capable without an undocumented/private endpoint.
- frontend/js/app.js is now explicitly bound as the existing provider/model-dropdown owner alongside chat.js and settings.js.
- Task .3 is one bounded availability/selection slice. It does not send ChatGPT content, transfer conversation context, change credential storage, request privacy acknowledgement, or activate production.
Affected Files:
- backend/llm_providers/codex_app_server.py
- backend/api/routers/system.py
- backend/services/model_catalog.py
- frontend/index.html
- frontend/js/app.js
- frontend/js/chat.js
- frontend/js/settings.js
- backend/tests/test_codex_connection_settings_api.py
- backend/tests/test_model_hierarchy_single_source.py
- tests/e2e/codex-connection-settings.spec.js
Evidence Focus:
- Derive ChatGPT availability and offered models only from the current successful `model/list` result of the active Janus-owned session.
- Keep ChatGPT unavailable and preserve the connected Janus account for empty, failed, expired, or absent verification; offer non-destructive retry with a non-sensitive message.
- Prevent static, cached, last-known, imported, or stale models from granting provider/model selection eligibility.
- Reject a selected ChatGPT model whose current verified usability is lost before any next ChatGPT submission; Task .4 owns all transport/content handling.
- Preserve API-key provider/model selection, hierarchy, Settings lifecycle, and credential isolation/redaction unchanged.
Scope-Regel:
- Implement only TASK-CHATGPT-DEVICE-CODE-PROVIDER.3 within the ten listed files. No architecture drift, provider/API-key fallback, static model fallback, credential-boundary change, chat transport, context transfer, privacy acknowledgement, production activation, release, or live account action.
- If current-session verification cannot be implemented exclusively through the documented `model/list` surface, if it requires a Task .1/.2 boundary change, or if API-key non-interference cannot be evidenced, stop execution and return BLOCKED.
Automated Evidence Gate:
- python -m pytest backend/tests/test_codex_connection_settings_api.py -q
- python -m pytest backend/tests/test_model_hierarchy_single_source.py -q
- python -m py_compile backend/llm_providers/codex_app_server.py backend/api/routers/system.py backend/services/model_catalog.py
- node --check frontend/js/app.js
- node --check frontend/js/chat.js
- node --check frontend/js/settings.js
- npx playwright test <runner> --headed --workers=1 --reporter=list
- npx playwright test tests/e2e/codex-connection-settings.spec.js --headed --workers=1 --reporter=list
- git diff --check -- backend/llm_providers/codex_app_server.py backend/api/routers/system.py backend/services/model_catalog.py frontend/index.html frontend/js/app.js frontend/js/chat.js frontend/js/settings.js backend/tests/test_codex_connection_settings_api.py backend/tests/test_model_hierarchy_single_source.py tests/e2e/codex-connection-settings.spec.js
Artifact Identity Check:
- PASS: Task, Target Task, Backlog Item, approved Feature Spec, Task .3 breakdown, and user-approved frontend/js/app.js scope correction verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. No TestSpec or generated test-plan artifact is in scope; route any later TestSpec change to janus-test-pipeline.
Keep Context:
- documentation/SPEC/CHATGPT_OFFICIAL_DEVICE_CODE_PROVIDER_REDESIGN_FEATURE_SPEC.md
- documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.md
- documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.3_task_breakdown.md
- documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_final_audit.md
- documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.2_final_audit.md
- ten affected files and the automated evidence commands
Drop Context:
- prior Task .3 blocked-precheck wording, BACKLOG-131, Task .2.2, unrelated dirty worktree paths, Tasks .4 and .5, release and Git history
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
User Action: Reply `ok` to start janus-executioner for Task .3 only; no live account, message submission, production, Git, or release action is authorized by this precheck.
