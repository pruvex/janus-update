PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC20.1
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC20_separate_dev_or_infrastructure_governance.md
Spec: documentation/SPEC/20_separate_dev_or_infrastructure_governance.md
Backlog Item: N/A
Assigned Model: 5.4
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it creates the first separate `development/` governance home only and does not pull forward backlog migration, AGENTS updates, workflow-playbook hardening, Janus backlog rewrites, or any active backend or OR runtime repair.
- Artifact identity is consistent across Spec 20, the generated TASK-SPEC20 artifact, the released handoff `documentation/tasks/TASK-SPEC20.1_task_breakdown.md`, and the target task `TASK-SPEC20.1`.
- The affected file cluster is concrete and bounded to three new top-level Dev source-of-truth artifacts: `development/README.md`, `development/DEV_STATE.md`, and `development/DEV_BACKLOG.md`.
- Implementation risk is LOW to MEDIUM because the slice is documentation-only but governance-sensitive: unclear wording could blur Source-of-Truth boundaries or accidentally let the new Dev area claim Janus product, Git, release, or production-routing authority. A git checkpoint is recommended through `janus-git-governance` before Skill 4 because the wider worktree still contains unrelated dirty scope.
Affected Files:
- development/README.md
- development/DEV_STATE.md
- development/DEV_BACKLOG.md
Evidence Focus:
- git diff --check -- development/README.md development/DEV_STATE.md development/DEV_BACKLOG.md
- one focused consistency pass that README, DEV_STATE, and DEV_BACKLOG use the same Source-of-Truth boundary and non-authority rules
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- git diff --check -- development/README.md development/DEV_STATE.md development/DEV_BACKLOG.md
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/20_separate_dev_or_infrastructure_governance.md
- documentation/tasks/TASK-SPEC20_separate_dev_or_infrastructure_governance.md
- documentation/tasks/TASK-SPEC20.1_task_breakdown.md
- the exact bounded files `development/README.md`, `development/DEV_STATE.md`, and `development/DEV_BACKLOG.md`
Drop Context:
- later migration slice `TASK-SPEC20.2`
- later Janus governance hardening slice `TASK-SPEC20.3`
- old backend environment debug history
- old OR experiment or routing history unrelated to the new Dev governance home
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The task is implementation-ready, tightly bounded to three new governance files under `development/`, and does not require migration or Janus governance rewrites in this first slice.
User Action: Say `ok` to start implementation of `TASK-SPEC20.1` with the bound scope and evidence gate above.
