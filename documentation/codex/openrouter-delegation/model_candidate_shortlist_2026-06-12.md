# OpenRouter Candidate Shortlist - 2026-06-12

Status: REVIEW-ONLY SHORTLIST / NO PRODUCTION ROUTING

Source inventory:

- `documentation/codex/openrouter-delegation/model_price_inventory_2026-06-12.json`
- `documentation/codex/openrouter-delegation/model_price_inventory_2026-06-12.md`

This shortlist uses only the read-only OpenRouter model catalog inventory. No chat, completion, responses, benchmark, or model inference endpoint was called for this review. No model is approved by this shortlist, and production routing remains `UNKNOWN`/disabled.

## Selection Rules

- Prefer models cheaper than GPT-5.4 mini on both input and output for `MINI_REPLACEMENT`.
- Prefer cheaper OpenAI-family models before non-OpenAI providers when capability and schema support are comparable to the current local baseline family.
- Require `response_format` or `structured_outputs` for schema-heavy fixture preparation.
- Prefer high context and structured output support for `LARGE_MODEL_COST_REDUCTION`.
- Treat all candidates as advisory until no-live fixtures and later explicitly approved live benchmark evidence exist.
- Carry forward existing `HOLD` evidence for models already tested or known risky.

## Reference Profile Baselines

| profile | token shape | GPT-5.4 mini | GPT-5.4 | GPT-5.5 |
| --- | --- | ---: | ---: | ---: |
| `mini_extract` | 3000 input / 500 output | $0.00450 | $0.01500 | $0.03000 |
| `docs_summary` | 8000 input / 1500 output | $0.01275 | $0.04250 | $0.08500 |
| `code_review_small` | 20000 input / 3000 output | $0.02850 | $0.09500 | $0.19000 |
| `large_review` | 60000 input / 6000 output | $0.07200 | $0.24000 | $0.48000 |

## OpenAI-family Cheaper-than-5.4-mini Candidates

Audit result: the previous shortlist under-prioritized OpenAI-family candidates because it sorted mostly by absolute catalog cost and the initial review set focused on the cheapest cross-provider rows. That was too blunt for Janus routing evaluation: cheaper same-family candidates should be reviewed before non-OpenAI providers when they advertise comparable schema, tool, and reasoning support.

Baseline for comparison: `openai/gpt-5.4-mini` is $0.7500 input / 1M, $4.5000 output / 1M, $0.0750 cached input / 1M, 400000 context, 128000 max completion, and supports `response_format`, `structured_outputs`, `tools`, and `reasoning`.

