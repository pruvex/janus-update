## Test Pipeline Triage OR Everyday Entry Validation

Date: `2026-06-24`
Skill: `janus-test-pipeline`
Lane: `test_result_triage_review`
Canonical state: `PASS`

### Goal

Validate that the bounded everyday OR lane inside `janus-test-pipeline` is practically usable for assist-only finding triage review with:

- visible operator gate
- bounded delegated triage review
- file-first capture
- telemetry and healthcheck visibility
- visible actual-cost output
- Codex-owned classification and routing authority

### Scope

- repo skill source `documentation/codex/skills/janus-test-pipeline/SKILL.md`
- consumer runner `documentation/codex/model-routing/scripts/codex_test_result_triage_review_runner.py`
- shared dispatcher `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`

### Validation steps

#### 1. Focused triage tests

Commands:

```powershell
python -m unittest documentation.codex.model-routing.tests.test_assistive_or_review_consumer_integration -k triage
python -m unittest documentation.codex.model-routing.tests.test_assistive_or_review_capture_dispatcher -k triage
```

Results:

- consumer integration triage tests: `PASS` (`3` tests)
- dispatcher capture triage test: `PASS` (`1` test)

### 2. Visible prompt gate

Command:

```powershell
python documentation/codex/model-routing/scripts/codex_test_result_triage_review_runner.py --task-label "Triage OR gate proof" --normal-target-model "5.4 medium" --operator-choice prompt --workflow-id WF-TRIAGE-EVERYDAY-PROMPT-001 --delegated-model-label qwen/qwen3-coder-30b-a3b-instruct --estimated-or-cost 0.00035 --cost-estimate-confidence-percent 79
```

Result: `PASS`

Observed prompt lines:

- `1 = Codex`
- `2 = OR`
- fixed delegated model `qwen/qwen3-coder-30b-a3b-instruct`
- estimated OR cost `0.000350000`
- confidence `79%`

### 3. Stale triage package fails closed at the bounded dispatcher seam

Command:

```powershell
python documentation/codex/model-routing/scripts/codex_test_result_triage_review_runner.py --task-label "Triage OR delegated file-first proof" --normal-target-model "5.4 medium" --operator-choice delegated --workflow-id WF-TRIAGE-EVERYDAY-DELEGATED-002 --estimated-or-cost 0.00035 --cost-estimate-confidence-percent 79 --input-package-json documentation/codex/model-routing/test-triage-fixtures/test_result_triage_input_package_2026-06-14.json --fixture-result-json documentation/codex/model-routing/test-triage-fixtures/test_result_triage_fixture_result_2026-06-14.json --use-local-or-fixture --or-local-fixture-response-path documentation/codex/model-routing/test-triage-fixtures/test_result_triage_fixture_result_2026-06-14.json
```

Result: `PASS`, but intentionally local fallback:

- `eligibility_result`: `OR_CONTEXT_REDACTION_REQUIRED`
- `eligibility_reason_code`: `REQUEST_PACKAGE_NOT_ALLOWLISTED`
- forbidden fields detected:
  - `test_spec_path`
  - `test_plan_path`
  - `test_result_path`

This confirmed that the shared dispatcher rejects over-broad triage request packages at the real bounded OR seam.

### 4. Current-shape redacted triage package

Created:

- `documentation/codex/model-routing/test-triage-fixtures/test_result_triage_input_package_current_shape_2026-06-24.json`

This package was generated from the current consumer contract and stays inside the approved redacted allowlist.

### 5. Current-shape file-first OR response fixture

Created:

- `documentation/codex/model-routing/test-triage-fixtures/test_result_triage_or_fixture_response_current_shape_2026-06-24.json`

This fixture contains a complete file-first OR-style response, including:

- `generation_id`
- `usage`
- `finish_reason`
- model output content

### 6. Delegated file-first proof with current-shape package

Command:

```powershell
python documentation/codex/model-routing/scripts/codex_test_result_triage_review_runner.py --task-label "Triage OR delegated file-first proof current-shape" --normal-target-model "5.4 medium" --operator-choice delegated --workflow-id WF-TRIAGE-EVERYDAY-DELEGATED-003 --estimated-or-cost 0.00035 --cost-estimate-confidence-percent 79 --input-package-json documentation/codex/model-routing/test-triage-fixtures/test_result_triage_input_package_current_shape_2026-06-24.json --use-local-or-fixture --or-local-fixture-response-path documentation/codex/model-routing/test-triage-fixtures/test_result_triage_or_fixture_response_current_shape_2026-06-24.json
```

Result: `PASS`

Key outcomes:

- `selected_path`: `delegated_assist_only_test_result_triage_review`
- `validation_result`: `PASS`
- `final_outcome`: `TEST_RESULT_TRIAGE_REVIEW_READY_FOR_CODEX_VALIDATION`
- `fallback_used`: `NO`
- `rework_required`: `NO`
- `generation_id`: `gen_assistive_fixture_triage_everyday_001`
- `actual_or_cost`: `0.00028765`
- `healthcheck_status`: `PASS`
- `codex_owned_outcome_status`: `DELEGATED_REVIEW_PENDING_CODEX_DECISION`

Operator-facing result line:

- `Tatsaechliche Kosten: 0.000287650`

Artifacts:

- `documentation/codex/model-routing/bounded-dispatch-runs/WF-TRIAGE-EVERYDAY-DELEGATED-003/*`
- `documentation/codex/model-routing/or_healthcheck_telemetry_assistive_or_review_2026-06-24_WF-TRIAGE-EVERYDAY-DELEGATED-003.jsonl`

### Boundaries confirmed

- assist-only delegated triage review only
- no delegated live test execution
- no delegated runner generation
- no delegated final PASS or release-readiness decision
- Codex remains classification, rerun, and routing owner

### Conclusion

`janus-test-pipeline` now has a validated everyday bounded OR lane for finding triage:

- visible gate works
- stale triage packages fail closed
- current-shape redacted input is accepted
- delegated file-first review completes with telemetry, healthcheck, and visible actual-cost output

This is valid everyday OR evidence for the `test_result_triage_review` consumer path.
