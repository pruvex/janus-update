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

## Context Budget

Default to the smallest context that can still make a safe routing decision:

- one bound artifact or one changed-file cluster
- one active decision question
- one next skill

Prefer compact summary artifacts over full source artifacts when available:

- audit package over full audit history
- selected backlog handoff over full backlog reread
- precheck/execution result over old chat history
- marker-specific documentation evidence over broad doc rereads

If you must expand context, state the reason in one line before doing so.

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

If `Neuer Chat: ja`, always include one compact fenced `text` handoff block directly in the user-visible answer so it renders as a gray copy box. Do not make the user reconstruct the next prompt from prose.

Use:

```text
NEW_CHAT_HANDOFF
NEXT: <next skill or audit entry point>
MODEL: <model>/<reasoning>
LOAD:
- <minimal bound artifact path>
- <second artifact path only if required>
ASK: <one-line instruction for the new chat>
DROP:
- <broad history to leave behind>
```

Keep the block minimal. Prefer one primary package such as `AUDIT_PACKAGE.md` over multiple raw artifacts whenever possible.

## Skill Selection

Use:

- `janus-feature-design` for vague feature ideas and product decisions.
- `janus-quickchange` for trivial low-risk copy, label, formatting, or tightly bounded UI fixes that do not need Backlog, Spec, or Precheck artifacts.
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

- Quickchange candidate: one tiny bounded change such as copy replacement, label tweak, percentage display, or visually local polish with low ambiguity, no architecture/storage/provider/security impact, and a validation plan that fits in a few targeted checks. Route to `janus-quickchange`.
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

For quickchange candidates, use:

```text
Kurzbewertung:
- Pfad: Quickchange
- Modelle:
- Aufwand: S
- Risiko: niedrig | mittel
- Nutzen: niedrig | mittel | hoch
- Naechster Skill: janus-quickchange
```

Only route to `janus-quickchange` when all are true:

- expected scope stays within one user-visible intent and one file cluster
- likely change footprint is about one to three files
- no new product decision, persistence change, API contract, provider logic, auth, security, privacy, or migration
- acceptance can be verified with targeted commands or one focused visual/manual check
- if the quick fix expands mid-flight, the next step is to stop and reroute to `janus-backlog-intake` or `janus-feature-design`

For larger features, do not create implementation tasks directly. Start decision mode, lock the user's decisions, then route to spec generation, normalization, review, task breakdown, and Backlog/dashboard visibility.

## Model Routing

- `5.5`, high/very high: architecture, security, privacy, prompt-injection, complex failure analysis, release gates, final audits.
- `5.4`, medium/high: Janus workhorse for feature design, specs, TestSpecs, implementation, refactoring, tests, debugging, local repository work, complex product decisions, and pipeline artifact review.
- `5.4 mini`, low/medium: separated Backlog cleanup, documentation normalization, snapshot sync, and mechanical checks only when cheaper than staying on warm `5.4`.
- `5.2`, low: summaries, small text edits, lightweight status checks.

Cache strategy: prefer staying on `5.4` and changing only reasoning effort inside an ongoing Janus workflow. If `5.4` is warm and the next task is short, mechanical, or tied to the same Janus artifacts, recommend `5.4` low instead of `5.4 mini`. Recommend switching to `5.4 mini` only for separated low-risk mechanical blocks where the lower model cost is still likely to beat the warm-cache benefit and the later return to `5.4`; recommend `5.5` only when justified by risk.

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

Prefer returning to the same chat after a local blocker fix when:

- the task scope did not change
- only one bounded artifact bundle changed
- the next skill can consume a compact delta handoff

Recommend a new chat only when the previous context is now more expensive than reloading a compact package.

## Working-Style Guardrails

Prefer a narrow guided flow:

- one goal
- one skill
- one bound artifact or one decision question
- one next handoff
- one evidence/check block

Stop and clarify when no artifact is bound, the chat conflicts with the artifact, a product decision is missing, scope has multiple plausible paths, evidence would be missing, or a risky Git/release/destructive action would be needed.

## Compact Handoff Rule

When routing to the next Janus skill, prefer a compact handoff block that tells the next skill what to keep and what to drop.

Use:

```text
KEEP_CONTEXT:
- <bound artifact path>
- <exact changed files or file cluster>
- <active blocker or evidence path>

DROP_CONTEXT:
- <broad history, old drafts, unrelated backlog items, stale failures>
```

Do not forward broad historical narrative when the next skill only needs artifact identity, changed files, and evidence.

When a new chat is recommended, convert the compact handoff into exactly one fenced `text` `NEW_CHAT_HANDOFF` block in the answer. The prose summary can stay brief, but the copy box is mandatory.

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
Recommended Model:
Recommended Reasoning:
Evidence Paths:
Keep Context:
Drop Context:
```

If `Neuer Chat: ja`, append exactly one fenced `text` `NEW_CHAT_HANDOFF` block after the normal completion format.
