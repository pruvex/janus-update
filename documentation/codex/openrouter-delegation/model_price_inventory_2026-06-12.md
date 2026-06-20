# OpenRouter Model Price Inventory - 2026-06-12

Status: READ-ONLY CATALOG INVENTORY / NO PRODUCTION ROUTING

Source: `GET https://openrouter.ai/api/v1/models`. No chat, completion, responses, benchmark, or inference endpoint was called.

Pricing note: negative catalog prices are treated as non-comparable router metadata, and zero-price/free-router entries are held out of production candidate shortlists.

## Reference Prices

| model | input / 1M | cached input / 1M | output / 1M |
| --- | ---: | ---: | ---: |
| GPT-5.4 mini | $0.75 | $0.075 | $4.50 |
| GPT-5.4 | $2.50 | $0.25 | $15.00 |
| GPT-5.5 | $5.00 | $0.50 | $30.00 |

## Summary Counts

- Total models: `338`
- Cheaper than GPT-5.4 mini input: `213`
- Cheaper than GPT-5.4 mini output: `248`
- Cheaper than GPT-5.4 mini both: `212`
- Cheaper than GPT-5.4 both: `283`
- Cheaper than GPT-5.5 both: `305`

## Bucket Counts

- `MINI_REPLACEMENT_CANDIDATE`: `160`
- `DOCS_ASSIST_CANDIDATE`: `248`
- `CODE_REVIEW_ASSIST_CANDIDATE`: `181`
- `LARGE_MODEL_COST_REDUCTION_CANDIDATE`: `243`
- `HOLD_SCHEMA_UNKNOWN`: `67`
- `HOLD_FREE_ONLY`: `26`
- `HOLD_TOO_EXPENSIVE`: `29`
- `HOLD_INSUFFICIENT_FEATURES`: `9`

## Top 10 Cheaper Than GPT-5.4 Mini Structured-Output Candidates

| model | context | input / 1M | output / 1M | profile cost | schema | tools | reasoning | buckets |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| `inclusionai/ling-2.6-flash` | 262144 | $0.0100 | $0.0300 | $0.00005 | yes | yes | no | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, CODE_REVIEW_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |
| `meta-llama/llama-3.1-8b-instruct` | 131072 | $0.0200 | $0.0300 | $0.00008 | yes | yes | no | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, CODE_REVIEW_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |
| `mistralai/mistral-nemo` | 131072 | $0.0200 | $0.0300 | $0.00008 | yes | yes | no | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, CODE_REVIEW_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |
| `sao10k/l3-lunaris-8b` | 8192 | $0.0400 | $0.0500 | $0.00015 | yes | no | no | MINI_REPLACEMENT_CANDIDATE |
| `openai/gpt-oss-20b` | 131072 | $0.0290 | $0.1400 | $0.00016 | yes | yes | yes | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, CODE_REVIEW_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |
| `cohere/command-r7b-12-2024` | 128000 | $0.0375 | $0.1500 | $0.00019 | yes | no | no | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |
| `mistralai/mistral-small-24b-instruct-2501` | 32768 | $0.0500 | $0.0800 | $0.00019 | yes | no | no | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE |
| `google/gemma-3-4b-it` | 131072 | $0.0500 | $0.1000 | $0.00020 | yes | no | no | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |
| `ibm-granite/granite-4.1-8b` | 131072 | $0.0500 | $0.1000 | $0.00020 | yes | yes | no | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, CODE_REVIEW_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |
| `openai/gpt-oss-120b` | 131072 | $0.0390 | $0.1800 | $0.00021 | yes | yes | yes | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, CODE_REVIEW_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |

## Top 10 Cheaper Than GPT-5.4 Large-Model Candidates

| model | context | input / 1M | output / 1M | profile cost | schema | tools | reasoning | buckets |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| `inclusionai/ling-2.6-flash` | 262144 | $0.0100 | $0.0300 | $0.00078 | yes | yes | no | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, CODE_REVIEW_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |
| `meta-llama/llama-3.1-8b-instruct` | 131072 | $0.0200 | $0.0300 | $0.00138 | yes | yes | no | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, CODE_REVIEW_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |
| `mistralai/mistral-nemo` | 131072 | $0.0200 | $0.0300 | $0.00138 | yes | yes | no | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, CODE_REVIEW_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |
| `openai/gpt-oss-20b` | 131072 | $0.0290 | $0.1400 | $0.00258 | yes | yes | yes | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, CODE_REVIEW_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |
| `cohere/command-r7b-12-2024` | 128000 | $0.0375 | $0.1500 | $0.00315 | yes | no | no | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |
| `openai/gpt-oss-120b` | 131072 | $0.0390 | $0.1800 | $0.00342 | yes | yes | yes | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, CODE_REVIEW_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |
| `google/gemma-3-4b-it` | 131072 | $0.0500 | $0.1000 | $0.00360 | yes | no | no | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |
| `ibm-granite/granite-4.1-8b` | 131072 | $0.0500 | $0.1000 | $0.00360 | yes | yes | no | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, CODE_REVIEW_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |
| `arcee-ai/trinity-mini` | 131072 | $0.0450 | $0.1500 | $0.00360 | yes | yes | yes | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, CODE_REVIEW_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |
| `google/gemma-3-12b-it` | 131072 | $0.0500 | $0.1500 | $0.00390 | yes | yes | no | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, CODE_REVIEW_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |

