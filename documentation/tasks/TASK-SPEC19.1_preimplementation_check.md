PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC19.1
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC19_bounded_or_worker_mode_for_janus_skills.md
Spec: documentation/SPEC/19_bounded_or_worker_mode_for_janus_skills.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it implements only the shared OR eligibility gate for explicitly allowed bounded skill classes, evidence-backed OR eligibility, and deterministic no-gate fallback for missing or blocked skills, without pulling the later unified gate prompt, cost-confidence rendering, or post-run accept-reject normalization into this slice.
- Artifact identity is consistent across reviewed Spec 19, the generated TASK-SPEC19 artifact, the released task-breakdown handoff `documentation/tasks/TASK-SPEC19.1_task_breakdown.md`, and the target task `TASK-SPEC19.1`.
- The affected file cluster is concrete and bounded to the shared eligibility surface: `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`, `documentation/codex/model-routing/scripts/doc_skill_mini_fixed_or_live_runner.py`, one narrow config family under `documentation/codex/model-routing/config/`, and one focused model-routing test module or fixture family under `documentation/codex/model-routing/tests/`.
- Implementation risk is MEDIUM because the slice is mechanically bounded but sits on a sensitive routing and delegation boundary where a wrong eligibility default could expose OR gates too broadly or suppress them incorrectly; a git checkpoint is recommended through `janus-git-governance` before Skill 4 because the worktree still contains unrelated changes outside this bounded slice.
Affected Files:
- documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- documentation/codex/model-routing/scripts/doc_skill_mini_fixed_or_live_runner.py
- documentation/codex/model-routing/config/
- documentation/codex/model-routing/tests/
Evidence Focus:
- python -m py_compile documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/model-routing/scripts/doc_skill_mini_fixed_or_live_runner.py
- pytest documentation/codex/model-routing/tests/ -q -k "eligibility or fixed_or"
- fixture-based local checks for `OR_ALLOWED`, `OR_NOT_ELIGIBLE`, and `OR_EVIDENCE_MISSING`
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m py_compile documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/model-routing/scripts/doc_skill_mini_fixed_or_live_runner.py
- pytest documentation/codex/model-routing/tests/ -q -k "eligibility or fixed_or"
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/19_bounded_or_worker_mode_for_janus_skills.md
- documentation/tasks/TASK-SPEC19_bounded_or_worker_mode_for_janus_skills.md
- documentation/tasks/TASK-SPEC19.1_task_breakdown.md
- documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- documentation/codex/model-routing/scripts/doc_skill_mini_fixed_or_live_runner.py
Drop Context:
- later TASK-SPEC19.2 unified gate prompt and cost-confidence display details
- later TASK-SPEC19.3 post-run accept-reject and fallback normalization details
- older sidecar and OR pilot history that does not change the first shared eligibility requirements
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The task is implementation-ready, repo-local, and bounded to the first shared OR eligibility contract before any later gate UI or acceptance-layer expansion.
User Action: Say `ok` to start implementation of `TASK-SPEC19.1` with the bound scope and evidence gate above.
