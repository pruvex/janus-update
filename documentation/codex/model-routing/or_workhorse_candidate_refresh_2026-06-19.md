# OR Workhorse Candidate Refresh - 2026-06-19

Status: PLANNING / CANDIDATE REFRESH ONLY / NO LIVE EVALS / NO PRODUCTION ROUTING / NO CANONICAL ROUTING-TABLE UPDATE

## Purpose

Refresh the next OpenRouter candidate pool for bounded Janus workhorse delegation after the first direct-OR evidence on `quickchange_patch_review` and the first negative live evidence on `execution_patch_candidate`.

This note exists because the earlier candidate focus was too narrow. The next pass should explicitly include stronger modern coding families, especially `Qwen`, `Kimi`, `DeepSeek`, `GLM`, and `GPT-5.3-Codex`, instead of over-learning from `gpt-oss-*` alone.

## Direct Answer To The Current Question

Yes:

- `openai/gpt-5.3-codex` is a valid OpenRouter candidate for our bounded OR worker path.
- A Qwen candidate should be in the next serious test pool.
- In fact, more than one Qwen row is justified now.

## Bound Inputs

Local evidence and inventories:

- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/model-routing/gpt54_or_candidate_family_shortlist_v2_2026-06-14.md`
- `documentation/codex/model-routing/gpt54_doc_skill_5model_batch_classification_2026-06-14.md`
- `documentation/codex/model-routing/direct_or_execution_patch_candidate_live_retry_result_2026-06-19.md`
- `documentation/codex/model-routing/quickchange_direct_or_live_retry_result_2026-06-19.md`
- `documentation/codex/openrouter-delegation/model_price_inventory_2026-06-12.json`

Current external discovery sources:

- [OpenRouter: GPT-5.3-Codex](https://openrouter.ai/openai/gpt-5.3-codex)
- [OpenRouter: Qwen3 Coder Flash](https://openrouter.ai/qwen/qwen3-coder-flash)
- [OpenRouter: Qwen3 Coder](https://openrouter.ai/qwen/qwen3-coder)
- [OpenRouter: Kimi K2.6](https://openrouter.ai/moonshotai/kimi-k2.6)
- [OpenRouter: Kimi K2.7 Code](https://openrouter.ai/moonshotai/kimi-k2.7-code)
- [OpenRouter: DeepSeek V4 Flash](https://openrouter.ai/deepseek/deepseek-v4-flash)
- [OpenRouter: DeepSeek V4 Pro](https://openrouter.ai/deepseek/deepseek-v4-pro)
- [OpenRouter: GLM 5.1](https://openrouter.ai/z-ai/glm-5.1)
- [OpenRouter: MiniMax M3](https://openrouter.ai/minimax/minimax-m3)
- [Artificial Analysis changelog](https://artificialanalysis.ai/changelog)

## What Changed Since The Earlier Shortlist

The current market picture is broader than the first narrowed Janus pool:

- `Qwen3 Coder Flash` is now a clear low-cost coding-first candidate, not just a side note.
- `Qwen3 Coder` is a realistic heavier candidate for patch-candidate work where better coding reliability may justify a moderate price increase.
- `Kimi K2.7 Code` now exists and should be treated as a real coding-family row rather than folding everything into `Kimi K2.6`.
- `DeepSeek V4 Flash` and `DeepSeek V4 Pro` remain strong coding candidates and should stay in the serious pool.
- `GLM 5.1` has become harder to ignore for long-horizon engineering tasks.
- `GPT-5.3-Codex` is expensive relative to the cheapest workers, but still materially below `GPT-5.4` and directly relevant as a coding-oriented OpenAI-family comparison row.

## Local Inventory Confirmation

The local OpenRouter inventory already contains these relevant rows:

- `openai/gpt-5.3-codex`
- `qwen/qwen3-coder-flash`
- `qwen/qwen3-coder`
- `qwen/qwen3-coder-30b-a3b-instruct`
- `moonshotai/kimi-k2.6`
- `moonshotai/kimi-k2.7-code`
- `deepseek/deepseek-v4-flash`
- `deepseek/deepseek-v4-pro`
- `z-ai/glm-5.1`
- `z-ai/glm-5-turbo`
- `minimax/minimax-m3`

Inference from the inventory and current model pages:

- we do not need to wait for catalog availability before planning the next batch
- the real gating issue is now task fit and capture/validation quality, not discovery

## Candidate Tiers

### Tier A: Immediate Next-Test Pool

Use these first for the next bounded comparison passes:

| model | why it belongs now | best first use |
| --- | --- | --- |
| `qwen/qwen3-coder-flash` | strong coding focus and low price; best new cheap Qwen row | `quickchange_patch_review`, `DOC-SKILL-008`, first larger advisory diffs |
| `deepseek/deepseek-v4-flash` | already looked promising in prior `5.4` doc-skill evidence and is still low-cost | `DOC-SKILL-008`, `execution_patch_candidate` advisory retry family |
| `moonshotai/kimi-k2.6` | still a serious long-horizon coding candidate and good family-coverage row | `execution_patch_candidate`, tougher docs-assist rows |
| `z-ai/glm-5.1` | strong engineering-oriented positioning for longer bounded tasks | `execution_patch_candidate`, bounded debug/test-review later |
| `openai/gpt-5.3-codex` | direct OpenAI-family coding comparator below `GPT-5.4` | one controlled comparison on a harder bounded task |

### Tier B: Expansion Pool

Use only after Tier A evidence is in:

| model | why it stays secondary |
| --- | --- |
| `qwen/qwen3-coder` | likely stronger than Flash, but more suitable after the cheaper Flash row is tested first |
| `moonshotai/kimi-k2.7-code` | high-interest coding row, but newer and should follow one simpler Kimi control first |
| `deepseek/deepseek-v4-pro` | stronger but likely less price-efficient than Flash for the first pass |
| `z-ai/glm-5-turbo` | valid, but `GLM 5.1` is the more interesting first comparison |
| `qwen/qwen3-coder-plus` | valid premium Qwen row, but not the first price-saving probe |

### Tier H: Hold / Caution

| model | current caution |
| --- | --- |
| `minimax/minimax-m3` | local inventory still carries a prior `HOLD` note about schema projection/provider compatibility |
| `openai/gpt-oss-20b` | keep for narrow quickchange-style work, but current live evidence is negative for `execution_patch_candidate` on the present provider path |
| `openai/gpt-oss-120b` | still valid for some bounded comparisons, but no longer the default “stronger cheap coding” assumption |

## Recommended Mapping By Task Class

### `quickchange_patch_review`

Recommended first pool:

1. `qwen/qwen3-coder-flash`
2. `deepseek/deepseek-v4-flash`
3. `openai/gpt-oss-20b`
4. `openai/gpt-5.3-codex`

Reason:

- this class already has one live OR success, so it is the cheapest place to compare families quickly
- `qwen/qwen3-coder-flash` is the best current cheap challenger for this class

### `DOC-SKILL-002`, `DOC-SKILL-006`, `DOC-SKILL-008`

Recommended next fixed-model pool:

1. `deepseek/deepseek-v4-flash`
2. `qwen/qwen3-coder-flash`
3. `moonshotai/kimi-k2.6`
4. `openai/gpt-5.3-codex`
5. `z-ai/glm-5.1`

Reason:

- this corrects the earlier underrepresentation of current strong coding/document families
- it keeps one OpenAI-family comparator in scope without letting OpenAI rows dominate the whole pool again

### `execution_patch_candidate`

Recommended first replacement pool after the current `gpt-oss-20b` negative evidence:

1. `qwen/qwen3-coder-flash`
2. `deepseek/deepseek-v4-flash`
3. `moonshotai/kimi-k2.6`
4. `z-ai/glm-5.1`
5. `openai/gpt-5.3-codex`

Reason:

- we now need a materially different family test, not another near-repeat of the current negative row
- this pool spans cheap flash, strong open coding, longer-horizon engineering, and one premium OpenAI-family comparator

## Recommended Next Batch Shape

Do not jump into a huge blind sweep.

Use a controlled family-first ladder:

1. one `quickchange_patch_review` comparison with `qwen/qwen3-coder-flash`
2. one `execution_patch_candidate` retry family with `qwen/qwen3-coder-flash`
3. one `execution_patch_candidate` comparison with `deepseek/deepseek-v4-flash`
4. one `DOC-SKILL-008` fixed-model comparison with `deepseek/deepseek-v4-flash`
5. review evidence before spending on `gpt-5.3-codex` or `kimi-k2.7-code`

## Non-Goals

- no live OR calls in this refresh note
- no production routing
- no canonical routing-table update
- no global OR approval
- no silent replacement of the fixed-model Auto-sparsam path
- no assumption that current model-page claims override Janus local validation

## Decision Summary

The next serious OR candidate pool should no longer be anchored on `gpt-oss-*` plus one or two legacy rows.

The strongest next bounded family set is:

- `qwen/qwen3-coder-flash`
- `deepseek/deepseek-v4-flash`
- `moonshotai/kimi-k2.6`
- `z-ai/glm-5.1`
- `openai/gpt-5.3-codex`

That means your instinct was right:

- `gpt-5.3-codex` belongs in the candidate set
- at least one Qwen row belongs in the candidate set
- realistically, Qwen should be one of the first families we test next
