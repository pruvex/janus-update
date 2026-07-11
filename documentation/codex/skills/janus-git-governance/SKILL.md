---
name: janus-git-governance
description: Govern Janus Git workflow for solo orchestrator mode — master + feature branches, backup remote, codex-sync for ChatGPT, and release publishing. Use when the user asks to save, commit, push, merge, sync CURRENT_STATE, checkpoint, or release.
---

# Janus Git Governance (Solo Git v2)

## Canonical Doc

Read first when unsure:

- `C:\KI\Janus-Projekt\documentation\codex\JANUS_SOLO_GIT.md`

Never commit, push, merge, tag, sync, or reset without **explicit operator approval**.

## Overview

Janus uses **Solo Git v2** — optimized for one orchestrator with VM snapshots, not a multi-dev team.

```text
master              integration branch (committed truth)
feature/<name>      one active feature at a time (recommended)
backup/master       private remote backup after feature lands
origin/codex-sync   ChatGPT remote truth for CURRENT_STATE.md only
origin/master       public releases + explicit tags only
```

**Legacy:** `develop` is deprecated. Do not create new work on `develop`.

## Hard Rules for Codex

1. Normal work happens on `feature/*`, merged to `master` when validated.
2. Do **not** start new work on `develop`.
3. Do **not** use git worktrees unless the operator explicitly requests parallel epics.
4. Do **not** classify, sort, or archaeology-scan dirty worktrees unless the operator explicitly asks.
5. Do **not** report dirty-entry counts as a default gate — parked dirt is normal context.
6. One validated delivery block = **one commit** is OK. Do not split into docs-only micro-commits.
7. Never use `git add .` except the one-time migration archive with operator approval.
8. Commit, push, merge, and codex-sync require explicit approval (`commit: YES`, `push: YES`, `sync: YES`). Bare `ok` is not enough for Git actions.

## Operator Backup Model

- **VM snapshot** = real rollback safety net (operator responsibility before risky work)
- **Git / backup** = feature history + offsite code backup
- **codex-sync** = ChatGPT visibility into what Codex did

## Daily Flow

### Start feature

```powershell
git checkout master
git pull backup master
git checkout -b feature/<short-name>
```

### Finish feature (after validation + CURRENT_STATE update)

```powershell
git checkout master
git merge feature/<short-name> --no-ff
git push backup master
git branch -d feature/<short-name>
```

Then recommend codex-sync (with approval):

```powershell
.\documentation\codex\scripts\sync_codex_current_state.ps1
```

## Remote Policy

| Remote | Branch | Purpose |
|--------|--------|---------|
| `backup` | `master` | private full-code backup |
| `origin` | `codex-sync` | CURRENT_STATE for ChatGPT |
| `origin` | `master` + tags | public release only |

Never push normal development commits to `origin` except codex-sync and release flow.

## codex-sync (Mandatory Recommendation)

After every **substantial** Janus work block:

1. Update `documentation/ai/CURRENT_STATE.md`
2. Recommend sync to `origin/codex-sync` with operator approval
3. Use `documentation/codex/scripts/sync_codex_current_state.ps1`

ChatGPT must treat `origin/codex-sync` as the remote truth for CURRENT_STATE — not `backup/master`.

If sync did not happen, state explicitly that ChatGPT cannot assume a current remote snapshot.

## Commit Timing

Recommend a commit when:

- a bounded feature slice passed validation
- before risky refactor (after VM snapshot reminder)
- before independent audit
- after documentation closeout for a completed item

Do **not** recommend a commit for:

- pure planning chat
- intermediate investigation with no validation boundary
- automatic cleanup of unrelated parked dirt

## Commit Message Format

```text
type(scope): summary

Evidence:
- <check/result>
```

Types: `feat`, `fix`, `docs`, `chore`, `test`, `refactor`, `build`, `release`

## Safe Commands (after approval)

Targeted staging only:

```powershell
git status --short
git add -- <bound paths>
git diff --cached --check
git commit -m "<message>"
git push backup master
```

Or on feature branch before merge:

```powershell
git push backup feature/<short-name>
```

Use `git_guard.py` / `propose_changesets.py` only when:

- scope is unclear
- release is imminent
- first commit after long mixed period and operator asked for review

Do **not** run broad archaeology on every small slice.

## Release Flow

Uses `janus-build-release` plus:

1. `master` clean and validated
2. version bump + tag on `master`
3. build / verify
4. push `master` and explicit release tag to `origin`

No `develop` merge dance.

## CURRENT_STATE Requirement

Before finishing a substantial block, update `documentation/ai/CURRENT_STATE.md`.

Substantial = files changed, validation run, blocker documented, or formal handoff produced.

Keep concise: goal, phase, changed files, checks, risks, next steps for ChatGPT/Codex, timestamp.

## One-Time Migration

If operator asks to clean legacy mixed state:

```powershell
.\documentation\codex\scripts\migrate_solo_git_once.ps1 -ArchiveMixedWip -IHaveVmSnapshot
```

Requires VM snapshot first. Then push `backup master` and run codex-sync with approval.

## Output Format

Keep it short:

```text
GIT CHECK (Solo v2)
- Branch:
- Active feature:
- Action: commit | merge | push | sync | stop
- Approval needed: YES | NO
- Commands:
- codex-sync needed: YES | NO
- Next skill:
```

If unsafe, say `stop` and explain in one sentence. Do not dump dirty-file inventories unless asked.
