# OR Family-First Comparison Debug Plan - 2026-06-19

SKILL 5 DEBUG RESULT: NEEDS RETEST

Iteration: 1
Progress-Validierung: Failure Code `EXECUTION_PATCH_CANDIDATE_MODEL_FIT_MISMATCH`; Evidence geaendert ggü. N-1: N/A; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN

Root Cause:
- The direct OpenRouter transport is now proven for bounded Janus work.
- `quickchange_patch_review` already has accepted live evidence on the direct OR path.
- The first larger direct OR class, `execution_patch_candidate`, is no longer blocked by transport.
- The current blocker is model/provider fit for structured JSON patch-candidate output on the tested combination `openai/gpt-oss-20b`.
- The next safe move is not to generalize from that one family, but to run a family-first comparison with materially different coding models.

Fix Summary:
- Refresh the candidate pool away from a narrow `gpt-oss-*` bias.
- Use the direct OR runners exactly as they exist today.
- Compare the next stronger low-cost families in the smallest meaningful order:
  1. `qwen/qwen3-coder-flash`
  2. `deepseek/deepseek-v4-flash`
- Keep the first comparison bounded to one known-good class and one known-problem class:
  - `quickchange_patch_review`
  - `execution_patch_candidate`

Auto-Verification:
- Status: PASS
- Evidence:
  - `documentation/codex/model-routing/quickchange_direct_or_live_retry_result_2026-06-19.md`
  - `documentation/codex/model-routing/direct_or_execution_patch_candidate_live_retry_result_2026-06-19.md`
  - `documentation/codex/model-routing/or_workhorse_candidate_refresh_2026-06-19.md`
  - targeted `WHAT_I_LEARNED` lookup for structured OR fallback/reviewability

Artifact Identity Check: PASS
Final Feature Suite: N/A WITH REASON
Changed Files:
- `documentation/codex/model-routing/or_family_first_comparison_debug_plan_2026-06-19.md`

## Bound Comparison Package

### Expected vs Actual

Expected:

- direct OR runner should accept a stronger family model slug
- file-first capture should persist all artifacts
- telemetry JSONL should ingest through `health_snapshot.py`
- `quickchange_patch_review` should be the low-risk calibration lane
- `execution_patch_candidate` should tell us whether the family can satisfy bounded structured JSON review contracts better than the current `gpt-oss-20b` result

Actual current state:

- `quickchange_patch_review` is already proven on direct OR transport
- `execution_patch_candidate` on `openai/gpt-oss-20b` failed with `finish_reason=error` and provider JSON-generation failure

### Failure Codes

Use these codes in the next result notes:

- `QUICKCHANGE_FAMILY_COMPARISON_PENDING`
- `EXECUTION_PATCH_CANDIDATE_MODEL_FIT_MISMATCH`
- `DIRECT_OR_CAPTURE_FAILURE`
- `DIRECT_OR_HEALTHCHECK_FAILURE`
- `DIRECT_OR_COST_CAP_EXCEEDED`
- `DIRECT_OR_FINISH_REASON_LENGTH`

## Next Two Concrete Comparisons

### Comparison 1

Task class:

- `quickchange_patch_review`

Model:

- `qwen/qwen3-coder-flash`

Why first:

- cheapest meaningful first Qwen control
- task class already has accepted live OR evidence, so this is the lowest-risk family comparison lane

Runner:

- `documentation/codex/model-routing/scripts/openrouter_direct_quickchange_patch_runner.py`

Acceptance gates:

- same one-file bounded prompt style as the accepted quickchange live retry
- `estimated_or_cost <= quickchange profile cap`
- `generation_id` present
- `usage` present
- `finish_reason != length`
- `validation_result=PASS`
- `health_snapshot.py` ingestion `PASS`

### Comparison 2

Task class:

- `execution_patch_candidate`

Model:

- `qwen/qwen3-coder-flash`

Why second:

- materially different family from the current negative `gpt-oss-20b` row
- same bounded structured JSON contract, so the comparison is clean

Runner:

- `documentation/codex/model-routing/scripts/openrouter_direct_execution_patch_candidate_runner.py`

Acceptance gates:

- same input package family as the prior live retry
- `estimated_or_cost <= execution_patch_candidate profile cap`
- `generation_id` present
- `usage` present
- `finish_reason != length`
- valid JSON payload
- bounded validation `PASS`
- `health_snapshot.py` ingestion `PASS`

## Deferred Immediately After These Two

If both `Qwen` comparisons capture and validate cleanly, the next follow-up is:

1. `execution_patch_candidate` with `deepseek/deepseek-v4-flash`
2. `DOC-SKILL-008` fixed-model comparison with `deepseek/deepseek-v4-flash`

If the quickchange comparison passes but execution still fails:

- classify `Qwen` as viable for lighter proposal work only
- do not generalize success upward to the larger class

If quickchange already fails:

- classify as capture/model mismatch for this family path
- stop before the larger execution call

## Operator Decision Rule

Before any live comparison call:

- show exact model slug
- show task class
- show cost cap from the active budget profile
- show pre-call estimated cost
- show confidence percent and sample-count caveat

Do not start a broad sweep yet.

## Reason This Is The Diamond Path

- It reuses the existing bounded runners.
- It keeps Codex as review/apply owner.
- It tests family change before architecture change.
- It minimizes wasted calls while still producing real evidence.

NEXT_STEP
Target Skill: janus-debug
Canonical State: HANDOFF
Required Artifacts:
- `documentation/codex/model-routing/or_family_first_comparison_debug_plan_2026-06-19.md`
- `documentation/codex/model-routing/or_workhorse_candidate_refresh_2026-06-19.md`
- `documentation/codex/model-routing/quickchange_direct_or_live_retry_result_2026-06-19.md`
- `documentation/codex/model-routing/direct_or_execution_patch_candidate_live_retry_result_2026-06-19.md`
Evidence Paths:
- `documentation/codex/model-routing/or_family_first_comparison_debug_plan_2026-06-19.md`
- `documentation/codex/model-routing/or_workhorse_candidate_refresh_2026-06-19.md`
Failure Code:
- `EXECUTION_PATCH_CANDIDATE_MODEL_FIT_MISMATCH`
Changed Files:
- `documentation/codex/model-routing/or_family_first_comparison_debug_plan_2026-06-19.md`
Decision:
- Run the next bounded family-first comparison on `qwen/qwen3-coder-flash` before spending on broader families.
Reason:
- The current problem is no longer transport; it is structured model fit on the larger class, so the next useful evidence is a materially different family under the same bounded contract.
Recommended Model:
- `5.4`
Recommended Intelligence:
- `medium`
Next User Action:
- Approve the first bounded family-first live comparison on `qwen/qwen3-coder-flash` for `quickchange_patch_review`.
