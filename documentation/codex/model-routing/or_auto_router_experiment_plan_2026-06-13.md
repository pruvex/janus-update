# OpenRouter Auto Router Experiment Plan - 2026-06-13

Status: SINGLE-CALL EXPERIMENT / BOUNDED AUTO-SPARSAM VARIANT / NO PRODUCTION ROUTING / NO CANONICAL ROUTING-TABLE UPDATE

## Purpose

Run one isolated Auto Router experiment for an already live-evidenced mini documentation skill without changing the fixed-model Auto-sparsam plan.

This experiment is separate from:

- the fixed selected-model Auto-sparsam implementation plan
- any production routing activation
- any canonical routing-table update
- any global OR approval
- any separate `5.4` candidate continuation

## Bound Scope

- skill: `DOC-SKILL-010`
- task: Prepare Non-Binding Review Notes
- router model: `openrouter/auto`
- plugin id: `auto-router`
- allowed models:
  - `openai/gpt-oss-20b`
  - `openai/gpt-oss-120b`
  - `qwen/qwen3.5-flash-02-23`
  - `minimax/minimax-m3`
  - `nvidia/nemotron-3-nano-30b-a3b`
- `cost_quality_tradeoff`: `8`
- call limit: exactly `1` live call
- single-call cost cap: `0.0020`

## Official Auto Router Notes

Reference used for this experiment:

- OpenRouter Auto Router documentation:
  - `openrouter/auto` selects a model from a curated set
  - `plugins[].allowed_models` can constrain the model pool
  - `plugins[].cost_quality_tradeoff` accepts `0..10`
  - pricing is the standard rate of the selected model

This experiment uses those controls only inside one bounded non-production call.

## Pre-Call Estimate

Sanitized `DOC-SKILL-010` payload estimate:

- estimated prompt tokens: `607`
- planned max completion tokens: `250`
- worst-case allowed-model price ceiling from the local price inventory:
  - `minimax/minimax-m3`
  - input: `$0.30 / 1M`
  - output: `$1.20 / 1M`
- conservative estimated OR cost:
  - `(607 * 0.30 / 1,000,000) + (250 * 1.20 / 1,000,000)`
  - `0.0004821`

Gate:

- `0.0004821 <= 0.0020`: PASS
- if the estimate had exceeded `0.0020`, the experiment would stop before the live call

## Wrapper And Capture Path

Use the existing file-first wrapper unchanged:

- `documentation/codex/model-routing/scripts/or_file_first_capture_wrapper.ps1`

Reason:

- the wrapper already posts an arbitrary JSON request body
- Auto Router plugin controls live inside the request body
- no wrapper patch is required for `openrouter/auto`

## Required Artifacts

The live run must persist:

- `request_body.json`
- `response_body.json`
- `response_headers.txt`
- `response_summary.json`
- `stdout.log`
- `stderr.log`
- `exit_code.txt`

## Experiment Telemetry Requirements

Only write the experiment telemetry row if all of these pass:

- exactly one live call was attempted
- `response_body.json` parses
- `response_summary.json` contains:
  - `generation_id`
  - selected routed model from `model`
  - usage
- actual cost is available from usage
- actual cost is `<= 0.0020`
- `health_snapshot.py --or-telemetry-jsonl` ingests the row

The telemetry row should also capture:

- the Auto Router request model `openrouter/auto`
- the selected routed model
- the allowed-model list
- `cost_quality_tradeoff=8`

## Comparison Target

The experiment result must compare against the fixed-model `DOC-SKILL-010` baseline:

- fixed selected model:
  - `qwen/qwen3.5-flash-02-23`
- fixed baseline estimated cost:
  - `0.00039156`
- fixed baseline actual cost:
  - `0.00060359`

## Boundary Reminder

- no production routing
- no canonical routing-table update
- no `DOC-SKILL-011` run
- no `DOC-SKILL-012` start
- no `5.4` candidate continuation
- no silent replacement of the fixed-model Auto-sparsam implementation plan
