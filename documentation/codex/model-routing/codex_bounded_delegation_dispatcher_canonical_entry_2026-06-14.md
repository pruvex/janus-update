# Codex Bounded Delegation Dispatcher Canonical Entry

## Purpose

`documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py` is the canonical bounded operator entry for the currently validated shared delegation classes inside the Janus workflow.

It gives the operator one stable gate with the same language pattern:

- `1 = Codex`
- `2 = OpenRouter`

The dispatcher then routes to the matching bounded helper without requiring the operator to select low-level scripts directly.

## Validated Task Classes

The dispatcher is currently the canonical shared bounded entry for exactly these validated classes:

| task_class | Meaning | Current delegated path | Status |
| --- | --- | --- | --- |
| `documentation_draft` | bounded read-only documentation draft work | `doc_skill_sidecar_draft_runner.py` with optional structured review | `PASS` |
| `quickchange_patch_review` | bounded quickchange patch proposal review flow | `quickchange_sidecar_write_pilot_runner.py` with optional structured patch capture | `PASS` |
| `generator_review` | bounded generator-backed review flow | `codex_structured_action_generator_review_runner.py` | `PASS` |

## Canonical Operator Choice

When the dispatcher is invoked in prompt mode, it must present the bounded workflow gate as:

- `Willst du 1 Codex das machen lassen?`
- `Oder 2 den bounded <task_class> Delegation-Pfad nutzen?`

This keeps the real workflow choice simple while preserving class-specific routing under the hood.

## Routing Rules

### `documentation_draft`

- Prompt mode returns the operator gate.
- `1` or `local` returns the Codex-only path summary.
- `2` or `delegated` invokes the read-only documentation sidecar draft flow.
- Optional structured review may run after an accepted draft package.

### `quickchange_patch_review`

- Prompt mode returns the operator gate.
- `1` or `local` keeps the work local in Codex.
- `2`, `or`, `openrouter`, or `delegated` invokes the bounded quickchange helper.
- Structured review remains capture-first and review-first.
- No auto-apply is introduced by the dispatcher.

### `generator_review`

- Prompt mode returns the operator gate.
- `1` or `local` keeps the work local in Codex.
- `2` or `delegated` means delegated intent, but execution stays local through the deterministic builder/executor/validator path.
- This class is intentionally not a sidecar write path.

## Workflow Position

The dispatcher is the canonical shared bounded entry for the validated delegation layer, but not every class is exposed through an installed Janus skill entry point yet.

Current exposure:

- `documentation_draft`: already wired into the installed `janus-documentation-update` skill guidance.
- `quickchange_patch_review`: validated through dispatcher-first helper usage and now aligned to the installed-skill OpenRouter wording.
- `generator_review`: validated through dispatcher-first helper usage, not yet an installed-skill operator entry.

## Boundaries

The dispatcher exists to standardize bounded operator choice, not to widen delegation authority.

It must remain inside these boundaries:

- no production routing
- no canonical routing-table update
- no Git or release authority by delegated path
- Codex App remains final reviewer and acceptance authority
- no global OpenRouter approval
- no Auto Router enablement through this entry

## Non-Goals

- It does not activate production delegation.
- It does not replace fixed-model or existing canonical routing tables.
- It does not make broad write-capable sidecar execution generally approved.
- It does not approve new task classes without explicit validation evidence.
- It does not turn `generator_review` into a live shell-delegated execution path.

## Current Decision

For the current Janus workflow state, the dispatcher should be treated as the canonical shared bounded entry for the three validated delegation classes above.

Documentation-skill operators should use the dispatcher-backed gate language instead of choosing helper scripts manually, while wider installed-skill adoption for the other classes remains a separate future decision.
