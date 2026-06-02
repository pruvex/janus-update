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

- `5.4 mini`: separated low-risk mechanical blocks when cheaper than staying on warm `5.4`.
- `5.4`: Janus workhorse for feature design, specs, TestSpecs, implementation, tests, local debugging, and artifact review.
- `5.5`: security, privacy, architecture risk, final audit, release gates.
- `5.2`: simple status or short summaries.

Cache strategy: stay on `5.4` when possible and change only reasoning effort.
If the `5.4` context is warm, handle short mechanical side steps with `5.4`
low unless switching to `5.4 mini` is still likely cheaper after accounting for
context loss and the return to `5.4`. Escalate to `5.5` only when confidence or
risk justifies the cost.

## Completion Checklist

Every substantive step should end with:

- Canonical State: `PASS`, `BLOCKED`, `NEEDS_INFO`, `FAILED`, `HANDOFF`, or
  `ESCALATED`
- Checks run or blocker documented
- Changed files or `NONE`
- Next skill or gate

For this profile itself, keep changes small, factual, and aligned with
`AGENTS.md`.
