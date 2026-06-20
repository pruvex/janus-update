# GPT-5.4 Documentation Skill 5-Model Batch Result - 2026-06-14

Status: BOUNDED LIVE EVIDENCE / NON-PRODUCTION / NO CANONICAL ROUTING-TABLE UPDATE

## Scope

Approved bounded comparison batch:

- `DOC-SKILL-002`
- `DOC-SKILL-006`
- `DOC-SKILL-008`

Candidate pool:

- `qwen/qwen3.5-flash-02-23`
- `deepseek/deepseek-v4-flash`
- `z-ai/glm-5-turbo`
- `moonshotai/kimi-k2.6`
- `openai/gpt-5.3-codex`

## Batch Outcome

| metric | value |
| --- | --- |
| workflow_id | `GPT54-DOC-SKILL-5MODEL-BATCH-001` |
| telemetry rows | `15` |
| accepted local postcheck rows | `4` |
| failed local postcheck rows | `11` |
| total actual cost | `0.05343850` |
| total estimated cost | `0.18909900` |
| models seen | `qwen/qwen3.5-flash-02-23`, `deepseek/deepseek-v4-flash`, `z-ai/glm-5-turbo`, `moonshotai/kimi-k2.6`, `openai/gpt-5.3-codex` |
| fallback_count | `0` |
| validation_result_counts | `PASS=4`, `FAIL=11` |
| recommendation_signal_counts | `OR_PREFERRED=4`, `MANUAL_REVIEW=11` |

## Per-Row Summary

| skill_id | model | validation_result | recommendation_signal | actual_cost | notes |
| --- | --- | --- | --- | ---: | --- |
| `DOC-SKILL-002` | `qwen/qwen3.5-flash-02-23` | `FAIL` | `MANUAL_REVIEW` | `0.00070681` | kept the main boundaries but still missed the exact `no global OpenRouter approval exists` phrase |
| `DOC-SKILL-002` | `deepseek/deepseek-v4-flash` | `FAIL` | `MANUAL_REVIEW` | `0.00027006` | same boundary miss as Qwen, but cheaper |
| `DOC-SKILL-002` | `z-ai/glm-5-turbo` | `FAIL` | `MANUAL_REVIEW` | `0.00316920` | same boundary miss with materially higher spend |
| `DOC-SKILL-002` | `moonshotai/kimi-k2.6` | `FAIL` | `MANUAL_REVIEW` | `0.01149026` | same boundary miss with the highest spend in this skill |
| `DOC-SKILL-002` | `openai/gpt-5.3-codex` | `FAIL` | `MANUAL_REVIEW` | `0.01082900` | boundary miss plus no clear next safe step |
| `DOC-SKILL-006` | `qwen/qwen3.5-flash-02-23` | `FAIL` | `MANUAL_REVIEW` | `0.00042029` | missed next-fixture guidance and drifted on blocked-scope wording |
| `DOC-SKILL-006` | `deepseek/deepseek-v4-flash` | `FAIL` | `MANUAL_REVIEW` | `0.00024710` | same formatting/governance drift as Qwen, at lower cost |
| `DOC-SKILL-006` | `z-ai/glm-5-turbo` | `FAIL` | `MANUAL_REVIEW` | `0.00264360` | same drift, with no acceptance upside |
| `DOC-SKILL-006` | `moonshotai/kimi-k2.6` | `FAIL` | `MANUAL_REVIEW` | `0.00546405` | `finish_reason=length`; response body captured but `assistant.content` was missing, so the row stayed postcheck-failed |
| `DOC-SKILL-006` | `openai/gpt-5.3-codex` | `FAIL` | `MANUAL_REVIEW` | `0.00588175` | same blocked-scope and operator-reminder drift |
| `DOC-SKILL-008` | `qwen/qwen3.5-flash-02-23` | `FAIL` | `MANUAL_REVIEW` | `0.00064019` | preserved the factual caveats but missed the required changelog tone |
| `DOC-SKILL-008` | `deepseek/deepseek-v4-flash` | `PASS` | `OR_PREFERRED` | `0.00009690` | cheapest accepted row in the whole batch and fully passed the local postcheck |
| `DOC-SKILL-008` | `z-ai/glm-5-turbo` | `PASS` | `OR_PREFERRED` | `0.00230400` | passed, but much pricier than DeepSeek |
| `DOC-SKILL-008` | `moonshotai/kimi-k2.6` | `PASS` | `OR_PREFERRED` | `0.00449780` | passed, but spend is high relative to the same skill on other passing candidates |
| `DOC-SKILL-008` | `openai/gpt-5.3-codex` | `PASS` | `OR_PREFERRED` | `0.00477750` | passed, but also significantly costlier than DeepSeek |

## Healthcheck Ingestion

Accepted telemetry file:

- `documentation/codex/model-routing/or_healthcheck_telemetry_gpt54_5model_batch_2026-06-14.jsonl`

`health_snapshot.py --or-telemetry-jsonl` ingestion passed on the batch file and reported:

- `record_count=15`
- `models_seen=5`
- `skills_seen=3`
- `actual_cost_total=0.05343850`
- `validation_result_counts={'FAIL': 11, 'PASS': 4}`
- `recommendation_signal_counts={'MANUAL_REVIEW': 11, 'OR_PREFERRED': 4}`

## Batch Decision

This batch still does not justify broad `5.4` OR rollout.

What it does support:

- strong negative evidence for `DOC-SKILL-006`
- still-negative evidence for `DOC-SKILL-002` across all five tested families
- the first broad positive multi-family signal for `DOC-SKILL-008`, with `deepseek/deepseek-v4-flash` as the strongest cost-quality candidate

## Boundaries

- no production routing was enabled
- no canonical routing-table update was made
- no global OR approval was created
- Auto Router was not used
- fixed-model mini Auto-sparsam remains unchanged