| model id | prompt / 1M | completion / 1M | cached input / 1M | context | max completion | response_format | structured_outputs | tools | reasoning | supported parameters | benchmark metadata | comparison vs `openai/gpt-5.4-mini` |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- |
| `openai/gpt-5.4-nano` | $0.2000 | $1.2500 | $0.0200 | 400000 | 128000 | yes | yes | yes | yes | `include_reasoning`, `max_completion_tokens`, `max_tokens`, `reasoning`, `response_format`, `seed`, `structured_outputs`, `tool_choice`, `tools` | Artificial Analysis: agentic `47.6`, coding `43.9`, intelligence `44.0` | Same GPT-5.4 family, 73.3% cheaper input and 72.2% cheaper output. First no-live candidate. |
| `openai/gpt-5-mini` | $0.2500 | $2.0000 | $0.0250 | 400000 | 128000 | yes | yes | yes | yes | `include_reasoning`, `max_completion_tokens`, `max_tokens`, `reasoning`, `response_format`, `seed`, `structured_outputs`, `tool_choice`, `tools` | Artificial Analysis: agentic `45.5`, coding `35.3`, intelligence `41.2`; Design Arena metadata present | Newer GPT-5-family mini; 66.7% cheaper input and 55.6% cheaper output. |
| `openai/gpt-5.1-codex-mini` | $0.2500 | $2.0000 | $0.0250 | 400000 | 100000 | yes | yes | yes | yes | `include_reasoning`, `max_completion_tokens`, `max_tokens`, `reasoning`, `response_format`, `seed`, `structured_outputs`, `tool_choice`, `tools` | Artificial Analysis: agentic `38.7`, coding `36.4`, intelligence `38.6`; Design Arena metadata present | Prioritize for Codex/code-review-like tasks; 66.7% cheaper input and 55.6% cheaper output. |
| `openai/gpt-5-nano` | $0.0500 | $0.4000 | $0.0100 | 400000 | unknown | yes | yes | yes | yes | `include_reasoning`, `max_completion_tokens`, `max_tokens`, `reasoning`, `response_format`, `seed`, `structured_outputs`, `tool_choice`, `tools` | Artificial Analysis: agentic `23.2`, coding `20.3`, intelligence `26.8`; Design Arena metadata present | Extremely cheap, but likely lower-depth; 93.3% cheaper input and 91.1% cheaper output. |
| `openai/gpt-4.1-mini` | $0.4000 | $1.6000 | $0.1000 | 1047576 | 32768 | yes | yes | yes | no | `max_completion_tokens`, `max_tokens`, `response_format`, `seed`, `structured_outputs`, `temperature`, `tool_choice`, `tools`, `top_p` | Artificial Analysis: agentic `25.2`, coding `18.5`, intelligence `22.9`; Design Arena metadata present | Cheaper but older and non-reasoning; 46.7% cheaper input and 64.4% cheaper output. Test only after newer GPT-5-family candidates. |

Additional OpenAI-family cheaper-than-5.4-mini entries found but not promoted into the corrected mini priority:

- `openai/gpt-oss-20b` and `openai/gpt-oss-120b`: strong low-cost structured/reasoning catalog candidates, but not the same managed GPT-5.x family as the current baseline.
- `openai/gpt-4.1-nano`: very cheap and large context, but older/lower benchmark profile than the requested GPT-5-family candidates.
- `openai/gpt-4o-mini`, `openai/gpt-4o-mini-2024-07-18`, and `openai/gpt-4o-mini-search-preview`: cheaper than GPT-5.4 mini, but older family and search/audio variants are less clean for schema-bound routing evaluation.
- `openai/gpt-3.5-turbo`: cheaper but old, lower context, and not a preferred Janus routing candidate.
- `openai/gpt-audio-mini`: cheaper but audio-oriented; not a clean text-only routing candidate.
- `openai/gpt-oss-safeguard-20b`: cheaper and response-format capable, but safety/safeguard specialization is not the first fit for mini replacement.
- `openai/gpt-oss-20b:free` and `openai/gpt-oss-120b:free`: retained as raw inventory but remain `HOLD_FREE_ONLY` and lack structured-output support in the catalog.

## MINI_REPLACEMENT

Recommended fixture type: the five first-batch mini retry fixtures, starting with schema-bound extraction/classification cases before advisory ranking cases.

