# GPT-5.4 OR Candidate Price Shortlist - 2026-06-14

Status: PRICE-BASED SHORTLIST / NO LIVE EVALS / NO PRODUCTION ROUTING / NO MODEL APPROVAL

## Source

Primary source: `documentation/codex/openrouter-delegation/model_price_inventory_2026-06-12.md` and `documentation/codex/openrouter-delegation/model_price_inventory_2026-06-12.json`.

Reference price from the inventory:

| reference_model | input_per_1m | output_per_1m |
| --- | ---: | ---: |
| `GPT-5.4` | `$2.50` | `$15.00` |

The shortlist below uses catalog metadata only. It is not live quality evidence and does not approve a model.

## Tier A: Structured Candidate Pool

These candidates are cheaper than `GPT-5.4` on input and output and have structured-output support in the inventory. They are candidates for sanitized fixture testing only.

| model | input_per_1m | output_per_1m | context | structured_outputs | tools | reasoning | initial_use |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| `inclusionai/ling-2.6-flash` | `$0.0100` | `$0.0300` | `262144` | yes | yes | no | cheapest structured docs-assist candidate |
| `meta-llama/llama-3.1-8b-instruct` | `$0.0200` | `$0.0300` | `131072` | yes | yes | no | low-cost structured baseline |
| `mistralai/mistral-nemo` | `$0.0200` | `$0.0300` | `131072` | yes | yes | no | low-cost structured baseline |
| `openai/gpt-oss-20b` | `$0.0290` | `$0.1400` | `131072` | yes | yes | yes | OpenAI-family low-cost candidate |
| `cohere/command-r7b-12-2024` | `$0.0375` | `$0.1500` | `128000` | yes | no | no | summary-only comparison candidate |
| `mistralai/mistral-small-24b-instruct-2501` | `$0.0500` | `$0.0800` | `32768` | yes | no | no | compact changelog/summary candidate |
| `google/gemma-3-4b-it` | `$0.0500` | `$0.1000` | `131072` | yes | no | no | low-cost summary candidate |
| `ibm-granite/granite-4.1-8b` | `$0.0500` | `$0.1000` | `131072` | yes | yes | no | structured/tool-capable comparison candidate |
| `openai/gpt-oss-120b` | `$0.0390` | `$0.1800` | `131072` | yes | yes | yes | stronger OpenAI-family candidate |
| `arcee-ai/trinity-mini` | `$0.0450` | `$0.1500` | `131072` | yes | yes | yes | reasoning-capable comparison candidate |
| `google/gemma-3-12b-it` | `$0.0500` | `$0.1500` | `131072` | yes | yes | no | broader structured comparison candidate |
| `qwen/qwen3-30b-a3b-instruct-2507` | below GPT-5.4 | below GPT-5.4 | inventory-derived | yes | yes | not primary | hold for later if Tier A breadth is needed |

## Tier B: Hold For Fixture Selection

These are cheaper in the catalog but weaker fits for structured documentation-skill evaluation because schema or tool metadata is missing or less complete.

| model | hold_reason |
| --- | --- |
| `ibm-granite/granite-4.0-h-micro` | no structured-output/tool support in the current inventory |
| `liquid/lfm-2-24b-a2b` | no structured-output/tool support in the current inventory |
| `qwen/qwen-2.5-7b-instruct` | no structured-output/tool support in the current inventory |
| `amazon/nova-micro-v1` | tool support exists, but structured-output support is not present in the current inventory |
| `meta-llama/llama-3.2-1b-instruct` | no structured-output/tool support in the current inventory |
| `nvidia/nemotron-3-nano-30b-a3b` | reasoning/tool metadata is interesting, but structured-output support is not present in the current inventory |

## Starting Candidate Recommendation

For the first no-live fixture preparation pass, use a small comparison set:

- `openai/gpt-oss-20b`
- `openai/gpt-oss-120b`
- `inclusionai/ling-2.6-flash`
- `mistralai/mistral-nemo`
- `ibm-granite/granite-4.1-8b`

Reason: this covers OpenAI-family continuity, cheapest structured candidates, and one non-OpenAI structured/tool-capable comparison without repeating the overly broad Auto Router pattern.

## Boundaries

- Catalog price is not quality evidence.
- No model in this file is approved for production routing.
- No model in this file replaces fixed-model mini Auto-sparsam.
- Future tests must compare against local `5.4` baselines for the exact documentation-skill fixture, not against generic benchmark claims.
