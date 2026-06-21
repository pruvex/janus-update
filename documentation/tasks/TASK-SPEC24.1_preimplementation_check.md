PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC24.1
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC24_lean_dev_governance_fuer_or_und_workhorse_arbeit.md
Spec: documentation/SPEC/24_lean_dev_governance_fuer_or_und_workhorse_arbeit.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_PRECHECK
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it codifies the approved Lean-Dev rule into repo-owned governance artifacts so internal OR- and workhorse-infrastructure work can run faster, while Janus product work stays fully strict.
- Artifact identity is consistent across Spec 24, the generated `TASK-SPEC24` artifact, the task-breakdown handoff, and target task `TASK-SPEC24.1`.
- The file scope is concrete and bounded to `AGENTS.md`, `documentation/codex/CODEX_WORKFLOW_PLAYBOOK.md`, `development/README.md`, and `development/DEV_STATE.md`.
- Risk is MEDIUM because this slice changes working-governance behavior for internal Dev work. Skill 4 must preserve the hard separation: Janus product work, release, and security/privacy-sensitive work remain outside the Lean mode.
- Installed skill copies under `C:\Users\pruve\.codex\skills\` are out of scope for this slice. Only repo-owned governance sources may be changed.
Affected Files:
- AGENTS.md
- documentation/codex/CODEX_WORKFLOW_PLAYBOOK.md
- development/README.md
- development/DEV_STATE.md
Evidence Focus:
- python -m py_compile documentation/codex/scripts/record_skill_usage.py
- git diff --check -- AGENTS.md documentation/codex/CODEX_WORKFLOW_PLAYBOOK.md development/README.md development/DEV_STATE.md documentation/tasks/TASK-SPEC24.1_preimplementation_check.md
- one targeted consistency check that Lean-vs-strict rules match across the four governance files
- one targeted negative check that Janus product work is still explicitly excluded from Lean mode
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- git diff --check -- AGENTS.md documentation/codex/CODEX_WORKFLOW_PLAYBOOK.md development/README.md development/DEV_STATE.md documentation/tasks/TASK-SPEC24.1_preimplementation_check.md
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/24_lean_dev_governance_fuer_or_und_workhorse_arbeit.md
- documentation/tasks/TASK-SPEC24_lean_dev_governance_fuer_or_und_workhorse_arbeit.md
- AGENTS.md
- documentation/codex/CODEX_WORKFLOW_PLAYBOOK.md
- development/README.md
- development/DEV_STATE.md
Drop Context:
- TASK-SPEC24.2
- janus-debug productive consumer work
- old OR experiment history
- Janus product backlog, release, and audit history not needed for this governance slice
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The first Lean-Dev governance slice is implementation-ready, tightly scoped to repo-owned governance artifacts, and explicitly fenced away from Janus product work.
User Action: Say `ok` to start implementation of `TASK-SPEC24.1` with the bound scope and evidence gate above.