| model id | prompt / 1M | completion / 1M | context | structured output fields | response_format | structured_outputs | tools | reasoning | `mini_extract` cost vs GPT-5.4 mini / GPT-5.4 / GPT-5.5 | reason for inclusion | known risks | next fixture type |
| --- | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `openai/gpt-5.4-nano` | $0.2000 | $1.2500 | 400000 | `response_format`, `structured_outputs` | yes | yes | yes | yes | $0.00123 vs $0.00450 / $0.01500 / $0.03000 | Same family as the current `5.4 mini` baseline and much cheaper; best first no-live candidate. | Still a nano model; must prove it matches local `5.4 mini low` behavior before any live run. | `OR-MINI-001` through `OR-MINI-005`, no-live first. |
| `openai/gpt-5-mini` | $0.2500 | $2.0000 | 400000 | `response_format`, `structured_outputs` | yes | yes | yes | yes | $0.00175 vs $0.00450 / $0.01500 / $0.03000 | Newer GPT-5-family mini with full schema/tool/reasoning support and lower price than `5.4 mini`. | More expensive than non-OpenAI cheap rows; must justify family preference with cleaner behavior. | Mini fixtures after `gpt-5.4-nano`. |
| `openai/gpt-5.1-codex-mini` | $0.2500 | $2.0000 | 400000 | `response_format`, `structured_outputs` | yes | yes | yes | yes | $0.00175 vs $0.00450 / $0.01500 / $0.03000 | Codex-family candidate should be prioritized for Codex/code-review-like tasks. | Needs proof it follows Janus delegation boundaries and avoids repo-write/final-audit authority. | Mini fixtures plus code-review-assist no-live fixture. |
| `openai/gpt-5-nano` | $0.0500 | $0.4000 | 400000 | `response_format`, `structured_outputs` | yes | yes | yes | yes | $0.00035 vs $0.00450 / $0.01500 / $0.03000 | Extremely cheap GPT-5-family candidate with full schema/tool/reasoning support. | Riskier low-depth candidate; do not let price outrank behavior. | Mini fixtures after stronger GPT-5-family candidates. |
| `openai/gpt-4.1-mini` | $0.4000 | $1.6000 | 1047576 | `response_format`, `structured_outputs` | yes | yes | yes | no | $0.00200 vs $0.00450 / $0.01500 / $0.03000 | Cheaper OpenAI-family fallback with very large context and schema support. | Older and non-reasoning; test only after newer GPT-5-family candidates. | Mini/docs fixtures only after GPT-5-family review. |
| `inclusionai/ling-2.6-flash` | $0.0100 | $0.0300 | 262144 | `response_format`, `structured_outputs` | yes | yes | yes | no | $0.00005 vs $0.00450 / $0.01500 / $0.03000 | Cheapest practical non-OpenAI structured candidate; very large context and tool support. | No Janus behavioral evidence yet; very low price may hide provider variability. | Non-OpenAI comparison after OpenAI-family no-live review. |
| `mistralai/mistral-nemo` | $0.0200 | $0.0300 | 131072 | `response_format`, `structured_outputs` | yes | yes | yes | no | $0.00008 vs $0.00450 / $0.01500 / $0.03000 | Low-cost non-OpenAI baseline candidate with schema and tools support. | No Janus behavioral evidence yet; must prove exact risk-flag discipline. | Non-OpenAI comparison after OpenAI-family no-live review. |

## DOCS_ASSIST

Recommended fixture type: sanitized documentation wording, label extraction, and concise advisory summaries. These are assistive only; Codex/User retains final policy authority.

| model id | prompt / 1M | completion / 1M | context | structured output fields | response_format | structured_outputs | tools | reasoning | `docs_summary` cost vs GPT-5.4 mini / GPT-5.4 / GPT-5.5 | reason for inclusion | known risks | next fixture type |
| --- | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `inclusionai/ling-2.6-flash` | $0.0100 | $0.0300 | 262144 | `response_format`, `structured_outputs` | yes | yes | yes | no | $0.00013 vs $0.01275 / $0.04250 / $0.08500 | Best catalog cost/context mix for docs assist. | Needs behavioral proof that low-cost output stays deterministic. | Sanitized docs wording and summary fixtures. |
| `mistralai/mistral-nemo` | $0.0200 | $0.0300 | 131072 | `response_format`, `structured_outputs` | yes | yes | yes | no | $0.00021 vs $0.01275 / $0.04250 / $0.08500 | Cheap and high-context with schema/tool support. | No Janus style or governance evidence yet. | Documentation extraction and summary fixtures. |
| `openai/gpt-oss-20b` | $0.0290 | $0.1400 | 131072 | `response_format`, `structured_outputs` | yes | yes | yes | yes | $0.00044 vs $0.01275 / $0.04250 / $0.08500 | Reasoning support may help advisory docs interpretation while staying inexpensive. | Must not imply policy authority; reasoning fields may need prompt discipline. | Advisory docs interpretation fixtures. |
| `cohere/command-r7b-12-2024` | $0.0375 | $0.1500 | 128000 | `response_format`, `structured_outputs` | yes | yes | no | no | $0.00053 vs $0.01275 / $0.04250 / $0.08500 | Simple structured docs-assist candidate with high context. | No tools; short max completion. | Concise docs-summary fixtures. |
| `mistralai/mistral-small-24b-instruct-2501` | $0.0500 | $0.0800 | 32768 | `response_format`, `structured_outputs` | yes | yes | no | no | $0.00052 vs $0.01275 / $0.04250 / $0.08500 | Low completion price and structured outputs fit small wording tasks. | Context ceiling limits broad docs review. | Small sanitized wording fixtures. |

