PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-INTENT-M2.1
Target Subtask: N/A
Task: documentation/tasks/TASK-INTENT-M2_confidence_routing_and_regex_freeze.md
Spec: documentation/Cursor specs/INTENT_ENGINE_HERMES_INSPIRED_UPGRADE_PLAN.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: soften the ambiguity hard-block through confidence-based routing on top of the sealed M1 auxiliary-classifier baseline, while preserving all current safety, medical, consent, and personal-recall-web guards.
- Artifact identity is consistent across Intent Spec section 6, Roadmap section 4 M2, the compiled task artifact `documentation/tasks/TASK-INTENT-M2_confidence_routing_and_regex_freeze.md`, the released handoff `documentation/tasks/TASK-INTENT-M2.1_task_breakdown.md`, and the checked-in benchmark baseline `documentation/test-runs/INTENT_BENCHMARK_BASELINE.md`.
- The affected file cluster is concrete and intentionally bounded to the intent-engine and execution-dispatcher routing seam, a new focused confidence-routing test surface, the existing calendar and benchmark regression surfaces, and the evidence artifact needed for the M2 proof run.
- Risk is MEDIUM because this slice changes live intent-routing behavior and ambiguity handling on the product path, but it stays bounded behind explicit acceptance gates and must not widen into Regex-Freeze, Entity-First routing, Memory follow-up work, Transport, OAuth, OpenRouter, or delegation hardening.
Affected Files:
- backend/services/orchestrator/execution_dispatcher.py
- backend/services/orchestrator/intent_engine.py
- backend/tests/test_intent_confidence_routing.py
- backend/tests/test_calendar_routing_fix.py
- backend/tests/test_intent_benchmark.py
- documentation/test-runs/TASK-INTENT-M2.1_confidence_routing_2026-07-08.md
Evidence Focus:
- python -m pytest backend/tests/test_intent_confidence_routing.py -q
- python -m pytest backend/tests/test_calendar_routing_fix.py backend/tests/test_intent_benchmark.py -q
- python -m py_compile backend/services/orchestrator/execution_dispatcher.py backend/services/orchestrator/intent_engine.py
- python -m backend.scripts.run_intent_benchmark --mode m2-proof --output documentation/test-runs/TASK-INTENT-M2.1_confidence_routing_2026-07-08.md
- git diff --check -- backend/services/orchestrator/execution_dispatcher.py backend/services/orchestrator/intent_engine.py backend/tests/test_intent_confidence_routing.py backend/tests/test_calendar_routing_fix.py backend/tests/test_intent_benchmark.py documentation/tasks/TASK-INTENT-M2_confidence_routing_and_regex_freeze.md documentation/tasks/TASK-INTENT-M2.1_task_breakdown.md documentation/tasks/TASK-INTENT-M2.1_preimplementation_check.md documentation/ai/CURRENT_STATE.md documentation/codex/SKILL_USAGE_LOG.md
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest backend/tests/test_intent_confidence_routing.py -q
- python -m pytest backend/tests/test_calendar_routing_fix.py backend/tests/test_intent_benchmark.py -q
- python -m py_compile backend/services/orchestrator/execution_dispatcher.py backend/services/orchestrator/intent_engine.py
- python -m backend.scripts.run_intent_benchmark --mode m2-proof --output documentation/test-runs/TASK-INTENT-M2.1_confidence_routing_2026-07-08.md
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/Cursor specs/INTENT_ENGINE_HERMES_INSPIRED_UPGRADE_PLAN.md
- documentation/Cursor specs/ROADMAP_EPIC_ORDER.md
- documentation/tasks/TASK-INTENT-M2_confidence_routing_and_regex_freeze.md
- documentation/tasks/TASK-INTENT-M2.1_task_breakdown.md
- documentation/test-runs/INTENT_BENCHMARK_BASELINE.md
- backend/services/orchestrator/execution_dispatcher.py
- backend/services/orchestrator/intent_engine.py
Drop Context:
- sealed M1 implementation details beyond the already-delivered auxiliary-classifier surface
- TASK-INTENT-M2.2 regex-freeze follow-up
- Memory A/B, Session-Search, Transport, OAuth, OpenRouter, and delegation hardening work
- unrelated dirty worktree changes
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The M2 I2 slice is now precheck-ready as one bounded confidence-routing block with explicit benchmark, regression, and safety evidence gates.
User Action: Say `ok` to start implementation of `TASK-INTENT-M2.1` with the bound scope and evidence gate above.
