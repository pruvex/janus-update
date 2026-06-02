# Codex Dev Environment Audit - 2026-06-02

## Scope

Audit of the Janus Codex project setup after converting
`C:\KI\Janus-Projekt` into the active Codex project workspace and hardening the
development workflow for Diamond-standard work with low token overhead.

This audit covers Codex workflow guardrails only. It does not audit Janus
product behavior.

## Result

Canonical State: `PASS`

The Janus Codex development environment is usable for normal work on `develop`.
Project startup, Git governance, local hooks, installed governance helpers,
healthcheck reminders, and fresh project-thread routing are aligned with the
Janus workflow.

## Implemented Guardrails

- Compact project startup profile:
  - `documentation/codex/CODEX_PROJECT_PROFILE.md`
- Operational runbook:
  - `documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md`
- Reproducible environment verifier:
  - `scripts/verify-codex-dev-environment.ps1`
- Safer save helper:
  - `scripts/save.ps1`
  - requires explicit `-Path` and `-Message`
  - does not use `git add .`
- Active pre-commit hook:
  - `git config core.hooksPath scripts/git-hooks`
  - `scripts/git-hooks/pre-commit.ps1` runs `git_guard.py --staged-only`
- Versioned Git governance helpers:
  - `documentation/codex/skills/janus-git-governance/scripts/git_guard.py`
  - `documentation/codex/skills/janus-git-governance/scripts/propose_changesets.py`
- Installed skill helper sync:
  - `C:\Users\pruve\.codex\skills\janus-git-governance\scripts\git_guard.py`
  - `C:\Users\pruve\.codex\skills\janus-git-governance\scripts\propose_changesets.py`

## Evidence

- `scripts/verify-codex-dev-environment.ps1`: PASS
- `git_guard.py` full-worktree: PASS
- `git_guard.py --staged-only`: PASS
- `propose_changesets.py`: PASS
- `scripts/git-hooks/pre-commit.ps1`: PASS
- `git diff --check`: PASS
- PowerShell parser checks:
  - `scripts/save.ps1`: PASS
  - `scripts/verify-codex-dev-environment.ps1`: PASS
- `/save` without explicit pathspecs:
  - BLOCKED as expected
  - confirms no blind `git add .` behavior
- Installed governance helper hash sync:
  - `git_guard.py`: PASS
  - `propose_changesets.py`: PASS

## Fresh Thread Smoke Test

Purpose: verify that a new Codex project thread in `C:\KI\Janus-Projekt`
starts with minimal context and routes instead of implementing.

Attempt 1:

- Thread: `019e88d8-2472-7393-9128-504a0e12eab5`
- Prompt used a model override.
- Result: system error before assistant routing output.
- Interpretation: tool/thread creation can fail with override; do not treat as
  project-rule failure.

Attempt 2:

- Thread: `019e88d8-d6a6-7160-a5b3-ca3be55816a1`
- No model override.
- Result: PASS.
- Output routed a small Janus UI improvement to `janus-backlog-intake`.
- It stated that Backlog/Handoff and `janus-preimplementation-check` are
  required before implementation.
- It did not modify files.

## Automation Alignment

Existing automations were inspected, not modified.

Janus automation:

- ID: `janus-weekly-monthly-healthcheck`
- Cadence: Saturdays, Europe/Berlin
- Behavior: reminder-only
- Mode logic: first Saturday = `MONTHLY`, other Saturdays = `WEEKLY`
- Workspace: `C:\KI\Janus-Projekt`
- Status: aligned with `AGENTS.md` and `CODEX_WORKFLOW_PLAYBOOK.md`

Personal Codex skill automation:

- ID: `codex-weekly-skill-healthcheck`
- Cadence: Mondays, Europe/Berlin
- Behavior: reminder-only
- Scope: personal Codex skills, not Janus product code
- Status: aligned as separate from Janus healthchecks

No duplicate automation was created.

## Residual Notes

- Fresh-thread creation with explicit model override produced a system error.
  Use default project-thread model for smoke tests unless a model override is
  specifically being tested.
- `master` remains the release branch at `67bff4f4e`.
- Normal work is on `develop`.
- `origin` remains release/update only; development checkpoints go to
  `backup/develop`.

## Recommended Operating Rule

At the start of future Janus work:

1. Read `CODEX_PROJECT_PROFILE.md`.
2. Run or trust the latest `verify-codex-dev-environment.ps1` result.
3. Route through `janus-skill-router`.
4. Load only the bound artifact.
5. Commit and push only via `janus-git-governance`.

## Next Gate

Commit this audit as a Codex governance checkpoint, then push
`develop` to `backup`.
