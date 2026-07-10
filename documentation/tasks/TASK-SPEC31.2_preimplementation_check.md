PRE-CHECK RESULT
PRE-CHECK PASSED

NEXT: janus-executioner
Target Task: TASK-SPEC31.2
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC31_semantisches_parameterisiertes_routine_reuse_mehrschrittige_routinen.md
Spec: documentation/SPEC/31_semantisches_parameterisiertes_routine_reuse_mehrschrittige_routinen.md
Backlog Item: BACKLOG-123
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: harden the already-delivered semantic multi-step routine-reuse path so missing parameters, conflicting values, and ambiguous candidate matches fail closed instead of reusing stale saved-routine values.
- This slice may harden only the currently accepted productive families `calendar.list_events + system.routing` and the existing `calendar.list_events + system.weather` regression path. It must not reopen the accepted positive pilot behavior from `TASK-SPEC31.1`.
- The main acceptance surface is negative and conservative: parameter gaps, conflicts, and ambiguity must stay on the normal request path instead of aggressively false-matching a saved routine.
- Risk is HIGH because this changes live saved-routine execution behavior on the same backend path that already serves productive natural reuse, and a too-broad hardening pass could silently regress the accepted routing or weather paths.
- Artifact identity is consistent across `BACKLOG-123`, the approved Spec 31, the generated `TASK-SPEC31` artifact, and the released breakdown handoff `TASK-SPEC31.2`.
Affected Files:
- backend/services/orchestrator/intent_engine.py
- backend/services/workflow/routine_runner.py
- backend/tests/test_routine_runner.py
- backend/tests/test_workflow_offer_service.py
- documentation/tasks/TASK-SPEC31_semantisches_parameterisiertes_routine_reuse_mehrschrittige_routinen.md
- documentation/tasks/TASK-SPEC31.2_task_breakdown.md
- documentation/tasks/TASK-SPEC31.2_preimplementation_check.md
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md
Evidence Focus:
- python -m pytest backend/tests/test_routine_runner.py -v
- python -m pytest backend/tests/test_workflow_offer_service.py -v
- python -m py_compile backend/services/orchestrator/intent_engine.py backend/services/workflow/routine_runner.py
- git diff --check -- backend/services/orchestrator/intent_engine.py backend/services/workflow/routine_runner.py backend/tests/test_routine_runner.py backend/tests/test_workflow_offer_service.py documentation/tasks/TASK-SPEC31_semantisches_parameterisiertes_routine_reuse_mehrschrittige_routinen.md documentation/tasks/TASK-SPEC31.2_task_breakdown.md documentation/tasks/TASK-SPEC31.2_preimplementation_check.md documentation/ai/CURRENT_STATE.md documentation/codex/SKILL_USAGE_LOG.md
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
- Do not reopen or re-implement `TASK-SPEC31.1` positive pilot behavior except where direct negative regression protection for the same path requires a bounded guard.
- No new routine families, no routine-management UI, no embedding/vector search, and no unrelated workflow architecture changes.
- Probe the shared execution gate before code changes so the current Cursor-first write-capable lane visibility is captured for this bounded hardening slice, but Codex remains owner of final review, validation, and state updates.
Automated Evidence Gate:
- python -m pytest backend/tests/test_routine_runner.py -v
- python -m pytest backend/tests/test_workflow_offer_service.py -v
- python -m py_compile backend/services/orchestrator/intent_engine.py backend/services/workflow/routine_runner.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/31_semantisches_parameterisiertes_routine_reuse_mehrschrittige_routinen.md
- documentation/tasks/TASK-SPEC31_semantisches_parameterisiertes_routine_reuse_mehrschrittige_routinen.md
- documentation/tasks/TASK-SPEC31.2_task_breakdown.md
- documentation/tasks/TASK-SPEC31.2_preimplementation_check.md
- documentation/Planned Features/backlog_BACKLOG-123_semantisches_parameterisiertes_routine_reuse_mehrschrittige_routinen.md
- backend/services/orchestrator/intent_engine.py
- backend/services/workflow/routine_runner.py
- backend/tests/test_routine_runner.py
- backend/tests/test_workflow_offer_service.py
Drop Context:
- sealed `TASK-SPEC31.1` positive-pilot closeout except as regression reference
- old Spec-29.2 debug chain except where it already informed the approved Spec 31 boundaries
- unrelated backlog items, model-matrix audit work, and unrelated dirty worktree changes
- broader future routine-family expansion ideas outside the locked hardening boundary
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: high
Reason: TASK-SPEC31.2 is now a bounded but user-visible backend hardening slice on the live saved-routine execution path with explicit files, negative acceptance criteria, and focused regression evidence.
User Action: Continue with janus-executioner for `TASK-SPEC31.2`, and probe the shared execution gate for a sensible Cursor-first write-capable lane before local implementation.
