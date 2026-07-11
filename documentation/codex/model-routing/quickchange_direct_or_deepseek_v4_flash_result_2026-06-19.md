# Quickchange Direct OR DeepSeek V4 Flash Result - 2026-06-19

Status: PASS / LIVE RESPONSE CAPTURED / FAMILY-FIRST COMPARISON ACCEPTED

## Summary

The second family-first bounded quickchange comparison, this time on `deepseek/deepseek-v4-flash`, passed the full Janus quickchange contract.

- Workflow: `DIRECT-OR-DEEPSEEK-QUICKCHANGE-LIVE-001`
- Task class: `quickchange_patch_review`
- OR model: `deepseek/deepseek-v4-flash`
- Response model field: `deepseek/deepseek-v4-flash-20260423`
- HTTP status: `200`
- Generation id: `gen-1781823945-HBOwkqNZKWna7EAULg2V`
- Finish reason: `stop`
- Estimated cost: `0.000207000`
- Actual cost: `0.000086600`
- Cost cap: `0.002000000`
- Healthcheck ingestion: `PASS`

## What Passed

- direct OpenRouter capture completed cleanly
- file-first artifacts were written
- `generation_id` and `usage` were captured
- actual cost stayed well below the quickchange cap
- `finish_reason` was `stop`
- bounded validation passed with no issues
- `health_snapshot.py` ingestion passed

## Returned Proposal Quality

The returned proposal used the correct Janus quickchange schema:

- `status`
- `summary`
- `changed_files`
- `unified_diff`
- `validation_notes`
- `risk_notes`

It stayed inside the one-file allowlist:

- `frontend/index.html`

It also preserved the exact narrow intent:

- change `Nachricht an Janus senden...`
- to `Nachricht an Janus schreiben...`
- no extra file
- no extra wording
- no delete, move, or rename

## Comparison Against The Qwen Quickchange Probe

On the same bounded lane:

- `qwen/qwen3-coder-flash`
  - semantic diff: promising
  - schema envelope: failed
  - final classification on this lane: `FAIL / NEEDS_SCHEMA_ADAPTATION`
- `deepseek/deepseek-v4-flash`
  - semantic diff: correct
  - schema envelope: correct
  - final classification on this lane: `PASS / READY_FOR_LARGER_CLASS_PROBE`

This means the family-first ladder did exactly what it was supposed to do:

- it prevented us from overgeneralizing from one family
- it identified a stronger next candidate for the larger bounded class

## Decision

`deepseek/deepseek-v4-flash` is now the best current next candidate for the first larger direct OR retry on:

- `execution_patch_candidate`

Reason:

- it already cleared the smaller bounded proposal lane
- it did so with correct schema discipline
- it was cheaper than estimated

## Boundary Reminder

- no production routing is activated
- no canonical routing-table update is made
- no global DeepSeek approval exists
- this is bounded local evidence only
