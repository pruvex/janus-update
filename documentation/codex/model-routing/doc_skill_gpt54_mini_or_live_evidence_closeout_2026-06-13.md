# GPT-5.4 Mini OR Live Evidence Closeout - 2026-06-13

Status: LIVE EVIDENCE CLOSEOUT / BOUNDED TELEMETRY ONLY / NO PRODUCTION ROUTING / NO CANONICAL ROUTING-TABLE UPDATE

## Scope

This closeout summarizes the accepted bounded live OR telemetry evidence for the completed `5.4 mini` documentation-skill scope only:

- `DOC-SKILL-001`
- `DOC-SKILL-002`
- `DOC-SKILL-003`
- `DOC-SKILL-006`
- `DOC-SKILL-008`
- `DOC-SKILL-009`
- `DOC-SKILL-010`

It does not create a global OR approval, does not activate production routing, does not update the canonical routing table, does not run `DOC-SKILL-011`, does not start `DOC-SKILL-012`, and does not continue the separate `5.4` candidate phase.

## Accepted Live Telemetry Rows

| skill_id | selected_or_option | telemetry_source | estimated_or_cost | actual_or_cost | estimation_error_percent | generation_id |
| --- | --- | --- | --- | --- | --- | --- |
| `DOC-SKILL-001` | `openai/gpt-oss-20b` | `or_healthcheck_telemetry_mini_live_batch_remaining_2026-06-13.jsonl` | `0.000196101` | `0.00009944` | `-49.29` | `gen-1781368054-6AwL5DuPv325hvLzv8Pd` |
| `DOC-SKILL-002` | `openai/gpt-oss-20b` | `or_healthcheck_telemetry_mini_live_batch_remaining_2026-06-13.jsonl` | `0.000207295` | `0.00009074` | `-56.23` | `gen-1781368060-0IkPKtPP6wutxzFB1PAy` |
| `DOC-SKILL-003` | `openai/gpt-oss-20b` | `or_healthcheck_telemetry_mini_live_batch_remaining_2026-06-13.jsonl` | `0.000205178` | `0.00012419` | `-39.47` | `gen-1781368064-nHzaKzJrguuG67B50I3O` |
| `DOC-SKILL-006` | `openai/gpt-oss-120b` | `or_healthcheck_telemetry_mini_live_batch_2026-06-13.jsonl` | `0.000260148` | `0.000044079` | `-83.06` | `gen-1781367419-y2bx6pp9gPO1Zk8KjGhz` |
| `DOC-SKILL-008` | `qwen/qwen3.5-flash-02-23` | `or_healthcheck_telemetry_smoke_test_live_retry_2026-06-13.jsonl` | `0.0009685` | `0.000570895` | `-41.05` | `gen-1781366532-8Xvtr6Rhfus4G6dlVdfW` |
| `DOC-SKILL-009` | `qwen/qwen3.5-flash-02-23` | `or_healthcheck_telemetry_mini_live_batch_2026-06-13.jsonl` | `0.000392015` | `0.00080743` | `105.97` | `gen-1781367395-YQQrf0d1hvvseX3GdTvZ` |
| `DOC-SKILL-010` | `qwen/qwen3.5-flash-02-23` | `or_healthcheck_telemetry_mini_live_batch_2026-06-13.jsonl` | `0.00039156` | `0.00060359` | `54.15` | `gen-1781367409-JQV3j86xU0hNeMfgM9zR` |

## Cost Summary

- total estimated OR cost across accepted rows: `0.002620797`
- total actual OR cost across accepted rows: `0.002340364`
- aggregate delta vs estimate: `-0.000280433`

Per skill:

- `DOC-SKILL-001`: estimate undershot? NO. Actual was `49.29%` below estimate.
- `DOC-SKILL-002`: estimate undershot? NO. Actual was `56.23%` below estimate.
- `DOC-SKILL-003`: estimate undershot? NO. Actual was `39.47%` below estimate.
- `DOC-SKILL-006`: estimate undershot? NO. Actual was `83.06%` below estimate.
- `DOC-SKILL-008`: estimate undershot? NO. Actual was `41.05%` below estimate.
- `DOC-SKILL-009`: estimate undershot? YES. Actual was `105.97%` above estimate.
- `DOC-SKILL-010`: estimate undershot? YES. Actual was `54.15%` above estimate.

## Healthcheck Evidence

Accepted healthcheck ingestion checkpoints:

- `DOC-SKILL-008` live retry JSONL ingested with `record_count=1`, `fallback_count=0`, `validation_result_counts={"PASS": 1}`
- mini live batch JSONL ingested with `record_count=3`, `fallback_count=0`, `validation_result_counts={"PASS": 3}`
- remaining mini live batch JSONL ingested with `record_count=3`, `fallback_count=0`, `validation_result_counts={"PASS": 3}`

## Debug-Only Exclusion

The first `DOC-SKILL-008` smoke-test row remains explicitly excluded from accepted telemetry:

- debug-only row:
  - `documentation/codex/model-routing/or_healthcheck_telemetry_smoke_test_debug_2026-06-13.jsonl`
- reason:
  - shell-side capture lost response body, `generation_id`, and `response_usage`
- accepted replacement evidence:
  - `documentation/codex/model-routing/or_healthcheck_telemetry_smoke_test_live_retry_2026-06-13.jsonl`

## Boundary Notes

- This closeout records bounded local telemetry evidence only.
- It does not change mini matrix counts, which remain `OR_CONFIRMED=7`, `NEEDS_STRONGER_TEST=0`, `OR_REJECTED=0`.
- It does not convert `real_work_equivalence` from `UNCLEAR` to a global approval state.
- It does not enable production routing.
