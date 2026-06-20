# Direct OR Execution Patch Candidate DeepSeek V4 Flash Hardened Retry Result - 2026-06-19

Status: FAIL / LIVE RESPONSE CAPTURED / REMAINING ISSUE LOOKS LIKE VALIDATOR NORMALIZATION SEAM

## Summary

The second live `execution_patch_candidate` retry on `deepseek/deepseek-v4-flash`, now using the hardened prompt/contract, closed the previous Codex-ownership wording gap but still did not reach acceptance.

- Workflow: `DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-002`
- Task class: `execution_patch_candidate`
- OR model: `deepseek/deepseek-v4-flash`
- Response model field: `deepseek/deepseek-v4-flash-20260423`
- HTTP status: `200`
- Generation id: `gen-1781824682-r5UdKPuY2lQvg6kSNWUO`
- Finish reason: `stop`
- Estimated cost: `0.000441000`
- Actual cost: `0.000735420`
- Cost cap: `0.050000000`
- Healthcheck ingestion: `PASS`

## What Improved

Compared with the first DeepSeek larger-class run:

- `manual_validation_note` now correctly says:
  - `Codex must manually validate this patch locally before task completion.`
- `codex_acceptance_rule` now correctly says:
  - `Codex must review and apply or reject locally.`

That means the prompt hardening did its job on the exact two previously failing governance fields.

## Remaining Failure

The only remaining validation issue was:

- `changed_files must match the files declared in patch_text`

Observed evidence:

- `patch_text` includes `--- a/.gitignore` / `+++ b/.gitignore`
- `changed_files` includes `.gitignore`
- allowed-files handling in the runner normalizes the allowlist entry to `gitignore`

This strongly suggests the remaining fail is not a broad model issue. It appears to be a path-normalization seam around `.gitignore` versus `gitignore` inside the bounded validator path.

## Why This Matters

This is materially different from the earlier failure classes:

- not a provider JSON-generation failure
- not a missing patch
- not a missing validation-step list
- not a Codex-ownership wording miss
- not a scope escape

The model now appears to satisfy the substantive larger-class contract. The remaining rejection looks like an internal comparison mismatch at the validator seam.

## Current Best Classification

- `deepseek/deepseek-v4-flash` remains the strongest larger-class `FURTHER_TEST_CANDIDATE`

More specifically:

- technical patch-candidate quality: strong
- governance wording: now corrected
- remaining blocker: likely bounded path-normalization mismatch for `.gitignore`

## Recommended Next Safe Step

Do not spend another live call immediately.

Instead:

1. inspect and tighten the local validation seam comparing:
   - declared `changed_files`
   - files extracted from `patch_text`
   - allowlist normalization for `.gitignore`
2. validate that seam locally with fixture data
3. only then decide whether a third live DeepSeek retry is even necessary

## Boundary Reminder

- no production routing is activated
- no canonical routing-table update is made
- no global DeepSeek approval exists
- Codex remains local apply/reject and validation owner
