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

## Git Safety

- Local hook path should be:
  - `git config core.hooksPath scripts/git-hooks`
- Verify local Codex setup with:
  - `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify-codex-dev-environment.ps1`
- Before staging:
  - `python documentation/codex/skills/janus-git-governance/scripts/git_guard.py C:\KI\Janus-Projekt`
  - `python documentation/codex/skills/janus-git-governance/scripts/propose_changesets.py C:\KI\Janus-Projekt`
  - `git diff --check`
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
  belong under `debug_logs/`.
- Versioned dev start paths should not create recurring backend or Vite
  runtime logs directly in the repository root.
- Historical root log artifacts are hygiene cleanup, not proof of the intended
  target path.

## Completion Template

End substantive work with:

- Canonical State
- Checks
- Changed files
- Next skill or gate
- Commit/push status if applicable
