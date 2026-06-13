# OR File-First Capture Wrapper Plan - 2026-06-13

Status: LOCAL WRAPPER PREP ONLY / NO OR CALLS / NO MODEL CALLS / NO LIVE EVALS / NO PRODUCTION ROUTING

## Purpose

Prepare a reusable local wrapper for future explicitly approved OR smoke-test execution so capture artifacts are written to disk before any operator summary depends on shell stdout.

## Wrapper Path

- `documentation/codex/model-routing/scripts/or_file_first_capture_wrapper.ps1`

## File-First Contract

The wrapper writes these artifacts under a per-run directory:

- `request_body.json`
- `response_body.json`
- `response_headers.txt`
- `response_summary.json`
- `stdout.log`
- `stderr.log`
- `exit_code.txt`

## Modes

- `local_fixture`
  - reads a local fake response body
  - validates file-first artifact creation without network usage
- `live_http`
  - reserved for a future explicitly approved run only
  - not used in this planning block

## Summary Fields

`response_summary.json` should contain:

- `capture_mode`
- `http_status`
- `generation_id`
- `model`
- `usage`

## Validation Strategy

Use only local fixture data in this block:

1. provide a minimal fake request JSON
2. provide a minimal fake response JSON that includes:
   - `id`
   - `model`
   - `usage`
3. run the wrapper with `-UseLocalFixture`
4. confirm all seven artifact files exist
5. confirm `response_summary.json` contains parsed `generation_id` and `usage`

## Local Fixture Validation Result

Fixture-only validation completed locally with:

- request fixture:
  - `documentation/codex/model-routing/wrapper_fixture_request_2026-06-13.json`
- response fixture:
  - `documentation/codex/model-routing/wrapper_fixture_response_2026-06-13.json`
- output directory:
  - `documentation/codex/model-routing/smoke-test-capture/fixture-validation-2026-06-13/`

Validated artifacts:

- `request_body.json`
- `response_body.json`
- `response_headers.txt`
- `response_summary.json`
- `stdout.log`
- `stderr.log`
- `exit_code.txt`

Validation outcome:

- wrapper created all required artifact files: PASS
- `response_summary.json` includes parsed `generation_id`: PASS
- `response_summary.json` includes parsed `usage`: PASS
- no OR call was made: PASS

## Non-Goals

- no OR calls
- no model calls
- no production routing activation
- no canonical routing-table update
- no `5.4` candidate continuation
