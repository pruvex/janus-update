PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC15.2
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC15_semi_automatisches_adressbuch_mit_memory_kopplung.md
Spec: documentation/SPEC/15_semi_automatisches_adressbuch_mit_memory_kopplung.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic enough for execution: rework only the existing direct-context contact-detection path so private contacts and private-contact updates become confirmation-first proposals instead of silent writes.
- Scope is limited to deterministic proposal states, duplicate or near-match routing, and persisted rejection or suppression outcomes across chat, calendar, and adjacent direct-context entry points already wired through the current contact tools.
- This task explicitly excludes public-web enrichment policy changes from TASK-SPEC15.3 and Memory coupling from TASK-SPEC15.4; execution must not pull internet-disambiguation, public-data proposal UX, or Memory write paths forward.
- Implementation risk is HIGH because the current extraction flow still auto-creates or auto-updates contacts and may auto-trigger enrichment, so the execution must preserve extraction usefulness while replacing silent mutation behavior with proposal-safe orchestration.
- The repository currently has a dirty worktree outside this task's bound artifacts, so execution must stage explicit pathspecs only and should recommend a `janus-git-governance` checkpoint before changing orchestration and persistence behavior.
Affected Files:
- backend/services/contact_manager.py
- backend/tools/contact_tools.py
- backend/tools/calendar_tools.py
- backend/services/chat_orchestrator.py
- backend/data/crud.py
- backend/data/models.py
- backend/tests/test_contact_manager.py
- backend/tests/test_calendar_tools.py
Evidence Focus:
- `python -m pytest backend/tests/test_contact_manager.py -q`
- `python -m pytest backend/tests/test_calendar_tools.py -q`
- Add or update regression coverage for confirmation-first proposal creation, duplicate or merge routing, and rejection or suppression persistence without scope expansion into public-web enrichment or Memory.
- `python -m py_compile backend/services/contact_manager.py backend/tools/contact_tools.py backend/tools/calendar_tools.py backend/services/chat_orchestrator.py backend/data/crud.py backend/data/models.py backend/tests/test_contact_manager.py backend/tests/test_calendar_tools.py`
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest backend/tests/test_contact_manager.py -q
- python -m pytest backend/tests/test_calendar_tools.py -q
- python -m py_compile backend/services/contact_manager.py backend/tools/contact_tools.py backend/tools/calendar_tools.py backend/services/chat_orchestrator.py backend/data/crud.py backend/data/models.py backend/tests/test_contact_manager.py backend/tests/test_calendar_tools.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- bound task/spec identity
- current direct-context extraction and update path in contact_manager plus contact/calendar tool entry points
- duplicate matching behavior and persisted proposal-state fields from TASK-SPEC15.1
- evidence commands above
Drop Context:
- TASK-SPEC15.1 persistence/UI migration details beyond the already-shipped contact schema
- later TASK-SPEC15.3 enrichment hardening and TASK-SPEC15.4 Memory coupling behavior
- unrelated dirty-worktree files, old audit chatter, and unbound implementation history
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: high
Reason: The task is implementation-ready and benefits from staying on warm 5.4 context while using higher reasoning for confirmation flow, duplicate routing, and suppression-state changes across existing orchestration paths.
User Action: Say `ok` to start implementation of `TASK-SPEC15.2` with the bound scope and evidence gate above.
