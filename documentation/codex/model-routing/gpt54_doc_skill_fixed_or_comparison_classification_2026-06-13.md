# GPT-5.4 Documentation Skill Fixed OR Comparison Classification - 2026-06-13

Status: DECISION NOTE / NON-PRODUCTION / NO CANONICAL ROUTING-TABLE UPDATE

## Skill-Level Classification

| skill_id | current classification | rationale |
| --- | --- | --- |
| `DOC-SKILL-002` | `FURTHER_TEST_CANDIDATE` | `ibm-granite/granite-4.1-8b` produced the only `PASS` row in the batch, but the skill is not broadly cleared because the other tested models stayed `HOLD` and `inclusionai/ling-2.6-flash` was technically blocked by upstream `429`. |
| `DOC-SKILL-006` | `KEEP_CODEX` | Every accepted candidate failed because formatting output drifted into unsafe live-call permission or dropped required operator-reminder boundaries. |
| `DOC-SKILL-008` | `KEEP_CODEX` | No candidate passed all required caveat gates; the best rows remained `HOLD`, and `mistralai/mistral-nemo` crossed into authority-violation territory. |

## Model-Level Takeaways

- `ibm-granite/granite-4.1-8b`: narrow positive signal only for `DOC-SKILL-002`
- `openai/gpt-oss-20b`: mixed; no passing row in this batch
- `openai/gpt-oss-120b`: mixed; no passing row in this batch
- `mistralai/mistral-nemo`: weak on these first `5.4` fixtures, including one authority-violation fail
- `inclusionai/ling-2.6-flash`: technically unclassified in this batch because all three calls hit upstream `429`

## Decision

The first `5.4` documentation-skill live comparison batch does not justify broad OR rollout.

The only model/skill pair worth a later narrow follow-up is:

- `DOC-SKILL-002` with `ibm-granite/granite-4.1-8b`

Everything else should remain local/Codex unless a later prompt revision or stricter task-specific system message changes the result.

## Boundary Reminder

- fixed-model mini Auto-sparsam remains canonical for the seven mini skills
- this `5.4` result is comparison evidence only
- no production routing is enabled
- no canonical routing-table update is made
- no global OR approval exists
