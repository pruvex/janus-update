---
name: janus-skill-router
description: Route Janus project work to the correct Diamond pipeline skill, model, reasoning level, chat strategy, context strategy, and next handoff. Use for any Janus request about feature ideas, backlog items, specs, testspecs, implementation, debugging, audits, documentation updates, dashboard sync, health checks, build, or release.
---

# Janus Skill Router

## Overview

Use this skill before acting on Janus work. Classify the user's request, recommend the next Janus skill, recommend model and reasoning settings, then either continue or stop at a model-switch gate.

Default posture for this user: guide the process actively, keep the next step explicit, and prevent skipped gates. If the user says only `ok`, `weiter`, `los`, or similar, continue with the last recommended safe next step. Still require explicit approval for commit, push, tag, merge, release, delete, publish, or risky auto-fix actions.

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

## Request Intake Contract

When the user describes a desired product change, classify it before implementation:

- Small bounded improvement: existing surface, one behavior, local bug, remembered setting, UI polish, small technical debt, low ambiguity. Route to `janus-backlog-intake`, then prioritization and dashboard handoff.
- Larger feature: new/unclear surface, multiple product decisions, persistence or integration design, multiple affected areas, security/privacy/provider risk, or unclear scope. Route to `janus-feature-design` first.

For small bounded improvements, give a compact assessment before or while preparing the Backlog item:

```text
Kurzbewertung:
- Pfad:
- Modelle:
- Aufwand: S | M | L
- Risiko: niedrig | mittel | hoch
- Nutzen: niedrig | mittel | hoch
- Naechster Skill:
```

For larger features, do not create implementation tasks directly. Start decision mode, lock the user's decisions, then route to spec generation, normalization, review, task breakdown, and Backlog/dashboard visibility.

## Model Routing

- `5.5`, high/very high: architecture, security, privacy, prompt-injection, complex failure analysis, release gates, final audits.
- `5.4`, medium/high: feature design, specs, TestSpecs, complex product decisions, pipeline artifact review.
- `5.4 mini`, low/medium: Backlog cleanup, documentation normalization, snapshot sync, mechanical checks.
- `5.3 codex`, medium/high: implementation, refactoring, tests, debugging, local repository work.
- `5.2`, low: summaries, small text edits, lightweight status checks.

## Plugin Routing

Plugins are support tools, not primary workflow owners. Route to a Janus skill first, then recommend plugin support only when it creates concrete evidence or a useful external artifact.

- `Codex Security`: security, privacy, provider, attack-path, validation, or release-risk checks.
- `GitHub Connector`: PRs, issues, review follow-up, CI checks, merge state, and publish flows when work moves through GitHub.
- `Documents`: shareable Word/docx reports, review documents, decision logs, or formal external documentation.
- `Spreadsheets`: tabular analysis for Skill Usage, Healthcheck, Backlog metrics, costs, test matrices, CSV/XLSX.
- `Presentations`: stakeholder decks, roadmap/review presentations, release summaries.
- `Browser`: if available, local UI/Dashboard inspection, screenshots, click-path evidence, visual checks.

Prefer the GitHub connector for:

- creating or updating pull requests
- reviewing actionable feedback
- checking or debugging GitHub Actions
- mirroring issues, labels, and assignments
- preparing reviewable publish flows

Do not recommend installing more plugins by default. Propose a new plugin only when repeated friction shows a clear missing capability.

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

## Working-Style Guardrails

Prefer a narrow guided flow:

- one goal
- one skill
- one bound artifact or one decision question
- one next handoff
- one evidence/check block

Stop and clarify when no artifact is bound, the chat conflicts with the artifact, a product decision is missing, scope has multiple plausible paths, evidence would be missing, or a risky Git/release/destructive action would be needed.

Use `documentation/codex/CODEX_WORKFLOW_PLAYBOOK.md` as the concise operating guide when the user asks how we should work.

## Usage Logging

For substantial Janus skill runs, record a compact usage entry after completion:

```powershell
python documentation\codex\scripts\record_skill_usage.py --skill <skill> --trigger "<short reason>" --model <model> --intelligence <level> --chat same --state <PASS|BLOCKED|NEEDS_INFO|FAILED|HANDOFF|ESCALATED> --artifacts "<paths>" --checks "<checks>" --friction "none" --optimization "none"
```

Do not log pure status replies, simple questions, or git-only execution that does not change the process decision. Use the log to identify repeated friction, over-expensive model choices, missing handoffs, and skill improvements.

## Completion Format

End each routed step with:

```text
Canonical State:
Executed Checks:
Changed Files:
Next Skill:
Evidence Paths:
```
