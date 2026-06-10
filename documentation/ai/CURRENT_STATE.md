# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
Align `janus-skill-router` model routing with the matrix and allowed policy levels.

## Active Phase
Skill Router Model Policy Microfix

## Last Decision
`documentation/backlog/BACKLOG.md` remains the binding backlog source.
`documentation/backlog/BACKLOG_ACTIVE_SUMMARY.md` becomes the preferred compact orientation artifact for backlog overview and orchestration questions.
When summary and backlog disagree or detail matters, skills must read `BACKLOG.md`.
The legacy `BLOCKED` section remains a note-only area, while the two structurally misplaced READY items live in the canonical `READY` section.
Repo-skill governance must distinguish versioned repo skill sources under `documentation/codex/skills/` from local installed Codex dev skills under `C:\Users\pruve\.codex\skills\`.
`janus-skill-router` must treat bare acknowledgements as continuation signals only, not as handoff substitutes.
`janus-skill-router` model policy should stay limited to `5.4 mini`, `5.4`, and `5.5` with `low`, `medium`, and `high` reasoning.

## Last Codex Work
Removed `5.2` from the router model policy and narrowed the allowed reasoning labels to the three supported levels.

## Changed Files
- documentation/ai/CURRENT_STATE.md
- documentation/codex/skills/janus-skill-router/SKILL.md

## Tests / Validation
- Targeted model-policy review of `janus-skill-router`
- Verified the router no longer mentions `5.2` or `very high`
- Validation that no other repo skill source file was edited

## Open Risks
- Other skill rows are still `UNREVIEWED`; the matrix remains inventory first, not a full skill-quality review.
- Future router edits may need another pass if model tiers or reasoning labels expand again.

## Next Recommended Step for ChatGPT
Review the updated `janus-skill-router` model policy against `documentation/ai/SKILL_COLLABORATION_MATRIX.md` and choose the next repo skill to move from `UNREVIEWED` into targeted individual review.

## Next Recommended Step for Codex
Use `janus-documentation-update` to keep the collaboration matrix and state aligned, then review the next repo skill one by one.

## Last Updated
2026-06-11 00:11 local time
