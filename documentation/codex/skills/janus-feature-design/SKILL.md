---
name: janus-feature-design
description: Guide vague Janus feature ideas into decision-locked, spec-ready summaries and route them to the full feature pipeline or backlog pipeline. Use when the user wants to brainstorm, shape, clarify, design, scope, or prepare a new Janus feature before writing a Spec.
---

# Janus Feature Design

## Overview

Use this skill to turn a rough Janus idea into a `LATEST DECISION SUMMARY`. Do not implement, create tasks, or make code-level architecture decisions.
This is primarily a ChatGPT-led clarification skill. Codex normally consumes the resulting locked decision handoff rather than leading the feature-design conversation.

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
- Do not send an idea forward to `janus-spec-generator` while relevant product questions are still open.

## Tri-Modal Rollout Note

Global delegation vocabulary across Janus is now:

- `1 = Codex`
- `2 = OpenRouter`
- `3 = Cursor Composer`
- `4 = Cursor API`

This skill's bounded feature-design consolidation lane is now wired through the shared manifest-backed `documentation/codex/model-routing/scripts/janus_delegate.py` entry. OpenRouter remains the recommended backend for this assist-only review slice; Cursor is visible as option `2` but is not the recommended backend here.

## Bounded Delegation Gate

For a narrowly bounded feature-design consolidation slice, this skill now has the shared cost-aware operator gate:

- `1 = Codex`
- `2 = OpenRouter`
- `4 = Cursor API`

Use the shared delegate entry first:

```powershell
python documentation/codex/model-routing/scripts/janus_delegate.py --lane feature_design_review --task-id TASK-FD-001 --workflow-id <WORKFLOW-ID> --operator-choice prompt --input-package-json development/openrouter-skill-tests/janus-feature-design/feature_design_input_package.json --estimated-codex-saved-tokens 12000 --estimated-delegation-overhead-tokens 4000
```

Reference no-live-ready operator path for this lane:

- `C:\KI\Janus-Projekt\documentation\codex\model-routing\FEATURE_DESIGN_REVIEW_NO_LIVE_PATH_2026-07-07.md`

For a narrowly bounded feature-design consolidation slice, this skill may offer one operator-facing delegated choice only when all of the following are true:

- exactly one bounded feature request package is bound
- the delegated task is limited to drafting one `LATEST DECISION SUMMARY` or exactly one blocking question from already-given answers
- no final product decision authority, implementation, task creation, Git action, or release action is delegated
- Codex remains the final owner of the decision summary and of any follow-up questioning

Binding implementation artifact:

- `C:\KI\Janus-Projekt\documentation\codex\model-routing\scripts\codex_feature_design_runner.py`

Current bounded winner for the representative existing-skill Codex-vs-OR feature slice:

- `qwen/qwen3-coder-30b-a3b-instruct`

Current passing alternative on the same bounded contract:

- `deepseek/deepseek-v4-flash`

Current lane behavior:

- OpenRouter remains the recommended backend for this bounded assist-only review slice.
- Cursor is visible as option `2`, but not the recommended backend.
- The existing `codex_feature_design_runner.py` remains the downstream OR helper planned by `janus_delegate.py`.
- The current everyday proof point is prompt/dry-run readiness; do not imply a live OR result unless that run was explicitly approved and actually executed.

Gate rules:

- if the user chooses `1`, `local`, or `codex`, stay local in Codex
- if the user chooses `2`, `or`, `opr`, or `openrouter`, the shared delegate currently plans the bounded feature-design helper path and hands off to the existing runner
- if the user chooses `4`, `cursor-api`, `cursor_api`, or `api`, do not imply a live Cursor feature-design path unless a later migration artifact explicitly adds one
- use only a bounded feature-design input package; do not delegate free-form final decision authority
- accepted delegated output remains draft material only; Codex must still decide the final `LATEST DECISION SUMMARY` or blocking question locally

Forbidden inside this path:

- delegated final product decision authority
- delegated implementation or task creation
- delegated Git, release, routing-table, or `CURRENT_STATE` writes

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

If any required product decision is still open, stop instead of forcing a summary forward. Do not treat a vague `ok` as a locked decision or as a valid handoff substitute.

When control moves from ChatGPT to Codex, output:

- model/reasoning header above the handoff
- exactly one compact fenced `text` block
- only the locked decision summary and the exact next skill

## Pipeline Routing

Choose `FULL FEATURE PIPELINE` for new features, complex UX, persistence, integrations, multiple surfaces, or medium/high risk.

Choose `BACKLOG PIPELINE` for small bugs, local UI tweaks, atomar behavior changes, low-risk improvements, and clearly bounded technical debt.

Route to `janus-spec-generator` only when the summary is decision-locked and spec-ready.
Route to `janus-backlog-intake` when the request is backlog-worthy but does not require feature-design clarification first.
