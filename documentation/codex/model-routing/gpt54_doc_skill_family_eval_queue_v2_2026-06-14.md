# GPT-5.4 Documentation Skill Family Eval Queue v2 - 2026-06-14

Status: REVISED EVAL QUEUE / FAMILY-COVERAGE FIRST / NO PRODUCTION ROUTING / NO AUTO ROUTER

## Purpose

Translate the revised family shortlist into a saner next-test order for `5.4` documentation-skill work.

This queue replaces the too-narrow spirit of the first live pool. It does not erase the completed batch evidence; it just fixes future candidate coverage.

## Fixed Inputs

Scoped skills for current `5.4` evaluation work:

- `DOC-SKILL-002`
- `DOC-SKILL-006`
- `DOC-SKILL-008`

Known current live-evidence outcome:

- `DOC-SKILL-002`: one narrow positive signal on `ibm-granite/granite-4.1-8b`
- `DOC-SKILL-006`: keep local/Codex unless a materially different family proves otherwise
- `DOC-SKILL-008`: keep local/Codex unless a materially different family proves otherwise

## Queue Design Rules

- prioritize family coverage over repeating the same family too early
- keep fixed-model testing only
- avoid Auto Router
- start with one model per family before going deeper
- keep `DOC-SKILL-006` and `DOC-SKILL-008` lower priority for broad reruns because their first batch was mostly negative

## Queue

| priority | skill_id | model | family | reason |
| --- | --- | --- | --- | --- |
| `1` | `DOC-SKILL-002` | `ibm-granite/granite-4.1-8b` | `Granite` | already has the only `PASS`; best narrow follow-up candidate |
| `2` | `DOC-SKILL-002` | `qwen/qwen3.5-flash-02-23` | `Qwen` | strong family, proven mini-path competence, deserves direct 5.4 docs test |
| `3` | `DOC-SKILL-002` | `moonshotai/kimi-k2.6` | `Kimi` | strong missing family with modern support |
| `4` | `DOC-SKILL-002` | `openai/gpt-5.3-codex` | `GPT/Codex` | obvious high-interest OpenAI-family comparison omitted from v1 |
| `5` | `DOC-SKILL-002` | `z-ai/glm-5-turbo` | `GLM` | missing family coverage |
| `6` | `DOC-SKILL-002` | `deepseek/deepseek-v4-flash` | `DeepSeek` | missing family coverage with strong low-cost profile |
| `7` | `DOC-SKILL-008` | `qwen/qwen3.5-flash-02-23` | `Qwen` | best first cross-family retry for changelog-style drafting |
| `8` | `DOC-SKILL-008` | `moonshotai/kimi-k2.6` | `Kimi` | next strong family for changelog-style drafting |
| `9` | `DOC-SKILL-006` | `qwen/qwen3-30b-a3b-instruct-2507` | `Qwen` | only retry formatting if we want one materially different family check |

## Recommended Immediate Next Step

Do not jump straight into another broad 15+ call sweep.

Use this narrower sequence instead:

1. `DOC-SKILL-002` with `ibm-granite/granite-4.1-8b`
2. `DOC-SKILL-002` with `qwen/qwen3.5-flash-02-23`
3. `DOC-SKILL-002` with `moonshotai/kimi-k2.6`
4. stop and review before touching `DOC-SKILL-006` or `DOC-SKILL-008` again

Reason: `DOC-SKILL-002` is the only current `5.4` doc skill with a real positive signal, so it is the cheapest place to learn quickly.

## Deferred But Valid Later Candidates

- `moonshotai/kimi-k2.5`
- `openai/gpt-oss-20b`
- `openai/gpt-oss-120b`
- `z-ai/glm-5.1`
- `deepseek/deepseek-chat-v3.1`

These remain valid candidates, but they do not need to be ahead of the first cross-family probes above.

## Boundaries

- no production routing
- no canonical routing-table update
- no global OR approval
- no Auto Router
- no silent replacement of current `KEEP_CODEX` classifications
