# Fixed OR Live Enablement For Mini Documentation Skills - 2026-06-13

Status: IMPLEMENTATION ENABLEMENT NOTE / SKILL-NATIVE OPERATOR CHOICE ACTIVE / NO AUTO ROUTER / NO PRODUCTION ROUTING / NO CANONICAL ROUTING-TABLE UPDATE

## Scope

This enablement is limited to the seven approved mini documentation skills only:

- `DOC-SKILL-001` -> `openai/gpt-oss-20b`
- `DOC-SKILL-002` -> `openai/gpt-oss-20b`
- `DOC-SKILL-003` -> `openai/gpt-oss-20b`
- `DOC-SKILL-006` -> `openai/gpt-oss-120b`
- `DOC-SKILL-008` -> `qwen/qwen3.5-flash-02-23`
- `DOC-SKILL-009` -> `qwen/qwen3.5-flash-02-23`
- `DOC-SKILL-010` -> `qwen/qwen3.5-flash-02-23`

Auto Router is disabled for this implementation.

## Operator Choice Path

When a bounded task:

- matches one of the seven enabled `DOC-SKILL-*` IDs
- stays inside documentation-skill intent
- would normally target `GPT-5.4 mini`

the operator can choose:

- local Codex handling
- fixed-model OR handling for that specific skill

The operator prompt includes:

- detected `skill_id`
- local Codex option
- OR option with fixed selected model
- estimated OR cost
- confidence and estimate status
- per-call cap
- session cap
- explicit note that this is operator-invoked fixed OR use only, not Auto Router and not production routing

## Skill-native Integration

`janus-documentation-update` now carries the bounded fixed-OR gate directly in the skill instructions.

For the seven eligible `DOC-SKILL-*` rows, the skill now:

- classifies the documentation request against the routing table
- runs the fixed-OR runner in `prompt` mode
- shows a `FIXED OR OPERATOR CHOICE` gate
- waits for `local` or `or` unless the user already stated the choice
- invokes the same runner for the chosen path

This makes the fixed-OR choice available during ordinary documentation-skill use instead of only through a separate manual runner call.

The operator-facing prompt is now phrased as a numbered choice:

- `1 = Codex`
- `2 = OpenRouter`

and explicitly shows:

- selected OR model
- estimated cost
- confidence percent

## Config

Primary config:

- `documentation/codex/model-routing/config/doc_skill_mini_fixed_or_live_enabled_2026-06-13.json`

The config includes:

- exactly all seven enabled mini skills
- fixed OR model mapping per skill
- local Codex option enabled
- OR option enabled
- Auto Router disabled
- per-call cap `0.0020`
- session cap `0.0060`
- max OR calls per session `3`
- file-first wrapper path
- session JSONL naming pattern
- healthcheck command
- fallback rules
- abort rules
- manual-review triggers
- operator summary fields

## Entrypoint

Primary runner:

- `documentation/codex/model-routing/scripts/doc_skill_mini_fixed_or_live_runner.py`

Implemented behavior:

- detects in-scope skill IDs
- checks that the normal target model matches `GPT-5.4 mini`
- writes operator choice prompt metadata before route execution
- supports local Codex path with no OR call
- supports fixed-model OR path with no model substitution
- requires file-first wrapper for the OR path
- appends accepted telemetry only if all post-call gates pass
- runs `health_snapshot.py --or-telemetry-jsonl` after accepted OR rows
- writes compact operator summary artifacts

## Local Validation

Fixture-only response used for bounded validation:

- `documentation/codex/model-routing/fixtures/fixed_or_live_success_fixture_2026-06-13.json`

Expected fixture/local validation coverage:

- local Codex option makes no OR call
- OR option builds fixed-model request body
- out-of-scope skills route to Codex-only before wrapper invocation
- missing estimate or confidence aborts before wrapper invocation

## Boundary Reminder

- fixed-model Auto-sparsam remains canonical
- Auto Router remains out of scope for this enablement
- no production routing is activated
- no canonical routing-table update is made
- no global OR approval is created
- no `DOC-SKILL-011` run
- no `DOC-SKILL-012` start
- no separate `5.4` candidate continuation
