# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
Review `janus-backlog-handoff` against the collaboration matrix and align its summary-first routing and handoff behavior with Diamond standard.

## Active Phase
Backlog Handoff Targeted Review

## Last Decision
`documentation/backlog/BACKLOG.md` remains the binding backlog source.
`documentation/backlog/BACKLOG_ACTIVE_SUMMARY.md` becomes the preferred compact orientation artifact for backlog overview and orchestration questions.
When summary and backlog disagree or detail matters, skills must read `BACKLOG.md`.
The legacy `BLOCKED` section remains a note-only area, while the two structurally misplaced READY items live in the canonical `READY` section.
Repo-skill governance must distinguish versioned repo skill sources under `documentation/codex/skills/` from local installed Codex dev skills under `C:\Users\pruve\.codex\skills\`.
`janus-skill-router` must treat bare acknowledgements as continuation signals only, not as handoff substitutes.
`janus-documentation-update` should be shared in governance, usually executed by Codex, and require a compact copyable handoff when the actor or chat boundary changes.
`janus-git-governance` must require explicit Git approval, reject bare `ok` as a substitute, and ask for a compact fenced `text` handoff on actor or chat boundaries.
`janus-backlog-handoff` should stay ChatGPT-led, prefer `BACKLOG_ACTIVE_SUMMARY.md` first, read `BACKLOG.md` only for the selected READY block or contradiction checks, and emit explicit model/reasoning plus one compact fenced `text` handoff for ChatGPT -> Codex transitions.

## Last Codex Work
Reviewed `janus-backlog-handoff`, clarified summary-first routing behavior, modernized next-skill handoff wording, and marked the matrix row as `UPDATED`.

## Changed Files
- documentation/ai/CURRENT_STATE.md
- documentation/ai/SKILL_COLLABORATION_MATRIX.md
- documentation/codex/skills/janus-backlog-handoff/SKILL.md

## Tests / Validation
- Targeted review of `janus-backlog-handoff` against `SKILL_COLLABORATION_MATRIX.md`
- Verified the skill remains ChatGPT-led and routes work into the next Codex-facing skill
- Verified `BACKLOG_ACTIVE_SUMMARY.md` stays the preferred orientation artifact and `BACKLOG.md` is only read selectively
- Verified ChatGPT -> Codex handoffs require model/reasoning plus one compact fenced `text` block and do not allow bare `ok` as a substitute
- Validation that no other repo skill source file was edited

## Open Risks
- Most other skill rows are still `UNREVIEWED`; the matrix remains inventory first, not a full skill-quality review.
- The backlog-handoff copy-box template may still be harmonized later with documentation-update or final-audit formatting.

## Next Recommended Step for ChatGPT
Review the updated `janus-backlog-handoff` row in `documentation/ai/SKILL_COLLABORATION_MATRIX.md` and choose the next repo skill to move from `UNREVIEWED` into targeted individual review.

## Next Recommended Step for Codex
Use `janus-backlog-handoff` to keep READY-item routing compact and deterministic, then review the next repo skill one by one.

## Last Updated
2026-06-11 14:19 local time
