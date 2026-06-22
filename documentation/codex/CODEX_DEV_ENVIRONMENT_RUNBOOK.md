# Janus Codex Dev Environment Runbook

Purpose: repeatable low-token workflow for Codex work inside
`C:\KI\Janus-Projekt`. This runbook operationalizes `AGENTS.md`,
`CODEX_PROJECT_PROFILE.md`, and the Janus pipeline. It does not replace them.

## Default Session Start

1. Confirm project root is `C:\KI\Janus-Projekt`.
2. Read `documentation/codex/CODEX_PROJECT_PROFILE.md`.
3. Route through `janus-skill-router`.
4. Load only the active binding artifact.
5. If the request starts normal Janus work after a release, verify branch is
   `develop` and that `master` has been merged back.

## Normal Work

- One goal, one leading skill, one bound artifact.
- Product changes require Backlog/Spec/task visibility and preimplementation
  evidence before code edits.
- Prefer narrow commands:
  - `rg`
  - targeted `Get-Content`
  - exact test files or scripts
- Keep archives, old logs, and broad registries out of context unless a bound
  artifact names them.

## Productive Dev-Workhorse Entry

- The dedicated productive Dev-workhorse entry is the runner
  `documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py`.
- This entry is bounded to `productive_dev_workhorse_path` only and must not be
  treated as a broad OR activation for existing Janus skills.
- The visible operator gate in this runner uses `1 = Codex` and `2 = OR`.
- The visible gate must show one fixed recommended OR model from the sealed
  class contract and one explicit pre-call cost basis derived from the bound
  budget profile before any wrapper or dispatcher path can start.
- Repo-versioned skill sources and installed skill working copies that expose
  this everyday Dev entry must mirror the same visible wording:
  `1 = Codex` and `2 = OR`.
- Missing fixed model mapping, missing cost basis, missing estimated cost,
  missing confidence, failed eligibility, or a path
  outside `productive_dev_workhorse_path` must abort before any wrapper or
  dispatcher invocation.
- The operator does not choose a free model in this path. The model remains
  fixed per allowed task class until a later bounded review changes the
  contract explicitly.
- Selecting `2 = OR` continues to use the already existing sealed bounded
  delegated runtime from `TASK-SPEC22.3` and then finalizes one dedicated
  Dev-workhorse session telemetry row plus one healthcheck summary for that
  workflow id.
- `TASK-SPEC25.2` changes only the visible gate wording and fail-closed prompt
  prerequisites. It does not create a new delegated runtime approval or a new
  production authority seam.
- Dedicated Dev-workhorse closeout must show actual OR cost when usage exists,
  or an explicit missing-usage / fallback note when truthful cost closeout is
  unavailable.
- This remains Dev-only workflow tooling. It is not production routing, not a
  canonical routing-table update, and not a broad activation of existing Janus
  skills.

## Lean-vs-Strict Entry Rules

- Lean-Dev eligible:
  - repo-owned Dev-governance artifacts under `development/`
  - this Dev-environment runbook when the slice only changes local Dev workflow guidance
  - the dedicated Dev-workhorse entry above and adjacent repo-owned Dev-only capture, telemetry, and operator-support artifacts when the slice stays explicitly Dev-only
- Strict-only:
  - any Janus product skill path or user-facing runtime flow
  - release, publish, merge, tag, and public remote actions
  - production routing claims, canonical routing-table changes, or new productive approvals
  - installed skill working copies under `C:\Users\pruve\.codex\skills`

If a requested slice crosses both categories, stop Lean handling and route back through the strict Janus path.

## Git Safety

- Local hook path should be:
  - `git config core.hooksPath scripts/git-hooks`
- Verify local Codex setup with:
  - `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify-codex-dev-environment.ps1`
- Before staging:
  - `python documentation/codex/skills/janus-git-governance/scripts/git_guard.py C:\KI\Janus-Projekt`
  - `python documentation/codex/skills/janus-git-governance/scripts/propose_changesets.py C:\KI\Janus-Projekt`
  - `git diff --check`
- Even in Lean-Dev mode, commit/push/tag/merge remain explicit `janus-git-governance` boundaries and require user approval.
- Stage explicit pathspecs only.
- Commit/push/tag/merge/release only after explicit user approval.
- Development commits go to `backup/develop`, never `origin`.

## Release Aftercare

After any release from `master`:

1. Stop running Janus processes before branch changes.
2. Fast-forward or merge `master` back into `develop`.
3. Return the main workspace to `develop`.
4. Re-run Git guard and `git status --short --branch`.
5. Do not resume normal work while beta/release fixes exist only on `master`.

## Quality And Cost Bias

- Quality gate first: routing, binding artifact, evidence, canonical state.
- Cost gate second: compact profile first, narrow files, no full-history reads.
- Escalate model/chat only when risk or confidence requires it.
- Log substantive workflow improvements in
  `documentation/codex/SKILL_USAGE_LOG.md`.

## Local Runtime Logs

- Local dev runtime logs for `npm run start-backend-only`,
  `npm run start-backend-only-without-reload`, and `npm run start-vite`
  belong under `documentation/logs/dev-runtime/`.
- Local startup telemetry markers and aggregated startup timing logs belong
  under `documentation/logs/janus_startup_telemetry.log`.
- Versioned dev start paths should not create recurring backend or Vite
  runtime logs directly in the repository root.
- Versioned startup telemetry paths should not write into ad-hoc folders such
  as `documentation/Startup log`.
- Historical root log artifacts are hygiene cleanup, not proof of the intended
  target path.

## Local Runtime Data

- The active Janus application SQLite database belongs under
  `%APPDATA%\Janus Projekt\janus.db`, matching `backend/data/database.py`.
- Root-level `chat_history.db` and `costs.db` are legacy local split-db
  artifacts, not the intended active runtime persistence path.
- Root-level `janus.db` or `janus_fallback.db` files are stray local-state
  artifacts and should not be treated as the canonical runtime data location.

## Completion Template

End substantive work with:

- Canonical State
- Checks
- Changed files
- Next skill or gate
- Commit/push status if applicable
