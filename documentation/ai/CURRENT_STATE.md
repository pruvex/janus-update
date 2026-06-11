# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
Review `janus-spec-review` against the collaboration matrix and align its single-spec, completeness, determinism, task-readiness, and handoff behavior with Diamond standard.

## Active Phase
Spec Review Targeted Review

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
`janus-spec-generator` should stay ChatGPT-led, require one locked decision source, block on open product questions, avoid re-brainstorming, and emit explicit model/reasoning plus exactly one compact fenced `text` handoff toward `janus-spec-normalizer` or `janus-spec-review`.
`janus-spec-normalizer` should stay ChatGPT-led, accept exactly one draft Spec, block on missing or unclear drafts, preserve product meaning, and emit explicit model/reasoning plus exactly one compact fenced `text` handoff toward `janus-spec-review` when control must pass to Codex.
`janus-spec-review` should stay ChatGPT-led, review exactly one Feature Spec, distinguish `APPROVED`, `NEEDS_REVISION`, and `BLOCKED`, never fill product gaps silently, and emit explicit model/reasoning plus exactly one compact fenced `text` handoff toward `janus-spec-to-task`, `janus-spec-generator`, or `janus-feature-design`.

## Last Codex Work
Reviewed `janus-spec-review`, tightened single-spec review rules, clarified decision states, and marked the matrix row as `UPDATED`.

## Changed Files
- documentation/ai/CURRENT_STATE.md
- documentation/ai/SKILL_COLLABORATION_MATRIX.md
- documentation/codex/skills/janus-spec-review/SKILL.md

## Tests / Validation
- Targeted review of `janus-spec-review` against `SKILL_COLLABORATION_MATRIX.md`
- Verified the skill remains ChatGPT-led and single-spec-first
- Verified completeness, determinism, and task-readiness are now explicitly defined
- Verified `APPROVED`, `NEEDS_REVISION`, and `BLOCKED` are clearly separated
- Verified the next handoff to `janus-spec-to-task` or the proper upstream skill is compact and explicit
- Verified bare `ok` is not accepted as a handoff substitute
- Validation that no other repo skill source file was edited

## Open Risks
- Most other skill rows are still `UNREVIEWED`; the matrix remains inventory first, not a full skill-quality review.
- The spec-review handoff may still be harmonized later with spec-to-task formatting.

## Next Recommended Step for ChatGPT
Review the updated `janus-spec-review` row in `documentation/ai/SKILL_COLLABORATION_MATRIX.md` and choose the next repo skill to move from `UNREVIEWED` into targeted individual review.

## Next Recommended Step for Codex
Use `janus-spec-review` only on one Feature Spec, then review the next repo skill one by one.

## Last Updated
2026-06-11 15:59 local time