## CODE_REVIEW_ASSIST

Recommended fixture type: sanitized small-code-review style advisory fixtures that require structured findings but explicitly exclude final audit, merge, release, or production authority.

| model id | prompt / 1M | completion / 1M | context | structured output fields | response_format | structured_outputs | tools | reasoning | `code_review_small` cost vs GPT-5.4 mini / GPT-5.4 / GPT-5.5 | reason for inclusion | known risks | next fixture type |
| --- | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `inclusionai/ling-2.6-flash` | $0.0100 | $0.0300 | 262144 | `response_format`, `structured_outputs` | yes | yes | yes | no | $0.00029 vs $0.02850 / $0.09500 / $0.19000 | Cheapest high-context code-review assist candidate. | No behavioral evidence; should start with sanitized toy diffs only. | No-live structured code-review assist fixture. |
| `mistralai/mistral-nemo` | $0.0200 | $0.0300 | 131072 | `response_format`, `structured_outputs` | yes | yes | yes | no | $0.00049 vs $0.02850 / $0.09500 / $0.19000 | Strong low-cost schema candidate with enough context for small reviews. | Must prove it will not overclaim audit authority. | No-live advisory review fixture. |
| `openai/gpt-oss-20b` | $0.0290 | $0.1400 | 131072 | `response_format`, `structured_outputs` | yes | yes | yes | yes | $0.00100 vs $0.02850 / $0.09500 / $0.19000 | Reasoning/tool/schema support make it a plausible review-assist candidate. | More capable model still must remain assist-only; no final audit decisions. | Sanitized review findings fixture. |
| `openai/gpt-oss-120b` | $0.0390 | $0.1800 | 131072 | `response_format`, `structured_outputs` | yes | yes | yes | yes | $0.00132 vs $0.02850 / $0.09500 / $0.19000 | Larger reasoning-capable candidate for assistive review while far below GPT-5.4/5.5 cost. | Needs careful boundary prompts; no release/final-audit authority. | No-live code-review assist fixture after cheaper candidates. |
| `ibm-granite/granite-4.1-8b` | $0.0500 | $0.1000 | 131072 | `response_format`, `structured_outputs` | yes | yes | yes | no | $0.00130 vs $0.02850 / $0.09500 / $0.19000 | High max completion, schema and tools support; useful diversity candidate. | No reasoning flag; no Janus behavioral evidence. | No-live structured review extraction fixture. |

## LARGE_MODEL_COST_REDUCTION

Recommended fixture type: large-context assist-only interpretation and review fixtures. These candidates must not be used for final audit, release approval, production routing, or Git authority.

