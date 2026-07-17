PRE-CHECK RESULT
PRE-CHECK PASSED

Target identity, source-of-truth alignment, scope, file boundary, credential-state authority, risks, and required evidence are complete for exactly `TASK-OPENROUTER-JANUS-CHAT-PROVIDER.2`.

- Risk: HIGH
- Implementation authorization: exactly the bound Task `.2` slice only
- Git checkpoint: recommend `janus-git-governance` after execution and required validation pass
- Live credential/provider access: forbidden; mocked and sentinel-based evidence only

```text
legacy handoff start
NEXT: janus-executioner
Target Task: TASK-OPENROUTER-JANUS-CHAT-PROVIDER.2
Target Subtask: N/A
Task: documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.2_task_breakdown.md
Spec: documentation/SPEC/OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md
Backlog Item: N/A
Assigned Model: 5.6 Terra
Assigned Intelligence: high
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- Implement only the isolated OpenRouter Settings credential lifecycle. A new, replaced, or unconfirmed key becomes UNVERIFIED when technical validation is incomplete; the same exact previously confirmed VALID key retains VALID through temporary technical revalidation failure; explicit authenticated 401 produces INVALID; replacement never inherits prior VALID.
- Store raw OpenRouter credential material only in the Janus-Projekt/openrouter keyring entry. Persist only Janus-owned non-secret validation metadata bound to the exact stored-key fingerprint, recompute the binding on read, and fail closed on missing or mismatched binding.
- Use only mocked HTTP/keyring evidence and a credential sentinel. Do not access a real credential or make a live OpenRouter call.
Affected Files:
- backend/api/routers/system.py
- backend/data/schemas.py
- frontend/index.html
- frontend/js/settings.js
- frontend/css/settings.css
- backend/tests/test_openrouter_key_settings_api.py
- tests/e2e/openrouter-settings.spec.js
Evidence Focus:
- python -m pytest backend/tests/test_openrouter_key_settings_api.py backend/tests/test_codex_connection_settings_api.py -q
- python -m py_compile backend/api/routers/system.py backend/data/schemas.py backend/tests/test_openrouter_key_settings_api.py
- node --check frontend/js/settings.js
- node --check tests/e2e/openrouter-settings.spec.js
- git diff --check -- backend/api/routers/system.py backend/data/schemas.py frontend/index.html frontend/js/settings.js frontend/css/settings.css backend/tests/test_openrouter_key_settings_api.py tests/e2e/openrouter-settings.spec.js
- Prove provider-specific keyring isolation, stale-VALID prevention, restart-safe exact-key binding, no retry/redirect/fallback, response/log/DOM redaction, OpenRouter-only deletion, existing API-key behavior, and ChatGPT-card non-interference.
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest backend/tests/test_openrouter_key_settings_api.py backend/tests/test_codex_connection_settings_api.py -q
- npx playwright test <runner> --headed --workers=1 --reporter=list
- npx playwright test tests/e2e/openrouter-settings.spec.js --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- corrected Task .2 credential-state contract
- exact seven-file implementation/test boundary
- mocked evidence commands and security gates
- existing OpenRouter Task .1 registry remains empty and production-disabled
Drop Context:
- old blocked precheck wording
- rejected delegated risk classification
- unrelated dirty-worktree and backlog/audit history
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.
legacy handoff end
```

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.6 Terra
Recommended Intelligence: high
User Action: Approve execution of exactly Task `.2`; no Git action is included.
