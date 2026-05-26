---
name: janus-git-governance
description: Govern Janus Git and GitHub workflow, including branch safety, backup commits, clean changesets, commit messages, pre-audit checkpoints, release branches, tags, and push targets. Use when the user asks to save, commit, push, prepare a PR, inspect git status, split changes, checkpoint work, run audits, build releases, publish to GitHub, or decide whether a commit is appropriate.
---

# Janus Git Governance

## Overview

Use this skill before any Janus commit, push, audit checkpoint, release merge, tag, or GitHub publication. Never commit, push, tag, merge, or reset without explicit user approval.

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

Before a commit, run:

```powershell
python C:\Users\pruve\.codex\skills\janus-git-governance\scripts\git_guard.py C:\KI\Janus-Projekt
git status --short
git diff --check
```

Then propose an explicit staging plan. Use pathspecs, not `git add .`, unless the entire dirty tree has been reviewed and belongs to one changeset.

Allowed only after user approval:

```powershell
git add -- <paths>
git commit -m "<message>"
git push backup develop
```

## Release Flow

Release uses `janus-build-release` plus this Git gate:

1. `develop` must be clean and pushed to `backup`.
2. Merge `develop` to `master` intentionally.
3. Version bump and tag only during release.
4. Run release build/verification.
5. Push `master` and explicit release tag to `origin`.
6. Merge `master` back to `develop`.

Never run release publishing from dirty worktree or normal development branch.

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
