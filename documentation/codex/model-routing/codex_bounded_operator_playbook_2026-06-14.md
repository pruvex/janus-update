# Codex Bounded Operator Playbook

## Purpose

This playbook explains how to use the currently validated bounded delegation gates in everyday Janus workflow.

The shared operator choice is always:

- `1 = Codex`
- `2 = Delegated`

The operator should not need to choose helper scripts manually.

## Canonical Entry

The shared bounded entry remains:

- `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`

This dispatcher sits underneath the skill-facing workflow guidance for the currently validated classes.

## The Everyday Classes

| Class | Use it for | Delegated meaning | Not for |
| --- | --- | --- | --- |
| `documentation_draft` | read-only documentation drafting and milestone wording | bounded sidecar draft plus Codex review | authoritative final documentation sync |
| `quickchange_patch_review` | tiny bounded patch proposals in a small allowlisted file cluster | bounded delegated patch proposal plus Codex review | broad write authority, auto-apply, multi-surface edits |
| `execution_patch_candidate` | bounded multi-file patch candidates on a prechecked task slice | direct OR patch candidate plus Codex review/apply-or-reject ownership | autonomous apply, broad repo edits, production routing |
| `generator_review` | deterministic generator-backed test pipeline preparation or validation review | delegated intent, but local builder/executor/validator execution | free-form sidecar code writing or general test authoring |

## When To Use `documentation_draft`

Choose this gate when all of these are true:

- the work is draft-safe
- the output is read-only recommendation content
- Codex should still perform final review before any authoritative repo update
- the task fits the documentation-skill bounded path

Prefer `1 = Codex` when:

- the work is already tiny enough locally
- the documentation task is authoritative, final, or state-changing
- the draft would likely need heavy Codex rewriting anyway

Prefer `2 = Delegated` when:

- the work is a bounded first draft
- the task is repetitive or wording-heavy
- you want to save Codex effort while keeping Codex as final reviewer

## When To Use `quickchange_patch_review`

Choose this gate when all of these are true:

- the change is still a real quickchange
- one user-visible intent is involved
- the editable path allowlist is explicit
- touched-file count can stay tiny
- Codex should review the proposed patch before acceptance

Prefer `1 = Codex` when:

- the patch is trivial enough to do directly
- the file cluster is ambiguous
- the task is starting to spill beyond tiny-scope quickchange rules

Prefer `2 = Delegated` when:

- the patch is small, local, and repetitive
- you already know the exact allowed file path or file cluster
- review-first patch capture is enough

Do not use this gate when:

- the change needs broad repo context
- multiple implementations are plausible
- backend, routing, persistence, auth, or release concerns appear

## When To Use `execution_patch_candidate`

Choose this gate when all of these are true:

- one prechecked execution task slice is already bound
- the editable-path allowlist is explicit
- max touched files are capped up front
- Codex should still review the patch and decide whether to apply or reject locally
- proposal capture is enough; no delegated local execution is needed

Prefer `1 = Codex` when:

- the patch scope is still evolving
- the task needs broader repo judgment than the prechecked slice allows
- the candidate would likely need heavy local restructuring anyway

Prefer `2 = Delegated` when:

- the task already has a clean precheck package
- the file cluster is bounded and known
- a candidate patch plus Codex review is the right trust seam
- you want to save Codex effort on bounded patch drafting without delegating acceptance

Current accepted evidence:

- `deepseek/deepseek-v4-flash` has accepted bounded evidence for this class across two real larger-class proposal runs
- `qwen/qwen3-coder-flash` has negative live evidence for this class on the current contract and is not the preferred larger-class candidate
- Codex remains final review, validation, and local apply/reject owner

Current accepted DeepSeek evidence points:

- `DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-002`
- `DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-006`

Important clarification:

- `DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-006` is the first accepted live proof for the compact larger-class contract redesign
- the accepted result is still proposal-first evidence only
- no delegated autonomous apply authority was added

Do not use this gate when:

- no precheck artifact exists
- the task needs direct delegated file execution
- the scope is wider than the allowlist/touched-file cap can safely express
- release, Git, routing, persistence, auth, or broader architectural decisions are involved

## When To Use `generator_review`

Choose this gate when all of these are true:

- one TestPlan or generator target is bound
- one deterministic generator family is being used
- the task is review-first
- local deterministic execution is preferred over prompt-level shell steering

Prefer `1 = Codex` when:

- the generator task is small enough to reason through directly
- the manifest or generator intent is still changing
- broader pipeline judgement is required before running anything

Prefer `2 = Delegated` when:

- the task is mainly mechanical generator preparation
- the manifest is already clear
- you want bounded delegated intent while keeping local deterministic execution

Important:

- this is not a free sidecar write mode
- it is delegated intent, not delegated shell authority
- the local executor still owns the actual deterministic run

## Simple Decision Rule

Use this quick rule in everyday work:

- If the step is authoritative, risky, ambiguous, or likely to expand, choose `1 = Codex`.
- If the step is bounded, repetitive, review-first, and already fits one validated class, `2 = Delegated` is appropriate.

## Shared Boundaries

All bounded gates stay inside the same boundaries:

- no production routing
- no canonical routing-table update
- no Git or release authority by delegated path
- no global OpenRouter approval
- Codex App remains final reviewer and acceptance authority

## Current Recommendation

For everyday use, the safest order is:

1. Start with the skill-facing operator gate.
2. Ask whether the step is truly bounded and review-first.
3. Choose `1 = Codex` if any risk or ambiguity appears.
4. Choose `2 = Delegated` only when the step clearly matches one of the four validated classes above.

This keeps delegation useful for saving Codex effort without pretending that delegation is broader or more autonomous than the validated evidence supports.
