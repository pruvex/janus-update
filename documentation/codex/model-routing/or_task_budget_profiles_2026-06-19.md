# OR Task Budget Profiles - 2026-06-19

Status: PLANNING-ALIGNED / LOCAL WORKFLOW GOVERNANCE / NO PRODUCTION ROUTING

## Purpose

Replace the misleading idea of one global OR cost cap with task-class-specific budget profiles.

The original `0.0020` cap remains appropriate for tiny `quickchange` proposal work, but it is intentionally too small for larger bounded worker classes such as debug review, test triage, execution patch candidates, or later bounded write-capable classes.

## Decision

Budgeting now follows task class, not one shared global threshold.

Current local profiles:

| Budget profile | Per-call cap (USD) | Session cap (USD) | Intended use |
| --- | ---: | ---: | --- |
| `quickchange_patch_review` | `0.002` | `0.006` | tiny one-file or one-cluster quickchange proposal work |
| `documentation_draft` | `0.01` | `0.03` | bounded documentation draft work |
| `debug_hypothesis_review` | `0.03` | `0.09` | assist-only debug review with larger reasoning budget |
| `test_result_triage_review` | `0.03` | `0.09` | assist-only test triage review |
| `execution_patch_candidate` | `0.05` | `0.15` | proposal-only code patch candidate work |
| `execution_write_apply_candidate` | `0.10` | `0.30` | future bounded write-capable execution class |

## Why This Matters

Without task-class profiles, we would reject otherwise good OR candidates too early:

- not because they are expensive in absolute terms
- not because they are more expensive than Codex
- only because they exceed a tiny quickchange-only ceiling

That would distort model search and make OR look weaker than it really is for larger work.

## Operational Rule

The budget gate should now be interpreted like this:

1. Pick the budget profile for the bounded task class.
2. Compare the pre-call estimate against that profile's cap.
3. Prefer later adding a relative economics gate as well:
   - OR cheaper than expected Codex-equivalent effort
   - or OR still acceptable within the current session budget

This artifact changes only the first part today: it removes the false global-cap assumption from the direct OR runner.

## Current Implementation Effect

`documentation/codex/model-routing/scripts/openrouter_direct_quickchange_patch_runner.py` now loads:

- `documentation/codex/model-routing/config/or_task_budget_profiles_2026-06-19.json`

Behavior:

- if no explicit cap override is passed, the runner uses the configured profile cap
- the dispatcher now forwards the bounded `task_class` to the direct OR runner
- quickchange stays on the original narrow cap
- future larger bounded classes can use higher caps without pretending the same tiny budget applies everywhere

## Non-Goals

- no production routing activation
- no canonical routing-table update
- no global OR approval
- no automatic economics ranking against Codex yet
- no live model search expansion by itself

## Next Safe Step

Use the same profile system when we promote the direct OR transport into the next bounded class, and then add a second economics gate that compares OR expected cost against the local Codex path instead of relying on absolute caps alone.
