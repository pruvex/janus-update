# Execution Patch Candidate Wave 1 Live Batch Result - 2026-06-20

Status: LIVE BATCH RESULT / BOUNDED TELEMETRY EVIDENCE / NO PRODUCTION ROUTING / NO CANONICAL ROUTING-TABLE UPDATE

## Scope

This note records the approved Wave 1 live comparison batch for the larger real task class:

- `execution_patch_candidate`

Bound slice:

- `BACKLOG-108`
- compact contract family
- Codex remains review / apply-or-reject / validation owner

Approved models executed:

1. `deepseek/deepseek-v4-flash`
2. `openai/gpt-5.3-codex`
3. `z-ai/glm-5.2`

## Aggregate Result

- `deepseek/deepseek-v4-flash`: clean bounded pass
- `openai/gpt-5.3-codex`: request rejected before model execution due schema incompatibility on provider side
- `z-ai/glm-5.2`: completed live response with `finish_reason=length`, no accepted JSON patch candidate, and actual cost above cap

Current Wave 1 winner:

- `deepseek/deepseek-v4-flash`

## Comparison Table

| model_slug | family | finish_reason | validation_result | final_outcome | generation_id_present | usage_present | actual_cost_usd | estimated_cost_usd | estimation_error_percent | latency_ms | changed_files_count | contract_cleanliness | codex_reviewability | fallback_used | recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `deepseek/deepseek-v4-flash` | `DeepSeek` | `stop` | `PASS` | `DIRECT_OR_EXECUTION_PATCH_READY_FOR_CODEX_REVIEW` | `YES` | `YES` | `0.00018936` | `0.00063` | `-69.94` | `27063` | `1` | `A` | `B` | `NO` | `KEEP_AS_BASELINE` |
| `openai/gpt-5.3-codex` | `Codex-family reference` | `N_A` | `FAIL` | `DIRECT_OR_REJECT_AND_FALLBACK` | `NO` | `NO` | `0.00000000` | `0.026775` | `0.00` | `1417` | `0` | `D` | `D` | `YES` | `DROP_UNTIL_SCHEMA_COMPAT_FIXED` |
| `z-ai/glm-5.2` | `GLM` | `length` | `FAIL` | `DIRECT_OR_REJECT_AND_FALLBACK` | `YES` | `YES` | `0.0810794` | `0.00846` | `858.15` | `244060+` | `0` | `D` | `D` | `YES` | `DROP_UNLESS_HIGHER_BUDGET_RETRY_IS_JUSTIFIED` |

## Human Review Notes

### `deepseek/deepseek-v4-flash`

- The run stayed inside the bounded one-result patch-candidate contract.
- File-first capture, `generation_id`, usage, telemetry JSONL, and healthcheck ingestion all completed successfully.
- The proposed diff stayed narrow and reviewable.
- The patch is still not a direct apply recommendation without Codex review:
  - it duplicates `_extract_confirmed_facts` in the patch text
  - it proposes a concrete persistence path that still needs local semantic review

Interpretation:

- strong contract behavior
- very good cost outcome
- usable proposal-first workhorse baseline

### `openai/gpt-5.3-codex`

- This did not fail as a model-quality comparison.
- The request was rejected with `HTTP 400` before usable model output.
- The provider error states that the JSON schema was invalid for this endpoint because `changed_files` was not included in the schema `required` array.

Interpretation:

- no meaningful task-quality evidence yet
- current result is transport / schema compatibility failure evidence
- do not score this as a substantive coding loss against DeepSeek

### `z-ai/glm-5.2`

- The run directory actually contains a completed file-first capture set, including:
  - `response_body.json`
  - `response_summary.json`
  - `patch_candidate_result.json`
  - `validation_summary.json`
  - operator summary and healthcheck summary
- The real result was a completed live response with `finish_reason=length`.
- Usage and cost were captured successfully.
- The returned payload did not yield a parseable bounded JSON patch candidate.
- Actual cost reached `0.0810794` USD, which is above the `execution_patch_candidate` cost cap of `0.05` USD.

Interpretation:

- no transport blocker remains in evidence
- current evidence is a real acceptance failure with cap overrun
- under the current contract this is materially worse than the accepted DeepSeek baseline

## Cost Summary

Known actual spend from completed rows:

- `deepseek/deepseek-v4-flash`: `0.00018936`
- `openai/gpt-5.3-codex`: `0.00000000` captured because no billable completed response payload was returned
- `z-ai/glm-5.2`: `0.0810794`

Known total actual spend with completed evidence only:

- `0.08126876` USD

Known estimated spend across all three planned runs:

- `0.035865` USD

## Time Summary

- fastest terminal result:
  - `openai/gpt-5.3-codex` failed fast at about `1417 ms`
- fastest successful bounded result:
  - `deepseek/deepseek-v4-flash` at `27063 ms`
- slowest technical result:
  - `z-ai/glm-5.2` completed after about `244060+ ms` but still failed acceptance

## Working Decision

After Wave 1:

- keep `deepseek/deepseek-v4-flash` as the current larger-class baseline
- do not count `openai/gpt-5.3-codex` as a quality loser; count it as schema-compatibility failure evidence
- count `z-ai/glm-5.2` as completed live failure evidence under the current contract because it exceeded cap and still failed output acceptance

## Recommended Next Step

Before widening the batch further:

1. decide whether to fix the `gpt-5.3-codex` schema compatibility issue
2. decide whether `z-ai/glm-5.2` deserves any higher-budget retry at all despite the cap overrun and failed output
3. keep `deepseek/deepseek-v4-flash` as the accepted live baseline

## Boundary Reminder

- no production routing
- no canonical routing-table update
- no global OR approval
- no local apply happened from any OR result in this batch
- Codex remains apply/reject and validation owner
