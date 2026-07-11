# Execution Patch Candidate Exact-Context Package Cleanup

Date: `2026-06-23`
Task: `BACKLOG-108`
Canonical state: `PASS`

## Summary

The exact-context `BACKLOG-108` input package was corrected after the live retry `EXEC-PATCH-EXACT-CONTEXT-LIVE-004` returned a bounded `BLOCKED` no-patch result.

The model correctly identified that the provided `stage_contact_update_from_memory(...)` excerpt referenced `proposal_payload` before that variable was shown as defined.

## Fix Applied

The `exact_code_context_blocks` entry for `backend/services/contact_manager.py::stage_contact_update_from_memory` now includes the real intermediate local flow before the auto-apply decision:

- ambiguous-contact guard
- no-contact-fields guard
- `proposal_payload: Dict[str, Any] = {}`
- the merge loop over extracted updates
- already-applied guard
- the auto-apply call using the now-defined `proposal_payload`

## Why This Matters

The previous live retry did not fail because OR hallucinated a wrong architecture.

It failed because the exact-context package itself was internally inconsistent.

Cleaning that package is necessary before one final fair live retry can tell us whether proposal-first OR can produce an apply-reviewable candidate on this lane.

## Validation

- exact-context package reviewed against the real local `backend/services/contact_manager.py` flow: `PASS`
- `git diff --check`: `PASS` with pre-existing CRLF warnings only

## Next Step

If this lane continues, the next step is one final bounded live retry using the cleaned exact-context package.