## Top 10 Cheaper Than GPT-5.5 Large-Model Candidates

| model | context | input / 1M | output / 1M | profile cost | schema | tools | reasoning | buckets |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| `inclusionai/ling-2.6-flash` | 262144 | $0.0100 | $0.0300 | $0.00078 | yes | yes | no | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, CODE_REVIEW_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |
| `meta-llama/llama-3.1-8b-instruct` | 131072 | $0.0200 | $0.0300 | $0.00138 | yes | yes | no | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, CODE_REVIEW_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |
| `mistralai/mistral-nemo` | 131072 | $0.0200 | $0.0300 | $0.00138 | yes | yes | no | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, CODE_REVIEW_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |
| `openai/gpt-oss-20b` | 131072 | $0.0290 | $0.1400 | $0.00258 | yes | yes | yes | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, CODE_REVIEW_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |
| `cohere/command-r7b-12-2024` | 128000 | $0.0375 | $0.1500 | $0.00315 | yes | no | no | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |
| `openai/gpt-oss-120b` | 131072 | $0.0390 | $0.1800 | $0.00342 | yes | yes | yes | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, CODE_REVIEW_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |
| `google/gemma-3-4b-it` | 131072 | $0.0500 | $0.1000 | $0.00360 | yes | no | no | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |
| `ibm-granite/granite-4.1-8b` | 131072 | $0.0500 | $0.1000 | $0.00360 | yes | yes | no | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, CODE_REVIEW_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |
| `arcee-ai/trinity-mini` | 131072 | $0.0450 | $0.1500 | $0.00360 | yes | yes | yes | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, CODE_REVIEW_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |
| `google/gemma-3-12b-it` | 131072 | $0.0500 | $0.1500 | $0.00390 | yes | yes | no | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, CODE_REVIEW_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |

## Models Already Tested

- `qwen/qwen3.7-plus`: HOLD: mini retry schema-valid 0/5, mode-correct 4/5; schema_version/findings failures.
- `stepfun/step-3.7-flash`: HOLD: retry 2 schema-valid 5/5, but production-safe 4/5 and mode-correct 4/5.
- `minimax/minimax-m3`: HOLD: schema projection history; provider compatibility needs reviewed follow-up.
- `inclusionai/ring-2.6-1t`: HOLD: prior evidence included ASSIST misclassified as ALLOW, timeout, and missing risk flags.
- `:free` and zero-price models: HOLD/inconclusive for production-style routing: :free, zero-price, and OpenRouter free-router models require separate review and are excluded from candidate shortlists.

## Recommended Next Candidate Shortlist

These are not approved. They are only candidates for no-live fixture preparation after review.

| model | context | input / 1M | output / 1M | profile cost | schema | tools | reasoning | buckets |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| `inclusionai/ling-2.6-flash` | 262144 | $0.0100 | $0.0300 | $0.00005 | yes | yes | no | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, CODE_REVIEW_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |
| `meta-llama/llama-3.1-8b-instruct` | 131072 | $0.0200 | $0.0300 | $0.00008 | yes | yes | no | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, CODE_REVIEW_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |
| `mistralai/mistral-nemo` | 131072 | $0.0200 | $0.0300 | $0.00008 | yes | yes | no | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, CODE_REVIEW_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |
| `sao10k/l3-lunaris-8b` | 8192 | $0.0400 | $0.0500 | $0.00015 | yes | no | no | MINI_REPLACEMENT_CANDIDATE |
| `openai/gpt-oss-20b` | 131072 | $0.0290 | $0.1400 | $0.00016 | yes | yes | yes | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, CODE_REVIEW_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |
| `cohere/command-r7b-12-2024` | 128000 | $0.0375 | $0.1500 | $0.00019 | yes | no | no | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |
| `mistralai/mistral-small-24b-instruct-2501` | 32768 | $0.0500 | $0.0800 | $0.00019 | yes | no | no | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE |
| `google/gemma-3-4b-it` | 131072 | $0.0500 | $0.1000 | $0.00020 | yes | no | no | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |
| `ibm-granite/granite-4.1-8b` | 131072 | $0.0500 | $0.1000 | $0.00020 | yes | yes | no | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, CODE_REVIEW_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |
| `openai/gpt-oss-120b` | 131072 | $0.0390 | $0.1800 | $0.00021 | yes | yes | yes | MINI_REPLACEMENT_CANDIDATE, DOCS_ASSIST_CANDIDATE, CODE_REVIEW_ASSIST_CANDIDATE, LARGE_MODEL_COST_REDUCTION_CANDIDATE |

## Exclusions And Safety Filters

- `:free` models are retained in raw inventory but marked `HOLD_FREE_ONLY` for production-style routing.
- Zero-price and OpenRouter free-router entries are also held out of production candidate shortlists until separately reviewed.
- Negative catalog prices are treated as non-comparable router metadata, not real savings.
- Models without `response_format` or `structured_outputs` are marked `HOLD_SCHEMA_UNKNOWN` for schema-heavy tasks.
- Models without enough effective context for the relevant profile are not promoted into that candidate bucket.
- Models that are not cheaper than GPT-5.5 on both input and output are marked `HOLD_TOO_EXPENSIVE`.
- No catalog metadata result overrides benchmark failures or Janus governance gates.

## Approval Status

No model is approved by this inventory. Production routing remains `UNKNOWN`/disabled and requires separate Codex/User review.
