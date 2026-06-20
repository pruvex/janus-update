# GPT-5.4 DOC-SKILL-002 and DOC-SKILL-006 Narrow Retest Plan - 2026-06-14

Status: PLANNING ONLY / NON-PRODUCTION / NO CANONICAL ROUTING-TABLE UPDATE

## Goal

Run one small follow-up retest block for `DOC-SKILL-002` and `DOC-SKILL-006` to separate two possible failure sources:

- prompt and acceptance-criteria wording drift
- insufficient completion budget on longer governance-heavy outputs

This plan does not assume that the previous failures prove OR impossibility. It treats them as current bounded evidence under a strict prompt plus postcheck contract.

## Why a Narrow Retest Is Justified

### DOC-SKILL-002

Observed pattern in the five-model batch:

- several responses stayed close to the intended safe scope
- failures mostly came from exact governance phrase misses
- the failures were not primarily `finish_reason=length`

Interpretation:

- the next retest should focus first on prompt-contract precision
- only a small completion-budget increase is needed

### DOC-SKILL-006

Observed pattern in the five-model batch:

- repeated blocked-scope drift
- repeated weak operator-reminder retention
- one `moonshotai/kimi-k2.6` row ended with `finish_reason=length`

Interpretation:

- the next retest should use both stronger prompt structure and a materially larger completion budget
- budget alone is not enough, but budget is a plausible contributing factor here

## Retest Scope

Exactly two skills:

- `DOC-SKILL-002`
- `DOC-SKILL-006`

Exactly two candidate models per skill:

### DOC-SKILL-002 candidates

- `deepseek/deepseek-v4-flash`
- `qwen/qwen3.5-flash-02-23`

Why these two:

- both were cheap
- both were close enough that prompt-contract repair is worth testing
- neither justifies jumping straight to a more expensive model first

### DOC-SKILL-006 candidates

- `deepseek/deepseek-v4-flash`
- `qwen/qwen3.5-flash-02-23`

Why these two:

- both were the cheapest serious rows in the previous batch
- both failed for the same structural reasons, which makes them good probe models for prompt and budget changes
- neither produced the heavy spend profile seen on `moonshotai/kimi-k2.6` or `openai/gpt-5.3-codex`

## Planned Prompt Changes

### DOC-SKILL-002 prompt revision

Add a short forced-boundary block near the end of the system or task prompt:

- include the exact sentence `No global OpenRouter approval exists.`
- include the exact sentence `No production routing is approved.`
- include the exact sentence `No canonical routing-table update is made.`
- require one explicit `next safe step`
- forbid paraphrasing those three governance lines

Retest intent:

- verify whether the previous failures were mostly boundary-phrase exactness issues

### DOC-SKILL-006 prompt revision

Add a short forced-output template:

- `Planning only`
- `Allowed scope`
- `Blocked scope`
- `Operator reminder`
- `Next safe fixture work`

Inside the prompt:

- require the exact phrase that live OR calls need explicit user approval
- require the blocked-scope lines for production routing and routing-table updates in explicit negative language
- forbid adding audit, release, or execution readiness claims

Retest intent:

- reduce structural drift before spending more on larger models

## Completion-Budget Changes

### DOC-SKILL-002

Current recommendation:

- keep the request compact
- raise completion budget only modestly from the previous broad-batch setting
- target enough room for the boundary lines plus one next-safe-step line

Practical rule:

- treat this as a prompt-precision retest, not a long-form generation retest

### DOC-SKILL-006

Current recommendation:

- increase completion budget clearly above the previous broad-batch setting
- do not accept another `finish_reason=length` row as sufficient evidence

Practical rule:

- this skill needs enough room for all required sections, blocked-scope repetition, and operator reminder retention

## Cost Strategy

Keep the retest intentionally small:

- total planned calls: `4`
- first pass only on the two cheapest strong candidates per skill
- do not include `moonshotai/kimi-k2.6` or `openai/gpt-5.3-codex` in the immediate retest

Reason:

- the previous batch already showed that higher-spend models did not buy reliable acceptance on `DOC-SKILL-002` or `DOC-SKILL-006`
- the next question is prompt-contract recoverability, not broad family discovery

## Acceptance Questions

The retest should answer exactly these questions:

### DOC-SKILL-002

- can a cheap model pass once exact governance wording is forced?
- if yes, was the prior failure mostly prompt-contract precision rather than model weakness?

### DOC-SKILL-006

- can a cheap model pass once the output structure is forced and completion budget is increased?
- if no, does the skill remain `KEEP_CODEX` even under a friendlier budget?

## Stop Rules

Stop the retest immediately for the affected row if any of these happen:

- `finish_reason=length`
- missing `generation_id`
- missing usage block
- missing response body
- healthcheck ingestion failure
- actual cost materially exceeds the approved per-call cap

Stop the broader retest idea after the first four calls if:

- `DOC-SKILL-002` still has zero passing rows
- `DOC-SKILL-006` still has zero passing rows

That outcome would mean:

- `DOC-SKILL-002`: prompt-contract sensitivity is still too high for practical OR replacement
- `DOC-SKILL-006`: local/Codex remains the realistic default unless the task contract itself is redesigned

## Expected Best-Case Outcome

- `DOC-SKILL-002`: possible upgrade from `KEEP_CODEX` back to `FURTHER_TEST_CANDIDATE`
- `DOC-SKILL-006`: possible reduction of uncertainty, but still more likely to remain `KEEP_CODEX`

## Expected Worst-Case Outcome

- both skills remain `KEEP_CODEX`
- we gain cleaner evidence that the failures are not mainly caused by too-tight budget

## Boundaries

- no production routing
- no canonical routing-table update
- no Auto Router
- no global OR approval
- no `DOC-SKILL-011` run
- no `DOC-SKILL-012` continuation
- fixed-model mini Auto-sparsam remains unchanged
