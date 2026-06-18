PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC19.4
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC19_bounded_or_worker_mode_for_janus_skills.md
Spec: documentation/SPEC/Spec Done/19_bounded_or_worker_mode_for_janus_skills.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it makes `janus-quickchange` the first real everyday consumer of the already completed bounded OR worker foundation and does not reopen shared eligibility policy, broad documentation-skill routing, production routing, or broad execution delegation.
- Artifact identity is consistent across the completed Spec 19 foundation, the generated TASK-SPEC19 artifact, the released handoff `documentation/tasks/TASK-SPEC19.4_task_breakdown.md`, and the target task `TASK-SPEC19.4`.
- The affected file cluster is concrete and bounded to quickchange gate semantics and bounded acceptance wording: `documentation/codex/skills/janus-quickchange/SKILL.md`, `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`, `documentation/codex/model-routing/scripts/quickchange_sidecar_write_pilot_runner.py`, `documentation/codex/model-routing/scripts/codex_quickchange_write_apply_runner.py`, and the focused quickchange regression tests under `documentation/codex/model-routing/tests/`.
- Implementation risk is MEDIUM because the slice is narrow but operator-facing: a wrong wording or route default could blur the intended `Codex` versus `OpenRouter` everyday choice or weaken bounded acceptance boundaries. A git checkpoint is recommended through `janus-git-governance` before Skill 4 because the wider worktree still contains unrelated dirty scope.
Affected Files:
- documentation/codex/skills/janus-quickchange/SKILL.md
- documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- documentation/codex/model-routing/scripts/quickchange_sidecar_write_pilot_runner.py
- documentation/codex/model-routing/scripts/codex_quickchange_write_apply_runner.py
- documentation/codex/model-routing/tests/test_quickchange_live_operator_path.py
- documentation/codex/model-routing/tests/test_quickchange_sidecar_write_pilot_runner.py
Evidence Focus:
- python -m py_compile documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/model-routing/scripts/quickchange_sidecar_write_pilot_runner.py documentation/codex/model-routing/scripts/codex_quickchange_write_apply_runner.py
- python -m pytest documentation/codex/model-routing/tests/test_quickchange_live_operator_path.py -q
- python -m pytest documentation/codex/model-routing/tests/test_quickchange_sidecar_write_pilot_runner.py -q
- one focused local regression for the quickchange operator prompt semantics if the existing tests do not fully cover the visible `1 = Codex` / `2 = OpenRouter` everyday wording boundary
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m py_compile documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/model-routing/scripts/quickchange_sidecar_write_pilot_runner.py documentation/codex/model-routing/scripts/codex_quickchange_write_apply_runner.py
- python -m pytest documentation/codex/model-routing/tests/test_quickchange_live_operator_path.py -q
- python -m pytest documentation/codex/model-routing/tests/test_quickchange_sidecar_write_pilot_runner.py -q
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/Spec Done/19_bounded_or_worker_mode_for_janus_skills.md
- documentation/tasks/TASK-SPEC19_bounded_or_worker_mode_for_janus_skills.md
- documentation/tasks/TASK-SPEC19.4_task_breakdown.md
- documentation/codex/skills/janus-quickchange/SKILL.md
- documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- documentation/codex/model-routing/scripts/quickchange_sidecar_write_pilot_runner.py
- documentation/codex/model-routing/scripts/codex_quickchange_write_apply_runner.py
Drop Context:
- older documentation-skill fixed-OR rollout details that do not affect quickchange operator semantics
- broader sidecar or live-eval history outside the first quickchange consumer boundary
- unrelated dirty worktree scope in backend, frontend, and non-quickchange governance files
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The task is implementation-ready, repo-local, and tightly bounded to the first operator-facing `janus-quickchange` consumer of the completed OR worker foundation.
User Action: Say `ok` to start implementation of `TASK-SPEC19.4` with the bound scope and evidence gate above.
