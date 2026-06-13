# OpenRouter Auto Router Completion-Budget Retry Result - 2026-06-13

Status: SINGLE-CALL RETRY COMPLETE / BOUNDED LOCAL EVIDENCE ONLY / NO PRODUCTION ROUTING / NO CANONICAL ROUTING-TABLE UPDATE

## Scope

- skill: `DOC-SKILL-010`
- request model: `openrouter/auto`
- plugin id: `auto-router`
- allowed models:
  - `openai/gpt-oss-20b`
  - `openai/gpt-oss-120b`
  - `qwen/qwen3.5-flash-02-23`
  - `minimax/minimax-m3`
  - `nvidia/nemotron-3-nano-30b-a3b`
- `cost_quality_tradeoff`: `8`
- completion budget retry:
  - first experiment `max_tokens=250`
  - retry `max_tokens=500`
- live call count: `1`

## Retry Result

- selected routed model: `openai/gpt-oss-120b`
- `generation_id`: `gen-1781372941-ovyPwDvuaaaqcHVWXslj`
- `finish_reason`: `stop`
- actual prompt tokens: `633`
- actual completion tokens: `424`
- actual reasoning tokens: `196`
- actual cost: `0.00053955`
- cost cap `0.0020`: PASS

## Acceptance Validation

- `response_body.json` parse: PASS
- `response_summary.json` contains `generation_id`: PASS
- `response_summary.json` contains selected routed model: PASS
- `response_summary.json` contains `finish_reason`: PASS
- `response_summary.json` contains usage: PASS
- `response_summary.json` contains actual cost: PASS
- `finish_reason != length`: PASS
- retry telemetry JSONL parse: PASS
- `health_snapshot.py --or-telemetry-jsonl` ingestion: PASS

## Comparison

### Fixed baseline

- fixed selected model: `qwen/qwen3.5-flash-02-23`
- fixed baseline actual cost: `0.00060359`

### First Auto Router experiment

- selected routed model: `openai/gpt-oss-120b`
- `finish_reason`: `length`
- actual cost: `0.00040905`

### Completion-budget retry

- selected routed model: `openai/gpt-oss-120b`
- `finish_reason`: `stop`
- actual cost: `0.00053955`

### Comparison summary

- routed model versus fixed baseline:
  - different model selected: YES
- routed model versus first Auto Router experiment:
  - same model selected: YES
- retry versus fixed baseline actual cost:
  - lower by `0.00006404`
  - relative reduction: `10.61%`
- retry versus first Auto Router experiment actual cost:
  - higher by `0.00013050`
  - relative increase: `31.90%`
- retry versus conservative pre-call retry estimate `0.0007821`:
  - lower by `31.01%`

## Interpretation

The completion-budget retry resolved the previous technical blocker:

- first Auto Router experiment:
  - `finish_reason=length`
- retry:
  - `finish_reason=stop`

The cost stayed below the bounded cap and remained below the fixed `qwen/qwen3.5-flash-02-23` baseline, but it was higher than the first length-limited Auto Router run because the response was allowed to complete.

This is still bounded experiment evidence only. It does not justify replacing the fixed-model Auto-sparsam implementation plan on its own.

## Boundary Reminder

- this retry is bounded local experiment evidence only
- it does not replace the fixed-model Auto-sparsam implementation plan
- it does not activate production routing
- it does not update the canonical routing table
- it does not create any global OR approval
- it does not continue the separate `5.4` candidate phase
