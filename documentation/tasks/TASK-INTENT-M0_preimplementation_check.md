PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-INTENT-M0.1
Target Subtask: N/A
Task: documentation/tasks/TASK-INTENT-M0_benchmark_baseline.md
Spec: documentation/Cursor specs/INTENT_ENGINE_HERMES_INSPIRED_UPGRADE_PLAN.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: build exactly the M0 benchmark corpus, runner, pytest suite, and baseline report for the current intent engine without changing routing logic.
- Artifact identity is consistent across Roadmap M0 (`documentation/Cursor specs/ROADMAP_EPIC_ORDER.md` sections 0, 4, 9, and 16), Intent Spec section 4, and the dedicated task artifact `documentation/tasks/TASK-INTENT-M0_benchmark_baseline.md`.
- The affected file cluster is concrete and bounded to a new JSONL fixture, a dedicated benchmark pytest module, a local benchmark runner script, and the baseline markdown report under `documentation/test-runs/`.
- Risk is MEDIUM because this slice defines the measurement contract for all later intent work. Skill 4 must preserve the hard boundary: no intent-engine logic edits, no transport or OAuth work, no OpenRouter product path, no delegation/gate/runner work, and no scope expansion into M1.
- The minimum corpus and reporting rules are already fixed by Intent Spec section 4.5 and the roadmap exit criteria: at least 80 cases, CI-runnable pytest, and separated Contact / Pet / Recall / Calendar reporting.
Affected Files:
- backend/tests/fixtures/intent_benchmark_cases.jsonl
- backend/tests/test_intent_benchmark.py
- backend/scripts/run_intent_benchmark.py
- documentation/test-runs/INTENT_BENCHMARK_BASELINE.md
Evidence Focus:
- python -m pytest backend/tests/test_intent_benchmark.py -q
- python -m backend.scripts.run_intent_benchmark --write-baseline
- python -m py_compile backend/scripts/run_intent_benchmark.py backend/tests/test_intent_benchmark.py
- git diff --check -- backend/tests/fixtures/intent_benchmark_cases.jsonl backend/tests/test_intent_benchmark.py backend/scripts/run_intent_benchmark.py documentation/test-runs/INTENT_BENCHMARK_BASELINE.md documentation/tasks/TASK-INTENT-M0_benchmark_baseline.md documentation/tasks/TASK-INTENT-M0_preimplementation_check.md
- one focused corpus integrity check for cluster counts and one focused negative-path check that no case requires a live provider call
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest backend/tests/test_intent_benchmark.py -q
- python -m backend.scripts.run_intent_benchmark --write-baseline
- python -m py_compile backend/scripts/run_intent_benchmark.py backend/tests/test_intent_benchmark.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/Cursor specs/ROADMAP_EPIC_ORDER.md
- documentation/Cursor specs/INTENT_ENGINE_HERMES_INSPIRED_UPGRADE_PLAN.md
- documentation/tasks/TASK-INTENT-M0_benchmark_baseline.md
- backend/services/orchestrator/intent_engine.py
- backend/tests/test_calendar_routing_fix.py
- backend/tests/integration/test_pet_recall_chat_path.py
Drop Context:
- delegation, gate, cursor-runner, transport, OAuth, and OpenRouter roadmap work
- unrelated dirty-tree product changes outside the bound benchmark slice
- any M1+ intent implementation ideas until the M0 baseline exists
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The M0 benchmark slice is implementation-ready and tightly bounded to measurement artifacts only.
User Action: Say `ok` to start implementation of `TASK-INTENT-M0.1` with the bound scope and evidence gate above.
