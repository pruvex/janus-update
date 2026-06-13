# OpenRouter Auto Router 7-Skill Batch Plan - 2026-06-13

Status: APPROVED BOUNDED LIVE BATCH PLAN / EXPERIMENT-ONLY / NO PRODUCTION ROUTING / NO CANONICAL ROUTING-TABLE UPDATE

## Scope

Run at most one live Auto Router call per already live-evidenced mini documentation skill:

- `DOC-SKILL-001`
- `DOC-SKILL-002`
- `DOC-SKILL-003`
- `DOC-SKILL-006`
- `DOC-SKILL-008`
- `DOC-SKILL-009`
- `DOC-SKILL-010`

Request model:

- `openrouter/auto`

Plugin configuration:

- `id=auto-router`
- `allowed_models=[openai/gpt-oss-20b, openai/gpt-oss-120b, qwen/qwen3.5-flash-02-23, minimax/minimax-m3, nvidia/nemotron-3-nano-30b-a3b]`
- `cost_quality_tradeoff=8`

## Execution Rules

- file-first wrapper only:
  - `documentation/codex/model-routing/scripts/or_file_first_capture_wrapper.ps1`
- completion budget:
  - `max_tokens=500`
- one sequential call at a time
- stop the current skill before call if the pre-call estimate exceeds `0.0020`
- stop the whole batch if cumulative accepted actual cost exceeds `0.0140`
- stop the whole batch if any call loses response body, `generation_id`, usage, cost capture, or healthcheck ingestion

## Pre-Call Estimate Rule

Conservative estimate inputs:

- prompt token estimate:
  - reuse the accepted fixed-model mini evidence `estimated_prompt_tokens` for the same skill
- completion token estimate:
  - use `max_tokens * 2` as a conservative reasoning-inclusive billing proxy
- price source:
  - `documentation/codex/openrouter-delegation/model_price_inventory_2026-06-12.json`
- estimate model:
  - use the highest input/output price inside the allowed Auto Router pool as the batch gate ceiling

This keeps the pre-call estimate conservative without assuming which allowed model the router will pick.

## Acceptance Gates

Each accepted row must have:

- parsed `response_body.json`
- parsed `response_summary.json`
- `generation_id`
- selected routed model in `response_summary.json`
- `finish_reason`
- usage block
- actual cost
- `validation_result=PASS`

After each accepted row:

- run `python documentation/codex/skills/janus-health-check/scripts/health_snapshot.py --or-telemetry-jsonl <batch_jsonl>`

## Comparison Targets

Each Auto Router result must be compared against the existing fixed-model live baseline for the same skill:

- fixed baseline selected model
- fixed baseline actual cost
- Auto Router selected model
- Auto Router actual cost
- absolute delta
- percent delta
- finish reason
- validation result
- recommendation signal

## Classification Outputs

Per skill classification must use one of:

- `AUTO_ROUTER_STABLE_CANDIDATE`
- `FURTHER_TEST_CANDIDATE`
- `KEEP_FIXED`
- `MANUAL_REVIEW`

## Boundary Reminder

- fixed-model Auto-sparsam remains canonical
- Auto Router remains experiment-only
- no production routing activation
- no canonical routing-table update
- no global OR approval
- no `DOC-SKILL-011` run
- no `DOC-SKILL-012` start
- no separate `5.4` candidate continuation
