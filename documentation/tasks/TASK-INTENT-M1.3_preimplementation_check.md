PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-INTENT-M1.3
Target Subtask: N/A
Task: documentation/tasks/TASK-INTENT-M1_auxiliary_action_subject_classifier.md
Spec: documentation/Cursor specs/INTENT_ENGINE_HERMES_INSPIRED_UPGRADE_PLAN.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: rerun the intent benchmark against the checked-in M0 baseline, prove the auxiliary-classifier latency and flag-off guardrails, and prepare the evidence package that decides whether M1 I1 can claim measured closure.
- Artifact identity is consistent across Spec sections 5.6, 5.8, and 5.9, the compiled task artifact `documentation/tasks/TASK-INTENT-M1_auxiliary_action_subject_classifier.md`, the released handoff `documentation/tasks/TASK-INTENT-M1.3_task_breakdown.md`, and the checked-in baseline `documentation/test-runs/INTENT_BENCHMARK_BASELINE.md`.
- The affected file cluster is concrete and intentionally bounded to the benchmark runner, benchmark pytest surface, already-existing auxiliary and calendar regression modules, and the benchmark/test-run evidence artifacts needed for final audit.
- Risk is MEDIUM because this slice decides whether the new routing path actually improved Contact/Pet/Recall enough to justify staged enablement. Skill 4 must not reopen M1.2 integration logic, must not widen into M2 confidence-routing, and must not mix in Memory A/B, transport, OAuth, or delegation work.
Affected Files:
- backend/scripts/run_intent_benchmark.py
- backend/tests/test_intent_benchmark.py
- backend/tests/test_intent_aux_classifier.py
- backend/tests/test_calendar_routing_fix.py
- documentation/test-runs/INTENT_BENCHMARK_BASELINE.md
- documentation/test-runs/
Evidence Focus:
- python -m pytest backend/tests/test_intent_benchmark.py backend/tests/test_intent_aux_classifier.py backend/tests/test_calendar_routing_fix.py -q
- python -m backend.scripts.run_intent_benchmark --write-baseline
- targeted latency/telemetry check for the auxiliary classifier execution path with explicit P95 evidence
- git diff --check -- backend/scripts/run_intent_benchmark.py backend/tests/test_intent_benchmark.py backend/tests/test_intent_aux_classifier.py backend/tests/test_calendar_routing_fix.py documentation/test-runs/INTENT_BENCHMARK_BASELINE.md documentation/tasks/TASK-INTENT-M1.3_preimplementation_check.md documentation/tasks/TASK-INTENT-M1.3_task_breakdown.md documentation/tasks/TASK-INTENT-M1_auxiliary_action_subject_classifier.md
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest backend/tests/test_intent_benchmark.py backend/tests/test_intent_aux_classifier.py backend/tests/test_calendar_routing_fix.py -q
- python -m backend.scripts.run_intent_benchmark --write-baseline
- targeted latency/telemetry check for the auxiliary classifier execution path
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/Cursor specs/INTENT_ENGINE_HERMES_INSPIRED_UPGRADE_PLAN.md
- documentation/tasks/TASK-INTENT-M1_auxiliary_action_subject_classifier.md
- documentation/tasks/TASK-INTENT-M1.3_task_breakdown.md
- documentation/test-runs/INTENT_BENCHMARK_BASELINE.md
- backend/scripts/run_intent_benchmark.py
- backend/tests/test_intent_benchmark.py
Drop Context:
- sealed TASK-INTENT-M1.1 and TASK-INTENT-M1.2 implementation details beyond the already-delivered routing surface
- M2 confidence-routing work
- Memory A/B, transport, OAuth, and delegation hardening work
- old startup-debug and contaminated-live-DB evidence except where reused as background only
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The M1.3 slice is now precheck-ready as a pure evidence gate for benchmark uplift, latency guardrails, and flag-off parity against the checked-in M0 baseline.
User Action: Say `ok` to start implementation of `TASK-INTENT-M1.3` with the bound scope and evidence gate above.
