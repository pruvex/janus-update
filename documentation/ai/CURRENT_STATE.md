# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
Skill-Orchestration Closeout abgeschlossen.

## Active Phase
Ready for Git Governance

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
`janus-spec-to-task` should stay ChatGPT-led, accept exactly one `APPROVED` Feature Spec, block on missing approval evidence, never fill product gaps silently, and emit explicit model/reasoning plus exactly one compact fenced `text` handoff toward `janus-task-breakdown`, `janus-spec-review`, or `janus-spec-generator`.
`janus-task-breakdown` should stay shared, accept exactly one compiled task artifact or clear backlog handoff, release exactly one precheck-ready target task, block on multiple plausible targets, and emit exactly one compact fenced `text` handoff toward `janus-preimplementation-check`, `janus-spec-to-task`, or `janus-backlog-handoff`.
`janus-test-pipeline` should stay Codex-led, keep TestSpec, TestPlan, TestRun, TestResult, and retest evidence clearly separated, allow execution only from a bound plan/run bundle, document `PASS`, `FAIL`, `FLAKY`, and `INCONCLUSIVE` explicitly, and emit exactly one compact fenced `text` handoff toward `janus-final-audit`, `janus-debug`, or caller review.
`janus-debug` should stay Codex-led, bind exactly one failure slice, block on unclear or contradictory evidence, forbid broad history reconstruction and silent product decisions, and emit exactly one compact fenced `text` handoff toward `janus-final-audit`, `janus-documentation-update`, `janus-test-pipeline`, `janus-executioner`, or caller review.
`janus-build-release` should stay Codex-led for local build/verify work, require final-audit and documentation-update evidence before release readiness, keep build/verify separate from publish/tag/push, require `janus-git-governance` plus explicit user approval for all Git/release boundaries, and emit exactly one compact fenced `text` release-evidence handoff toward `janus-git-governance`, `janus-debug`, `janus-final-audit`, or caller review.
`janus-backlog-intake` should stay ChatGPT-led, transform raw wishes/bugs into structured backlog candidates, use `BACKLOG_ACTIVE_SUMMARY.md` first and `BACKLOG.md` only for targeted duplicate or status checks, avoid product decisions, prioritization, and implementation, and emit exactly one compact fenced `text` handoff toward `janus-backlog-prioritization` or `janus-feature-design`.
`janus-backlog-prioritization` should stay ChatGPT-led, work only on existing backlog candidates, use `BACKLOG_ACTIVE_SUMMARY.md` first and `BACKLOG.md` only for targeted cache/status verification, avoid inventing product scope, and emit exactly one compact fenced `text` handoff toward `janus-backlog-handoff` or `janus-feature-design`.
`janus-health-check` should stay Codex-led, stay bounded and read-only, separate reminder-gate behavior from actual hygiene scans, avoid auto-fixes/tests/builds/Git actions unless separately authorized, and emit exactly one short evidence-first fenced `text` handoff when another actor or chat boundary must take over.
`codex-start-of-work-check` should stay Codex-led, remain reminder-only, stay tiny, route the user to `janus-health-check` only after explicit confirmation, and emit a very short fenced `text` block only when a cross-actor boundary really occurs.
`codex-audit-package-builder` should stay Codex-led, build compact packages only from bound evidence, avoid final audit decisions, product decisions, tests, builds, and Git actions, and emit exactly one compact fenced `text` handoff toward `janus-final-audit` when a fresh audit chat or actor boundary is needed.

## Last Codex Work
Completed the final skill-orchestration closeout after the audit-package-builder output-shape alignment.
Confirmed the versioned audit-package-builder script and its skill now use `NEXT: janus-final-audit`, the skill remains consistent with the script, and the matrix still has no `UNREVIEWED` rows.
No further skill work was needed; only Git governance remains if the user approves commit and push.

## Changed Files
- documentation/ai/CURRENT_STATE.md
- documentation/codex/skills/codex-audit-package-builder/SKILL.md

## Tests / Validation
- Verified `git status`, `git diff --name-only`, and `git diff --check`
- Verified no `NEXT: final-skill-audit` remains in the audit-package-builder script or skill
- Verified `NEXT: janus-final-audit` is now the consistent next skill
- Verified `SKILL_COLLABORATION_MATRIX.md` still contains no `UNREVIEWED` rows
- Verified no matrix change is needed
- Ran `git diff --check`

## Open Risks
- Commit and push have not been user-approved yet.

## Next Recommended Step for ChatGPT
Ask the user for explicit commit/push approval or mark the closeout complete locally.

## Next Recommended Step for Codex
Use `janus-git-governance` only after explicit user approval for commit/push.

## Last Updated
2026-06-11 19:55 local time
