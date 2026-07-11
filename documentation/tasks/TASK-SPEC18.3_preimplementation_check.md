PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC18.3
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC18_bounded_execution_write_apply_candidate_for_or_sidecar_delegation.md
Spec: documentation/SPEC/18_bounded_execution_write_apply_candidate_for_or_sidecar_delegation.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it adds only `validation_summary.json` as a mandatory delegated write-candidate artifact, rejects missing or failed local validation, and normalizes the operator-facing final outcome to an explicit Codex-owned accept-or-reject stance.
- Artifact identity is consistent across reviewed Spec 18, the generated `TASK-SPEC18` artifact, and the completed `documentation/tasks/TASK-SPEC18.2_execution_result.md`. The implementation must build directly on the now-bounded entry-gate and artifact-capture slices and must not reopen allowlist or diff-capture work.
- The affected file cluster is concrete and bounded to the final delegated write-candidate evaluation seam: `documentation/codex/model-routing/scripts/codex_execution_write_apply_candidate_runner.py`, `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`, one narrow run-artifact family under `documentation/codex/model-routing/structured-action-runs/`, and one focused bounded-delegation test module under `documentation/codex/model-routing/tests/`.
- Implementation risk is MEDIUM because the slice is still mechanically narrow but sits on the final trust boundary where missing validation state or overreaching final-outcome wording would weaken Codex-owned review governance. A git checkpoint is recommended through `janus-git-governance` before Skill 4 because the worktree still contains unrelated dirt outside this bounded slice.
Affected Files:
- documentation/codex/model-routing/scripts/codex_execution_write_apply_candidate_runner.py
- documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- documentation/codex/model-routing/structured-action-runs/
- documentation/codex/model-routing/tests/
Evidence Focus:
- python -m py_compile documentation/codex/model-routing/scripts/codex_execution_write_apply_candidate_runner.py documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- pytest documentation/codex/model-routing/tests/test_bounded_write_candidate_validation_acceptance.py -q
- fixture-based local checks for missing `validation_summary.json`, failed local validation, and normalized Codex-owned final outcomes
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m py_compile documentation/codex/model-routing/scripts/codex_execution_write_apply_candidate_runner.py documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- pytest documentation/codex/model-routing/tests/test_bounded_write_candidate_validation_acceptance.py -q
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and predecessor execution result verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/18_bounded_execution_write_apply_candidate_for_or_sidecar_delegation.md
- documentation/tasks/TASK-SPEC18_bounded_execution_write_apply_candidate_for_or_sidecar_delegation.md
- documentation/tasks/TASK-SPEC18.2_execution_result.md
- documentation/codex/model-routing/scripts/codex_execution_write_apply_candidate_runner.py
- documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- exact artifact names: `summary.json`, `stdout.log`, `stderr.log`, `exit_code.txt`, `git_diff.patch`, `changed_files.txt`, `validation_summary.json`
Drop Context:
- old sidecar live-run history outside the bounded write-candidate seam
- earlier TASK-SPEC18.1 entry-gate implementation details that no longer change
- unrelated OR evaluation artifacts and contact/debug history
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The task is implementation-ready, repo-local, and bounded to the final validation-summary plus Codex-owned accept-or-reject seam for delegated write candidates.
User Action: Say `ok` to start implementation of `TASK-SPEC18.3` with the bound scope and evidence gate above.
