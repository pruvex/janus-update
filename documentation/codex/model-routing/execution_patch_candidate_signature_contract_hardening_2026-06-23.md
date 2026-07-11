# Execution Patch Candidate Signature Contract Hardening

Date: `2026-06-23`
Task: `BACKLOG-108`
Canonical state: `PASS`

## Summary

The `BACKLOG-108` proposal-first OR contract now carries not only seam-family guidance, but also explicit local function signatures and call-shape examples.

## Changes

- extended `openrouter_direct_execution_patch_candidate_runner.py` with optional:
  - `signature_context`
  - `call_shape_examples`
- extended the focused runner test coverage
- updated the current-shape `BACKLOG-108` input package with the real local signatures and invocation examples for:
  - `_apply_contact_memory_update_directly(...)`
  - `stage_contact_update_from_memory(...)`
  - `handle_memory_write(...)`

## Validation

- `python -m unittest documentation.codex.model-routing.tests.test_openrouter_direct_execution_patch_candidate_runner`
  - `PASS`
- fixture contract smoke:
  - `EXEC-PATCH-CURRENT-SHAPE-SIGNATURE-CONTRACT-001`
  - result: `FAIL` as expected
  - classification: bounded rejection still works under the stricter signature-aware contract

## Meaning

This is the strongest bounded `BACKLOG-108` OR input contract so far.

The next real live proposal-first OR retry can now be guided by:

- real seam names
- forbidden legacy anchors
- required current anchors
- explicit local signatures
- explicit local call-shape examples
