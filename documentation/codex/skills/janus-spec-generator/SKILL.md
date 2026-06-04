---
name: janus-spec-generator
description: Generate deterministic Janus Diamond feature specs from the latest approved decision summary or explicit feature description. Use when the user asks to create, draft, compile, or prepare a Janus Feature Spec after feature design and before spec review, task breakdown, implementation, or tests.
---

# Janus Spec Generator

## Overview

Generate a final Janus Feature Spec from a locked decision source. Do not brainstorm, implement, create tasks, or invent unresolved requirements.

## Source Priority

Use only one source:

1. Latest `LATEST DECISION SUMMARY`.
2. Latest explicit user-approved feature decision.
3. If neither exists, ask exactly one blocking question.

Ignore earlier brainstorming, rejected options, stale drafts, contradictory chat context, implementation suggestions, and optional nice-to-haves.

## References

Read only when exact wording or current governance alignment is needed:

- `C:\KI\Janus-Projekt\AGENTS.md`
- `C:\KI\Janus-Projekt\documentation\codex\CODEX_WORKFLOW_PLAYBOOK.md`
- `C:\KI\Janus-Projekt\documentation\pipeline\PIPELINE_CONTRACT.md`

## Blocking Rule

If one essential product decision is missing, output only:

```text
BLOCKING QUESTION
- Question: <exactly one question>
- Option A: <concrete option>
- Option B: <concrete option>
- Recommendation: <short recommendation>
```

Do not output a Spec with missing, optional, maybe, TBD, or ambiguous core decisions.

## Output Contract

Write the full Spec to the target file under `documentation/SPEC/`.

Do not paste the full Spec body into the user-facing response.

Successful user-facing output must stay compact and end in a small next-step summary. Keep it short enough that the user can just read it and answer `ok`.

Use:

```text
SPEC GENERATION RESULT
- Spec: <path>
- Decision: GENERATED | BLOCKED
- Complexity Score: <0-100 integer | N/A>
- Model Recommendation: <5.4 | 5.5>, <low | medium | medium-high | high>
- Key Note: <one short sentence>
- Next Skill: janus-spec-review | janus-spec-normalizer | NEEDS_INFO
```

If a model or chat switch is recommended for the next step, follow repository governance and emit the normal `MODEL SWITCH GATE` instead of dumping the Spec body.

## Required Structure

Use these headings exactly and in this order inside the written Spec:

```markdown
# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING

## FEATURE IDENTITY

## USER VALUE

## TARGET SURFACE

## USER ACTION SURFACE

## SYSTEM BEHAVIOR

## DATA / PERSISTENCE

## CONSTRAINTS

## SECURITY / PRIVACY

## EDGE CASES

## DEFINITION OF DONE

## TEST STRATEGY

## OUT OF SCOPE

## INTERNAL COMPLEXITY BREAKDOWN
```

If a section is not applicable, write `Nicht zutreffend: <kurze Begruendung>`.

## Routing Block

Directly under `## SPEC REVIEW EXECUTION ROUTING`, include exactly these fields, one per physical line:

```text
target_skill: janus-spec-review
recommended_model: 5.4 | 5.5
recommended_reasoning: low | medium | medium-high | high
new_chat: yes | no
complexity_score: <0-100 integer>
confidence: LOW | MEDIUM | HIGH
dashboard_hint: SAFE | CAUTION | CRITICAL
reason: <single-line reason, max 180 chars>
```

No bullets, tables, comments, duplicate keys, empty values, code fences, translated keys, or merged fields in this block.

## Structured Fields

These sections must use bullet key-value fields:

- `## FEATURE IDENTITY`
- `## TARGET SURFACE`
- `## USER ACTION SURFACE`
- `## DATA / PERSISTENCE`
- `## SECURITY / PRIVACY`
- `## TEST STRATEGY`

Use `- Field: value`. Do not use tables, numbered lists, bold labels, or two-line key/value pairs.

## Definition of Done

Every item must be observable and use checkbox syntax:

```markdown
- [ ] Wenn <Bedingung>, dann <beobachtbares Ergebnis>.
```

No implementation tasks in Definition of Done.

## Complexity Consistency

Internal complexity dimensions each range 0-20:

- Scope Size
- Architectural Risk
- State / Persistence Complexity
- Cross-System Dependencies
- Ambiguity Level

`Total Complexity Score` must equal their sum.

These values must match exactly:

- routing `complexity_score` = `Total Complexity Score`
- routing `recommended_model` = `Routing Decision`
- routing `recommended_reasoning` = `Routing Reasoning`
- routing `confidence` = `Routing Confidence`
- routing `dashboard_hint` = `Dashboard Hint`

Prefer `5.4` as the normal Janus workhorse for spec review.

Escalate to `5.5` only for high ambiguity, security/privacy risk, architecture risk, or release-critical decisions.

Use `new_chat: yes` only when the next review should happen in a fresh thread because of context size, audit independence, or scope shift. Otherwise use `no`.

## Forbidden Content

Do not include implementation code, API signatures, database schema, concrete file structure, task lists, execution steps, test code, code-level architecture, speculative requirements, optional nice-to-haves, or unresolved alternatives.

## Next Gate

After a valid Spec is created, default to `janus-spec-review`.

Recommend `janus-spec-normalizer` only when the generated Spec still needs mechanical parser-safe cleanup.
