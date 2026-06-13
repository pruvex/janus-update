# OpenRouter Auto Router Experiment Result - 2026-06-13

Status: SINGLE-CALL EXPERIMENT COMPLETE / BOUNDED LOCAL EVIDENCE ONLY / NO PRODUCTION ROUTING / NO CANONICAL ROUTING-TABLE UPDATE

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
- live call count: `1`

## Live Call Result

- selected routed model from response: `openai/gpt-oss-120b`
- `generation_id`: `gen-1781372419-fZa4I8hjsSVYiGMd3VFF`
- actual prompt tokens: `633`
- actual completion tokens: `250`
- actual reasoning tokens: `196`
- actual cost: `0.00040905`
- cost cap `0.0020`: PASS

## Capture Validation

- `response_body.json` parse: PASS
- `response_summary.json` contains `generation_id`: PASS
- `response_summary.json` contains selected routed model: PASS
- `response_summary.json` contains usage: PASS
- telemetry JSONL parse: PASS
- `health_snapshot.py --or-telemetry-jsonl` ingestion: PASS

## Healthcheck Summary

- `record_count=1`
- `models_seen=["openai/gpt-oss-120b"]`
- `skills_seen=["DOC-SKILL-010"]`
- `estimated_cost_total=0.0004821`
- `actual_cost_total=0.00040905`
- `confidence_average=35.0`
- `fallback_count=0`
- `validation_result_counts={"PASS": 1}`
- `recommendation_signal_counts={"MANUAL_REVIEW": 1}`

## Comparison To Fixed Baseline

Fixed-model `DOC-SKILL-010` baseline from the accepted live evidence closeout:

- fixed selected model: `qwen/qwen3.5-flash-02-23`
- fixed baseline estimated cost: `0.00039156`
- fixed baseline actual cost: `0.00060359`

Auto Router experiment:

- request model: `openrouter/auto`
- selected routed model: `openai/gpt-oss-120b`
- experiment estimated cost: `0.0004821`
- experiment actual cost: `0.00040905`

Comparison:

- selected routed model differs from the fixed baseline: YES
- Auto Router actual cost was lower than the fixed baseline actual cost by `0.00019454`
- relative cost reduction vs fixed baseline actual cost: `32.23%`
- experiment actual cost stayed below the conservative pre-call estimate by `15.15%`

## Quality Note

The response completed within the single allowed call and the technical capture path passed, but the response finished with `finish_reason=length`. Because the experiment is bounded to exactly one live call, no retry was attempted. The telemetry row therefore records:

- `validation_result=PASS`
- `rework_required=YES`
- `recommendation_signal=MANUAL_REVIEW`

This means the Auto Router experiment succeeded as a bounded routing-and-capture experiment, but it does not justify replacing the fixed-model Auto-sparsam path.

## Boundary Reminder

- this result is bounded local experiment evidence only
- it does not replace the fixed-model Auto-sparsam implementation plan
- it does not activate production routing
- it does not update the canonical routing table
- it does not create any global OR approval
- it does not continue the separate `5.4` candidate phase
