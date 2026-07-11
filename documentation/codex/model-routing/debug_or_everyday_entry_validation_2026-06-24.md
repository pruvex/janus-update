## Debug OR Everyday Entry Validation

Date: `2026-06-24`
Skill: `janus-debug`
Canonical state: `PASS`

### Goal

Validate that the everyday `janus-debug` bounded OR path is practically usable with:

- visible operator gate
- bounded assist-only delegation
- file-first capture
- telemetry and healthcheck visibility
- Codex-owned validation and acceptance

### Scope

- repo skill source `documentation/codex/skills/janus-debug/SKILL.md`
- installed skill copy `C:\Users\pruve\.codex\skills\janus-debug\SKILL.md`
- consumer runner `documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py`
- shared dispatcher `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`

### Skill alignment

Repo and installed `janus-debug` copies already align on the visible operator wording:

- `1 = Codex`
- `2 = OR`

The bounded task class remains:

- `debug_hypothesis_review`

### Validation steps

#### 1. Focused runner tests

Command:

```powershell
python -m unittest documentation.codex.model-routing.tests.test_assistive_or_review_consumer_integration documentation.codex.model-routing.tests.test_bounded_or_worker_gate_prompt
```

Result: `PASS` (`17` tests)

Note:

- two consumer-integration tests were refreshed so they patch the currently loaded dispatcher module explicitly
- this keeps the test evidence aligned with the present consumer loading path

#### 2. Gate rejection with stale/non-allowlisted input package

Command:

```powershell
python documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py --task-label "Debug OR gate proof" --normal-target-model "5.4 medium" --operator-choice prompt --workflow-id WF-DEBUG-EVERYDAY-PROMPT-001 --delegated-model-label qwen/qwen3-coder-30b-a3b-instruct --estimated-or-cost 0.0004 --cost-estimate-confidence-percent 81 --input-package-json documentation/codex/model-routing/debug-review-fixtures/debug_hypothesis_input_package_2026-06-14.json
```

Result: `PASS`, but intentionally local fallback:

- `eligibility_result`: `OR_CONTEXT_REDACTION_REQUIRED`
- `eligibility_reason_code`: `REQUEST_PACKAGE_NOT_ALLOWLISTED`
- `final_outcome`: `LOCAL_CODEX_PATH_SELECTED`

This proved the gate is fail-closed when the debug package no longer matches the approved redacted allowlist.

#### 3. Current-shape redacted package

Created:

- `documentation/codex/model-routing/debug-review-fixtures/debug_hypothesis_input_package_current_shape_2026-06-24.json`

This package was generated from the current consumer contract and stays inside the approved redacted field set.

#### 4. Prompt gate with current-shape package

Command:

```powershell
python documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py --task-label "Debug OR gate proof current-shape" --normal-target-model "5.4 medium" --operator-choice prompt --workflow-id WF-DEBUG-EVERYDAY-PROMPT-002 --estimated-or-cost 0.0004 --cost-estimate-confidence-percent 81 --input-package-json documentation/codex/model-routing/debug-review-fixtures/debug_hypothesis_input_package_current_shape_2026-06-24.json
```

Result: `PASS`

Key outcomes:

- `selected_path`: `operator_choice_pending`
- `choice_1`: `Codex`
- `choice_2`: `OR`
- `eligibility_result`: `OR_ALLOWED`
- `per_call_cap_usd`: `0.03`
- `session_cap_usd`: `0.09`

Observed prompt lines:

- `1 = Codex`
- `2 = OR`
- fixed delegated model `qwen/qwen3-coder-30b-a3b-instruct`
- estimated OR cost `0.000400000`
- confidence `81%`

#### 5. Delegated fixture run with correct OR-response fixture type

Created:

- `documentation/codex/model-routing/debug-review-fixtures/debug_hypothesis_or_fixture_response_current_shape_2026-06-24.json`

This is a complete file-first OR-style response fixture containing:

- `generation_id`
- `usage`
- `finish_reason`
- model output content

Command:

```powershell
python documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py --task-label "Debug OR delegated proof current-shape" --normal-target-model "5.4 medium" --operator-choice delegated --workflow-id WF-DEBUG-EVERYDAY-DELEGATED-003 --estimated-or-cost 0.0004 --cost-estimate-confidence-percent 81 --input-package-json documentation/codex/model-routing/debug-review-fixtures/debug_hypothesis_input_package_current_shape_2026-06-24.json --fixture-result-json documentation/codex/model-routing/debug-review-fixtures/debug_hypothesis_or_fixture_response_current_shape_2026-06-24.json
```

Result: `PASS`

Key outcomes:

- `selected_path`: `delegated_assist_only_hypothesis_review`
- `validation_result`: `PASS`
- `final_outcome`: `DEBUG_HYPOTHESIS_REVIEW_READY_FOR_CODEX_VALIDATION`
- `fallback_used`: `NO`
- `rework_required`: `NO`
- `generation_id`: `gen_assistive_fixture_debug_everyday_001`
- `actual_or_cost`: `0.00045678`
- `healthcheck_status`: `PASS`
- `codex_owned_outcome_status`: `DELEGATED_REVIEW_PENDING_CODEX_DECISION`

Operator-facing result line:

- `Tatsaechliche Kosten: 0.000456780`

Artifacts:

- `documentation/codex/model-routing/bounded-dispatch-runs/WF-DEBUG-EVERYDAY-DELEGATED-003/*`
- `documentation/codex/model-routing/or_healthcheck_telemetry_assistive_or_review_2026-06-24_WF-DEBUG-EVERYDAY-DELEGATED-003.jsonl`

### Boundaries confirmed

- assist-only delegated hypothesis review only
- no delegated local command execution
- no delegated test execution
- no delegated final fix claim
- Codex remains local validation and acceptance owner

### Conclusion

`janus-debug` is currently the strongest next everyday OR lane after the productive `janus-executioner` entry:

- the visible prompt gate works
- stale/non-allowlisted input is fail-closed
- current-shape redacted input is accepted
- delegated bounded review can complete with capture, telemetry, healthcheck, and visible actual-cost output

This is valid bounded everyday OR evidence for the `janus-debug` consumer path.
