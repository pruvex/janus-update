---
name: janus-skill-router
description: Route Janus project work to the correct Diamond pipeline skill, model, reasoning level, chat strategy, context strategy, and next handoff. Use for any Janus request about feature ideas, backlog items, specs, testspecs, implementation, debugging, audits, documentation updates, dashboard sync, health checks, build, or release.
---

# Janus Skill Router

## Overview

Use this skill before acting on Janus work. Classify the user's request, recommend the next Janus skill, recommend model and reasoning settings, then either continue or stop at a model-switch gate.

## Required Context

Prefer these files, only as needed:

- `C:\KI\Janus-Projekt\AGENTS.md`
- `C:\KI\Janus-Projekt\documentation\pipeline\PIPELINE_CONTRACT.md`
- `C:\KI\Janus-Projekt\documentation\backlog\BACKLOG.md`
- bound Spec, TestSpec, Handoff, TestRun, or changed files named by the user

Do not load broad archives unless the active artifact references them.

## Routing Output

Before substantial work, output:

```text
MODEL SWITCH GATE
- Skill:
- Empfohlenes Modell:
- Empfohlene Intelligenz:
- Neuer Chat:
- Kontextstrategie:
- Grund:
```

If current setup is acceptable, say so and continue. If a switch is recommended, wait for user `ok`, `bleib hier`, or another explicit instruction.

## Skill Selection

Use:

- `janus-feature-design` for vague feature ideas and product decisions.
- `janus-spec-generator` for generating a feature spec from a decision summary.
- `janus-spec-normalizer` for final copy-safe parser-safe spec formatting.
- `janus-backlog-intake`, `janus-backlog-prioritization`, or `janus-backlog-handoff` for small bugs, improvements, and execution routing.
- `janus-spec-review`, `janus-spec-to-task`, `janus-task-breakdown`, or `janus-preimplementation-check` before implementation.
- `janus-executioner` for code changes.
- `janus-debug` for failed tests, regressions, or unclear broken behavior.
- `janus-test-pipeline` for TestSpec to TestPlan to execution evidence.
- `janus-final-audit` for release-critical or post-implementation audit.
- `janus-documentation-update` for registry, Backlog, dashboard, changelog, and handoff updates.
- `janus-build-release` for build, packaging, release notes, and artifact verification.
- `janus-health-check` for hygiene, stale artifacts, drift, or documentation consistency.
- `janus-git-governance` for save, commit, push, branch, tag, PR, checkpoint, audit-prep, or release Git/GitHub decisions.

## Model Routing

- `5.5`, high/very high: architecture, security, privacy, prompt-injection, complex failure analysis, release gates, final audits.
- `5.4`, medium/high: feature design, specs, TestSpecs, complex product decisions, pipeline artifact review.
- `5.4 mini`, low/medium: Backlog cleanup, documentation normalization, snapshot sync, mechanical checks.
- `5.3 codex`, medium/high: implementation, refactoring, tests, debugging, local repository work.
- `5.2`, low: summaries, small text edits, lightweight status checks.

## Chat Strategy

Recommend a new chat for:

- new feature design
- large spec generation
- independent audit
- release gate review
- long or noisy current context

Stay in the current chat for:

- ongoing implementation
- follow-up tests
- documentation update tied to just-completed work
- user asks for status or continuation

## Completion Format

End each routed step with:

```text
Canonical State:
Executed Checks:
Changed Files:
Next Skill:
Evidence Paths:
```
