# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
Review `janus-feature-design` against the collaboration matrix and align its decision-locking and handoff behavior with Diamond standard.

## Active Phase
Feature Design Targeted Review

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
`janus-preimplementation-check` should stay Codex-led, validate exactly one target task, emit a compact execution handoff for `janus-executioner` on PASS, and emit a compact fenced `text` handoff back to ChatGPT on `BLOCKED`, `NEEDS_INFO`, `SCOPE_MISMATCH`, or model-switch escalation.
`janus-quickchange` should stay Codex-led, allow only one tiny low-risk change, reroute immediately on scope growth, use same-context `NEXT: janus-documentation-update` on success when possible, and emit exactly one compact fenced `text` handoff when ChatGPT must take over.
`janus-executioner` should stay Codex-led, implement exactly one target task from a valid precheck, stop immediately on scope growth, hand successful bounded work to `janus-final-audit`, and emit exactly one compact fenced `text` handoff when ChatGPT must take over.
`janus-final-audit` should stay shared, prefer independent ChatGPT review for risk/release/unclear evidence, stay strictly evidence-bound, block on unclear packages, route PASS/PASS WITH FIXES to `janus-documentation-update`, and emit exactly one compact fenced `text` handoff when an actor or chat boundary changes.
`janus-feature-design` should stay ChatGPT-led, lock product decisions before spec generation, route simple backlog-worthy requests to `janus-backlog-intake`, and emit explicit model/reasoning plus exactly one compact fenced `text` handoff for ChatGPT -> Codex transitions.

## Last Codex Work
Reviewed `janus-feature-design`, clarified decision-locking boundaries, tightened routing to spec-generator vs backlog-intake, and marked the matrix row as `UPDATED`.

## Changed Files
- documentation/ai/CURRENT_STATE.md
- documentation/ai/SKILL_COLLABORATION_MATRIX.md
- documentation/codex/skills/janus-feature-design/SKILL.md

## Tests / Validation
- Targeted review of `janus-feature-design` against `SKILL_COLLABORATION_MATRIX.md`
- Verified the skill remains ChatGPT-led and user-goal-first
- Verified open product questions now block instead of leaking into `janus-spec-generator`
- Verified locked feature decisions route cleanly to `janus-spec-generator`
- Verified simple backlog-worthy requests route clearly to `janus-backlog-intake`
- Verified bare `ok` is not accepted as a handoff substitute
- Validation that no other repo skill source file was edited

## Open Risks
- Most other skill rows are still `UNREVIEWED`; the matrix remains inventory first, not a full skill-quality review.
- The feature-design decision handoff may still be harmonized later with spec-generator formatting.

## Next Recommended Step for ChatGPT
Review the updated `janus-feature-design` row in `documentation/ai/SKILL_COLLABORATION_MATRIX.md` and choose the next repo skill to move from `UNREVIEWED` into targeted individual review.

## Next Recommended Step for Codex
Use `janus-feature-design` only to lock product decisions before specs, then review the next repo skill one by one.

## Last Updated
2026-06-11 15:27 local time
