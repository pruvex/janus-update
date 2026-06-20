# GPT-5.4 Documentation Skill 5-Model Batch Classification - 2026-06-14

Status: DECISION NOTE / NON-PRODUCTION / NO CANONICAL ROUTING-TABLE UPDATE

## Skill-Level Classification

| skill_id | current classification | rationale |
| --- | --- | --- |
| `DOC-SKILL-002` | `KEEP_CODEX` | All five tested candidates failed the hardened local postcheck. The failures were mostly governance-phrase exactness misses rather than wild content drift, but there is still no passing replacement row after this broader family sweep. |
| `DOC-SKILL-006` | `KEEP_CODEX` | All five tested candidates failed. The pattern stayed consistent: blocked-scope wording drift, weak operator reminder retention, and one `finish_reason=length` capture-only Kimi row. |
| `DOC-SKILL-008` | `FURTHER_TEST_CANDIDATE` | Four of five tested candidates passed the hardened local postcheck. `deepseek/deepseek-v4-flash` is the strongest current candidate because it passed cleanly and was by far the cheapest accepted row. |

## Model-Level Takeaways

- `deepseek/deepseek-v4-flash`: strongest new candidate in this batch, specifically for `DOC-SKILL-008`
- `qwen/qwen3.5-flash-02-23`: cheap, but no passing row in this batch
- `z-ai/glm-5-turbo`: one positive signal on `DOC-SKILL-008`, but cost is too high for immediate preference
- `moonshotai/kimi-k2.6`: broad spend is high; only one passing row and one length-limited failure
- `openai/gpt-5.3-codex`: one positive signal on `DOC-SKILL-008`, but no justification yet to prefer it over cheaper accepted options

## Decision

The broad five-model sweep improves the `5.4` picture, but only for one skill.

What should stay true after this batch:

- `DOC-SKILL-002` remains local/Codex for now
- `DOC-SKILL-006` remains local/Codex for now
- `DOC-SKILL-008` is the only `5.4` documentation skill that now merits a narrow follow-up replacement decision

The best next narrow follow-up, if the user wants to continue, is:

- `DOC-SKILL-008` with `deepseek/deepseek-v4-flash`

Possible secondary references, but not current favorites:

- `DOC-SKILL-008` with `z-ai/glm-5-turbo`
- `DOC-SKILL-008` with `openai/gpt-5.3-codex`
- `DOC-SKILL-008` with `moonshotai/kimi-k2.6`

## Boundary Reminder

- fixed-model mini Auto-sparsam remains canonical for the seven mini skills
- this `5.4` result is comparison evidence only
- no production routing is enabled
- no canonical routing-table update is made
- no global OR approval exists
