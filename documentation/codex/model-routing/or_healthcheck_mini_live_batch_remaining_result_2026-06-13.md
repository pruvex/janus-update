# OR Healthcheck Mini Live Batch Remaining Result - 2026-06-13

Status: BOUNDED LIVE EVIDENCE / FILE-FIRST CAPTURE / NO PRODUCTION ROUTING / NO CANONICAL ROUTING-TABLE UPDATE / NO 5.4 CANDIDATE CONTINUATION

## Scope

- batch id: `OR-BATCH-REMAINING-2026-06-13-MINI-LIVE-001`
- approved call limit: `3`
- executed call count: `3`
- accepted call count: `3`
- per-call cap: `0.0020`
- total batch cap: `0.0060`
- accepted telemetry file:
  - `documentation/codex/model-routing/or_healthcheck_telemetry_mini_live_batch_remaining_2026-06-13.jsonl`

## Per-Call Result

### DOC-SKILL-001

- selected OR model: `openai/gpt-oss-20b`
- run directory:
  - `documentation/codex/model-routing/smoke-test-capture/mini-batch-remaining-2026-06-13-live-001/doc-skill-001-openai-gpt-oss-20b`
- response summary model: `openai/gpt-oss-20b`
- generation id: `gen-1781368054-6AwL5DuPv325hvLzv8Pd`
- estimated OR cost: `0.000196101`
- actual OR cost: `0.00009944`
- estimation error percent: `-49.29`
- latency proxy: `5808 ms`
- acceptance result: PASS

### DOC-SKILL-002

- selected OR model: `openai/gpt-oss-20b`
- run directory:
  - `documentation/codex/model-routing/smoke-test-capture/mini-batch-remaining-2026-06-13-live-001/doc-skill-002-openai-gpt-oss-20b`
- response summary model: `openai/gpt-oss-20b`
- generation id: `gen-1781368060-0IkPKtPP6wutxzFB1PAy`
- estimated OR cost: `0.000207295`
- actual OR cost: `0.00009074`
- estimation error percent: `-56.23`
- latency proxy: `4173 ms`
- acceptance result: PASS

### DOC-SKILL-003

- selected OR model: `openai/gpt-oss-20b`
- run directory:
  - `documentation/codex/model-routing/smoke-test-capture/mini-batch-remaining-2026-06-13-live-001/doc-skill-003-openai-gpt-oss-20b`
- response summary model: `openai/gpt-oss-20b`
- generation id: `gen-1781368064-nHzaKzJrguuG67B50I3O`
- estimated OR cost: `0.000205178`
- actual OR cost: `0.00012419`
- estimation error percent: `-39.47`
- latency proxy: `2328 ms`
- acceptance result: PASS

## Batch Healthcheck Summary

Healthcheck command:

```powershell
python C:\KI\Janus-Projekt\documentation\codex\skills\janus-health-check\scripts\health_snapshot.py --repo C:\KI\Janus-Projekt --mode DAILY --or-telemetry-jsonl documentation/codex/model-routing/or_healthcheck_telemetry_mini_live_batch_remaining_2026-06-13.jsonl
```

Returned OR summary:

- `record_count=3`
- `models_seen=["openai/gpt-oss-20b"]`
- `skills_seen=["DOC-SKILL-001","DOC-SKILL-002","DOC-SKILL-003"]`
- `estimated_cost_total=0.00060857`
- `actual_cost_total=0.00031437`
- `confidence_average=55.0`
- `fallback_count=0`
- `validation_result_counts={"PASS": 3}`
- `recommendation_signal_counts={"OR_PREFERRED": 3}`

## Validation

- call count <= `3`: PASS
- each call actual cost <= `0.0020`: PASS
- total actual cost `0.00031437` <= `0.0060`: PASS
- each accepted row has response body, `generation_id`, usage, actual cost, and `validation_result=PASS`: PASS
- `health_snapshot.py` ingests the remaining-batch telemetry file: PASS
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
