# PRE-IMPLEMENTATION CHECK - TASK-OPENROUTER-JANUS-CHAT-PROVIDER.1

PRE-CHECK RESULT
PRE-CHECK PASSED

```text
legacy handoff start
NEXT: janus-executioner
Target Task: TASK-OPENROUTER-JANUS-CHAT-PROVIDER.1
Target Subtask: N/A
Task: documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.1_task_breakdown.md
Spec: documentation/SPEC/OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md
Backlog Item: N/A
Assigned Model: 5.6 Terra
Assigned Intelligence: high
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The approved Spec and refined Task .1 bind exactly one release-owned OpenRouter certification authority and no production candidate activation.
- backend/utils/config_loader.py is the existing API catalog loader but currently merges AppData values over release data; OpenRouter certification must be applied after that merge and may only come from the packaged release registry.
- backend/services/model_catalog.py is a second catalog path; it can share the same filtered decision by delegating to backend.utils.config_loader.load_model_catalog() without a new product or architecture decision.
- backend/api/routers/system.py already serves load_model_catalog() through /api/models/catalog; it must not append or restore an uncertified OpenRouter entry through any other model source.
- janus_backend.spec already packages backend/config as release resources, so the new registry can remain release-owned without AppData bootstrap or a mutable second authority.
- Relevant product/config/test files are clean in the current worktree. Existing unrelated changes remain out of scope and must be preserved.
Affected Files:
- backend/config/openrouter_certified_models.json
- backend/config/model_catalog.json
- backend/utils/config_loader.py
- backend/services/model_catalog.py
- backend/api/routers/system.py
- backend/tests/test_openrouter_certification_registry.py
- backend/tests/test_model_hierarchy_single_source.py
Evidence Focus:
- Make the packaged registry the sole source of OpenRouter certification; AppData, user config, remote state, aliases, and cached last-known data cannot grant eligibility.
- Bind exact model ID, concrete model version, battery version, passed status, and complete mandatory test/audit evidence state in one unambiguous record.
- Fail closed for missing, malformed, duplicate, incomplete, failed, alias-based, unknown-version, or binding-mismatched registry content.
- Keep the Task .1 production registry empty or non-certified; use only temporary fixtures for valid-record tests and defer real candidates/evidence to Task .6.
- Return the same filtered OpenRouter set from config_loader, the service loader, and /api/models/catalog while preserving every non-OpenRouter entry.
- Do not introduce runtime imports, hot pulls, real provider calls, credential access, chat behavior, UI behavior, telemetry, MOA routing, release, or production activation.
Scope-Regel:
- Implement only TASK-OPENROUTER-JANUS-CHAT-PROVIDER.1 within the seven listed files. No architecture drift, provider fallback, remote/runtime catalog import, AppData certification authority, real model selection, candidate certification, credential work, chat transport, UI, telemetry, release, production activation, or scope expansion.
- If one shared filtered decision cannot cover both catalog loaders and /api/models/catalog, if a real model ID or battery-content decision is required, or if user-/runtime-controlled state must grant certification, stop execution and return BLOCKED.
Automated Evidence Gate:
- python -m pytest backend/tests/test_openrouter_certification_registry.py backend/tests/test_model_hierarchy_single_source.py -q
- python -m py_compile backend/utils/config_loader.py backend/services/model_catalog.py backend/api/routers/system.py backend/tests/test_openrouter_certification_registry.py backend/tests/test_model_hierarchy_single_source.py
- python -c "import json, pathlib; json.loads(pathlib.Path('backend/config/model_catalog.json').read_text(encoding='utf-8')); json.loads(pathlib.Path('backend/config/openrouter_certified_models.json').read_text(encoding='utf-8'))"
- npx playwright test <runner> --headed --workers=1 --reporter=list
- npx playwright test tests/e2e/codex-connection-settings.spec.js --headed --workers=1 --reporter=list
- git diff --check -- backend/config/openrouter_certified_models.json backend/config/model_catalog.json backend/utils/config_loader.py backend/services/model_catalog.py backend/api/routers/system.py backend/tests/test_openrouter_certification_registry.py backend/tests/test_model_hierarchy_single_source.py
Artifact Identity Check:
- PASS: Approved Spec, refined Task .1 artifact, Target Task, Backlog Item N/A, assigned model, files, exclusions, acceptance criteria, tests, packaging evidence, and single-target handoff verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. No TestSpec, generated test-plan, or test-result artifact is in scope; route any later TestSpec change to janus-test-pipeline.
Keep Context:
- documentation/SPEC/OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md
- documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.1_task_breakdown.md
- the seven affected files
- janus_backend.spec as read-only packaging evidence
- the automated evidence commands and stop gates
Drop Context:
- Decision Summary, Cursor draft, prior review history, Tasks .2 through .6, real OpenRouter model research, old OpenRouter delegation history, ChatGPT provider history, unrelated dirty worktree paths, Git history, release, and production context
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
User Action: Reply `ok` to implement Task `.1` only; no live provider, credential, real model certification, later task, Git, release, or production action is authorized.
