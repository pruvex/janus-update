# Fixed OR Live 7-Skill Batch Result - 2026-06-14

Status: LIVE BATCH COMPLETE / ALL 7 PASS / NO AUTO ROUTER / NO PRODUCTION ROUTING

## Scope

This batch re-ran the seven live-evidenced mini documentation skills through the normal bounded fixed-OR skill path:

- `DOC-SKILL-001`
- `DOC-SKILL-002`
- `DOC-SKILL-003`
- `DOC-SKILL-006`
- `DOC-SKILL-008`
- `DOC-SKILL-009`
- `DOC-SKILL-010`

Workflow:

- `FIXED-OR-LIVE-BATCH7-001`

Session telemetry:

- `documentation/codex/model-routing/or_healthcheck_telemetry_fixed_or_session_2026-06-13_FIXED-OR-LIVE-BATCH7-001.jsonl`

## Per-Skill Results

| skill_id | or_model | finish_reason | estimated_or_cost | actual_or_cost | validation_result | operator result |
| --- | --- | --- | --- | --- | --- | --- |
| `DOC-SKILL-001` | `openai/gpt-oss-20b` | `stop` | `0.000196101` | `0.000071730` | `PASS` | `Ergebnis: OR erfolgreich (stop)` |
| `DOC-SKILL-002` | `openai/gpt-oss-20b` | `stop` | `0.000207295` | `0.000065170` | `PASS` | `Ergebnis: OR erfolgreich (stop)` |
| `DOC-SKILL-003` | `openai/gpt-oss-20b` | `stop` | `0.000205178` | `0.000053760` | `PASS` | `Ergebnis: OR erfolgreich (stop)` |
| `DOC-SKILL-006` | `openai/gpt-oss-120b` | `stop` | `0.000260148` | `0.000043416` | `PASS` | `Ergebnis: OR erfolgreich (stop)` |
| `DOC-SKILL-008` | `qwen/qwen3.5-flash-02-23` | `stop` | `0.000968500` | `0.000644995` | `PASS` | `Ergebnis: OR erfolgreich (stop)` |
| `DOC-SKILL-009` | `qwen/qwen3.5-flash-02-23` | `stop` | `0.000392015` | `0.000505050` | `PASS` | `Ergebnis: OR erfolgreich (stop)` |
| `DOC-SKILL-010` | `qwen/qwen3.5-flash-02-23` | `stop` | `0.000391560` | `0.000535080` | `PASS` | `Ergebnis: OR erfolgreich (stop)` |

## Cost Summary

- total estimated OR cost: `0.002620797`
- total actual OR cost: `0.001919201`
- aggregate delta vs estimate: `-0.000701596`
- total actual cost remained below the bounded session cap `0.006000000`

## Healthcheck Summary

From the cumulative batch healthcheck summary:

- `record_count=7`
- `models_seen=[openai/gpt-oss-120b, openai/gpt-oss-20b, qwen/qwen3.5-flash-02-23]`
- `skills_seen=[DOC-SKILL-001, DOC-SKILL-002, DOC-SKILL-003, DOC-SKILL-006, DOC-SKILL-008, DOC-SKILL-009, DOC-SKILL-010]`
- `actual_cost_total=0.0019192`
- `fallback_count=0`
- `validation_result_counts={"PASS": 7}`

## Boundary Notes

- This batch confirms bounded live operation of the fixed-OR path for all seven approved mini documentation skills.
- It does not activate production routing.
- It does not update the canonical routing table.
- It does not create a global OR approval outside this bounded workflow layer.
