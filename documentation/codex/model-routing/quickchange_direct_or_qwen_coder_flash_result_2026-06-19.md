# Quickchange Direct OR Qwen3 Coder Flash Result - 2026-06-19

Status: FAIL / LIVE RESPONSE CAPTURED / FAMILY-FIRST COMPARISON STOPPED

## Summary

The first family-first bounded quickchange comparison on `qwen/qwen3-coder-flash` completed live transport successfully, stayed under the quickchange cost cap, and produced a semantically correct patch proposal, but it failed the bounded contract because the response shape did not match the required quickchange JSON schema.

- Workflow: `DIRECT-OR-QWEN-QUICKCHANGE-LIVE-001`
- Task class: `quickchange_patch_review`
- OR model: `qwen/qwen3-coder-flash`
- HTTP status: `200`
- Generation id: `gen-1781823601-o1gVP27tbOMhjMOAyUTQ`
- Finish reason: `stop`
- Estimated cost: `0.000975000`
- Actual cost: `0.000241020`
- Cost cap: `0.002000000`
- Healthcheck ingestion: `PASS`

## What Passed

- direct OpenRouter capture completed cleanly
- file-first artifacts were written
- `generation_id` and `usage` were captured
- actual cost stayed far below the quickchange cap
- `finish_reason` was `stop`, not `length`
- `health_snapshot.py` ingestion passed

## Why It Still Failed

The model returned a useful patch-like object, but not the exact schema required by `openrouter_direct_quickchange_patch_runner.py`.

Expected schema keys:

- `status`
- `summary`
- `changed_files`
- `unified_diff`
- `validation_notes`
- `risk_notes`

Returned shape:

- `file`
- `diff`
- `summary` as nested object

Validation therefore failed with:

- `status must be PATCH_PROPOSAL, NO_CHANGE, or BLOCKED`
- `changed_files must be a list`
- `unified_diff must be a string`

## Important Interpretation

This is not the same failure pattern as the earlier `execution_patch_candidate` `gpt-oss-20b` result.

What this result suggests:

- `qwen/qwen3-coder-flash` understood the bounded quickchange task
- it generated a correct semantic diff for the requested placeholder change
- but it did not obey the stricter Janus quickchange response envelope

So the current failure is best classified as:

- `DIRECT_OR_SCHEMA_ENVELOPE_MISMATCH`

not:

- transport failure
- cost failure
- finish-reason truncation
- semantic task failure

## Immediate Decision

Per the family-first debug plan, do not proceed automatically to the larger `execution_patch_candidate` call on this family.

Stop here and classify the result first.

Reason:

- if the family already misses the smaller quickchange schema contract, the larger structured execution contract should not be attempted immediately under the same assumption set

## Best Next Follow-Up Options

1. Keep the current strict quickchange schema and mark this family as `needs prompt/schema adaptation before larger-class retry`.
2. Compare `deepseek/deepseek-v4-flash` next on the same quickchange lane to learn whether the issue is Qwen-specific or common among non-OpenAI coding families.
3. If we want to preserve Qwen as a candidate, add a narrow compatibility shim or prompt tightening experiment for the quickchange envelope before any larger-class Qwen retry.

## Boundary Reminder

- no production routing is activated
- no canonical routing-table update is made
- no broad Qwen approval exists
- no automatic continuation into `execution_patch_candidate` is approved by this result
