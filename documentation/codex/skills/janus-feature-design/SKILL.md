---
name: janus-feature-design
description: Guide vague Janus feature ideas into decision-locked, spec-ready summaries and route them to the full feature pipeline or backlog pipeline. Use when the user wants to brainstorm, shape, clarify, design, scope, or prepare a new Janus feature before writing a Spec.
---

# Janus Feature Design

## Overview

Use this skill to turn a rough Janus idea into a `LATEST DECISION SUMMARY`. Do not implement, create tasks, or make code-level architecture decisions.

## Source Reference

This skill is the Codex-native successor to:

- `C:\KI\Janus-Projekt\documentation\prompts\1. BRAINSTORMING MODE v5.0.md`

Read the source only if exact legacy wording is needed. Otherwise follow this concise version.

## Operating Mode

- Ask exactly one decision question at a time.
- Offer at most two options.
- Treat every user answer as locked unless the user explicitly corrects it.
- Stay at product behavior level.
- Avoid code, APIs, file paths, database design, model assignment, and task breakdown.
- Do not list many open alternatives.
- Do not start implementation.

## Decision Areas

Cover every relevant area:

- Feature behavior: trigger, user-visible result, success behavior, failure behavior.
- Target surface: exactly one primary surface, existing/new status, explicit non-surfaces.
- User action surface: action type, input, feedback, cancel/undo behavior.
- Data and persistence: whether data is created, updated, deleted, or remembered.
- Security and privacy: sensitive data, external services, secrets, risky actions.
- Edge cases: empty state, failure state, ambiguity, permission, retry.
- Scope: out-of-scope items and non-goals.

## Existing Surface Rule

If the user chooses an existing surface, confirm whether they know it exists.

Record:

```text
Existence Confirmation: confirmed by user | not confirmed by user
```

Never claim an existing surface is real unless confirmed by user or verified in repo.

## Question Format

Use:

```text
Blaue Entscheidungsfrage:
<eine konkrete Frage>

A) <Option 1>
B) <Option 2>

Empfehlung:
<ein kurzer Satz>
```

## Final Output

When all relevant decisions are locked, output:

```text
LATEST DECISION SUMMARY
Feature Name:
Primary Goal:
User Problem:
User Value:
Primary Target Surface:
Existing or New Surface:
Existence Confirmation:
User Trigger:
Success Behavior:
Failure Behavior:
User Action Surface:
Data / Persistence:
Security / Privacy:
Edge Cases:
Out of Scope:
Routing Decision: FULL FEATURE PIPELINE | BACKLOG PIPELINE
Routing Reason:
Recommended Next Skill:
```

## Pipeline Routing

Choose `FULL FEATURE PIPELINE` for new features, complex UX, persistence, integrations, multiple surfaces, or medium/high risk.

Choose `BACKLOG PIPELINE` for small bugs, local UI tweaks, atomar behavior changes, low-risk improvements, and clearly bounded technical debt.
