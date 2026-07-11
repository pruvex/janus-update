PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC23.2
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC23_erster_produktiver_or_consumer_fuer_janus_debug.md
Spec: documentation/SPEC/23_erster_produktiver_or_consumer_fuer_janus_debug.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_PRECHECK
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it adds the productive `janus-debug` runtime and direct local fallback seam that `TASK-SPEC23.1` explicitly left open, while reusing the already accepted productive gate unchanged.
- Artifact identity is consistent across Spec 23, the generated `TASK-SPEC23` artifact, the released `TASK-SPEC23.2` handoff, and the accepted `TASK-SPEC23.1` audit boundary.
- The affected file cluster is concrete and bounded to the repo-versioned `janus-debug` skill source, the existing debug consumer runner, the shared bounded dispatcher and outcome helper, and the focused consumer-integration regression module.
- Risk is MEDIUM because this slice turns an accepted operator-visible gate into a real delegated runtime path with Codex-owned acceptance and direct local fallback. Skill 4 must preserve the sealed `TASK-SPEC23.1` gate-only boundary, must not reopen eligibility design, and must not broaden OR authority outside the bounded `janus-debug` path.
- This slice owns runtime and fallback semantics only. It may execute one bounded OR debug-analysis or patch-candidate path, evaluate the returned result locally in Codex, and produce a clear accepted or fallback completion state, but it must not imply production routing, global OR approval, or activation in other debug modes or other Janus skills.
Affected Files:
- documentation/codex/skills/janus-debug/SKILL.md
- documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py
- documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- documentation/codex/model-routing/scripts/bounded_or_worker_outcome.py
- documentation/codex/model-routing/tests/test_assistive_or_review_consumer_integration.py
Evidence Focus:
- python -m unittest documentation.codex.model-routing.tests.test_assistive_or_review_consumer_integration
- python -m unittest documentation.codex.model-routing.tests.test_assistive_or_review_capture_dispatcher
- python -m py_compile documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/model-routing/scripts/bounded_or_worker_outcome.py documentation/codex/model-routing/tests/test_assistive_or_review_consumer_integration.py
- git diff --check -- documentation/codex/skills/janus-debug/SKILL.md documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/model-routing/scripts/bounded_or_worker_outcome.py documentation/codex/model-routing/tests/test_assistive_or_review_consumer_integration.py documentation/tasks/TASK-SPEC23.2_preimplementation_check.md
- one focused negative-path check that weak, incomplete, or cap-violating OR results fall back directly to a visible local Codex completion state
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m unittest documentation.codex.model-routing.tests.test_assistive_or_review_consumer_integration
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/23_erster_produktiver_or_consumer_fuer_janus_debug.md
- documentation/tasks/TASK-SPEC23_erster_produktiver_or_consumer_fuer_janus_debug.md
- documentation/tasks/TASK-SPEC23.2_task_breakdown.md
- documentation/tasks/TASK-SPEC23.1_final_audit.md
- documentation/codex/skills/janus-debug/SKILL.md
- documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py
- documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- documentation/codex/model-routing/scripts/bounded_or_worker_outcome.py
- documentation/codex/model-routing/tests/test_assistive_or_review_consumer_integration.py
Drop Context:
- completed `TASK-SPEC23.1` implementation chatter beyond the accepted gate-only boundary
- unrelated direct-OR, sidecar, quickchange, release, and Janus product workflow history
- broader OR experimentation outside the bounded productive `janus-debug` path
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: high
Reason: The productive `janus-debug` runtime and fallback slice is implementation-ready, tightly bounded to one existing consumer path, and explicitly fenced away from renewed gate design or broader OR activation.
User Action: Say `ok` to start implementation of `TASK-SPEC23.2` with the bound scope and evidence gate above.
