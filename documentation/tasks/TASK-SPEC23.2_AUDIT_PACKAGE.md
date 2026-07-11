# AUDIT PACKAGE

## Scope

- Target Task: `TASK-SPEC23.2`
- Spec: `documentation/SPEC/23_erster_produktiver_or_consumer_fuer_janus_debug.md`
- Task File: `documentation/tasks/TASK-SPEC23_erster_produktiver_or_consumer_fuer_janus_debug.md`
- Prior Sealed Slice: `documentation/tasks/TASK-SPEC23.1_final_audit.md`
- Precheck: `documentation/tasks/TASK-SPEC23.2_preimplementation_check.md`
- Execution Result: `documentation/tasks/TASK-SPEC23.2_execution_result.md`

## Goal

Turn the already approved productive `janus-debug` OR entry seam into one real bounded runtime path. The consumer may execute exactly one assist-only delegated `debug_hypothesis_review`, but Codex must still own local validation, review, and fallback. Weak, incomplete, uncaptured, or failed healthcheck results must stop at a visible Codex fallback state instead of a silent pending placeholder.

## Pipeline Completion Status

- `TASK-SPEC23.1`: COMPLETE and sealed by final audit - productive eligibility plus visible operator gate remain unchanged and must not be reopened here.
- `TASK-SPEC23.2`: implementation COMPLETE - the bounded delegated runtime plus direct visible Codex fallback seam is now wired into the productive `janus-debug` consumer path.
- Remaining validation gate: run `janus-final-audit` for this slice only. No production routing, no broader OR authority, and no activation in other skills are included.

## Changed Files

- `documentation/codex/skills/janus-debug/SKILL.md`
- `documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py`
- `documentation/codex/model-routing/tests/test_assistive_or_review_consumer_integration.py`
- `documentation/tasks/TASK-SPEC23.2_execution_result.md`
- `documentation/tasks/TASK-SPEC23.2_AUDIT_PACKAGE.md`

## Validation

- `python -m unittest documentation.codex.model-routing.tests.test_assistive_or_review_consumer_integration`
- `python -m unittest documentation.codex.model-routing.tests.test_assistive_or_review_capture_dispatcher`
- `python -m py_compile documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/model-routing/scripts/bounded_or_worker_outcome.py documentation/codex/model-routing/tests/test_assistive_or_review_consumer_integration.py`
- direct CLI fixture probe: `exit_code=0`, `selected_path=delegated_assist_only_hypothesis_review`, `self_spawn_detected=false`, `response_summary_exists=true`, `telemetry_exists=true`
- `python C:\Users\pruve\.codex\skills\janus-executioner\scripts\validate_execution_result.py documentation/tasks/TASK-SPEC23.2_execution_result.md`
- `git diff --check -- documentation/codex/skills/janus-debug/SKILL.md documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/model-routing/scripts/bounded_or_worker_outcome.py documentation/codex/model-routing/tests/test_assistive_or_review_consumer_integration.py documentation/tasks/TASK-SPEC23.2_preimplementation_check.md documentation/tasks/TASK-SPEC23.2_execution_result.md documentation/tasks/TASK-SPEC23.2_AUDIT_PACKAGE.md documentation/ai/CURRENT_STATE.md`
- `git diff --cached --check`

## Known Risks

- The productive delegated path must stay bounded to `debug_hypothesis_review`; widening to other debug classes or other Janus skills remains out of scope.
- This slice still does not grant delegated command execution, delegated test execution, or delegated final-fix authority. Codex remains validation and acceptance owner.
- No commit or push has happened for this local execution state yet, so remotes may not contain the latest implementation or `CURRENT_STATE`.

## Blocker Delta Summary

- Repaired failure code `DELEGATED_RUNNER_SELF_RECURSION` by resolving delegated runtime mode in the consumer before dispatcher invocation.
- Fixture-backed delegated runs now auto-select `use_local_or_fixture=True` and pass the same fixture artifact through the file-first wrapper path instead of relaunching the same runner.
- Missing or conflicting delegated runtime mode now returns a visible Codex fallback result before dispatch rather than spawning a recursive subprocess chain.
- Added one unmocked consumer-to-dispatcher fixture regression and one direct CLI fixture probe that both prove `self_spawn_detected=false`.

## Audit Focus

- The productive `janus-debug` consumer path must still honor the sealed pre-gate from `TASK-SPEC23.1`.
- Delegated debug review must write the bounded package first and then resolve exactly one runtime mode before invoking the existing bounded runtime path.
- Failed delegated review must surface a visible Codex fallback state at the consumer seam.
- Fixture/local validation support must remain bounded, must not imply a live OR call, and must not relaunch `codex_debug_hypothesis_review_runner.py` as a delegated child.
- `janus-debug` skill instructions must match the new runtime/fallback behavior exactly.
