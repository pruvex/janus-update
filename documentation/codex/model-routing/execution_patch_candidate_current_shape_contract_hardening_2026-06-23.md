# Execution Patch Candidate Current-Shape Contract Hardening

Date: `2026-06-23`
Task: `BACKLOG-108`
Canonical state: `PASS`

## Summary

The direct OpenRouter execution patch candidate contract now supports explicit current-shape guidance so `BACKLOG-108` can be bound to the real local seam instead of drifting back to the obsolete `ContactManager` architecture.

## Changes

- extended `openrouter_direct_execution_patch_candidate_runner.py` to pass optional:
  - `current_seam_context`
  - `forbidden_anchors`
  - `required_current_anchors`
- added a new bounded input package:
  - `documentation/codex/model-routing/execution-review-fixtures/backlog_108_execution_patch_candidate_input_package_current_shape_2026-06-23.json`
- hardened the runner test so the new anchor guidance is covered

## Validation

- `python -m unittest documentation.codex.model-routing.tests.test_openrouter_direct_execution_patch_candidate_runner`
  - `PASS`
- fixture contract smoke with the new current-shape package:
  - `EXEC-PATCH-CURRENT-SHAPE-CONTRACT-001`
  - result: `FAIL` as expected
  - reason: the old fixture attempted to touch `scripts/dev-log-utils.cjs`, which correctly escaped the `BACKLOG-108` allowlist

## Meaning

This is a good failure.

It proves the new input package is no longer generic enough to silently accept an unrelated or stale patch shape. The next live `BACKLOG-108` proposal-first attempt can therefore be made with a much tighter contract around:

- `stage_contact_update_from_memory`
- `handle_memory_write`
- `memory_write_tool`

and explicit rejection of:

- `class ContactManager`
- `get_or_resolve_contact`
- `persist_contact_updates`
- `store_memory_facts`
- `create_contact_proposal`
