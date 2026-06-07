PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC15.1
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC15_semi_automatisches_adressbuch_mit_memory_kopplung.md
Spec: documentation/SPEC/15_semi_automatisches_adressbuch_mit_memory_kopplung.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic enough for execution: extend only the contact-card storage, schema/API contract, and existing settings address-book surface needed for richer cards and proposal-management metadata.
- This task explicitly excludes proposal orchestration, public-web enrichment decisions, and Memory write coupling; those remain in later TASK-SPEC15.2 through TASK-SPEC15.4 and must not be pulled forward.
- Implementation risk is MEDIUM to HIGH because the work touches persisted contact data, lightweight SQLite schema migration, an existing API path, and the current address-book UI in one pass.
- The repository currently has a dirty worktree outside this task's bound artifacts, so execution must stage explicit pathspecs only and should recommend a `janus-git-governance` checkpoint before risky persistence edits.
Affected Files:
- backend/data/models.py
- backend/data/database.py
- backend/data/contact_schemas.py
- backend/data/crud.py
- backend/api/routers/contacts.py
- frontend/index.html
- frontend/js/settings.js
- frontend/css/settings.css
- backend/tests/test_contact_manager.py
- backend/tests/integration/test_error_resilience.py
Evidence Focus:
- `python -m pytest backend/tests/test_contact_manager.py -q`
- `python -m pytest backend/tests/integration/test_error_resilience.py -q`
- Add or update CRUD/API regression coverage for richer contact-card fields and migration-safe defaults.
- `node --check frontend/js/settings.js`
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest backend/tests/test_contact_manager.py -q
- python -m pytest backend/tests/integration/test_error_resilience.py -q
- node --check frontend/js/settings.js
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- bound task/spec identity
- contact persistence and migration files
- existing settings address-book UI flow
- evidence commands above
Drop Context:
- later TASK-SPEC15 proposal, enrichment, and Memory-coupling logic
- old audit chatter and unrelated backlog history
- unrelated dirty-worktree files outside the bound execution set
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: high
Reason: The task is implementation-ready and bounded, but it changes persisted contact shape plus existing UI and should keep 5.4 context warm while using higher reasoning for migration-safe edits.
User Action: Say `ok` to start implementation of `TASK-SPEC15.1` with the bound scope and evidence gate above.
