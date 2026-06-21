---
name: janus-git-governance
description: Govern Janus Git and GitHub workflow, including branch safety, backup commits, clean changesets, commit messages, pre-audit checkpoints, release branches, tags, and push targets. Use when the user asks to save, commit, push, prepare a PR, inspect git status, split changes, checkpoint work, run audits, build releases, publish to GitHub, or decide whether a commit is appropriate.
---

# Janus Git Governance

## Overview

Use this skill before any Janus commit, push, audit checkpoint, release merge, tag, or GitHub publication. Never commit, push, tag, merge, or reset without explicit user approval.
Do not treat bare acknowledgements like `ok` as approval for commit, push, tag, merge, reset, or release actions.

## Source References

Read only if exact legacy wording is needed:

- `C:\KI\Janus-Projekt\documentation\AI_STUDIO_SYSTEM_PROMPT_V33.md`
- `C:\KI\Janus-Projekt\AGENTS.md`

## Branch Policy

- `develop`: primary working branch for Codex and daily work.
- `master`: stable release branch only.
- Do not commit directly to `master` except during the explicit release protocol.
- If on `master` during normal work, stop and ask to switch to `develop`.

## Remote Policy

- `backup`: private full-code remote. Daily safe commits push here.
- `origin`: public/update remote. Push only `master` and explicit release tags during release.
- Never push development commits to `origin`.
- Never push tags implicitly. Push release tags explicitly only in release flow.

## GitHub Connector Preference

When the next step happens on GitHub, prefer the GitHub connector before raw CLI fallbacks for:

- opening or updating pull requests
- reading or responding to review feedback
- checking or debugging GitHub Actions
- mirroring issues, labels, and assignments
- preparing publishable review state for a PR or release

## Commit Timing

Recommend a commit checkpoint:

- before risky implementation or large refactor
- after a coherent subtask passes validation
- before an independent audit
- before strategy switch after repeated failures
- after documentation update closes a pipeline step
- before release build, only when develop is coherent and validated

Do not recommend a commit:

- for pure planning chat with no file changes
- when tests or validation are known broken and not documented as a WIP checkpoint
- when unrelated dirty changes are mixed with the intended changeset
- immediately after an equivalent checkpoint with no changes

## Changeset Rules

Prefer small, coherent commits:

- one Backlog item, Spec, TestSpec, TestRun, or feature slice per commit
- code + directly related tests + directly related docs together
- generated evidence with the test/spec it proves
- no unrelated formatting or cleanup
- no secret files, local DBs, large binaries, build output, or private logs unless explicitly required and reviewed

## Lean Delivery Mode (Default)

Use Lean Delivery Mode for normal Janus work. The objective is reliable recovery with minimal Git overhead, not a commit for every intermediate artifact.

For internal Dev-/OR-/workhorse-infrastructure slices, Lean Delivery may be used only after the active governance sources classify the slice as Lean-Dev eligible. This skill remains a strict boundary even then: commit, push, tag, merge, release, and remote decisions still require explicit user approval and never become automatic just because the implementation slice itself ran in Lean mode.

- one completed delivery block gets one commit: implementation, directly related tests, required evidence, closeout documentation, `CURRENT_STATE.md`, and `SKILL_USAGE_LOG.md` belong together
- do not create separate commits merely because code, tests, telemetry, task artifacts, or documentation live in different folders
- do not create a checkpoint after each investigation, fixture run, planning note, or status update; checkpoint after the bounded work item has reached its intended validation boundary
- after the requested block is committed and optionally pushed, stop by default; do not reopen old worktree debris for sorting, cleanup, or follow-up commits
- keep unrelated pre-existing changes parked. A dirty worktree is context, not an automatic cleanup task.
- use strict multi-commit splitting only for genuinely independent product changes, a dedicated skill-rule change, release-only work, or a risk boundary that needs independent rollback
- a dedicated governance skill change may include its matching `CURRENT_STATE.md` and `SKILL_USAGE_LOG.md` update as one governance commit; it must not include product work

Strict-only Git boundary even during Lean Dev work:

- explicit user approval is still required for `git add`, `git commit`, and `git push`
- `backup/develop` remains the only normal remote target for development checkpoints
- product, release, and public-remote decisions never inherit Lean authority from a Dev-only slice

Lean mode for small validated Janus work means:

