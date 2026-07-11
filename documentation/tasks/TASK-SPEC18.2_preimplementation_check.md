PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC18.2
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC18_bounded_execution_write_apply_candidate_for_or_sidecar_delegation.md
Spec: documentation/SPEC/18_bounded_execution_write_apply_candidate_for_or_sidecar_delegation.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it adds only `git_diff.patch`, `changed_files.txt`, and required run-artifact completeness checks for an already admitted delegated write candidate, without taking on final acceptance or validation-summary ownership.
- Artifact identity is consistent across reviewed Spec 18, the generated `TASK-SPEC18` artifact, and the completed `documentation/tasks/TASK-SPEC18.1_execution_result.md`. The implementation must build directly on the now-bounded entry gate and must not reopen allowlist-contract work from `TASK-SPEC18.1`.
- The affected file cluster is concrete and bounded to the delegated artifact seam: `documentation/codex/model-routing/scripts/codex_sidecar_skill_runner.ps1`, `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`, one narrow run-artifact or fixture family under `documentation/codex/model-routing/structured-action-runs/`, and one focused bounded-delegation test module under `documentation/codex/model-routing/tests/`.
- Implementation risk is MEDIUM because the slice is mechanically narrow but sits on a sensitive artifact-trust seam where missing diff capture, missing changed-files capture, or incomplete summary artifacts would weaken later Codex review. A git checkpoint is recommended through `janus-git-governance` before Skill 4 because the worktree still contains unrelated dirt outside this bounded slice.
Affected Files:
- documentation/codex/model-routing/scripts/codex_sidecar_skill_runner.ps1
- documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- documentation/codex/model-routing/structured-action-runs/
- documentation/codex/model-routing/tests/
Evidence Focus:
- python -m py_compile documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- pytest documentation/codex/model-routing/tests/test_bounded_write_candidate_artifact_capture.py -q
- fixture-based local checks for missing `git_diff.patch`, missing `changed_files.txt`, and run-artifact completeness for `summary.json`, `stdout.log`, `stderr.log`, and `exit_code.txt`
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m py_compile documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- pytest documentation/codex/model-routing/tests/test_bounded_write_candidate_artifact_capture.py -q
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and predecessor execution result verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/18_bounded_execution_write_apply_candidate_for_or_sidecar_delegation.md
- documentation/tasks/TASK-SPEC18_bounded_execution_write_apply_candidate_for_or_sidecar_delegation.md
- documentation/tasks/TASK-SPEC18.1_execution_result.md
- documentation/codex/model-routing/scripts/codex_sidecar_skill_runner.ps1
- documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- exact artifact names: `summary.json`, `stdout.log`, `stderr.log`, `exit_code.txt`, `git_diff.patch`, `changed_files.txt`
Drop Context:
- old sidecar live-run history outside the bounded write-candidate seam
- later `TASK-SPEC18.3` validation-summary and accept-reject normalization details
- unrelated OR evaluation artifacts and contact/debug history
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The task is implementation-ready, repo-local, and bounded to one exact delegated write-candidate artifact-capture seam before later validation-summary and accept-reject work.
User Action: Say `ok` to start implementation of `TASK-SPEC18.2` with the bound scope and evidence gate above.
