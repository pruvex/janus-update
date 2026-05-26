---
name: janus-spec-review
description: Review exactly one Janus Feature Spec before task compilation. Use when the user asks to review, approve, block, refine, split, mark, or make a Spec ready for the Diamond implementation pipeline and before janus-spec-to-task.
---

# Janus Spec Review

## Purpose

Use this skill as the mandatory pre-compilation gate for one Feature Spec under `documentation/SPEC/`.

It checks whether the Spec is complete, deterministic, scoped, testable, and ready for `janus-spec-to-task`. It does not create tasks and does not implement anything.

## Inputs

- Exactly one Spec file.
- Mode: `REVIEW_ONLY` by default, or `OPTIMIZE_WRITE` for mechanical structure cleanup only.

When a Spec path is provided, treat that file as the only source of truth. Ignore conflicting chat history, drafts, and side notes.

## Hard Rules

- No tasks.
- No implementation.
- No product decisions from chat context.
- No architecture decisions.
- No invented requirements.
- Write or update only the `SPEC REVIEW METADATA` block when the review decision is clear.
- If a blocking product decision is missing, ask exactly one blocking question with at most two options.

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

## Decisions

Return exactly one:

- `APPROVED`: ready for task compilation.
- `APPROVED_WITH_NOTES`: ready, with non-blocking notes.
- `NEEDS_REFINEMENT`: repairable but not ready.
- `BLOCKED`: one essential product decision missing.
- `TOO_LARGE`: split required.
- `SPEC FILE INVALID`: file missing, unreadable, or not a final Spec.

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

Recommend `5.4` for normal Spec review. Recommend `5.5` only for score above 70, central security/privacy/persistence/IPC risk, or multiple plausible interpretations. Use `5.4 mini` only for mechanical metadata checks.

## Required Metadata Block

Write or update this block in the Spec when the review decision is clear:

```markdown
## SPEC REVIEW METADATA

- **Review Status:** APPROVED | APPROVED_WITH_NOTES | NEEDS_REFINEMENT | BLOCKED | TOO_LARGE | SPEC FILE INVALID
- **Complexity Score:** <0-100>
- **Risk:** LOW | MEDIUM | HIGH | CRITICAL
- **Recommended Review Model:** 5.4 | 5.5
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

For `APPROVED` or `APPROVED_WITH_NOTES`, next skill is `janus-spec-to-task`.
