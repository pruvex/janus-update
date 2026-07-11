# Quickchange Direct OR Live Retry Result - 2026-06-19

Status: PASS / LIVE DIRECT OR EVIDENCE ACCEPTED / PROPOSAL-ONLY

## Summary

The first bounded live `janus-quickchange` retry through the corrected direct OpenRouter transport succeeded.

- Workflow: `DIRECT-OR-DISPATCH-LIVE-001`
- Task class: `quickchange_patch_review`
- OR model: `openai/gpt-oss-20b`
- Finish reason: `stop`
- Generation id: `gen-1781821344-IVDxjXK4ohnN4JDVxLF3`
- Estimated cost: `0.000250000`
- Actual cost: `0.000144430`
- Cost cap: `0.002000000`
- Healthcheck ingestion: `PASS`

## What Passed

- Direct OpenRouter HTTP call returned `200`.
- File-first artifacts were persisted:
  - `request_body.json`
  - `response_body.json`
  - `response_headers.txt`
  - `response_summary.json`
  - `stdout.log`
  - `stderr.log`
  - `exit_code.txt`
- `generation_id`, `usage`, and `actual_or_cost` were captured from the real response.
- The structured patch proposal stayed inside the one-file allowlist:
  - `frontend/index.html`
- `finish_reason` was `stop`, not `length`.
- Telemetry JSONL parsed and `health_snapshot.py` ingested it successfully.

## Patch Proposal Outcome

The direct OR worker returned a valid bounded patch proposal for the two chat placeholder lines in `frontend/index.html` only:

- from: `Nachricht an Janus senden...`
- to: `Nachricht an Janus schreiben...`

No second file, no delete, no rename, and no move operation appeared.

## Interpretation

This resolves the transport blocker that existed in the ChatGPT-account-backed Codex CLI sidecar model-selection path.

The result does **not** mean:

- production routing is active
- OR has broad write authority
- Codex review is skipped
- global OR approval exists

It does mean:

- the direct OpenRouter worker path is viable for bounded quickchange proposal work
- OpenRouter can now serve as a real bounded worker under the Diamond model
- Codex can remain the acceptance and local-apply owner

## Next Safe Step

Use this live success as the acceptance anchor for the first everyday `janus-quickchange` OpenRouter option, then either:

1. Codex reviews and locally applies this exact accepted placeholder change, or
2. we promote the same direct transport pattern into the next bounded task class

Any broader write-capable OR rollout still needs separate bounded evidence.
