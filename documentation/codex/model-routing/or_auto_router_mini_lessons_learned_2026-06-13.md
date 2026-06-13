# OpenRouter Auto Router Mini Lessons Learned - 2026-06-13

Status: DECISION NOTE / EXPERIMENT-ONLY / NO PRODUCTION ROUTING / NO CANONICAL ROUTING-TABLE UPDATE

## Core Decision

Auto Router is not broadly confirmed for the seven live-evidenced mini documentation skills.

Fixed-model Auto-sparsam remains canonical.

Auto Router remains experiment-only.

## Skill-Level Lessons

### `DOC-SKILL-001`

Decision: `KEEP_FIXED`

Rationale:

- Auto Router selected `openai/gpt-oss-120b`
- accepted actual cost was `0.00052500`
- fixed baseline actual cost was `0.00009944`
- the Auto Router route was therefore higher by `0.00042556` or `427.96%`
- that cost delta is too unfavorable to justify replacing the fixed baseline

### `DOC-SKILL-002`

Decision: `MANUAL_REVIEW`

Rationale:

- Auto Router selected `openai/gpt-oss-120b`
- response capture, `generation_id`, usage, and actual cost were recovered
- the call still ended with `finish_reason=length`
- that completion-adequacy failure triggered the approved batch abort rule
- this is not clean replacement evidence for the fixed baseline

### `DOC-SKILL-010`

Decision: `FURTHER_TEST_CANDIDATE`

Rationale:

- the prior bounded Auto Router retry resolved the earlier `finish_reason=length` issue to `finish_reason=stop`
- the retry selected `openai/gpt-oss-120b`
- retry actual cost `0.00053955` remained below the fixed `qwen/qwen3.5-flash-02-23` baseline actual cost `0.00060359`
- that positive prior evidence remains valid because the broad batch aborted before reaching `DOC-SKILL-010`

### `DOC-SKILL-003`, `DOC-SKILL-006`, `DOC-SKILL-008`, `DOC-SKILL-009`

Decision: no new broad-batch evidence

Rationale:

- the approved 7-skill batch stopped early after `DOC-SKILL-002`
- these four skills were not reached in the batch
- their fixed-model baselines therefore remain the active bounded evidence layer

## Batch-Level Lessons

- the 7-skill Auto Router breadth check did not confirm broad usefulness across the mini documentation scope
- one accepted row is not enough to support broad adoption
- the only accepted row in the batch favored the fixed baseline rather than the Auto Router route
- the second attempted row exposed a completion-control weakness that was strong enough to stop the whole batch

## Forward Decision

Future Auto Router testing should be:

- targeted, not broad
- limited to skills where the fixed baseline is weak
- limited to skills where the fixed baseline is comparatively expensive
- limited to skills where prior Auto Router evidence is already positive

That means future Auto Router follow-up should start from narrow, evidence-led candidates rather than another broad seven-skill sweep.

## Boundary Reminder

- fixed-model Auto-sparsam remains canonical
- Auto Router remains experiment-only
- no production routing is activated
- no canonical routing-table update is made
- no global OR approval is created
- no `DOC-SKILL-011` run or `DOC-SKILL-012` start occurred
- no separate `5.4` candidate continuation occurred
