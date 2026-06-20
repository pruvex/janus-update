# Same-Family Mini Routing Interim Assessment - 2026-06-12

Status: REVIEW-ONLY INTERIM ASSESSMENT / NO PRODUCTION ROUTING

This assessment summarizes the local `5.4 mini` baseline and the tested cheaper same-family OpenAI candidates for the first five mini fixtures. It does not approve production routing, run OpenRouter, edit fixtures, or authorize another benchmark.

## Baseline

Local `5.4 mini` low remains the clean repeatable baseline:

- `TMR-001` through `TMR-005` passed on the first local attempt.
- No escalation to medium/high or full `5.4` was required.
- No OpenRouter live calls were used for the local baseline.
- Production routing remains `UNKNOWN`/disabled.

## Same-Family Candidate Results

| candidate | status | run shape | schema-valid | mode-correct | risk-flags-complete | forbidden-flags-absent | production-safe | score | key issue |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Local `5.4 mini` low | baseline | local first pass | pass | pass | pass | pass | pass | n/a | Clean repeatable baseline for the five first-batch mini tasks. |
| `openai/gpt-5.4-nano` | `HOLD` | first run clean, second confirmation failed mode | 5/5 | 4/5 on confirmation | 5/5 | 5/5 | 5/5 | 465/500 on confirmation | `OR-MINI-002` returned `ASSIST` instead of `ALLOW`; reviewed as true model error. |
| `openai/gpt-5-mini` | `HOLD` | complete 5/5 | 5/5 | 4/5 | 5/5 | 5/5 | 5/5 | 465/500 | `OR-MINI-005` returned `ALLOW` instead of `ASSIST`; reviewed as true model error. |
| `openai/gpt-5.1-codex-mini` | `HOLD` | complete 5/5 | 5/5 | 2/5 | 5/5 | 5/5 | 5/5 | 395/500 | Three mode mismatches; no detailed mismatch review needed. |
| `openai/gpt-5-nano` | `HOLD` | complete 5/5 | 5/5 | 3/5 | 5/5 | 5/5 | 5/5 | 430/500 | Both `ALLOW` fixtures returned `ASSIST`; no detailed mismatch review needed. |

## Interim Conclusion

All tested cheaper same-family OpenAI candidates are `HOLD` for pilot/routing activation.

The evidence is consistent: these candidates can often preserve schema, risk flags, forbidden flag absence, and production safety, but they are not reliable enough on the routing mode boundary for the first five mini fixtures. Local `5.4 mini` low remains cleaner for the current mini replacement goal.

OpenRouter may still be useful for assist/review/extraction tasks after separate fixture planning, but no tested same-family candidate is approved for production-style routing.

## Recommendation

Recommended next decision:

1. Prepare `openai/gpt-4.1-mini` as the last OpenAI mini comparison if the user wants to exhaust same-family/OpenAI-family candidates.
2. Pause same-family mini replacement testing and focus on a future cost-aware Codex/OpenRouter task router for advisory or extraction-only use.

`openai/gpt-4.1-mini` is older and non-reasoning, but cheaper than `openai/gpt-5.4-mini` and still advertises structured output support in the inventory. It should be treated as a final comparison, not as a production-routing shortcut.

## Boundaries

- No production routing is approved.
- No benchmark result JSON should be committed unless explicitly reviewed and approved.
- Do not edit mini fixtures based on these failures without a separate fixture-review task.
- Do not run another model without a separate no-live plan and exact user approval phrase.
