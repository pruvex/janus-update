PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC16.3
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC16_adressbuch_karten_redesign_und_spitzname_besonderheiten.md
Spec: documentation/SPEC/16_adressbuch_karten_redesign_und_spitzname_besonderheiten.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it updates focused regression coverage so the automated contact evidence matches the already implemented nickname, card, and dialog contract from TASK-SPEC16.1 and TASK-SPEC16.2.
- Source-of-truth identity is consistent across Spec 16, the TASK-SPEC16 artifact, and the execution result of TASK-SPEC16.2, which already documents that the current Playwright failure comes from legacy expectations for removed status badges.
- The affected files are concrete and bounded to the regression surface: `backend/tests/test_contact_manager.py`, `tests/e2e/generated/TASK-SPEC15-address-book-ui-evidence.spec.js`, and only product files strictly needed to support stable assertions if a tiny test-facing adjustment is unavoidable.
- Implementation risk is MEDIUM because this task touches the automated oracle for a live UI contract; a git checkpoint is recommended through `janus-git-governance` before Skill 4 because the worktree already contains multiple code, docs, and test changes.
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- pytest backend/tests/test_contact_manager.py -q
- npx playwright test tests/e2e/generated/TASK-SPEC15-address-book-ui-evidence.spec.js --headed --workers=1 --reporter=list
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
Reason: The task is implementation-ready and narrowly scoped to bringing the regression oracle in line with the approved and already landed address-book contract.
User Action: Say `ok` to start implementation of `TASK-SPEC16.3` with the bound scope and evidence gate above.
