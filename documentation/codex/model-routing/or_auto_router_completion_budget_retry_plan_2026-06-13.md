# OpenRouter Auto Router Completion-Budget Retry Plan - 2026-06-13

Status: SINGLE-CALL RETRY PLAN / COMPLETION-BUDGET CHECK ONLY / NO PRODUCTION ROUTING / NO CANONICAL ROUTING-TABLE UPDATE

## Purpose

Run exactly one additional Auto Router experiment call for `DOC-SKILL-010` to test whether a higher completion budget removes the previous `finish_reason=length` outcome.

This retry does not replace:

- the fixed-model Auto-sparsam implementation plan
- the previous Auto Router experiment record
- any production routing or canonical routing-table decision

## Bound Scope

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
- live call count: exactly `1`
- completion budget change:
  - previous call `max_tokens=250`
  - retry call `max_tokens=500`
- per-call cost cap: `0.0020`

## Pre-Call Cost Gate

Sanitized payload estimate:

- estimated prompt tokens: `607`
- retry max completion tokens: `500`

Conservative ceiling price still uses the most expensive allowed model from the local price inventory:

- `minimax/minimax-m3`
- input: `$0.30 / 1M`
- output: `$1.20 / 1M`

Retry estimate:

- `(607 * 0.30 / 1,000,000) + (500 * 1.20 / 1,000,000)`
- `0.0007821`

Gate:

- `0.0007821 <= 0.0020`: PASS
- if the estimate had exceeded `0.0020`, the retry would stop before the live call

## Capture Requirements

Persist through the file-first wrapper:

- `request_body.json`
- `response_body.json`
- `response_headers.txt`
- `response_summary.json`
- `stdout.log`
- `stderr.log`
- `exit_code.txt`

Required summary fields for this retry:

- `generation_id`
- selected routed model
- `finish_reason`
- `usage`
- `actual_or_cost`

## Acceptance Rules

Accepted retry telemetry may be written only if:

- exactly one live call was attempted
- `response_body.json` parses
- `response_summary.json` contains `generation_id`
- `response_summary.json` contains selected routed model
- `response_summary.json` contains `finish_reason`
- `response_summary.json` contains usage and actual cost
- actual cost is `<= 0.0020`
- `finish_reason != length`
- `health_snapshot.py --or-telemetry-jsonl` ingests the retry telemetry row

## Comparison Targets

The result note must compare the retry against:

- fixed baseline:
  - `qwen/qwen3.5-flash-02-23`
  - actual cost `0.00060359`
- first Auto Router experiment:
  - selected routed model `openai/gpt-oss-120b`
  - actual cost `0.00040905`
  - `finish_reason=length`

## Boundary Reminder

- no production routing
- no canonical routing-table update
- no global OR approval
- no `DOC-SKILL-011` run
- no `DOC-SKILL-012` start
- no `5.4` candidate continuation
- no silent replacement of the fixed-model Auto-sparsam plan
