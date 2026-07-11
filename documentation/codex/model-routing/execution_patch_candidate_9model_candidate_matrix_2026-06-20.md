# Execution Patch Candidate 9-Model Candidate Matrix - 2026-06-20

Status: CANDIDATE MATRIX / BATCH-PLANNING ONLY / NO LIVE OR CALL / NO PRODUCTION ROUTING / NO CANONICAL ROUTING-TABLE UPDATE

## Purpose

This matrix defines the candidate set for the next serious OR comparison phase on the larger real task class:

- `execution_patch_candidate`

The goal is not to optimize for the cheapest token list price alone.
The goal is to find models with the best real task economics:

- clean contract completion
- low fallback / retry rate
- acceptable latency
- acceptable review quality
- acceptable total cost per completed bounded task

## Candidate Selection Rule

Candidates were selected with this priority order:

1. fit for larger coding / agentic / long-horizon execution work
2. likely ability to stay inside bounded patch-candidate contracts
3. realistic cost-performance tradeoff for real proposal-first execution tasks
4. provider-family diversity

The matrix intentionally mixes:

- efficiency candidates
- stronger quality candidates
- explicit coding-specialist candidates

## Candidate Matrix

| family | model_slug | role | why included | current status before batch |
| --- | --- | --- | --- | --- |
| `DeepSeek` | `deepseek/deepseek-v4-flash` | baseline efficiency candidate | accepted larger-class evidence already exists; very strong cost-efficiency profile | `BASELINE_ACCEPTED` |
| `DeepSeek` | `deepseek/deepseek-v4-pro` | stronger DeepSeek quality challenger | same family, stronger capability profile for difficult bounded engineering tasks | `UNTESTED_FOR_THIS_CLASS` |
| `Kimi` | `moonshotai/kimi-k2.6` | generalist Kimi long-horizon challenger | explicitly positioned for long-horizon coding and multi-agent orchestration | `UNTESTED_FOR_THIS_CLASS` |
| `Kimi` | `moonshotai/kimi-k2.7-code` | coding-focused Kimi challenger | explicit code-specialist Kimi variant with long-context coding focus | `UNTESTED_FOR_THIS_CLASS` |
| `Qwen` | `qwen/qwen3.7-plus` | price-conscious stronger Qwen challenger | coding/tool-use capable Qwen candidate with lower cost than top-tier Qwen | `UNTESTED_FOR_THIS_CLASS` |
| `Qwen` | `qwen/qwen3-max` | stronger Qwen quality challenger | stronger reasoning/coding Qwen option for bounded execution tasks | `UNTESTED_FOR_THIS_CLASS` |
| `GLM` | `z-ai/glm-5.2` | long-horizon GLM challenger | explicitly targeted at project-level software engineering and long-horizon workflows | `UNTESTED_FOR_THIS_CLASS` |
| `GLM` | `z-ai/glm-5` | stronger GLM engineering challenger | strong coding and system-construction profile, useful for harder proposal-first tasks | `UNTESTED_FOR_THIS_CLASS` |
| `Codex-family reference` | `openai/gpt-5.3-codex` | premium reference candidate | useful control reference for whether cheaper OR candidates truly save cost without collapsing quality | `UNTESTED_FOR_THIS_CLASS` |

## Excluded For Now

### `qwen/qwen3-coder-flash`

Excluded from the next clean batch start because:

- current live evidence on this class is negative
- the model drifted into multi-item patch output
- it overshot the estimate heavily
- it should be revisited only after a Qwen-specific contract hardening pass

### write-capable lanes

Not part of this matrix:

- `execution_write_apply_candidate`

Reason:

- that lane is still not live-approved
- proposal-first comparison must remain separate from live write delegation

## Recommended Batch Order

The batch should not start with all nine live calls at once.
The safer and more interpretable order is:

### Wave 1 - core signal

1. `deepseek/deepseek-v4-flash`
2. `openai/gpt-5.3-codex`
3. `openai/gpt-oss-120b` if retained as an optional non-matrix comparison reference, otherwise skip
4. `z-ai/glm-5.2`

Reason:

- establish baseline
- establish premium control reference
- establish first strong non-DeepSeek challenger

### Wave 2 - high-upside challengers

5. `moonshotai/kimi-k2.6`
6. `qwen/qwen3.7-plus`
7. `z-ai/glm-5`

Reason:

- these are plausible workhorse challengers with strong larger-task positioning

### Wave 3 - stronger / more expensive stretch challengers

8. `deepseek/deepseek-v4-pro`
9. `moonshotai/kimi-k2.7-code`
10. `qwen/qwen3-max`

Reason:

- these are more likely to win on quality than on raw token price
- they are best interpreted after earlier waves establish the cheaper baseline behavior

## Required Constant Test Shape

For the batch to be meaningful, each candidate in a given wave must use:

- same task class:
  - `execution_patch_candidate`
- same slice family:
  - `BACKLOG-108`
- same input package:
  - `documentation/codex/model-routing/execution-review-fixtures/backlog_108_execution_patch_candidate_input_package_2026-06-19.json`
- same bounded ownership rule:
  - Codex remains review / apply-or-reject / validation owner
- same telemetry capture path:
  - file-first artifacts
- same healthcheck ingestion rule:
  - required after accepted telemetry row creation

## Evaluation Table Schema

The final comparison output should be shown as a real table with at least these columns:

| model_slug | family | finish_reason | validation_result | final_outcome | generation_id_present | usage_present | actual_cost_usd | estimated_cost_usd | estimation_error_percent | latency_ms | changed_files_count | contract_cleanliness | codex_reviewability | fallback_used | recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Human Review Notes Per Run

Each model row should also capture a short human review note answering:

- did the model stay inside the one bounded patch-candidate contract?
- did the diff look locally reviewable?
- did the model widen scope?
- did the output need obvious rescue by Codex?

Recommended qualitative grading:

- `A = clean bounded patch candidate`
- `B = usable but noisy`
- `C = contract drift or expensive rescue`
- `D = reject / fallback`

## Primary Decision Metrics

The batch should be judged in this order:

1. `validation_result`
2. `finish_reason`
3. `contract_cleanliness`
4. `codex_reviewability`
5. `actual_cost_usd`
6. `latency_ms`

This means:

- a cheaper model is not better if it repeatedly fails the contract
- a more expensive model can still win if it produces a much cleaner accepted patch candidate with fewer retries

## Expected Output After Batch

After the batch, the result note should answer:

1. Which model is the best `cost-to-clean-completion` candidate?
2. Which model is the best `quality-first` candidate?
3. Which model should become the working baseline for the next larger-class OR phase?
4. Which providers should be dropped from further testing on this class?

## Working Decision

Use this 9-model matrix as the candidate source for the next larger-class OR comparison phase.

Do not yet execute the full batch without explicit approval.
Do not mix this batch with write-capable live delegation.
Do not reopen mini documentation routing decisions inside this phase.

## Boundary Reminder

- no live OR call in this matrix step
- no production routing
- no canonical routing-table update
- no global OR approval
- Codex remains validation and apply/reject owner
