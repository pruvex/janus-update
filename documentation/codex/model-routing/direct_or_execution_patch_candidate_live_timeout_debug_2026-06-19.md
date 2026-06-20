# Direct OR Execution Patch Candidate Live Timeout Debug - 2026-06-19

Status: BLOCKED / ONE LIVE ATTEMPT MADE / NO ACCEPTED TELEMETRY

## Summary

The first bounded live `execution_patch_candidate` attempt through the new direct OpenRouter path did not produce an accepted result package.

- Workflow: `DIRECT-OR-EXECUTION-DISPATCH-LIVE-001`
- Live call attempts in this note: `1`
- Accepted telemetry rows from this live attempt: `0`

## What Happened

The dispatcher launched the new direct execution patch candidate runner and the runner launched the file-first OpenRouter wrapper.

The outer shell command then timed out before the wrapper returned a response package.

Observed artifact state after the forced stop:

- present:
  - `input_package.json`
  - `request_body.json`
  - `request_body_source.json`
- missing:
  - `response_body.json`
  - `response_headers.txt`
  - `response_summary.json`
  - `operator_summary.json`
  - telemetry JSONL for this live run

## Root Cause

The file-first wrapper had no explicit HTTP timeout on the underlying `HttpWebRequest`.

That meant:

- the outer caller timeout could fire first
- the in-flight wrapper and Python process chain could remain hanging
- no bounded response artifacts would be guaranteed before termination

This is a transport-hardening issue, not evidence that the direct OR execution patch candidate concept is invalid.

## Fix Applied

`documentation/codex/model-routing/scripts/or_file_first_capture_wrapper.ps1` now sets:

- `Timeout`
- `ReadWriteTimeout`

using:

- `RequestTimeoutMs`
- default `120000`

This keeps the timeout boundary inside the wrapper-owned transport layer instead of relying only on the outer shell timeout.

## Validation After Fix

Local fixture validation after timeout hardening:

- workflow: `DIRECT-OR-EXECUTION-FIXTURE-TIMEOUT-HARDEN-001`
- result: `PASS`
- final outcome: `DIRECT_OR_EXECUTION_PATCH_READY_FOR_CODEX_REVIEW`
- healthcheck ingestion: `PASS`

This proves the timeout hardening did not break the direct execution patch candidate flow in fixture mode.

## Interpretation

- One live OR call was attempted.
- That live attempt does not count as accepted operational evidence.
- No second live OR call was made in this debug step.

## Next Safe Step

If the user explicitly approves it, run exactly one additional bounded live `execution_patch_candidate` retry after the wrapper timeout hardening, then accept the result only if full response artifacts, usage, generation id, validation summary, and healthcheck ingestion all succeed.
