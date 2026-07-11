PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC19.3
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC19_bounded_or_worker_mode_for_janus_skills.md
Spec: documentation/SPEC/19_bounded_or_worker_mode_for_janus_skills.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it implements only the post-run Codex-owned accept, reject, and fallback normalization for already-routed OR paths and does not reopen eligibility policy, gate-display policy, or any new production-routing behavior.
- Artifact identity is consistent across reviewed Spec 19, the generated TASK-SPEC19 artifact, the released task-breakdown handoff `documentation/tasks/TASK-SPEC19.3_task_breakdown.md`, and the target task `TASK-SPEC19.3`.
- The affected file cluster is concrete and bounded to post-run normalization surfaces: `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`, `documentation/codex/model-routing/scripts/doc_skill_mini_fixed_or_live_runner.py`, focused model-routing tests under `documentation/codex/model-routing/tests/`, and existing bounded OR telemetry JSONL shapes only as evidence/reference surfaces rather than a new live-eval track.
- Implementation risk is MEDIUM because the slice is narrow but sits on the final Codex-owned outcome boundary where a wrong default could silently accept incomplete OR results; a git checkpoint is recommended through `janus-git-governance` before Skill 4 because the worktree still contains unrelated changes outside this bounded slice.
Affected Files:
- documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- documentation/codex/model-routing/scripts/doc_skill_mini_fixed_or_live_runner.py
- documentation/codex/model-routing/tests/
- documentation/codex/model-routing/or_healthcheck_telemetry_*.jsonl
Evidence Focus:
- python -m py_compile documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/model-routing/scripts/doc_skill_mini_fixed_or_live_runner.py
- pytest documentation/codex/model-routing/tests/ -q -k "accept or reject or fallback or codex_owned"
- fixture-based local checks for accepted OR result, missing validation reject, incomplete artifact reject, and Codex-only or assist-only regression outcome labeling
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m py_compile documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/model-routing/scripts/doc_skill_mini_fixed_or_live_runner.py
- pytest documentation/codex/model-routing/tests/ -q -k "accept or reject or fallback or codex_owned"
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/19_bounded_or_worker_mode_for_janus_skills.md
- documentation/tasks/TASK-SPEC19_bounded_or_worker_mode_for_janus_skills.md
- documentation/tasks/TASK-SPEC19.3_task_breakdown.md
- documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- documentation/codex/model-routing/scripts/doc_skill_mini_fixed_or_live_runner.py
Drop Context:
- earlier TASK-SPEC19.1 eligibility implementation details that do not change post-run acceptance rules
- earlier TASK-SPEC19.2 gate-prompt wording details that do not change post-run outcome normalization
- older sidecar and OR pilot history that does not alter this bounded Codex-owned acceptance slice
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The task is implementation-ready, repo-local, and bounded to Codex-owned post-run acceptance and fallback normalization after the already-completed eligibility and gate slices.
User Action: Say `ok` to start implementation of `TASK-SPEC19.3` with the bound scope and evidence gate above.
