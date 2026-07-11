# Productive Dev-Workhorse Current-Shape Fixture Validation - 2026-06-24

## Scope

Validate the dedicated productive Dev-workhorse entry from the current worktree without any new live OR call:

- visible operator gate for `execution_patch_candidate`
- visible operator gate for `execution_write_apply_candidate`
- local Codex path for both allowed classes
- bounded OR fixture path for `execution_patch_candidate`
- accepted-source delegated validation path for `execution_write_apply_candidate`

## Finding

The productive two-class entry still worked, but the old local `execution_patch_candidate` fixture response from `2026-06-19` no longer matched the current `BACKLOG-108` allowlist. It proposed `scripts/dev-log-utils.cjs`, so the OR branch correctly fell back with:

- `changed file escapes allowlist: scripts/dev-log-utils.cjs`

That was a fixture-staleness problem, not a productive runner regression.

## Fix

- Added a fresh current-shape direct-OR fixture response:
  - `documentation/codex/model-routing/execution-review-fixtures/direct_or_execution_patch_candidate_current_shape_fixture_response_2026-06-24.json`
- Added a regression proving the fixture stays inside the current `BACKLOG-108` allowlist:
  - `documentation/codex/model-routing/tests/test_openrouter_direct_execution_patch_candidate_runner.py`

The new fixture is derived from the already accepted current-shape `DIRECT-OR-DEEPSEEK-EXECUTION-POST-WRITE-008` response and keeps the bounded proposal on:

- `backend/services/contact_manager.py`

## Validation

- `python -m unittest documentation.codex.model-routing.tests.test_openrouter_direct_execution_patch_candidate_runner documentation.codex.model-routing.tests.test_codex_dev_workhorse_runner`: PASS (`26` tests)
- `python documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py --task-class execution_patch_candidate --task-label "Spec25 current-state gate check" --normal-target-model "5.4 medium" --operator-choice prompt --workflow-id WF-SPEC25-CURR-GATE-EP-001 --path-id productive_dev_workhorse_path --estimated-or-cost 0.00072 --cost-estimate-confidence-percent 87`: PASS
- `python documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py --task-class execution_patch_candidate --task-label "Spec25 current-state local path" --normal-target-model "5.4 medium" --operator-choice local --workflow-id WF-SPEC25-CURR-LOCAL-EP-001 --path-id productive_dev_workhorse_path --estimated-or-cost 0.00072 --cost-estimate-confidence-percent 87`: PASS
- `python documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py --task-class execution_patch_candidate --task-label "Spec25 current-state fixture OR path refreshed" --normal-target-model "5.4 medium" --operator-choice or --workflow-id WF-SPEC25-CURR-OR-EP-002 --path-id productive_dev_workhorse_path --estimated-or-cost 0.00072 --cost-estimate-confidence-percent 87 --execution-input-package documentation/codex/model-routing/execution-review-fixtures/backlog_108_execution_patch_candidate_input_package_current_shape_2026-06-24.json --use-local-or-fixture --or-local-fixture-response-path documentation/codex/model-routing/execution-review-fixtures/direct_or_execution_patch_candidate_current_shape_fixture_response_2026-06-24.json`: PASS
- `python documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py --task-class execution_write_apply_candidate --task-label "Spec25 current-state gate check write-apply" --normal-target-model "5.4 medium" --operator-choice prompt --workflow-id WF-SPEC25-CURR-GATE-EW-001 --path-id productive_dev_workhorse_path --estimated-or-cost 0.00095 --cost-estimate-confidence-percent 87`: PASS
- `python documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py --task-class execution_write_apply_candidate --task-label "Spec25 current-state local path write-apply" --normal-target-model "5.4 medium" --operator-choice local --workflow-id WF-SPEC25-CURR-LOCAL-EW-001 --path-id productive_dev_workhorse_path --estimated-or-cost 0.00095 --cost-estimate-confidence-percent 87`: PASS
- `python documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py --task-class execution_write_apply_candidate --task-label "Spec25 current-state delegated validation write-apply" --normal-target-model "5.4 medium" --operator-choice or --workflow-id WF-SPEC25-CURR-OR-EW-001 --path-id productive_dev_workhorse_path --estimated-or-cost 0.00095 --cost-estimate-confidence-percent 87 --accepted-source-run-dir documentation/codex/model-routing/execution-write-apply-source-bridges/EXEC-WRITE-APPLY-SOURCE-BRIDGE-003`: PASS

## Result

The current productive Dev-workhorse entry is locally green again for both allowed classes:

- `execution_patch_candidate` prompt/local/fixture-OR path: PASS
- `execution_write_apply_candidate` prompt/local/delegated accepted-source validation path: PASS

This remains:

- no production routing
- no canonical routing-table update
- no new live OR call
- no broad skill activation
