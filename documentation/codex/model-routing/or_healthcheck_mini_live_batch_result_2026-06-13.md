# OR Healthcheck Mini Live Batch Result - 2026-06-13

Status: BOUNDED LIVE EVIDENCE / FILE-FIRST CAPTURE / NO PRODUCTION ROUTING / NO CANONICAL ROUTING-TABLE UPDATE / NO 5.4 CANDIDATE CONTINUATION

## Scope

- batch id: `OR-BATCH-2026-06-13-MINI-LIVE-001`
- approved call limit: `3`
- executed call count: `3`
- accepted call count: `3`
- per-call cap: `0.0020`
- total batch cap: `0.0060`
- accepted telemetry file:
  - `documentation/codex/model-routing/or_healthcheck_telemetry_mini_live_batch_2026-06-13.jsonl`

## Per-Call Result

### DOC-SKILL-009

- selected OR model: `qwen/qwen3.5-flash-02-23`
- run directory:
  - `documentation/codex/model-routing/smoke-test-capture/mini-batch-2026-06-13-live-001/doc-skill-009-qwen-qwen3.5-flash-02-23`
- response summary model: `qwen/qwen3.5-flash-20260224`
- generation id: `gen-1781367395-YQQrf0d1hvvseX3GdTvZ`
- estimated OR cost: `0.000392015`
- actual OR cost: `0.00080743`
- estimation error percent: `105.97`
- latency proxy: `14166 ms`
- acceptance result: PASS

### DOC-SKILL-010

- selected OR model: `qwen/qwen3.5-flash-02-23`
- run directory:
  - `documentation/codex/model-routing/smoke-test-capture/mini-batch-2026-06-13-live-001/doc-skill-010-qwen-qwen3.5-flash-02-23`
- response summary model: `qwen/qwen3.5-flash-20260224`
- generation id: `gen-1781367409-JQV3j86xU0hNeMfgM9zR`
- estimated OR cost: `0.00039156`
- actual OR cost: `0.00060359`
- estimation error percent: `54.15`
- latency proxy: `9766 ms`
- acceptance result: PASS

### DOC-SKILL-006

- selected OR model: `openai/gpt-oss-120b`
- run directory:
  - `documentation/codex/model-routing/smoke-test-capture/mini-batch-2026-06-13-live-001/doc-skill-006-openai-gpt-oss-120b`
- response summary model: `openai/gpt-oss-120b`
- generation id: `gen-1781367419-y2bx6pp9gPO1Zk8KjGhz`
- estimated OR cost: `0.000260148`
- actual OR cost: `0.000044079`
- estimation error percent: `-83.06`
- latency proxy: `14966 ms`
- acceptance result: PASS

## Batch Healthcheck Summary

Healthcheck command:

```powershell
python C:\KI\Janus-Projekt\documentation\codex\skills\janus-health-check\scripts\health_snapshot.py --repo C:\KI\Janus-Projekt --mode DAILY --or-telemetry-jsonl documentation/codex/model-routing/or_healthcheck_telemetry_mini_live_batch_2026-06-13.jsonl
```

Returned OR summary:

- `record_count=3`
- `models_seen=["openai/gpt-oss-120b","qwen/qwen3.5-flash-02-23"]`
- `skills_seen=["DOC-SKILL-006","DOC-SKILL-009","DOC-SKILL-010"]`
- `estimated_cost_total=0.00104372`
- `actual_cost_total=0.0014551`
- `confidence_average=55.0`
- `fallback_count=0`
- `validation_result_counts={"PASS": 3}`
- `recommendation_signal_counts={"OR_PREFERRED": 3}`

## Validation

- call count <= `3`: PASS
- each call actual cost <= `0.0020`: PASS
- total actual cost `0.0014551` <= `0.0060`: PASS
- each accepted row has response body, `generation_id`, usage, actual cost, and `validation_result=PASS`: PASS
- `health_snapshot.py` ingests the batch telemetry file: PASS
- production routing activation: NOT DONE
- canonical routing-table update: NOT DONE
- `DOC-SKILL-011` run: NOT DONE
- `DOC-SKILL-012` start: NOT DONE
- separate `5.4` candidate continuation: NOT DONE

## Boundary Notes

- This batch adds bounded local live telemetry evidence only.
- It does not create a global OR approval.
- It does not activate production routing.
- It does not update the canonical routing table.
- The mini matrix counts remain `OR_CONFIRMED=7`, `NEEDS_STRONGER_TEST=0`, `OR_REJECTED=0` unless a separate explicit review updates evidence status.
