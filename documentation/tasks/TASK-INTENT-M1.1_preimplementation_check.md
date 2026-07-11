PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-INTENT-M1.1
Target Subtask: N/A
Task: documentation/tasks/TASK-INTENT-M1_auxiliary_action_subject_classifier.md
Spec: documentation/Cursor specs/INTENT_ENGINE_HERMES_INSPIRED_UPGRADE_PLAN.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: define the auxiliary classifier contract, its provider/config wrapper, and focused unit coverage without integrating it into `detect_all_intents()` yet.
- Artifact identity is consistent across the source spec section 5, the compiled task artifact `documentation/tasks/TASK-INTENT-M1_auxiliary_action_subject_classifier.md`, and the released handoff `documentation/tasks/TASK-INTENT-M1.1_task_breakdown.md`.
- The affected file cluster is concrete and intentionally allows new-file creation exactly where the spec names it: classifier service, config surface, schema, and focused tests.
- Risk is MEDIUM because this slice introduces a new intent classification seam, but the boundary is tight: no production merge into the live intent engine, no benchmark-uplift claims, no Memory A/B work, and no transport/provider-product refactor.
Affected Files:
- backend/services/orchestrator/intent_aux_classifier.py
- backend/services/orchestrator/intent_config.py
- backend/data/schemas_intent.py
- backend/tests/test_intent_aux_classifier.py
- backend/tests/test_intent_action_subject_mapping.py
Evidence Focus:
- python -m pytest backend/tests/test_intent_aux_classifier.py -q
- python -m pytest backend/tests/test_intent_action_subject_mapping.py -q
- python -m py_compile backend/services/orchestrator/intent_aux_classifier.py backend/services/orchestrator/intent_config.py backend/data/schemas_intent.py
- git diff --check -- backend/services/orchestrator/intent_aux_classifier.py backend/services/orchestrator/intent_config.py backend/data/schemas_intent.py backend/tests/test_intent_aux_classifier.py backend/tests/test_intent_action_subject_mapping.py documentation/tasks/TASK-INTENT-M1.1_preimplementation_check.md documentation/tasks/TASK-INTENT-M1.1_task_breakdown.md documentation/tasks/TASK-INTENT-M1_auxiliary_action_subject_classifier.md
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest backend/tests/test_intent_aux_classifier.py -q
- python -m pytest backend/tests/test_intent_action_subject_mapping.py -q
- python -m py_compile backend/services/orchestrator/intent_aux_classifier.py backend/services/orchestrator/intent_config.py backend/data/schemas_intent.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/Cursor specs/INTENT_ENGINE_HERMES_INSPIRED_UPGRADE_PLAN.md
- documentation/tasks/TASK-INTENT-M1_auxiliary_action_subject_classifier.md
- documentation/tasks/TASK-INTENT-M1.1_task_breakdown.md
- documentation/test-runs/INTENT_BENCHMARK_BASELINE.md
- backend/services/orchestrator/intent_engine.py
Drop Context:
- later TASK-INTENT-M1.2 integration work
- later TASK-INTENT-M1.3 benchmark uplift and staged enablement work
- Memory A/B roadmap work
- delegation, transport, OAuth, and OpenRouter roadmap work
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
User Action: Say `ok` to start implementation of `TASK-INTENT-M1.1` with the bound scope and evidence gate above.
