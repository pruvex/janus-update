# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
Give ChatGPT a reliable compact backlog overview from the repo without loading the full BACKLOG.md every time.

## Active Phase
Backlog Summary Rollout

## Last Decision
`documentation/backlog/BACKLOG.md` remains the binding backlog source.
`documentation/backlog/BACKLOG_ACTIVE_SUMMARY.md` becomes the preferred compact orientation artifact for backlog overview and orchestration questions.
When summary and backlog disagree or detail matters, skills must read `BACKLOG.md`.

## Last Codex Work
Created `documentation/backlog/BACKLOG_ACTIVE_SUMMARY.md`, summarized active backlog state from `BACKLOG.md`, and updated Janus routing/backlog skills so they prefer the summary for overview but fall back to `BACKLOG.md` for details and contradictions.

## Changed Files
- documentation/ai/CURRENT_STATE.md
- documentation/backlog/BACKLOG_ACTIVE_SUMMARY.md
- documentation/codex/skills/janus-skill-router/SKILL.md
- documentation/codex/skills/janus-backlog-intake/SKILL.md
- documentation/codex/skills/janus-backlog-prioritization/SKILL.md
- documentation/codex/skills/janus-backlog-handoff/SKILL.md

## Tests / Validation
- Verified that `documentation/backlog/BACKLOG.md` exists and remains the canonical source
- Targeted backlog review of active `NEEDS INFO`, `READY`, `IN PROGRESS`, and malformed `BLOCKED` area
- Repo skill review and update for backlog-summary-first orchestration guidance
- Manual consistency check that summary explicitly defers to `BACKLOG.md` for details and contradictions

## Open Risks
- `BACKLOG_ACTIVE_SUMMARY.md` can drift if later backlog edits are not mirrored promptly.
- The current `BLOCKED` area in `BACKLOG.md` is structurally inconsistent and may confuse future summary/parsing logic if left unchanged.
- No remote reflects this backlog-summary follow-up until a later user-approved Git step happens.

## Next Recommended Step for ChatGPT
Use `documentation/backlog/BACKLOG_ACTIVE_SUMMARY.md` first for backlog overview, then open `BACKLOG.md` only for exact item details, contradictions, or acceptance criteria.

## Next Recommended Step for Codex
Use `janus-git-governance` to prepare a checkpoint plan for the backlog-summary rollout and decide later whether the malformed `BLOCKED` section should be normalized as a separate cleanup item.

## Last Updated
2026-06-10 23:16 local time
