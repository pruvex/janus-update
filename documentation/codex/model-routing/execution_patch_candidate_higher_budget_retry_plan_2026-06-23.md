# execution_patch_candidate Higher-Budget Retry Plan

Date: `2026-06-23`
Scope: one additional bounded live retry only
Skill surface: `janus-executioner`
Task class: `execution_patch_candidate`
Target slice: `BACKLOG-108`
Workflow baseline:
- prior live run: `DEV-WORKHORSE-EXECUTION-GATE-001`
- latest live retry: `DEV-WORKHORSE-EXECUTION-GATE-002`

## Goal

Run exactly one additional bounded OpenRouter retry for the prechecked `BACKLOG-108` execution patch candidate with a materially larger completion budget, so we can answer one narrow question:

- is the current execution-class failure mainly a completion-budget truncation problem
- or is this class still not reliable enough for accepted bounded patch proposals on the current contract

This plan does not approve production routing, does not broaden delegated authority, and does not replace Codex-owned local review.

## Current Evidence

- `DEV-WORKHORSE-EXECUTION-GATE-001`
  - transport: PASS
  - usage capture: PASS
  - finish reason: `stop`
  - result shape: bounded fallback-style result without valid unified diff
- `DEV-WORKHORSE-EXECUTION-GATE-002`
  - transport: PASS
  - usage capture: PASS
  - finish reason: `length`
  - actual cost: `0.00075572`
  - completion tokens used: `2200`
  - result shape: truncated, parser fallback, rejected

Inference:
- transport, file-first capture, generation tracking, usage accounting, telemetry JSONL, and healthcheck ingestion are already proven
- the remaining live blocker is output adequacy for a larger patch-candidate class

## Recommended Retry Shape

- live call count: `1`
- OR model: `deepseek/deepseek-v4-flash`
- same bounded input package:
  - `documentation/codex/model-routing/execution-review-fixtures/backlog_108_execution_patch_candidate_input_package_2026-06-19.json`
- keep the same task class and healthcheck path
- increase completion budget from:
  - previous `max_tokens=2200`
  - to recommended `max_tokens=3600`

Why `3600`:
- the last retry exhausted the full `2200` completion-token budget
- `3600` is a clear but still bounded increase
- it should be enough to tell us whether the truncation is the main blocker without turning the run into an open-ended long-form attempt
- the expected spend still remains comfortably below the configured `execution_patch_candidate` per-call cap of `0.05`

## Cost Expectation

Using the last real retry as the closest evidence:

- prompt-side cost from latest retry: about `0.00013972`
- completion-side cost at `2200` tokens: `0.000616`
- implied completion cost per token: about `0.00000028`

Conservative higher-budget estimate:
- prompt side: `0.00014`
- completion side at `3600`: about `0.00101`
- estimated total: about `0.00115`

Recommended displayed operator estimate for the retry:
- `estimated_or_cost=0.001150000`
- `cost_estimate_confidence_percent=35`

Reason for raising confidence only modestly:
- transport is proven
- output adequacy is still unresolved
- this is still a one-off bounded retry, not a stable repeated success lane

## Acceptance Gates

Accept the retry as valid bounded execution evidence only if all are true:

- OR call count = `1`
- response body parses
- `generation_id` exists
- `usage` exists
- healthcheck ingestion passes
- `finish_reason != length`
- validation result = `PASS`
- returned payload is either:
  - a valid bounded unified diff patch candidate
  - or a valid bounded `BLOCKED` result with complete non-truncated JSON

If a valid bounded `BLOCKED` result is returned:
- treat the retry as contract-valid but `CODEX_PREFERRED`
- do not treat it as accepted patch evidence

## Abort / Reject Rules

Reject the retry and fall back to Codex-only if any of these happen:

- `finish_reason=length`
- missing `generation_id`
- missing `usage`
- missing or unparsable response body
- healthcheck ingestion failure
- malformed JSON result
- result touches files outside the allowlist
- actual cost unexpectedly spikes beyond the displayed bounded expectation in a way that suggests prompt drift or model mismatch

## Operational Boundaries

- no production routing
- no canonical routing-table update
- no global OR approval
- no automatic continuation into `execution_write_apply_candidate`
- no change to Codex final ownership
- no broad model-family wave hidden inside this retry

## Decision Rule After The Retry

If the higher-budget retry returns:

- valid unified diff plus `validation_result=PASS`
  - classify the class as improved and keep one later apply/review decision separate
- valid bounded `BLOCKED` plus `validation_result=PASS`
  - classify the class as transport-proven but patch-insufficient on the current prompt contract
- any new `finish_reason=length`
  - classify the current DeepSeek execution patch lane as not worth further immediate retries on this contract
  - pivot back to Codex-owned execution for larger slices unless a different model family is explicitly chosen later

## Suggested Next Command Shape

This is the intended next live shape only after explicit user approval:

```text
python documentation/codex/model-routing/scripts/openrouter_direct_execution_patch_candidate_runner.py
  --task-label "BACKLOG-108 execution patch candidate higher-budget retry"
  --normal-target-model "5.4 medium"
  --model "deepseek/deepseek-v4-flash"
  --task-class execution_patch_candidate
  --workflow-id DEV-WORKHORSE-EXECUTION-GATE-003
  --input-package-json documentation/codex/model-routing/execution-review-fixtures/backlog_108_execution_patch_candidate_input_package_2026-06-19.json
  --estimated-or-cost 0.00115
  --cost-estimate-confidence-percent 35
  --max-tokens 3600
  --execute-live
```

The wrapper, telemetry write, and local healthcheck ingestion remain mandatory.
