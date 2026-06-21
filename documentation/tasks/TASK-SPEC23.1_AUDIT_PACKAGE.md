# AUDIT PACKAGE

## Scope

- Target Task: `TASK-SPEC23.1`
- Spec: `documentation/SPEC/23_erster_produktiver_or_consumer_fuer_janus_debug.md`
- Task File: `documentation/tasks/TASK-SPEC23_erster_produktiver_or_consumer_fuer_janus_debug.md`
- Precheck: `documentation/tasks/TASK-SPEC23.1_preimplementation_check.md`
- Execution Result: `documentation/tasks/TASK-SPEC23.1_execution_result.md`

## Goal

Add the first productive, operator-visible OR entry seam to `janus-debug`, but only for clearly bounded `debug_hypothesis_review` cases. All other debug flows must remain deterministically Codex-only, and later delegated execution/fallback wiring remains out of scope for `TASK-SPEC23.2`.

## Pipeline Completion Status

- `TASK-SPEC23.1`: implementation COMPLETE - bounded productive eligibility and visible operator-gate behavior are now wired for `janus-debug`, and any OR selection remains explicitly non-executing in this slice.
- `TASK-SPEC23.2`: NOT STARTED - delegated execution, direct Codex fallback runtime, and final acceptance semantics remain intentionally untouched.
- Remaining validation gate: run `janus-final-audit` on this slice only; no production routing, canonical routing-table update, or broader skill activation is included here.

## Changed Files

- `documentation/codex/skills/janus-debug/SKILL.md`
- `documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py`
- `documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py`
- `documentation/codex/model-routing/tests/test_assistive_or_review_consumer_integration.py`
- `documentation/tasks/TASK-SPEC23.1_AUDIT_PACKAGE.md`
- `documentation/tasks/TASK-SPEC23.1_execution_result.md`

## Validation

- `python -m unittest documentation.codex.model-routing.tests.test_assistive_or_review_consumer_integration`
- `python -m unittest documentation.codex.model-routing.tests.test_bounded_or_worker_eligibility`
- `python -m py_compile documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py documentation/codex/model-routing/tests/test_assistive_or_review_consumer_integration.py`
- `python -c "import sys; from pathlib import Path; sys.path.insert(0, str(Path('documentation/codex/model-routing/scripts').resolve())); import codex_debug_hypothesis_review_runner as r; x=r.productive_gate_summary(workflow_id='AUDIT-CLI-BYPASS', task_label='audit', normal_target_model='5.4 medium', delegated_model_label='qwen/qwen3.5-flash-02-23', estimated_or_cost=0.0004, cost_estimate_confidence_percent=81.0, input_payload=None); print(x['selected_path']); print(x.get('eligibility_reason_code'))"`
- `git diff --check -- documentation/codex/skills/janus-debug/SKILL.md documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py documentation/codex/model-routing/tests/test_assistive_or_review_consumer_integration.py documentation/tasks/TASK-SPEC23.1_preimplementation_check.md`

## Known Risks

- The productive gate is now operator-visible for one bounded debug class, so any later widening beyond `debug_hypothesis_review` must stay blocked unless separately specified and audited.
- This slice intentionally does not implement delegated execution acceptance, direct Codex fallback runtime, or final debug completion semantics; those remain a later seam and must not be inferred from this gate-only rollout.
- No commit or push has happened for this local execution state yet, so remotes may not contain the latest implementation or `CURRENT_STATE`.

## Blocker Delta Summary

- Repaired the runner CLI entry so the visible Codex-vs-OR prompt now requires the same bounded productive gate as the consumer path.
- Repaired the gate-only scope boundary so an eligible OR selection is recorded without invoking delegated hypothesis review inside `TASK-SPEC23.1`.
- The slice remains intentionally incomplete by design with respect to `TASK-SPEC23.2`; delegated execution, direct fallback runtime, and final acceptance are still a later task, not part of this repaired slice.

## Audit Focus

- Only clearly bounded and redaction-ready `debug_hypothesis_review` packages can expose the productive Codex-vs-OR choice.
- The direct CLI prompt path must not bypass that productive gate.
- An OR selection must remain non-executing in this slice and must not invoke delegated review yet.
- Non-eligible `janus-debug` cases remain Codex-only with no visible OR gate.
- Other debug modes and other Janus skills do not gain a productive OR path from this slice.
