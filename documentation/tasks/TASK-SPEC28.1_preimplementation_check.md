PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC28.1
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC28_bounded_or_lane_fuer_live_test_execution.md
Spec: documentation/SPEC/28_bounded_or_lane_fuer_live_test_execution.md
Backlog Item: BACKLOG-118
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it adds only the fail-closed eligibility and visible operator gate for local `LIVE_TEST_EXECUTION` retests inside the existing `janus-test-pipeline` path.
- Artifact identity is consistent across `BACKLOG-118`, approved Spec 28, generated `TASK-SPEC28`, and the released target-task handoff `TASK-SPEC28.1`.
- The affected file cluster is concrete and bounded to the repo-versioned `janus-test-pipeline` skill text, the shared bounded eligibility helper, the existing live-test gate runner path, and the focused regression tests for eligibility and gate visibility.
- Risk is HIGH because this slice opens a new operator-visible OR entry seam inside a real live-retest path. Skill 4 must preserve the hard boundary: no local auth/header contract work, no worker package details, no delegated evidence-write semantics, no final Codex-owned accept/reject wiring, and no broad live-test delegation beyond the eligible local lane.
- This slice is visibility-only for the first live-retest OR rollout. It may decide when the normal `1 = Codex` / `2 = OR` choice appears for bounded local retests, but it must not implement the later bounded worker/auth/evidence contract from `TASK-SPEC28.2` or the later accept/reject and registry-regression fence from `TASK-SPEC28.3`.
Affected Files:
- documentation/codex/skills/janus-test-pipeline/SKILL.md
- documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py
- documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py
- documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py
- documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py
Evidence Focus:
- python -m pytest documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py -q
- python -m pytest documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py -q -k "live or gate or eligibility"
- python -m py_compile documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py
- git diff --check -- documentation/codex/skills/janus-test-pipeline/SKILL.md documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py documentation/tasks/TASK-SPEC28.1_preimplementation_check.md
- one focused negative-path check that non-eligible, too-broad, or non-local live-retest flows remain Codex-only without a visible OR gate
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py -q
- python -m pytest documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py -q -k "live or gate or eligibility"
- python -m py_compile documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/28_bounded_or_lane_fuer_live_test_execution.md
- documentation/tasks/TASK-SPEC28_bounded_or_lane_fuer_live_test_execution.md
- documentation/tasks/TASK-SPEC28.1_task_breakdown.md
- documentation/codex/skills/janus-test-pipeline/SKILL.md
- documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py
- documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py
- documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py
- documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py
Drop Context:
- later TASK-SPEC28.2 worker/auth/evidence-contract work
- later TASK-SPEC28.3 accept-reject and registry-regression work
- unrelated historical OR pilot, release, audit, or product-runtime bug history
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The first live-retest OR lane slice is implementation-ready and tightly bounded to fail-closed eligibility plus visible gate behavior only.
User Action: Say `ok` to start implementation of `TASK-SPEC28.1` with the bound scope and evidence gate above.
