# Productive Dev Workhorse Operator Recommendation Matrix - 2026-06-23

Status: OPERATOR GUIDANCE / LIVE EVIDENCE ONLY / NO PRODUCTION ROUTING / NO CANONICAL ROUTING-TABLE UPDATE

## Scope

This matrix compresses the current real OpenRouter everyday evidence into one operator-facing view for the bounded Janus workhorse paths we have actually exercised.

It covers:

- the seven live-evidenced `5.4 mini` documentation skills
- `quickchange_patch_review`
- `execution_patch_candidate`

It does not create global OR approval, does not activate production routing, does not grant autonomous apply/write authority, and does not change Codex final ownership.

## Operator Recommendation Matrix

| lane_id | task_class_or_skill | selected_or_model | latest_accepted_actual_cost | operator_recommendation | reason |
| --- | --- | --- | --- | --- | --- |
| `DOC-SKILL-001` | `janus-documentation-update` | `openai/gpt-oss-20b` | `0.000087240` | `PREFER_OR` | cheapest accepted deterministic mini documentation lane |
| `DOC-SKILL-002` | `janus-documentation-update` | `openai/gpt-oss-20b` | `0.000098740` | `PREFER_OR` | cheap accepted summary/report lane |
| `DOC-SKILL-003` | `janus-documentation-update` | `openai/gpt-oss-20b` | `0.000084080` | `PREFER_OR` | clean accepted handoff lane and lowest cost in the set |
| `DOC-SKILL-006` | `janus-documentation-update` | `openai/gpt-oss-120b` | `0.000090940` | `PREFER_OR` | mechanical formatting lane stayed extremely cheap and bounded |
| `DOC-SKILL-008` | `janus-documentation-update` | `qwen/qwen3.5-flash-02-23` | `0.000641095` | `OR_OPTIONAL` | accepted and bounded, but less cost-attractive than the primary mini lanes |
| `DOC-SKILL-009` | `janus-documentation-update` | `qwen/qwen3.5-flash-02-23` | `0.000444210` | `OR_OPTIONAL` | accepted and bounded, but not a top savings lane |
| `DOC-SKILL-010` | `janus-documentation-update` | `qwen/qwen3.5-flash-02-23` | `0.000525460` | `OR_OPTIONAL` | accepted and bounded, but clearly pricier than the smallest deterministic lanes |
| `QUICKCHANGE-001` | `quickchange_patch_review` | `deepseek/deepseek-v4-flash` | `0.000119840` | `PREFER_OR` | real accepted bounded patch proposal on the productive direct-OR path with clean capture and healthcheck ingestion |
| `EXECUTION-001` | `execution_patch_candidate` | `deepseek/deepseek-v4-flash` | `0.000477680` | `OR_REVIEW_FIRST` | accepted bounded patch-candidate evidence exists, but Codex must still inspect and often adapt or reject the proposed repo diff |

## Practical Rule

- Use `PREFER_OR` when the lane already shows both stable transport and strong bounded output fitness for the class.
- Use `OR_OPTIONAL` when the lane is valid and bounded but not yet the best default from a cost/value perspective.
- Use `OR_REVIEW_FIRST` when the lane is now technically proven and can return accepted bounded artifacts, but the output still requires strict Codex repo-contract review before any apply decision.

## Decision Summary

Primary OR workhorse lanes today:

- `DOC-SKILL-001`
- `DOC-SKILL-002`
- `DOC-SKILL-003`
- `DOC-SKILL-006`
- `quickchange_patch_review`

Secondary OR lanes today:

- `DOC-SKILL-008`
- `DOC-SKILL-009`
- `DOC-SKILL-010`

Review-first OR lane today:

- `execution_patch_candidate`

## Why `execution_patch_candidate` Is Not Yet `PREFER_OR`

The higher-budget `DEV-WORKHORSE-EXECUTION-GATE-003` retry proved the important missing technical points:

- `finish_reason=stop`
- accepted bounded validation
- usage and actual cost captured
- healthcheck ingestion passed

But the concrete returned patch still proposed helper names and persistence assumptions that do not map cleanly onto the current local repo contracts for `BACKLOG-108`. That means the class is now proven as a real OR candidate lane, but still not a blind-apply lane.

## What Remains Forbidden

- no production routing activation
- no canonical routing-table update
- no autonomous OR apply/write authority
- no global OR approval
- no bypass of Codex diff review, validation review, or final ownership

## Fast Operator Heuristic

- Tiny deterministic mini docs: choose `OR` first.
- Small bounded quickchange patch proposals: choose `OR` first.
- Larger prechecked implementation slices: `OR` is now a real option, but treat the result as a candidate patch for Codex review, not as an accepted implementation by default.
