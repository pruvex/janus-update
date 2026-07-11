PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC19.2
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC19_bounded_or_worker_mode_for_janus_skills.md
Spec: documentation/SPEC/19_bounded_or_worker_mode_for_janus_skills.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it implements only the unified pre-run operator gate for already allowed bounded skill classes, normalizes the visible `1 = Codex` and `2 = OpenRouter` choice style, and enforces model-plus-cost-plus-confidence as mandatory gate-display fields without pulling post-run accept-reject ownership or fallback-after-run normalization into this slice.
- Artifact identity is consistent across reviewed Spec 19, the generated TASK-SPEC19 artifact, the released task-breakdown handoff `documentation/tasks/TASK-SPEC19.2_task_breakdown.md`, and the target task `TASK-SPEC19.2`.
- The affected file cluster is concrete and bounded to the gate-rendering surface: `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`, `documentation/codex/model-routing/scripts/doc_skill_mini_fixed_or_live_runner.py`, `documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py`, `documentation/codex/model-routing/scripts/codex_test_result_triage_review_runner.py`, and focused model-routing tests under `documentation/codex/model-routing/tests/`.
- Implementation risk is MEDIUM because the slice is bounded but sits on an operator-facing routing boundary where missing prompt data must suppress the OR option deterministically; a git checkpoint is recommended through `janus-git-governance` before Skill 4 because the worktree still contains unrelated changes outside this bounded slice.
Affected Files:
- documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- documentation/codex/model-routing/scripts/doc_skill_mini_fixed_or_live_runner.py
- documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py
- documentation/codex/model-routing/scripts/codex_test_result_triage_review_runner.py
- documentation/codex/model-routing/tests/
Evidence Focus:
- python -m py_compile documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/model-routing/scripts/doc_skill_mini_fixed_or_live_runner.py documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py documentation/codex/model-routing/scripts/codex_test_result_triage_review_runner.py
- pytest documentation/codex/model-routing/tests/ -q -k "gate or confidence or cost or codex_only"
- fixture-based local checks for visible gate rendering, missing cost suppression, missing confidence suppression, and explicit Codex-only fallback before wrapper invocation
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m py_compile documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/model-routing/scripts/doc_skill_mini_fixed_or_live_runner.py documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py documentation/codex/model-routing/scripts/codex_test_result_triage_review_runner.py
- pytest documentation/codex/model-routing/tests/ -q -k "gate or confidence or cost or codex_only"
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/19_bounded_or_worker_mode_for_janus_skills.md
- documentation/tasks/TASK-SPEC19_bounded_or_worker_mode_for_janus_skills.md
- documentation/tasks/TASK-SPEC19.2_task_breakdown.md
- documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- documentation/codex/model-routing/scripts/doc_skill_mini_fixed_or_live_runner.py
- documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py
- documentation/codex/model-routing/scripts/codex_test_result_triage_review_runner.py
Drop Context:
- later TASK-SPEC19.3 post-run accept-reject and fallback normalization details
- earlier TASK-SPEC19.1 eligibility implementation details that do not change the gate-display requirements
- older sidecar and OR pilot history that does not alter this bounded pre-run gate slice
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The task is implementation-ready, repo-local, and bounded to the unified operator-gate prompt surface before the later Codex-owned post-run acceptance slice.
User Action: Say `ok` to start implementation of `TASK-SPEC19.2` with the bound scope and evidence gate above.
