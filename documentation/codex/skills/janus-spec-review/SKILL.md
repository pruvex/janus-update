---
name: janus-spec-review
description: Review exactly one Janus Feature Spec before task compilation. Use when the user asks to review, approve, block, refine, split, mark, or make a Spec ready for the Diamond implementation pipeline and before janus-spec-to-task.
---

# Janus Spec Review

## Purpose

Use this skill as the mandatory pre-compilation gate for one Feature Spec under `documentation/SPEC/`.

It checks whether the Spec is complete, deterministic, scoped, testable, and ready for `janus-spec-to-task`. It does not create tasks and does not implement anything.
This is primarily a ChatGPT-led review skill. Codex normally consumes the approval or revision handoff rather than leading the review decision.

## Inputs

- Exactly one Spec file.
- Mode: `REVIEW_ONLY` by default, or `OPTIMIZE_WRITE` for mechanical structure cleanup only.

When a Spec path is provided, treat that file as the only source of truth. Ignore conflicting chat history, drafts, and side notes.
If the Spec file is missing, unreadable, or not a final Feature Spec, block instead of inferring intent from other artifacts.

## Hard Rules

- No tasks.
- No implementation.
- No product decisions from chat context.
- No architecture decisions.
- No invented requirements.
- No silent filling of product gaps.
- Write or update only the `SPEC REVIEW METADATA` block when the review decision is clear.
- If a blocking product decision is missing, ask exactly one blocking question with at most two options.
- Do not treat a vague `ok` as an approval signal or as a valid handoff substitute.

## Tri-Modal Rollout Note

Global delegation vocabulary across Janus is now:

- `1 = Codex`
- `2 = Cursor`
- `3 = OpenRouter`

This skill's bounded `REVIEW_ONLY` lane is now wired through the shared manifest-backed `documentation/codex/model-routing/scripts/janus_delegate.py` entry. OpenRouter remains the recommended backend for this assist-only review slice; Cursor is visible as option `2` but is not the recommended backend here.

## Bounded Delegation Gate

For a narrowly bounded `REVIEW_ONLY` slice, this skill now has the shared tri-modal operator gate:

- `1 = Codex`
- `2 = Cursor`
- `3 = OpenRouter`

Use the shared delegate entry first:

```powershell
python documentation/codex/model-routing/scripts/janus_delegate.py --lane spec_review --task-id TASK-SR-002 --workflow-id <WORKFLOW-ID> --operator-choice prompt --input-package-json development/openrouter-skill-tests/janus-spec-review/spec_review_input_package.json --estimated-codex-saved-tokens 12000 --estimated-delegation-overhead-tokens 4000
```

For a narrowly bounded `REVIEW_ONLY` slice, this skill may offer one operator-facing delegated choice only when all of the following are true:

- exactly one finalized Spec file is under review
- the delegated task is recommendation-only and bounded to review output plus metadata suggestion
- no authoritative metadata write, task creation, Git action, release action, or product decision is delegated
- Codex remains the final reviewer and local writer of any accepted `SPEC REVIEW METADATA` block

Binding implementation artifact:

- `C:\KI\Janus-Projekt\documentation\codex\model-routing\scripts\codex_spec_review_runner.py`

Current bounded winner for the representative Spec 21 review slice:

- `qwen/qwen3-coder-30b-a3b-instruct`

Current lane behavior:

- OpenRouter remains the recommended backend for this bounded assist-only review slice.
- Cursor is visible as option `2`, but not the recommended backend.
- The existing `codex_spec_review_runner.py` remains the downstream OR helper planned by `janus_delegate.py`.
- Current shared-gate productive evidence shows this lane is usable, but materially costlier than the first planning estimate; prefer it for substantive `REVIEW_ONLY` bundles rather than tiny metadata-only checks.

Gate rules:

