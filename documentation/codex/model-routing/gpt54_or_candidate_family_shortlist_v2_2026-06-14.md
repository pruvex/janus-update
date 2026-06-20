# GPT-5.4 OR Candidate Family Shortlist v2 - 2026-06-14

Status: REVISED CANDIDATE SHORTLIST / FAMILY-BASED / NO PRODUCTION ROUTING / NO MODEL APPROVAL

## Why This Revision Exists

The first `5.4` candidate shortlist was too narrow. It over-weighted a tiny starter pool and under-represented several strong model families that are both available in the local OpenRouter inventory and widely used in public comparison tools.

This revision corrects that mistake.

## Sources

Local availability and feature metadata:

- `documentation/codex/openrouter-delegation/model_price_inventory_2026-06-12.json`
- `documentation/codex/openrouter-delegation/model_price_inventory_2026-06-12.md`

External comparison sources used to broaden family coverage:

- [Artificial Analysis Models](https://artificialanalysis.ai/models)
- [Artificial Analysis Leaderboard](https://artificialanalysis.ai/leaderboards/models)
- [OpenRouter Models](https://openrouter.ai/models)
- [WhatLLM](https://whatllm.org/)

These sources are used here for discovery and comparison context only. They do not grant approval.

## Correction Summary

The following families were underrepresented or omitted in the earlier shortlist and are now explicitly included:

- `Qwen`
- `Kimi`
- `GPT/Codex`
- `GLM`
- `DeepSeek`

## Family-Based Candidate Set

| family | candidate models | local inventory signal | why included now | current status |
| --- | --- | --- | --- | --- |
| `Qwen` | `qwen/qwen3-30b-a3b-instruct-2507`, `qwen/qwen3.5-flash-02-23` | present locally; structured outputs and tools visible on at least one strong candidate | strong cost/performance family; obvious omission from v1 | `READY_FOR_EVAL_QUEUE` |
| `Kimi` | `moonshotai/kimi-k2.5`, `moonshotai/kimi-k2.6` | present locally; structured outputs and tools supported | major modern reasoning family; should be tested explicitly | `READY_FOR_EVAL_QUEUE` |
| `GPT/Codex` | `openai/gpt-5.3-codex`, `openai/gpt-oss-20b`, `openai/gpt-oss-120b` | present locally; strong parameter/tool support | keeps OpenAI-family continuity and coding/agentic strength in scope | `READY_FOR_EVAL_QUEUE` |
| `GLM` | `z-ai/glm-5-turbo`, `z-ai/glm-5.1` | present locally; modern parameter support | good candidate family that was missing from v1 | `READY_FOR_EVAL_QUEUE` |
| `DeepSeek` | `deepseek/deepseek-v4-flash`, `deepseek/deepseek-chat-v3.1` | present locally; structured outputs/tools visible | strong low-cost family; should not be absent from a serious 5.4 alternative scan | `READY_FOR_EVAL_QUEUE` |
| `Granite` | `ibm-granite/granite-4.1-8b` | present locally; already produced one narrow `PASS` on `DOC-SKILL-002` | keep as proven narrow positive signal | `READY_FOR_NARROW_FOLLOWUP` |
| `Mistral` | `mistralai/mistral-nemo` | present locally; already tested | keep as known comparison reference, but not a front-runner after batch evidence | `ALREADY_TESTED_MIXED` |

## Family-Level Notes

### `Qwen`

- `qwen/qwen3.5-flash-02-23` already worked well in the completed mini path on other documentation skills.
- `qwen/qwen3-30b-a3b-instruct-2507` was already visible in the local shortlist but was unfairly left in a side position.

### `Kimi`

- `moonshotai/kimi-k2.5` and `moonshotai/kimi-k2.6` are both present in the local inventory and support the type of structured/text workflow relevant here.
- They should be treated as first-class `5.4` candidates rather than “maybe later”.

### `GPT/Codex`

- `openai/gpt-5.3-codex` is present in the local inventory and was missing from the narrowed live pool.
- `gpt-oss-20b` and `gpt-oss-120b` stay in scope because they are cheap and already partially tested, but they are no longer the whole OpenAI-family story.

### `GLM`

- `z-ai/glm-5-turbo` and `z-ai/glm-5.1` are both present locally with modern parameter support.
- Their omission from the earlier shortlist was a coverage mistake, not an evidence-based rejection.

### `DeepSeek`

- `deepseek/deepseek-v4-flash` and `deepseek/deepseek-chat-v3.1` are present locally and belong in any serious low-cost alternative scan.
- They were excluded by shortlist narrowness, not because of a documented fail result.

## Revised Inclusion Rule

For `5.4` documentation-skill candidate discovery, a family should be pulled into the shortlist when all are true:

- locally present in the OpenRouter inventory
- cheaper or plausibly competitive relative to `GPT-5.4`
- relevant public comparison coverage exists
- parameter support is adequate for sanitized docs-assist tasks
- no direct local evidence already rules it out for the target skill

## Boundaries

- This file is a corrected candidate-discovery artifact, not an approval artifact.
- Family inclusion does not override actual fixture results.
- No production routing is enabled.
- No canonical routing-table update is made.
- No global OR approval is created.
