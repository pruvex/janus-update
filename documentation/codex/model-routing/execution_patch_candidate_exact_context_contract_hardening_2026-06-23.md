# Execution Patch Candidate Exact-Context Contract Hardening

Date: `2026-06-23`
Task: `BACKLOG-108`
Canonical state: `PASS`

## Summary

The bounded `execution_patch_candidate` contract was tightened again for `BACKLOG-108`.

This hardening adds explicit `exact_code_context_blocks` so the OR prompt can see real local code excerpts instead of relying only on seam names, forbidden anchors, signatures, and call-shape examples.

## What Changed

- added `exact_code_context_blocks` support to `openrouter_direct_execution_patch_candidate_runner.py`
- extended the runner request contract with a `context_rule`
- updated the current-shape `BACKLOG-108` input package with real excerpts from:
  - `backend/services/contact_manager.py::_apply_contact_memory_update_directly`
  - `backend/services/contact_manager.py::stage_contact_update_from_memory`
  - `backend/tools/memory_tools.py::handle_memory_write`
- updated unit tests so the new context field is required in the generated request payload

## Validation

- `python -m unittest documentation.codex.model-routing.tests.test_openrouter_direct_execution_patch_candidate_runner`: `PASS`
- fixture contract smoke `EXEC-PATCH-EXACT-CONTEXT-CONTRACT-001`: expected bounded `FAIL`
- `git diff --check`: `PASS` with pre-existing CRLF warnings only

## Interpretation

The fixture contract smoke still rejects the stale old fixture under the stricter exact-context contract.

That is the intended result. It shows the bounded gate is getting stricter rather than silently accepting a patch that is still shaped against the wrong local implementation context.

## Next Step

The next fair test, if this lane continues, is one fresh live proposal-first OR retry using the exact-context package.
