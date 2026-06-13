# OpenRouter Auto Router 7-Skill Batch Result - 2026-06-13

Status: PARTIAL BATCH RESULT / EXPERIMENT-ONLY / NO PRODUCTION ROUTING / NO CANONICAL ROUTING-TABLE UPDATE

## Batch Outcome

- accepted telemetry rows: `1`
- attempted live calls: `2`
- cumulative accepted actual cost: `0.000525`
- batch aborted: `YES`
- abort reason: `DOC-SKILL-002 finished with length`

The batch stayed bounded and stopped early on the first completion-budget failure. Fixed-model Auto-sparsam remains canonical. Auto Router remains experiment-only.

## Per-Skill Comparison

| skill_id | fixed baseline model | fixed baseline actual cost | auto-router selected model | auto-router actual cost | delta absolute | delta percent | finish_reason | validation_result | recommendation_signal | batch status |
| --- | --- | ---: | --- | ---: | ---: | ---: | --- | --- | --- | --- |
| `DOC-SKILL-001` | `openai/gpt-oss-20b` | `0.00009944` | `openai/gpt-oss-120b` | `0.00052500` | `0.00042556` | `427.96%` | `stop` | `PASS` | `CODEX_PREFERRED` | `PASS` |
| `DOC-SKILL-002` | `openai/gpt-oss-20b` | `0.00009074` | `openai/gpt-oss-120b` | `0.00060180` | `n/a` | `n/a` | `length` | `FAIL` | `MANUAL_REVIEW` | `FINISH_REASON_LENGTH` |
| `DOC-SKILL-003` | `openai/gpt-oss-20b` | `0.00012419` | `NOT_RUN` | `0.00000000` | `n/a` | `n/a` | `NOT_RUN` | `NOT_RUN` | `MANUAL_REVIEW` | `BATCH_ABORT_BEFORE_CALL` |
| `DOC-SKILL-006` | `openai/gpt-oss-120b` | `0.00004408` | `NOT_RUN` | `0.00000000` | `n/a` | `n/a` | `NOT_RUN` | `NOT_RUN` | `MANUAL_REVIEW` | `BATCH_ABORT_BEFORE_CALL` |
| `DOC-SKILL-008` | `qwen/qwen3.5-flash-02-23` | `0.00057089` | `NOT_RUN` | `0.00000000` | `n/a` | `n/a` | `NOT_RUN` | `NOT_RUN` | `MANUAL_REVIEW` | `BATCH_ABORT_BEFORE_CALL` |
| `DOC-SKILL-009` | `qwen/qwen3.5-flash-02-23` | `0.00080743` | `NOT_RUN` | `0.00000000` | `n/a` | `n/a` | `NOT_RUN` | `NOT_RUN` | `MANUAL_REVIEW` | `BATCH_ABORT_BEFORE_CALL` |
| `DOC-SKILL-010` | `qwen/qwen3.5-flash-02-23` | `0.00060359` | `NOT_RUN` | `0.00000000` | `n/a` | `n/a` | `NOT_RUN` | `NOT_RUN` | `MANUAL_REVIEW` | `BATCH_ABORT_BEFORE_CALL` |

## Accepted Telemetry Evidence

- accepted row: `DOC-SKILL-001`
- selected routed model: `openai/gpt-oss-120b`
- `generation_id`: `gen-1781374913-piprg74O2tsxkgvDuYCM`
- `finish_reason`: `stop`
- actual cost: `0.00052500`
- healthcheck ingestion: PASS with `record_count=1`

## Failure Edge

- `DOC-SKILL-002` selected `openai/gpt-oss-120b`
- `finish_reason=length` despite the raised `max_tokens=500` budget
- response body, `generation_id`, usage, and actual cost were still captured successfully
- because the completion adequacy gate failed, the batch stopped before `DOC-SKILL-003`, `DOC-SKILL-006`, `DOC-SKILL-008`, `DOC-SKILL-009`, and `DOC-SKILL-010` were attempted

## Healthcheck Summary

- `record_count=1`
- `models_seen=['openai/gpt-oss-120b']`
- `skills_seen=['DOC-SKILL-001']`
- `estimated_cost_total=0.0013425`
- `actual_cost_total=0.000525`
- `validation_result_counts={'PASS': 1}`
- `recommendation_signal_counts={'CODEX_PREFERRED': 1}`

## Boundary Reminder

- fixed-model Auto-sparsam remains canonical
- Auto Router remains experiment-only
- no production routing is activated
- no canonical routing-table update is made
- no global OR approval is created
- no `DOC-SKILL-011` run or `DOC-SKILL-012` start occurred
- no separate `5.4` candidate continuation occurred
