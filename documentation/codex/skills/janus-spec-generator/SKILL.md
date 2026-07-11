---
name: janus-spec-generator
description: Generate deterministic Janus Diamond feature specs from the latest approved decision summary or explicit feature description. Use when the user asks to create, draft, compile, or prepare a Janus Feature Spec after feature design and before spec review, task breakdown, implementation, or tests.
---

# Janus Spec Generator

## Overview

Generate a final Janus Feature Spec from a locked decision source. Do not brainstorm, implement, create tasks, or invent unresolved requirements.
This is primarily a ChatGPT-led generation skill. Codex normally consumes the resulting Spec handoff rather than leading the spec-generation decision step.

## Source Priority

Use only one locked source:

1. Latest `LATEST DECISION SUMMARY`.
2. Latest explicit user-approved feature decision, but only if it is already decision-locked and not a fresh brainstorm.
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
Do not treat a vague `ok` as a locked decision or as a valid handoff substitute.

## Tri-Modal Rollout Note

Global delegation vocabulary across Janus is now:

- `1 = Codex`
- `2 = Cursor`
- `3 = OpenRouter`

This skill's bounded locked-decision Spec generation lane is now wired through the shared manifest-backed `documentation/codex/model-routing/scripts/janus_delegate.py` entry. OpenRouter remains the recommended backend for this assist-only review slice; Cursor is visible as option `2` but is not the recommended backend here.

## Bounded Delegation Gate

For a narrowly bounded locked-decision Spec generation slice, this skill now has the shared tri-modal operator gate:

- `1 = Codex`
- `2 = Cursor`
- `3 = OpenRouter`

Use the shared delegate entry first:

```powershell
python documentation/codex/model-routing/scripts/janus_delegate.py --lane spec_generator_review --task-id TASK-SG-001 --workflow-id <WORKFLOW-ID> --operator-choice prompt --input-package-json development/openrouter-skill-tests/janus-spec-generator/spec_generator_input_package.json --estimated-codex-saved-tokens 12000 --estimated-delegation-overhead-tokens 4000
```

For a narrowly bounded locked-decision Spec generation slice, this skill may offer one operator-facing delegated choice only when all of the following are true:

- exactly one locked decision summary is bound
- the delegated task is bounded to a structured Spec draft proposal only
- no authoritative Spec file write, task creation, Git action, release action, or final product decision is delegated
- Codex remains the final reviewer and local writer of any accepted Spec draft

Binding implementation artifact:

- `C:\KI\Janus-Projekt\documentation\codex\model-routing\scripts\codex_spec_generator_review_runner.py`

Current bounded winner for the representative first-real-OR-pilot Spec slice:

- `qwen/qwen3-coder-30b-a3b-instruct`

Current passing alternatives on the same structured contract:

- `deepseek/deepseek-v4-flash`
- `qwen/qwen3.5-flash-02-23`
- `moonshotai/kimi-k2.5`

Current lane behavior:

- OpenRouter remains the recommended backend for this bounded assist-only review slice.
- Cursor is visible as option `2`, but not the recommended backend.
- The existing `codex_spec_generator_review_runner.py` remains the downstream OR helper planned by `janus_delegate.py`.

Gate rules:

- if the user chooses `1`, `local`, or `codex`, stay local in Codex
- if the user chooses `2`, `cursor`, or `Cursor`, do not imply a live Cursor spec-generation path unless a later migration artifact explicitly adds one
- if the user chooses `3`, `or`, `opr`, or `openrouter`, the shared delegate currently plans the bounded spec-generator helper path and hands off to the existing runner
- use only a bounded locked-decision input package; do not delegate the authoritative Spec file write
- accepted delegated output remains draft material only; Codex must still perform any real Spec write locally

Forbidden inside this path:

- delegated authoritative Spec writes
- delegated task creation or implementation authority
- delegated final next-skill authority beyond bounded draft suggestion
- delegated Git, release, routing-table, or `CURRENT_STATE` writes

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
- Model Recommendation: <5.6 Terra | 5.6 Sol>, <low | medium | high>
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

If any required product decision is still open, stop with the blocking question instead of drafting around the gap.

## Routing Block

Directly under `## SPEC REVIEW EXECUTION ROUTING`, include exactly these fields, one per physical line:

```text
target_skill: janus-spec-review
recommended_model: 5.6 Terra | 5.6 Sol
recommended_reasoning: low | medium | high
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

Prefer `5.6 Terra` as the normal Janus workhorse for spec review.

Escalate to `5.6 Sol` only for high ambiguity, security/privacy risk, architecture risk, or release-critical decisions.

Use `new_chat: yes` only when the next review should happen in a fresh thread because of context size, audit independence, or scope shift. Otherwise use `no`.

## Forbidden Content

Do not include implementation code, API signatures, database schema, concrete file structure, task lists, execution steps, test code, code-level architecture, speculative requirements, optional nice-to-haves, or unresolved alternatives.

## Next Gate

After a valid Spec is created, default to `janus-spec-review`.

Recommend `janus-spec-normalizer` only when the generated Spec still needs mechanical parser-safe cleanup.

When control moves from ChatGPT to Codex, output model/reasoning above exactly one compact fenced `text` block that contains only:

- `NEXT: janus-spec-normalizer` or `NEXT: janus-spec-review`
- the Spec path
- the locked decision source
- one short note if a mechanical cleanup is still required
