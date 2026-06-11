# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
Review `codex-audit-package-builder` against the collaboration matrix and align its evidence-bound audit-package handoff behavior with Diamond standard.

## Active Phase
Audit Package Builder Targeted Review

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
Reviewed `codex-audit-package-builder`, tightened evidence requirements, final-audit boundaries, no-tests/no-builds/no-Git rules, and fresh audit handoff behavior, and marked the matrix row as `UPDATED`.

## Changed Files
- documentation/ai/CURRENT_STATE.md
- documentation/ai/SKILL_COLLABORATION_MATRIX.md
- documentation/codex/skills/codex-audit-package-builder/SKILL.md

## Tests / Validation
- Targeted review of `codex-audit-package-builder` against `SKILL_COLLABORATION_MATRIX.md`
- Verified the skill remains Codex-led and package-building only
- Verified required evidence includes changed files, validation evidence, known risks, audit notes, unresolved blockers, and bound artifacts
- Verified the skill does not decide final audit `PASS`, `PASS WITH FIXES`, or `BLOCKED`
- Verified the skill forbids product decisions, broad chat-history reconstruction, tests, builds, Git actions, and release actions
- Verified the next handoff to `janus-final-audit`, `janus-debug`, `janus-test-pipeline`, or caller review is explicit and compact
- Verified bare `ok` is not accepted as a handoff substitute
- Validation that no other repo skill source file was edited

## Open Risks
- Most other skill rows are still `UNREVIEWED`; the matrix remains inventory first, not a full skill-quality review.
- The audit package builder may still be harmonized later with the concrete output shape of `scripts/build_audit_package.py`.

## Next Recommended Step for ChatGPT
Review the updated `codex-audit-package-builder` row in `documentation/ai/SKILL_COLLABORATION_MATRIX.md` and choose the next repo skill to move from `UNREVIEWED` into targeted individual review.

## Next Recommended Step for Codex
Use `codex-audit-package-builder` only to prepare compact evidence packages, then route actual audit decisions to `janus-final-audit`.

## Last Updated
2026-06-11 18:09 local time
