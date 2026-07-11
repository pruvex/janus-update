# Quickchange Fixed OpenRouter Candidate Shortlist - 2026-06-18

Status: PLANNING ONLY / NO LIVE OR CALLS / NO PRODUCTION ROUTING / NO CANONICAL ROUTING-TABLE UPDATE

## Purpose

Define the first fixed-model OpenRouter shortlist for the first everyday bounded worker consumer:

- owning skill: `janus-quickchange`
- bounded classes:
  - `quickchange_patch_review`
  - later `quickchange_write_apply`

This shortlist is optimized for:

1. low token cost
2. strong instruction following on tiny bounded edits
3. tool/agent compatibility for later bounded workflow growth
4. low-risk first live validation before any Auto Router widening

## Current Starting Point

Already finished in local Janus workflow:

- shared bounded OR worker eligibility
- shared `1 = Codex` / `2 = OpenRouter` gate
- Codex-owned accept/reject/fallback normalization
- first everyday consumer integration for `janus-quickchange`

What is still missing:

- fixed model assignment for the first real quickchange live runs
- per-model evidence on real quickchange tasks

## Current Pricing Snapshot

Source date for this shortlist: `2026-06-18`

Reviewed current OpenRouter model pages:

- `openai/gpt-oss-20b`: `$0.029 / $0.14` per 1M
- `openai/gpt-oss-120b`: `$0.039 / $0.18` per 1M
- `qwen/qwen3-30b-a3b-instruct-2507`: `$0.04815 / $0.1931` per 1M
- `qwen/qwen3.5-flash-02-23`: `$0.065 / $0.26` per 1M
- `qwen/qwen3-32b`: `$0.08 / $0.28` per 1M
- `deepseek/deepseek-v4-flash`: `$0.09 / $0.18` per 1M
- `z-ai/glm-4.5-air`: `$0.13 / $0.85` per 1M
- `deepseek/deepseek-v3.2`: `$0.2288 / $0.3432` per 1M
- `minimax/minimax-m3`: `$0.30 / $1.20` per 1M
- `moonshotai/kimi-k2`: `$0.57 / $2.30` per 1M
- `z-ai/glm-4.5`: `$0.60 / $2.20` per 1M`

Interpretation boundary:

- this is pricing metadata only
- this is not quality approval
- this is not production routing evidence

## First-Line Candidate Set

These are the first models that should be tested for `janus-quickchange`.

### Tier A - first real quickchange test corridor

1. `openai/gpt-oss-20b`
2. `openai/gpt-oss-120b`
3. `qwen/qwen3-30b-a3b-instruct-2507`

Why this Tier A set:

- all three are still very cheap
- all three are positioned for instruction following, tool use, or agentic work
- none of them carries the immediate price penalty of Kimi, MiniMax, or full GLM flagships
- they cover two families instead of overfitting to one provider

### Tier B - cheap but second-wave candidates

4. `qwen/qwen3.5-flash-02-23`
5. `deepseek/deepseek-v4-flash`

Why Tier B stays second:

- both are still reasonably cheap
- both already produced useful evidence in earlier documentation-skill work
- but the current price edge is weaker than the new Tier A trio

## Hold / Not First-Line

These models should not be in the first quickchange batch.

### `minimax/minimax-m3`

Hold reason:

- much more expensive than the first-line set
- prior Janus notes already marked compatibility concerns

### `moonshotai/kimi-k2`

Hold reason:

- materially too expensive for the first cost-saving quickchange corridor
- better reserved for later targeted comparison if cheaper candidates fail quality gates

### `z-ai/glm-4.5-air`

Hold reason:

- output cost is high relative to the cheaper first-line set
- not a strong first cost-saving choice

### `z-ai/glm-4.5`

Hold reason:

- very expensive for the intended worker role
- page currently shows `Going away June 19, 2026`

### `deepseek/deepseek-v3.2`

Hold reason:

- stronger premium pricing than the first-line set
- better treated as later escalation candidate, not first cheap worker test

### `qwen/qwen3-235b-a22b-thinking-2507`

Hold reason:

- thinking-only bias is not ideal for tiny bounded quickchange work
- higher reasoning overhead is unnecessary for first small edit tests

## Fixed-Model Recommendation For First Quickchange Tests

Use fixed models first, not Auto Router first.

Recommended first assignment logic:

- default cheapest candidate: `openai/gpt-oss-20b`
- cheap stronger fallback: `openai/gpt-oss-120b`
- cross-family fallback: `qwen/qwen3-30b-a3b-instruct-2507`
- optional later backup set: `qwen/qwen3.5-flash-02-23`, `deepseek/deepseek-v4-flash`

Why fixed-model first:

- easier failure attribution
- easier cost comparison
- cleaner per-model evidence
- better fit for the first real bounded quickchange acceptance loop

## Recommended Test Order

For the first real `janus-quickchange` live evidence runs:

1. `quickchange_patch_review` with `openai/gpt-oss-20b`
2. same bounded class with `openai/gpt-oss-120b`
3. same bounded class with `qwen/qwen3-30b-a3b-instruct-2507`

Promote to `quickchange_write_apply` only after:

- patch-review output stays inside allowlist
- Codex review quality is acceptable
- validation summaries are complete
- reject/fallback behavior stays clean

## Auto Router Position

Auto Router should not be the first quickchange test path.

Use it later only after:

- at least 3 accepted fixed-model quickchange runs exist
- one or two families clearly outperform the others
- the allowed-model pool is evidence-backed instead of speculative

Until then:

- fixed-model quickchange remains the canonical evidence path
- Auto Router remains a later optimization experiment

## Next Safe Step

Prepare the first bounded quickchange live test package with this exact candidate order:

1. `openai/gpt-oss-20b`
2. `openai/gpt-oss-120b`
3. `qwen/qwen3-30b-a3b-instruct-2507`

and keep:

- no production routing
- no canonical routing-table update
- Codex-owned final acceptance
