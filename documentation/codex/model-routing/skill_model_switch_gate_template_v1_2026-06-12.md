# Skill Model Switch Gate Template v1 - 2026-06-12

## Purpose

Provide a reusable model-switch gate pattern for future Janus skills that need task-specific model and reasoning sufficiency checks before acting.

## Required `DECLARED CODEX MODEL`

Treat the current Codex model and reasoning level as user-declared, not self-detected.

If `DECLARED CODEX MODEL` is missing, stop before deciding sufficiency and ask the user to provide or confirm the selected model and reasoning level.

## Stop-Before-Sufficiency Rule

Do not decide whether the selected model/reasoning is sufficient until the request is classified against the skill's routing table or model requirements and the declared model/reasoning is known.

If the declared model/reasoning is insufficient, stop before editing, validating, routing with authority, or producing binding output.

## User-Confirmation Rule

Tell the user exactly which model and reasoning level to select. Continue only after the user confirms the selection or explicitly instructs Codex to stay in the current setup.

## Blocked-Scope Upstream Rule

If the matching task is outside the skill's safe scope or belongs to upstream governance, do not solve it inside the current skill. Route to the required upstream skill path and return only after the upstream decision, audit, validation, or approval evidence exists.

## No Auto-Switch / No OR / No Production Routing

Do not switch models automatically.

Do not activate OpenRouter.

Do not enable production routing.

## Required Dry-Run Cases

Run these five dry-run cases before adopting the gate for a future skill:

- sufficient declared setup: expected `PASS`
- insufficient declared setup: expected `PASS`
- user confirmation after model switch: expected `PASS`
- missing `DECLARED CODEX MODEL`: expected `PASS`
- blocked_scope routing: expected `PASS`
