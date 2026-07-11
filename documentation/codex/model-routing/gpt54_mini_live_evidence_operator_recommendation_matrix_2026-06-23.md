# GPT-5.4 Mini Live Evidence Operator Recommendation Matrix - 2026-06-23

Status: OPERATOR GUIDANCE / LIVE EVIDENCE ONLY / NO PRODUCTION ROUTING / NO CANONICAL ROUTING-TABLE UPDATE

## Scope

This matrix converts the completed seven-skill mini-documentation live evidence set into simple operator guidance for bounded everyday use.

It applies only to:

- `DOC-SKILL-001`
- `DOC-SKILL-002`
- `DOC-SKILL-003`
- `DOC-SKILL-006`
- `DOC-SKILL-008`
- `DOC-SKILL-009`
- `DOC-SKILL-010`

It does not create a global OR approval, does not activate production routing, does not update the canonical routing table, and does not change the fixed-model `Auto-sparsam` baseline.

## Operator Recommendation Matrix

| skill_id | selected_or_model | actual_or_cost | operator_recommendation | reason |
| --- | --- | --- | --- | --- |
| `DOC-SKILL-001` | `openai/gpt-oss-20b` | `0.000087240` | `PREFER_OR` | very cheap, deterministic summary lane |
| `DOC-SKILL-002` | `openai/gpt-oss-20b` | `0.000098740` | `PREFER_OR` | cheap summary/report lane with clean live completion |
| `DOC-SKILL-003` | `openai/gpt-oss-20b` | `0.000084080` | `PREFER_OR` | cheapest accepted handoff lane |
| `DOC-SKILL-006` | `openai/gpt-oss-120b` | `0.000090940` | `PREFER_OR` | mechanical formatting lane stayed extremely cheap |
| `DOC-SKILL-008` | `qwen/qwen3.5-flash-02-23` | `0.000641095` | `OR_OPTIONAL` | valid and bounded, but materially more expensive than the cheapest lanes |
| `DOC-SKILL-009` | `qwen/qwen3.5-flash-02-23` | `0.000444210` | `OR_OPTIONAL` | valid and bounded, but not a top savings lane |
| `DOC-SKILL-010` | `qwen/qwen3.5-flash-02-23` | `0.000525460` | `OR_OPTIONAL` | valid and bounded, but more expensive than small summary/handoff work |

## Quick Rule

- If the task is a tiny deterministic summary, handoff, or mechanical formatting block, prefer `OpenRouter`.
- If the task is still in the eligible mini scope but feels less deterministic or less cost-attractive, keep `OpenRouter` available as an option, not the default.
- If the task drifts into state authority, policy interpretation, release, git-governance, canonical routing, or broader product meaning, stay on local `Codex`.

## Decision

Primary OR workhorse lane:

- `DOC-SKILL-001`
- `DOC-SKILL-002`
- `DOC-SKILL-003`
- `DOC-SKILL-006`

Secondary OR lane:

- `DOC-SKILL-008`
- `DOC-SKILL-009`
- `DOC-SKILL-010`

## Boundary Reminder

- fixed-model `Auto-sparsam` remains canonical
- OpenRouter remains bounded workflow support only
- no production routing is activated
- no canonical routing-table update is made
- no global OR approval is created
