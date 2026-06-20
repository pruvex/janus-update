TASK-SPEC21.2 AUDIT PACKAGE

Scope
- Target Task: `TASK-SPEC21.2`
- Feature: Assistierter OR-Arbeitspferd-Modus fuer Janus-Skills
- Slice Goal: Expose the first visible bounded operator gate for the two approved pilot classes and require selected-model, estimated-cost, and confidence fields before OR can be chosen.

Bound Artifacts
- Spec: `documentation/SPEC/21_assisted_or_workhorse_mode_for_janus_skills.md`
- Task: `documentation/tasks/TASK-SPEC21_assisted_or_workhorse_mode_for_janus_skills.md`
- Task Breakdown: `documentation/tasks/TASK-SPEC21.2_task_breakdown.md`
- Preimplementation Check: `documentation/tasks/TASK-SPEC21.2_preimplementation_check.md`
- Execution Result: `documentation/tasks/TASK-SPEC21.2_execution_result.md`

Changed Files
- `documentation/codex/model-routing/scripts/bounded_or_worker_gate_prompt.py`
- `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`
- `documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py`
- `documentation/codex/model-routing/scripts/codex_test_result_triage_review_runner.py`
- `documentation/codex/model-routing/tests/test_bounded_or_worker_gate_prompt.py`
- `documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py`
- `documentation/codex/skills/janus-debug/SKILL.md`
- `documentation/codex/skills/janus-test-pipeline/SKILL.md`

Implementation Summary
- Normalized the visible pilot gate so the approved debug and triage review classes now show `1 = Codex` and `2 = OR-Arbeitspferd`.
- Extended the shared prompt helper so the visible gate includes the selected OR model plus estimated cost and confidence before OR can be chosen.
- Preserved deterministic Codex-only fallback when model, cost, or confidence data is missing.
- Aligned the versioned `janus-debug` and `janus-test-pipeline` skill instructions to the same bounded operator-gate wording while keeping Codex as validation and acceptance owner.
- Added focused tests for gate prompt composition and updated the existing eligibility regression expectations to the new pilot-facing wording.

Validation
- `python -m unittest documentation/codex/model-routing/tests/test_bounded_or_worker_gate_prompt.py`
- `python -m unittest documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py`
- `python -` with a temp-target `py_compile` harness over `bounded_or_worker_gate_prompt.py`, `codex_bounded_delegation_dispatcher.py`, `codex_debug_hypothesis_review_runner.py`, `codex_test_result_triage_review_runner.py`, and `doc_skill_mini_fixed_or_live_runner.py`
- `git diff --check -- documentation/codex/model-routing/scripts/bounded_or_worker_gate_prompt.py documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py documentation/codex/model-routing/scripts/codex_test_result_triage_review_runner.py documentation/codex/model-routing/tests/test_bounded_or_worker_gate_prompt.py documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py documentation/codex/skills/janus-debug/SKILL.md documentation/codex/skills/janus-test-pipeline/SKILL.md`

Manual Validation Gate
- Status: `N/A WITH REASON`
- Reason: This slice updates bounded Codex-skill operator-gate wording and local prompt validation only. It does not yet add a Janus app UI surface, live OR execution, telemetry capture, or post-run cost display.

Known Risks
- The pilot scope must remain fixed to `debug_hypothesis_review` and `test_result_triage_review`; later slices must not treat this wording change as permission to widen rollout.
- Actual-cost display, OR telemetry capture, healthcheck ingestion, and consumer integration are still deferred to `TASK-SPEC21.3` and `TASK-SPEC21.4`.
- No live OR call or end-to-end runner integration is enabled by this slice alone.