- if the user chooses `1`, `local`, or `codex`, stay local in Codex
- if the user chooses `2`, `cursor`, or `Cursor`, do not imply a live Cursor spec-review path unless a later migration artifact explicitly adds one
- if the user chooses `3`, `or`, `opr`, or `openrouter`, the shared delegate currently plans the bounded spec-review helper path and hands off to the existing runner
- use only a bounded review package; do not delegate full spec authority
- accepted delegated output remains review material only; Codex must still perform any real metadata write locally

Forbidden inside this path:

- delegated authoritative metadata writes
- delegated task creation or next-skill authority
- delegated Git, release, routing-table, or `CURRENT_STATE` writes

## Review Gates

Check:

- goal, user problem, user value, and bounded scope
- target surface and non-surfaces
- user action surface, trigger, result, non-effects, and data effects
- persistence and state behavior
- inputs, outputs, source of truth, and side effects
- security, privacy, secrets, and external dependencies
- binary acceptance criteria and failure cases
- decomposition readiness for `janus-spec-to-task`
- size and split boundaries

Use these interpretations:

- complete: all required behavior, boundaries, constraints, and acceptance checks for one feature are present
- deterministic: no conflicting interpretations, hidden branches, or unresolved product choices remain
- task-ready: `janus-spec-to-task` can decompose the Spec without inventing scope, files, or acceptance meaning

## Decisions

Return exactly one:

- `APPROVED`: ready for task compilation with no blocking ambiguity.
- `NEEDS_REVISION`: repairable but not yet complete, deterministic, or task-ready.
- `BLOCKED`: an essential product decision is missing, the file is invalid, or the scope must be split before review can pass.

## Complexity And Model Routing

Score 0-100:

- Scope Size: 0-20
- Architectural Risk: 0-20
- State / Persistence Complexity: 0-20
- Cross-System Impact: 0-20
- Ambiguity Level: 0-20

Risk:

- 0-30: `LOW`
- 31-60: `MEDIUM`
- 61-80: `HIGH`
- 81-100: `CRITICAL`

Recommend `5.6 Terra` for normal Spec review. Recommend `5.6 Sol` only for score above 70, central security/privacy/persistence/IPC risk, or multiple plausible interpretations. Use `5.6 Terra` low for mechanical metadata checks when the current `5.6 Terra` context is warm or review continues in `5.6 Terra`; use `5.6 Luna` only for separated metadata batches that are still likely cheaper than staying on warm `5.6 Terra`.

## Required Metadata Block

Write or update this block in the Spec when the review decision is clear:

```markdown
## SPEC REVIEW METADATA

- **Review Status:** APPROVED | NEEDS_REVISION | BLOCKED
- **Complexity Score:** <0-100>
- **Risk:** LOW | MEDIUM | HIGH | CRITICAL
- **Recommended Review Model:** 5.6 Terra | 5.6 Sol
- **Skill-1 Ready:** YES | NO
- **Split Required:** YES | NO
- **Reviewed At:** YYYY-MM-DD
- **Review Confidence:** LOW | MEDIUM | HIGH
- **Review Source:** janus-spec-review
```

Validate metadata when useful:

```powershell
python C:\Users\pruve\.codex\skills\janus-spec-review\scripts\validate_spec_review.py --spec <Spec>
```

## Output

Use:

```text
SPEC REVIEW RESULT
- Spec:
- Mode:
- Decision:
- Complexity Score:
- Risk:
- Model Recommendation:
- Readiness Checklist:
- Key Issues:
- Required Refinements:
- Split Recommendation:
- Metadata Written:
- Next Skill:
```

For `APPROVED`, next skill is `janus-spec-to-task`.
For `NEEDS_REVISION`, route back to `janus-spec-generator`.
For `BLOCKED`, route back to `janus-feature-design` when a product decision is missing, otherwise route to `janus-spec-generator`.

When control moves from ChatGPT to Codex, output model/reasoning above exactly one compact fenced `text` block that contains only:

- `NEXT: janus-spec-to-task` or `NEXT: janus-spec-generator` or `NEXT: janus-feature-design`
- the Spec path
- the review decision
- one short note with the key blocking issue or approval note
