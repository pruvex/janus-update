PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC16.1
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC16_adressbuch_karten_redesign_und_spitzname_besonderheiten.md
Spec: documentation/SPEC/16_adressbuch_karten_redesign_und_spitzname_besonderheiten.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it adds nickname persistence and keeps existing details/notes compatible under the new `Besonderheiten` interpretation without touching the later card/dialog redesign task.
- Source-of-truth identity is consistent across Spec 16, the generated TASK-SPEC16 artifact, and the released target task `TASK-SPEC16.1`.
- Affected files are concrete and bounded to the existing contact persistence stack: `backend/data/models.py`, `backend/data/contact_schemas.py`, `backend/data/crud.py`, `backend/data/database.py`, and `backend/tests/test_contact_manager.py`.
- Implementation risk is MEDIUM because the task changes persisted contact shape and must preserve old content semantics; a git checkpoint is recommended through `janus-git-governance` before Skill 4 because the worktree already contains other changes, including `frontend/js/settings.js`.
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m py_compile backend/data/models.py backend/data/contact_schemas.py backend/data/crud.py backend/data/database.py
- pytest backend/tests/test_contact_manager.py -q
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-step handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The task is implementation-ready, bounded to the contact persistence contract, and should land before the later UI restructuring builds on the new field.
User Action: Say `ok` to start implementation of `TASK-SPEC16.1` with the bound scope and evidence gate above.
