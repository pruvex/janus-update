# GPT-5.4 DOC-SKILL-002 and DOC-SKILL-006 Narrow Retest Result - 2026-06-14

Status: BOUNDED LIVE EVIDENCE / NON-PRODUCTION / NO CANONICAL ROUTING-TABLE UPDATE

## Scope

Approved narrow retest workflow:

- workflow_id: `GPT54-DOC-SKILL-002-006-RETEST-001`
- `DOC-SKILL-002`
- `DOC-SKILL-006`
- `deepseek/deepseek-v4-flash`
- `qwen/qwen3.5-flash-02-23`

Retest intent:

- separate prompt-contract failures from completion-budget failures

## Outcome

| metric | value |
| --- | --- |
| total calls | `4` |
| accepted local postcheck rows | `0` |
| failed local postcheck rows | `4` |
| total estimated cost | `0.00397600` |
| total actual cost | `0.00165697` |
| healthcheck ingestion | `PASS` |
| finish_reason=length rows | `0` |

## Per-Row Summary

| skill_id | model | finish_reason | actual_cost | validation_result | key reason |
| --- | --- | --- | ---: | --- | --- |
| `DOC-SKILL-002` | `deepseek/deepseek-v4-flash` | `stop` | `0.00039529` | `FAIL` | still missed exact `No production routing is approved.` and `No global OpenRouter approval exists.` |
| `DOC-SKILL-002` | `qwen/qwen3.5-flash-02-23` | `stop` | `0.00071019` | `FAIL` | now preserved `No production routing is approved.`, but still missed exact `No global OpenRouter approval exists.` |
| `DOC-SKILL-006` | `deepseek/deepseek-v4-flash` | `stop` | `0.00009870` | `FAIL` | structure held, but still missed `Next safe fixture work`, blocked-scope exactness, and live-call gate preservation |
| `DOC-SKILL-006` | `qwen/qwen3.5-flash-02-23` | `stop` | `0.00045279` | `FAIL` | same failure shape as DeepSeek despite higher completion budget |

## Main Finding

The retest weakens the idea that the earlier failures were mainly caused by too-tight completion caps.

Why:

- all four rows finished with `finish_reason=stop`
- all four rows preserved `generation_id`, usage, and cost
- `DOC-SKILL-006` still failed on structure and governance exactness even after the larger completion budget
- `DOC-SKILL-002` improved slightly on one required boundary, but still could not reliably emit all required exact governance lines

## Interpretation

### DOC-SKILL-002

This looks less like a budget problem and more like a precision problem around one exact governance sentence:

- `No global OpenRouter approval exists.`

The retest did improve one boundary:

- Qwen now preserved `No production routing is approved.`

But that still was not enough for local acceptance.

Result:

- `DOC-SKILL-002` should remain `KEEP_CODEX` for now
- a future retry would need a stricter prompt contract or a different evaluator rule, not just more budget

### DOC-SKILL-006

This looks even less like a budget problem after the retest.

The larger completion budget prevented another `length` failure, but it did not solve:

- missing next-fixture guidance
- blocked-scope exactness misses
- live-call gate preservation misses

Result:

- `DOC-SKILL-006` remains `KEEP_CODEX`
- further OR retesting is low priority unless the task contract itself is redesigned

## Decision Impact

After this retest:

- `DOC-SKILL-002`: still `KEEP_CODEX`
- `DOC-SKILL-006`: still `KEEP_CODEX`
- the strongest remaining positive `5.4` path is still `DOC-SKILL-008`, not these two skills

## Healthcheck

Telemetry file:

- `documentation/codex/model-routing/or_healthcheck_telemetry_gpt54_doc_skill_002_006_retest_2026-06-14.jsonl`

Healthcheck summary:

- `record_count=4`
- `actual_cost_total=0.00165697`
- `validation_result_counts={'FAIL': 4}`
- `recommendation_signal_counts={'MANUAL_REVIEW': 4}`

## Boundaries

- no production routing was enabled
- no canonical routing-table update was made
- no global OR approval was created
- no Auto Router was used