- one small `BACKLOG-XXX` item may stay in one commit even if it spans product code, related tests, task/precheck/execution/final-audit artifacts, backlog marker updates, dashboard sync, registry/project-state/changelog updates, `AUDIT_PACKAGE.md`, and `documentation/codex/SKILL_USAGE_LOG.md`
- do not split only because code, audit evidence, backlog sync, and closeout docs land in different folders
- split only when there is genuinely unrelated scope, especially parallel product work, separate skill-rule changes, release-only verification, local debris, or a second independent feature slice

Default stop rule after small work:

- after the intended small Backlog item is committed and, if requested, pushed to `backup`, stop by default
- do not automatically start historical cleanup, archaeology, leftover sorting, or follow-up commit hunting just because the worktree is still dirty
- treat pre-existing unrelated dirt as parked context unless the user explicitly asks to clean it up now
- at most recommend one product commit and, if truly needed, one small follow-up governance/doc commit for the same item; anything beyond that needs explicit user intent

If the worktree is dirty, inspect and propose commit groups before staging.

## Commit Message Format

Use concise Conventional Commit style:

```text
type(scope): summary

Evidence:
- <test/check/result>

Artifacts:
- <Spec/TestSpec/TestRun/Backlog path if relevant>
```

Types:

- `feat`
- `fix`
- `test`
- `docs`
- `chore`
- `refactor`
- `build`
- `release`

For Backlog-linked work, include `BACKLOG-XXX` in the summary or body.

## Safe Commands

For a clearly bound Lean Delivery block, run only the targeted safety checks:

```powershell
git status --short
git add -- <bound paths>
git diff --cached --check
git diff --cached --name-only
```

Use pathspecs, not `git add .`, unless the entire dirty tree has been reviewed and belongs to one changeset. State the bound paths once, then keep the operator summary short.

Run the full-worktree guard and broad diff checks only when the scope is unclear, the first commit in a long-running mixed worktree is being selected, a release or independent audit is imminent, or a risky/refactoring change crosses multiple product areas. Do not run broad archaeology repeatedly for an already bound and validated work item.
If the actor or chat boundary changes, include exactly one compact fenced `text` handoff block before any Git action plan.

Treat the guard as a coherence check, not a mechanical bucket counter:

- if one validated Backlog item plus its evidence and closeout docs is the only intended scope, a single commit is usually correct
- if `skill-rules` appears alongside product work, keep it separate unless the user explicitly wants a governance follow-up in the same batch
- if uncertain, prefer one intentional commit over automatically exploding the same feature into several docs-only commits
- if the intended item is already safely committed, prefer `STOP` over proposing cleanup of older unrelated leftovers

Allowed only after user approval:

```powershell
git add -- <paths>
git commit -m "<message>"
git push backup develop
```

Approval must be explicit and specific; a bare `ok` only continues work when it clearly refers to a previously recommended non-Git step.

## Release Flow

Release uses `janus-build-release` plus this Git gate:

1. `develop` must be clean and pushed to `backup`.
2. Merge `develop` to `master` intentionally.
3. Version bump and tag only during release.
4. Run release build/verification.
5. Push `master` and explicit release tag to `origin`.
6. Merge `master` back to `develop`.

Never run release publishing from dirty worktree or normal development branch.

## CURRENT_STATE Requirement

Before finishing a substantial Janus work block, update `documentation/ai/CURRENT_STATE.md`.

A Janus work block is substantial when at least one of these is true:

- files changed
- validation executed
- a blocker documented
- a formal next-skill handoff produced

Pure routing replies, short status answers, and other mini-interactions do not require a CURRENT_STATE update.

Keep the update concise and include:

- what changed
- which files changed
- which checks ran
- what remains risky or open
- what ChatGPT should review next
- what Codex should do next

CURRENT_STATE does not replace Backlog, Spec, TestSpec, TestRun, TestResult, audit package, or dashboard artifacts.

Commit and push remain gated by `janus-git-governance` and explicit user approval.

If no push happens or push fails, the Git result or recommendation must explicitly say that a remote such as GitHub may not contain the latest CURRENT_STATE yet.

## Output Format

Use:

```text
GIT GOVERNANCE CHECK
- Branch:
- Dirty State:
- Remote Safety:
- Large File Risk:
- Recommended Action:
- Commit Needed: YES | NO | WAIT
- Proposed Changesets:
- Commands Requiring Approval:
- Next Skill:
```

If action is unsafe, set `Commit Needed: WAIT` and explain the blocker.
