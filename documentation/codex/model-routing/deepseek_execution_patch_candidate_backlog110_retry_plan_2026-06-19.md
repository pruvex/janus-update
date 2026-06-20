# DeepSeek BACKLOG-110 Higher-Completion Retry Plan - 2026-06-19

Status: READY FOR EXPLICIT LIVE APPROVAL

## Goal

Run at most one higher-completion retry for the existing `BACKLOG-110` DeepSeek `execution_patch_candidate` slice after the prior live probe ended with `finish_reason=length`.

This plan does not authorize a live call by itself.

## Why A Retry Is Justified

The previous workflow `DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-003` already proved that:

- transport worked
- file-first capture worked
- `generation_id` and usage were captured
- actual cost stayed well below the `execution_patch_candidate` cap
- telemetry JSONL parsing worked
- `health_snapshot.py` ingestion worked

The remaining blocker was narrow:

- `finish_reason=length`
- truncated JSON response
- fallback artifact without usable `patch_text`

That makes a higher-completion retry the shortest disciplined next step.

## Boundaries

- exactly one live OR call if explicitly approved
- same task class: `execution_patch_candidate`
- same slice: `BACKLOG-110`
- same OR family: `deepseek/deepseek-v4-flash`
- no production routing
- no canonical routing-table update
- no local apply during the retry itself
- Codex remains local validation and apply-or-reject owner

## Proposed Retry Settings

- workflow pattern: `DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-004`
- task label: `BACKLOG-110 execution patch candidate higher completion retry`
- model: `deepseek/deepseek-v4-flash`
- budget profile: `execution_patch_candidate`
- class cap: `0.05` USD
- proposed `--max-tokens`: `3200`
- proposed `--estimated-completion-tokens`: `3200`
- proposed `--estimated-prompt-tokens`: `1200`
- proposed `--estimated-or-cost`: `0.000684`
- proposed confidence: `30%`

## Cost Rationale

The earlier `BACKLOG-110` live probe used:

- prompt tokens: `978`
- completion tokens: `2200`
- actual cost: `0.00048402`

The retry keeps the same model and prompt shape but raises the completion budget so the model can finish the JSON object. Even with a conservative estimate of `1200` prompt tokens and `3200` completion tokens, the projected cost remains far below the class cap.

## Acceptance Gates

Accept the retry as real larger-class evidence only if all are true:

- OR call count = `1`
- response body parses
- `generation_id` exists
- usage exists
- actual cost is below `0.05`
- `finish_reason != length`
- `patch_text` is valid unified diff text
- `changed_files` matches the diff
- `suggested_validation_steps` is non-empty
- `health_snapshot.py` ingests the telemetry JSONL successfully

If any gate fails, classify the run as debug-only evidence and fall back to Codex-only.

## Proposed Command

```powershell
python documentation\codex\model-routing\scripts\openrouter_direct_execution_patch_candidate_runner.py `
  --task-label "BACKLOG-110 execution patch candidate higher completion retry" `
  --normal-target-model "5.4/medium" `
  --model "deepseek/deepseek-v4-flash" `
  --input-package-json documentation\codex\model-routing\execution-review-fixtures\backlog_110_execution_patch_candidate_input_package_2026-06-19.json `
  --estimated-prompt-tokens 1200 `
  --estimated-completion-tokens 3200 `
  --estimated-or-cost 0.000684 `
  --cost-estimate-confidence-percent 30 `
  --cost-estimate-sample-count 1 `
  --cost-estimate-mean-abs-error-percent 66.76 `
  --cost-estimate-p50-error-percent 66.76 `
  --cost-estimate-p90-error-percent 66.76 `
  --cost-estimate-basis "deepseek/deepseek-v4-flash+execution_patch_candidate+backlog110+higher_completion_retry" `
  --prompt-template-hash "sha256:direct_or_execution_patch_candidate_v1_hardened" `
  --task-variant "execution_patch_candidate" `
  --price-snapshot-source "https://openrouter.ai/deepseek/deepseek-v4-flash" `
  --price-snapshot-timestamp "2026-06-19T16:10:00+02:00" `
  --workflow-id DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-004 `
  --max-tokens 3200 `
  --execute-live
```

## Decision Rule

- Best next step if the user wants to keep pushing the larger-class OR worker lane: run this one retry.
- Best next step if the user wants to minimize live spend: stop here and keep the current larger-class evidence set unchanged.