| model id | prompt / 1M | completion / 1M | context | structured output fields | response_format | structured_outputs | tools | reasoning | `large_review` cost vs GPT-5.4 mini / GPT-5.4 / GPT-5.5 | reason for inclusion | known risks | next fixture type |
| --- | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `inclusionai/ling-2.6-flash` | $0.0100 | $0.0300 | 262144 | `response_format`, `structured_outputs` | yes | yes | yes | no | $0.00078 vs $0.07200 / $0.24000 / $0.48000 | Best high-context cost reducer on paper. | No behavior evidence; low price requires reliability verification. | No-live large-summary fixture. |
| `openai/gpt-oss-20b` | $0.0290 | $0.1400 | 131072 | `response_format`, `structured_outputs` | yes | yes | yes | yes | $0.00258 vs $0.07200 / $0.24000 / $0.48000 | Good reasoning-capable lower-cost assist candidate. | Must stay advisory and concise; no final authority. | No-live large advisory review fixture. |
| `openai/gpt-oss-120b` | $0.0390 | $0.1800 | 131072 | `response_format`, `structured_outputs` | yes | yes | yes | yes | $0.00342 vs $0.07200 / $0.24000 / $0.48000 | Larger reasoning candidate for reducing GPT-5.4/GPT-5.5 assist costs. | More capable does not mean authorized; still no final audit/release decisions. | No-live large review-assist fixture. |
| `arcee-ai/trinity-mini` | $0.0450 | $0.1500 | 131072 | `response_format`, `structured_outputs` | yes | yes | yes | yes | $0.00360 vs $0.07200 / $0.24000 / $0.48000 | Additional high-context structured candidate with reasoning and very high max completion metadata. | No Janus evidence; new provider behavior unknown. | No-live long-output schema stress fixture. |
| `cohere/command-r7b-12-2024` | $0.0375 | $0.1500 | 128000 | `response_format`, `structured_outputs` | yes | yes | no | no | $0.00315 vs $0.07200 / $0.24000 / $0.48000 | High context and structured outputs at low cost. | Max completion 4000 may be too small for some large reviews; no tools/reasoning. | No-live concise large-summary fixture. |

## HOLD_OR_EXCLUDED

| model / group | status | reason |
| --- | --- | --- |
| `qwen/qwen3.7-plus` | HOLD | Mini retry was schema-invalid on `5/5` fixtures, with mode-correct `4/5`. Do not shortlist again until schema behavior changes or a separate repair experiment is approved. |
| `stepfun/step-3.7-flash` | HOLD | Retry 2 completed and was schema-valid `5/5`, but mode-correct `4/5` and production-safe `4/5`; does not match local `5.4 mini low`. |
| `minimax/minimax-m3` | HOLD | Provider/schema compatibility history, including Boolean enum projection concerns; review schema projection before any future retry. |
| `inclusionai/ring-2.6-1t` | HOLD | Prior evidence includes timeout, missing risk flags, and ASSIST misclassified as ALLOW. |
| `:free` and zero-price models | HOLD / inconclusive | Retained in raw inventory, but excluded from production-style routing because free/zero-price routing is not stable evidence. |
| `mistralai/mistral-small-24b-instruct-2501` for large review | Excluded from large bucket | Good mini/docs candidate, but `32768` context is below the `large_review` 60000-input profile. |

## Recommended First 3 No-Live Fixture Candidates

1. `openai/gpt-5.4-nano`
2. `openai/gpt-5-mini`
3. `openai/gpt-5.1-codex-mini`

Rationale:

- All three are cheaper than `openai/gpt-5.4-mini` on both input and output.
- All three support `response_format`, `structured_outputs`, `tools`, and `reasoning`.
- They keep the first no-live comparison inside the OpenAI/GPT-5 family before testing lower-cost non-OpenAI providers.
- `openai/gpt-5.4-nano` is first because it is the same family as the current local baseline and materially cheaper.
- `openai/gpt-5.1-codex-mini` is specifically relevant for Codex/code-review-like assistive tasks.
- None has existing Janus `HOLD` evidence.

## Review Conclusion

This shortlist is suitable for no-live fixture preparation only. It does not approve any OpenRouter model, does not approve production routing, and does not authorize live benchmark calls. The next safe step is to prepare no-live fixtures for `openai/gpt-5.4-nano` first against `TMR-001` through `TMR-005`, then decide whether to prepare `openai/gpt-5-mini` and `openai/gpt-5.1-codex-mini`.
