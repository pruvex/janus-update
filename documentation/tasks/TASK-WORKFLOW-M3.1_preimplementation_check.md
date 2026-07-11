PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-WORKFLOW-M3.1
Target Subtask: N/A
Task: documentation/tasks/TASK-WORKFLOW-M3_learned_workflows_phase_1_2.md
Spec: documentation/Cursor specs/LEARNED_WORKFLOWS_SPEC.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: implement Workflow Phase 1 Store and Phase 2 Detector as one guarded foundation slice with persisted routine metadata, registry validation, step-fingerprint dedup, and deterministic workflow trace extraction.
- Artifact identity is consistent across the Workflow spec sections 5 and 7, the roadmap M3 entry, the compiled task artifact `documentation/tasks/TASK-WORKFLOW-M3_learned_workflows_phase_1_2.md`, and the released handoff `documentation/tasks/TASK-WORKFLOW-M3.1_task_breakdown.md`.
- The affected file cluster is concrete and intentionally bounded to workflow persistence, schema, trace extraction, and focused workflow regression tests.
- Risk is MEDIUM because this slice introduces new persisted workflow state and new interpretation of tool traces, but it remains bounded by `ROUTINES_ENABLED=false`, no proactive offer text, and no routine execution path.
Affected Files:
- backend/data/models.py
- backend/data/database.py
- backend/services/workflow/routine_store.py
- backend/services/workflow/routine_schema.py
- backend/services/workflow/workflow_detector.py
- backend/services/workflow/step_trace_extractor.py
- backend/services/capability_registry.py
- backend/tests/test_routine_store.py
- backend/tests/test_workflow_detector.py
Evidence Focus:
- python -m pytest backend/tests/test_routine_store.py -v
- python -m pytest backend/tests/test_workflow_detector.py -v
- python -m py_compile backend/services/workflow/routine_store.py backend/services/workflow/routine_schema.py backend/services/workflow/workflow_detector.py backend/services/workflow/step_trace_extractor.py
- git diff --check -- backend/data/models.py backend/data/database.py backend/services/workflow/routine_store.py backend/services/workflow/routine_schema.py backend/services/workflow/workflow_detector.py backend/services/workflow/step_trace_extractor.py backend/services/capability_registry.py backend/tests/test_routine_store.py backend/tests/test_workflow_detector.py documentation/tasks/TASK-WORKFLOW-M3_learned_workflows_phase_1_2.md documentation/tasks/TASK-WORKFLOW-M3.1_task_breakdown.md documentation/tasks/TASK-WORKFLOW-M3.1_preimplementation_check.md documentation/ai/CURRENT_STATE.md documentation/codex/SKILL_USAGE_LOG.md
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest backend/tests/test_routine_store.py -v
- python -m pytest backend/tests/test_workflow_detector.py -v
- python -m py_compile backend/services/workflow/routine_store.py backend/services/workflow/routine_schema.py backend/services/workflow/workflow_detector.py backend/services/workflow/step_trace_extractor.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/Cursor specs/LEARNED_WORKFLOWS_SPEC.md
- documentation/Cursor specs/ROADMAP_EPIC_ORDER.md
- documentation/tasks/TASK-WORKFLOW-M3_learned_workflows_phase_1_2.md
- documentation/tasks/TASK-WORKFLOW-M3.1_task_breakdown.md
- backend/data/models.py
- backend/data/database.py
Drop Context:
- sealed Intent and Memory slices except their roadmap completion state
- Workflow Phase 3/4/5 details beyond explicit out-of-scope boundaries
- Transport, OAuth, OpenRouter, and delegation hardening work
- unrelated dirty worktree changes
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The M3 Phase 1+2 slice is now precheck-ready as one bounded workflow foundation block with explicit store, detector, and validation gates.
User Action: Say `ok` to start implementation of `TASK-WORKFLOW-M3.1` with the bound scope and evidence gate above.
