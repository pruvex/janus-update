# Execution Write Apply Candidate Live Sidecar Enablement

Date: `2026-06-23`
Scope: `janus-executioner` bounded Dev-workhorse infrastructure only
Canonical state: `PASS`

## Summary

`execution_write_apply_candidate` can now progress beyond accepted-source validation into a bounded delegated `workspace-write` pilot path.

This closes the previous gap where the class could only consume and validate a normalized accepted source package, but could not itself invoke a real delegated write runtime.

## What Changed

- extended `codex_execution_write_apply_candidate_runner.py` with an optional live sidecar mode
- added prompt generation that binds the live write to the exact accepted source package and exact changed-file allowlist
- added sidecar-run validation requiring:
  - `summary.json` status `PASS`
  - `allowlist_ok = true`
  - `touched_file_cap_ok = true`
  - `delete_rename_move_ok = true`
  - touched files exactly matching the expected accepted-source changed-file list
  - non-empty `git_diff.patch`
- forwarded the new execution live-sidecar flags through:
  - `codex_bounded_delegation_dispatcher.py`
  - `codex_dev_workhorse_runner.py`

## Validation

- `python -m unittest documentation.codex.model-routing.tests.test_execution_write_apply_candidate_live_operator_path documentation.codex.model-routing.tests.test_bounded_write_candidate_validation_acceptance documentation.codex.model-routing.tests.test_bounded_write_candidate_entry_gate documentation.codex.model-routing.tests.test_codex_dev_workhorse_runner`
  - `PASS`
- `git diff --check`
  - `PASS` with pre-existing CRLF warnings only
- `git diff --cached --name-only`
  - empty

## Boundary

No live delegated write was executed in this enablement block.

The new path is implementation-ready and locally validated with fake/fixture sidecar output only.

## Next Gate

The next explicit operator step can now be one first real bounded `execution_write_apply_candidate` live pilot using the accepted-source package, instead of more infrastructure work.
