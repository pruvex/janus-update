# Direct OR Execution Patch Candidate Enablement - 2026-06-19

Status: PASS / FIXTURE-VALIDATED / NO LIVE OR CALL

## Summary

The direct OpenRouter worker path is now wired into the first larger bounded consumer class:

- `execution_patch_candidate`

This means the bounded dispatcher no longer depends only on the old Codex CLI sidecar path for proposal-only code patch candidates. It can now route that class through direct OpenRouter transport when an OpenRouter model slug is selected.

## Implemented Changes

- Added:
  - `documentation/codex/model-routing/scripts/openrouter_direct_execution_patch_candidate_runner.py`
- Updated:
  - `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`

The new direct runner:

- loads the prechecked execution input package
- builds a bounded direct OpenRouter request
- uses the file-first capture wrapper
- parses the structured result contract
- validates allowed files and touched-file cap
- writes telemetry JSONL
- runs `health_snapshot.py` ingestion
- leaves Codex as apply/reject and validation owner

## Validation

Direct runner fixture:

- workflow: `DIRECT-OR-EXECUTION-FIXTURE-001`
- result: `PASS`
- final outcome: `DIRECT_OR_EXECUTION_PATCH_READY_FOR_CODEX_REVIEW`
- budget profile: `execution_patch_candidate`
- estimated cost: `0.020000000`
- actual cost: `0.000211400`
- healthcheck ingestion: `PASS`

Dispatcher fixture:

- workflow: `DIRECT-OR-EXECUTION-DISPATCH-FIXTURE-001`
- result: `PASS`
- final outcome: `DIRECT_OR_EXECUTION_PATCH_READY_FOR_CODEX_REVIEW`
- codex-owned status: `CODEX_REVIEW_REQUIRED`
- healthcheck ingestion: `PASS`

Syntax:

```powershell
python -m py_compile documentation\codex\model-routing\scripts\openrouter_direct_execution_patch_candidate_runner.py documentation\codex\model-routing\scripts\codex_bounded_delegation_dispatcher.py
```

Result: PASS

## Why This Matters

This is the first proof that the direct OR worker path is not just good for tiny placeholder or copy proposals.

It now also supports a real larger bounded contract:

- prechecked task slice
- multi-file allowlist
- proposal-only code patch candidate
- Codex-owned acceptance and validation

That is much closer to the actual “cheap workhorse” role we want from OR.

## Boundaries

- no live OR call was made in this enablement step
- no production routing
- no canonical routing-table update
- no broad OR write authority
- no global OR approval

## Next Safe Step

Run exactly one bounded live `execution_patch_candidate` OpenRouter call through the new direct transport, then compare the returned patch candidate against the existing Codex-owned review standards before any local apply decision.
