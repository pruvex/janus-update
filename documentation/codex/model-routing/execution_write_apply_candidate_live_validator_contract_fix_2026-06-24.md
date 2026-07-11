# execution_write_apply_candidate Live Validator Contract Fix - 2026-06-24

Canonical state: `PASS`
Scope: bounded Dev-workhorse validator seam only

## Goal

Repair the false-negative live validation seam discovered in `EXEC-WRITE-APPLY-LIVE-PILOT-002`.

## Fixed Validator Seams

- corrected `artifact_success` calculation in `codex_sidecar_skill_runner.ps1`
  - successful exit code `0` now counts as success instead of being treated as null-only
- normalized sidecar `touched_files` in `codex_execution_write_apply_candidate_runner.py`
  - string payloads now collapse to one-item lists before exact comparison
- relaxed the identical pre/post status rejection for already-dirty files
  - when bounded apply success is explicitly present, expected touched files match, and `git_diff.patch` exists, identical status lines no longer cause a false negative

## Validation

- `python -m unittest documentation.codex.model-routing.tests.test_execution_write_apply_candidate_live_operator_path`
  - `PASS`
- `python -m py_compile documentation/codex/model-routing/scripts/codex_execution_write_apply_candidate_runner.py documentation/codex/model-routing/tests/test_execution_write_apply_candidate_live_operator_path.py`
  - `PASS`

## Important Boundary

The immediate recheck run `EXEC-WRITE-APPLY-LIVE-PILOT-002-RECHECK` did not provide a second acceptance result.

Reason:

- after the first live pilot changed `backend/services/contact_manager.py`, accepted-source bridge `002` no longer matched the current working tree snapshot
- the repaired runner correctly blocked the recheck before sidecar execution with:
  - `working tree drift detected for source snapshot: backend/services/contact_manager.py`

## Decision

Bridge `002` is no longer the blocker.

The validator contract is now repaired locally.

The next real live retry must use a freshly regenerated accepted-source bridge from the current working tree, not bridge `002` again.
