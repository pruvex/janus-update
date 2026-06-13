# Controlled OR Telemetry Smoke Test Result - 2026-06-13

Status: EXECUTED ONCE / DEBUG EVIDENCE ONLY / NO PRODUCTION ROUTING / NO CANONICAL ROUTING-TABLE UPDATE / NO 5.4 CANDIDATE CONTINUATION

## Scope

- selected skill: `DOC-SKILL-008`
- selected OR model: `qwen/qwen3.5-flash-02-23`
- approved OR call count: `1`
- executed OR call count: `1`
- cost cap: `0.0020`

## Pre-Call Gate

- price snapshot source: `documentation/codex/openrouter-delegation/model_price_inventory_2026-06-12.json`
- price snapshot timestamp: `2026-06-13T17:32:59.4069295+02:00`
- prompt price per 1M tokens: `0.065`
- completion price per 1M tokens: `0.26`
- estimated prompt tokens: `900`
- estimated completion tokens: `3500`
- estimated OR cost: `0.0009685`
- cost estimate confidence: `55%`
- cost estimate sample count: `1`
- pre-call cap check: PASS

## Execution Outcome

- the one approved OR call was attempted exactly once
- no second OR call was made
- the direct shell execution returned no recoverable response body in the captured command output
- `generation_id` could not be recovered from the shell-side smoke-test command
- `response_usage` could not be recovered from the shell-side smoke-test command
- capture-path debug note:
  - `documentation/codex/model-routing/or_healthcheck_smoke_test_capture_debug_2026-06-13.md`

## Telemetry Handling

- debug telemetry row path:
  - `documentation/codex/model-routing/or_healthcheck_telemetry_smoke_test_debug_2026-06-13.jsonl`
- usage source recorded: `fallback_estimate`
- accepted operational telemetry persist: NO
- no-persist rule for accepted telemetry: APPLIED

Fallback basis:

- exact task/model/prompt family was already present in local `DOC-SKILL-008` evidence
- price snapshot remained available locally
- fallback estimate was used only to keep the healthcheck ingestion path testable after the single approved call

## Validation

- OR call count = `1`: PASS
- pre-call cost <= `0.0020`: PASS
- actual response usage/cost capture from `response_usage`: FAIL
- fallback path documented and recorded: PASS
- telemetry JSONL parses: PASS
- `health_snapshot.py` can ingest the debug JSONL row: pending below
- production routing activation: NOT DONE
- canonical routing-table update: NOT DONE
- `DOC-SKILL-011` run: NOT DONE
- `DOC-SKILL-012` start: NOT DONE

## Conclusion

This smoke test executed the single approved OR call but did not complete clean response capture. The resulting JSONL row is retained as debug failure evidence only. It must not be treated as accepted operational telemetry or as any production routing approval.
