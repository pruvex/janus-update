# Codex Project Profile: Janus

Purpose: compact startup profile for Codex threads opened inside
`C:\KI\Janus-Projekt`. This file is an orientation layer only. Binding rules
remain `AGENTS.md`, the Janus skills, and the named pipeline artifacts.
Operational details live in `documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md`.

## What Janus Is

Janus is a modular AI assistant project with backend, frontend, Electron app,
provider silos, skills, memory, calendar, mail, release, backlog, specs,
tests, dashboard data, and documentation. Work is governed by the Diamond
pipeline: route first, bind artifacts, verify with evidence, then close with a
canonical state.

## First Files

Load only what the active request needs.

1. `AGENTS.md`
2. `documentation/codex/CODEX_WORKFLOW_PLAYBOOK.md`
3. `documentation/pipeline/PIPELINE_CONTRACT.md`
4. The bound Backlog, Spec, TestSpec, task, handoff, TestRun, or changed file
   named by the user or selected skill

Do not load broad archives, historical logs, full registries, or the whole
repository unless a bound artifact explicitly requires it.

## Routing Defaults

- Always start Janus product/project work through `janus-skill-router`.
- Small bugs, improvements, and technical debt go through Backlog intake,
  prioritization, dashboard handoff, preimplementation check, then execution.
- Vague or product-shaping feature ideas go through feature design and the Spec
  pipeline before implementation.
- Code edits require a valid task artifact and passed preimplementation check.
- Git commit, push, tag, merge, release, delete, and publish actions require
  explicit user approval and `janus-git-governance`.

## Branch Defaults

- `develop`: normal Janus work.
- `master`: release and production publish only.
- After release, merge `master` back to `develop` before normal work resumes.
- Never stage with `git add .`; use explicit pathspecs only.
- Local clone guard: `git config core.hooksPath scripts/git-hooks`.
- Environment verification: `scripts/verify-codex-dev-environment.ps1`.

## Model Defaults

- `5.6 Luna`: separated low-risk mechanical blocks and simple status/short-summary work when cheaper than staying on warm `5.6 Terra`.
- `5.6 Terra`: Janus workhorse for feature design, specs, TestSpecs, implementation, tests, local debugging, and artifact review.
- `5.6 Sol`: security, privacy, architecture risk, final audit, release gates, and the hardest deep-review or escalation slices when the current Codex run can actually start `gpt-5.6-sol`.
- `5.5` plus `5.4` / `5.4-mini`: legacy fallbacks when an existing warm context or older handoff makes a same-model finish more efficient than an immediate switch.

Cache strategy: stay on `5.6 Terra` when possible and change only reasoning
effort. If the `5.6 Terra` context is warm, handle short mechanical side steps
with `5.6 Terra` low unless switching to `5.6 Luna` is still likely cheaper
after accounting for context loss and the return to `5.6 Terra`. Escalate to
`5.6 Sol` only when confidence or risk justifies the cost and runtime support is
confirmed. If Codex reports `gpt-5.6-sol` is unsupported for the active ChatGPT
account, use `5.6 Terra` high and record
`SOL_UNAVAILABLE_FOR_CHATGPT_CODEX_ACCOUNT`. Older warm `5.5` or `5.4`
contexts may still be finished in place when the remaining block is shorter and
cheaper than a fresh model migration.

## Completion Checklist

Every substantive step should end with:

- Canonical State: `PASS`, `BLOCKED`, `NEEDS_INFO`, `FAILED`, `HANDOFF`, or
  `ESCALATED`
- Checks run or blocker documented
- Changed files or `NONE`
- Next skill or gate

For this profile itself, keep changes small, factual, and aligned with
`AGENTS.md`.
