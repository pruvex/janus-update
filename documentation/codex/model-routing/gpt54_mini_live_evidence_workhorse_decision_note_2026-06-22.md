# GPT-5.4 Mini Live Evidence Workhorse Decision Note - 2026-06-22

Status: DECISION NOTE / LIVE EVIDENCE ONLY / NO PRODUCTION ROUTING / NO CANONICAL ROUTING-TABLE UPDATE

## Scope

This note summarizes the seven accepted bounded live OR rows for the eligible `5.4 mini` documentation-skills set:

- `DOC-SKILL-001`
- `DOC-SKILL-002`
- `DOC-SKILL-003`
- `DOC-SKILL-006`
- `DOC-SKILL-008`
- `DOC-SKILL-009`
- `DOC-SKILL-010`

It does not create a global OR approval, does not activate production routing, does not update the canonical routing table, does not run `DOC-SKILL-011`, does not start `DOC-SKILL-012`, and does not change the separate `5.4` candidate phase.

## Accepted Live Rows

| skill_id | selected_or_model | actual_or_cost | estimated_or_cost | delta_vs_estimate | finish_reason | recommendation_signal |
| --- | --- | --- | --- | --- | --- | --- |
| `DOC-SKILL-001` | `openai/gpt-oss-20b` | `0.000087240` | `0.000196101` | `-0.000108861` | `stop` | `OR_PREFERRED` |
| `DOC-SKILL-002` | `openai/gpt-oss-20b` | `0.000098740` | `0.000207295` | `-0.000108555` | `stop` | `OR_PREFERRED` |
| `DOC-SKILL-003` | `openai/gpt-oss-20b` | `0.000084080` | `0.000205178` | `-0.000121098` | `stop` | `OR_PREFERRED` |
| `DOC-SKILL-006` | `openai/gpt-oss-120b` | `0.000090940` | `0.000260148` | `-0.000169208` | `stop` | `OR_PREFERRED` |
| `DOC-SKILL-008` | `qwen/qwen3.5-flash-02-23` | `0.000641095` | `0.000968500` | `-0.000327405` | `stop` | `OR_PREFERRED` |
| `DOC-SKILL-009` | `qwen/qwen3.5-flash-02-23` | `0.000444210` | `0.000392015` | `+0.000052195` | `stop` | `OR_PREFERRED` |
| `DOC-SKILL-010` | `qwen/qwen3.5-flash-02-23` | `0.000525460` | `0.000391560` | `+0.000133900` | `stop` | `OR_PREFERRED` |

## Cost Summary

- total actual OR cost: `0.001971765`
- total estimated OR cost: `0.002620797`
- aggregate delta vs estimate: `-0.000649032`
- average confidence display: `55%`

## Decision Summary

- `DOC-SKILL-001`: `KEEP_FIXED`
- `DOC-SKILL-002`: `KEEP_FIXED`
- `DOC-SKILL-003`: `KEEP_FIXED`
- `DOC-SKILL-006`: `KEEP_FIXED`
- `DOC-SKILL-008`: `KEEP_FIXED` for now
- `DOC-SKILL-009`: `KEEP_FIXED` for now
- `DOC-SKILL-010`: `KEEP_FIXED` for now

## Why

The live evidence shows a clear split:

- the shortest summary and handoff-style tasks are very cheap and reliable under fixed OR
- the changelog and formatting lanes are still acceptable, but they are not yet compelling enough to replace the fixed default everywhere
- the three qwen runs were valid and completed cleanly, but they were materially more expensive than the cheapest OpenAI-family summary runs

## Workhorse Recommendation

Best current OR workhorse candidates among the live-evidenced mini documentation skills:

- `DOC-SKILL-003`
- `DOC-SKILL-001`
- `DOC-SKILL-002`
- `DOC-SKILL-006`

Secondary candidates:

- `DOC-SKILL-008`
- `DOC-SKILL-009`
- `DOC-SKILL-010`

## Forward Decision

If we keep testing OR in everyday documentation work, the next most useful follow-up is targeted testing on the cheapest deterministic lanes first. The current data does not support broad replacement of the fixed path, but it does support a bounded OR-assisted workflow for the small summary/handoff tasks.

## Boundary Reminder

- fixed-model Auto-sparsam remains canonical
- OpenRouter remains bounded workflow support only
- no production routing is activated
- no canonical routing-table update is made
- no global OR approval is created
- no `DOC-SKILL-011` run or `DOC-SKILL-012` start occurred
- no separate `5.4` candidate continuation occurred
