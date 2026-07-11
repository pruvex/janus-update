# Execution Patch Candidate DeepSeek vs GPT-OSS-120B Comparison Plan - 2026-06-20

Status: COMPARISON PLAN ONLY / NO LIVE OR CALL / NO PRODUCTION ROUTING / NO CANONICAL ROUTING-TABLE UPDATE

## Goal

Prepare the next bounded larger-class OR comparison block on the real `execution_patch_candidate` lane.

This block is intentionally narrow:

- same task class
- same compact contract family
- same prechecked slice family
- one accepted baseline model
- one challenger model

No live OR call is executed in this planning step.

## Comparison Decision

### Baseline

- model: `deepseek/deepseek-v4-flash`
- role: accepted larger-class reference lane

Why baseline:

- accepted bounded evidence already exists for:
  - `DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-002`
  - `DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-006`
- the compact-contract redesign is already proven on a real larger-class slice
- this is the strongest current larger-class OR worker for proposal-first execution work

### Challenger

- model: `openai/gpt-oss-120b`
- role: next serious larger-class comparison candidate

Why challenger:

- it is a plausible workhorse-family candidate for larger proposal-first tasks
- it avoids reopening the already negative Qwen execution-candidate lane too early
- it gives the next comparison a cleaner baseline-vs-challenger structure than another broad family sweep

### Deferred For Now

- `qwen/qwen3-coder-flash`

Reason:

- current live evidence is negative for this class on the present contract
- the model drifted into multi-item patch output
- actual cost overshot the estimate heavily
- it should only be revisited after a contract shape explicitly designed for Qwen multi-item behavior

## Bound Slice For Comparison

Use the same real larger-class slice family that already produced the accepted compact-contract DeepSeek evidence:

- fixture/input package:
  - `documentation/codex/model-routing/execution-review-fixtures/backlog_108_execution_patch_candidate_input_package_2026-06-19.json`

Why this slice:

- it is already prechecked
- it already has real larger-class DeepSeek evidence
- it keeps the next challenger run apples-to-apples against the accepted baseline

## Class And Budget

- task class: `execution_patch_candidate`
- budget profile: `execution_patch_candidate`
- per-call cap: `0.05` USD
- session cap for this class: `0.15` USD

Working rule:

- authorize at most one challenger live call in the next block
- do not broaden into another family until this comparison is classified

## Comparison Acceptance Gates

Accept the future challenger result only if all are true:

- OR call count = `1`
- response body parses
- `generation_id` exists
- usage exists
- actual cost is below `0.05`
- `finish_reason != length`
- `patch_text` is valid unified diff text
- `changed_files` matches the diff
- `changed_files` stays inside the allowlist
- touched-file count stays within the bounded cap
- `suggested_validation_steps` is non-empty
- `health_snapshot.py` ingests the telemetry JSONL successfully

If any gate fails:

- classify the run as negative or debug-only evidence
- keep DeepSeek as the current larger-class baseline
- do not treat the challenger as a viable replacement

## Comparison Questions To Answer

The next live comparison should answer exactly these questions:

1. Can `openai/gpt-oss-120b` finish the larger-class compact contract cleanly on the `BACKLOG-108` slice?
2. Does it preserve the one bounded patch-candidate contract better than the rejected Qwen lane?
3. Does it stay cost-reasonable relative to the accepted DeepSeek baseline?
4. Does it produce a patch candidate that looks reviewable enough for Codex-owned apply/reject review?

## Proposed Challenger Run Shape

- workflow id:
  - `DIRECT-OR-GPTOSS120-EXECUTION-LIVE-001`
- model:
  - `openai/gpt-oss-120b`
- task class:
  - `execution_patch_candidate`
- input package:
  - `documentation/codex/model-routing/execution-review-fixtures/backlog_108_execution_patch_candidate_input_package_2026-06-19.json`
- contract family:
  - compact larger-class contract, same lane as accepted `DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-006`

## Provisional Challenger Parameters

These values are planning defaults and may be adjusted before the live run if a stronger estimate is available:

- proposed `--estimated-prompt-tokens`: `900`
- proposed `--estimated-completion-tokens`: `1800`
- proposed `--estimated-or-cost`: `0.001200`
- proposed `--cost-estimate-confidence-percent`: `20`
- proposed `--cost-estimate-sample-count`: `0`
- proposed `--cost-estimate-mean-abs-error-percent`: `0`
- proposed `--cost-estimate-p50-error-percent`: `0`
- proposed `--cost-estimate-p90-error-percent`: `0`
- proposed `--cost-estimate-basis`: `openai/gpt-oss-120b+execution_patch_candidate+backlog108+first_comparison_probe`
- proposed `--prompt-template-hash`: `sha256:direct_or_execution_patch_candidate_v2_compact`
- proposed `--task-variant`: `execution_patch_candidate`
- proposed `--max-tokens`: `1800`

These defaults are conservative and remain far below the class cap.

## Proposed Challenger Command

```powershell
python documentation\codex\model-routing\scripts\openrouter_direct_execution_patch_candidate_runner.py `
  --task-label "BACKLOG-108 execution patch candidate compact-contract comparison" `
  --normal-target-model "5.4/medium" `
  --model "openai/gpt-oss-120b" `
  --input-package-json documentation\codex\model-routing\execution-review-fixtures\backlog_108_execution_patch_candidate_input_package_2026-06-19.json `
  --estimated-prompt-tokens 900 `
  --estimated-completion-tokens 1800 `
  --estimated-or-cost 0.001200 `
  --cost-estimate-confidence-percent 20 `
  --cost-estimate-sample-count 0 `
  --cost-estimate-mean-abs-error-percent 0 `
  --cost-estimate-p50-error-percent 0 `
  --cost-estimate-p90-error-percent 0 `
  --cost-estimate-basis "openai/gpt-oss-120b+execution_patch_candidate+backlog108+first_comparison_probe" `
  --prompt-template-hash "sha256:direct_or_execution_patch_candidate_v2_compact" `
  --task-variant "execution_patch_candidate" `
  --price-snapshot-source "manual_current_openrouter_model_page" `
  --price-snapshot-timestamp "<fill before live run>" `
  --workflow-id DIRECT-OR-GPTOSS120-EXECUTION-LIVE-001 `
  --max-tokens 1800 `
  --execute-live
```

## Expected Classification Outcomes

Possible future classification after the challenger run:

- `ACCEPTED_BOUNDED_EVIDENCE`
  - if the challenger passes all bounded gates cleanly
- `NEGATIVE_LIVE_EVIDENCE`
  - if the challenger completes capture but fails contract, finish, cost, or validation gates
- `DEBUG_ONLY_EVIDENCE`
  - if wrapper or local artifact capture fails and the result is not trustworthy enough for comparison

## Working Decision

The next larger-class OR comparison should be:

- baseline: `deepseek/deepseek-v4-flash`
- challenger: `openai/gpt-oss-120b`
- slice: `BACKLOG-108`
- contract: compact `execution_patch_candidate`

Do not move to write-capable live OR and do not reopen the Qwen lane before this comparison is complete.

## Boundary Reminder

- no production routing
- no canonical routing-table update
- no global OR approval
- no local apply inside the OR run itself
- Codex remains review, validation, and apply-or-reject owner
