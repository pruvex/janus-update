PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: BACKLOG-112
Target Subtask: N/A
Task: documentation/tasks/backlog_BACKLOG-112_quickchange_delegationspfad_live_execute_handoff.md
Spec: N/A WITH REASON - This is a bounded backlog-driven infrastructure and governance fix for the existing janus-quickchange delegation path, not a new product feature spec.
Backlog Item: BACKLOG-112
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: enable exactly one real bounded live-execute path for the existing `quickchange_patch_review` flow without widening authority beyond the already planned janus-quickchange pilot contract.
- Artifact identity is consistent across `documentation/backlog/BACKLOG.md`, `documentation/tasks/backlog_BACKLOG-112_quickchange_delegationspfad_live_execute_handoff.md`, and the current runner evidence that shows `quickchange_sidecar_write_pilot_runner.py` still invokes `codex_sidecar_skill_runner.ps1` without `-Execute`.
- The affected file cluster is concrete and bounded to the quickchange delegation seam: `documentation/codex/model-routing/scripts/quickchange_sidecar_write_pilot_runner.py`, `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`, `documentation/codex/model-routing/scripts/codex_sidecar_skill_runner.ps1`, and one focused regression test module or fixture family under `documentation/codex/model-routing/tests/` if needed.
- Implementation risk is MEDIUM because the change is mechanically small but sits on the first real write-attempt trust boundary; allowlist drift, touched-file-cap drift, or accidental bypass of delete-rename-move tripwires would weaken the bounded OR pilot contract. A git checkpoint is recommended through `janus-git-governance` before Skill 4 because the worktree still contains unrelated dirt.
Affected Files:
- documentation/codex/model-routing/scripts/quickchange_sidecar_write_pilot_runner.py
- documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- documentation/codex/model-routing/scripts/codex_sidecar_skill_runner.ps1
- documentation/codex/model-routing/tests/
Evidence Focus:
- python -m py_compile documentation/codex/model-routing/scripts/quickchange_sidecar_write_pilot_runner.py documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- PowerShell fixture or local dry-run validation that proves the quickchange path now requests a real execute attempt only when the sidecar path is intentionally selected
- focused regression checks for allowlist retention, touched-file cap retention, and delete-rename-move tripwire retention
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m py_compile documentation/codex/model-routing/scripts/quickchange_sidecar_write_pilot_runner.py documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- python -m pytest documentation/codex/model-routing/tests -q
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/backlog/BACKLOG.md
- documentation/tasks/backlog_BACKLOG-112_quickchange_delegationspfad_live_execute_handoff.md
- documentation/codex/model-routing/scripts/quickchange_sidecar_write_pilot_runner.py
- documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- documentation/codex/model-routing/scripts/codex_sidecar_skill_runner.ps1
Drop Context:
- unrelated READY backlog items
- historical Auto Router experiments
- broad Spec-17 and Spec-18 audit narrative outside the already chosen pilot boundary
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The task is implementation-ready, repo-local, and bounded to one exact quickchange delegated live-execute seam before any broader OR rollout.
User Action: Say `ok` to start implementation of `BACKLOG-112` with the bound scope and evidence gate above.
