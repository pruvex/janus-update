# execution_write_apply_candidate Readiness Gap - 2026-06-23

Status: READINESS NOTE / LOCAL VALIDATION ONLY / NO LIVE WRITE ACTIVATION

## Summary

`execution_write_apply_candidate` is no longer blocked by missing runner scaffolding.

The current state is:

- productive Dev-workhorse gate support exists
- dispatcher support exists
- dedicated validation runner exists
- fixture/local validation exists

The remaining blocker is now narrower:

- an accepted `execution_patch_candidate` run directory does not yet automatically provide the exact source-package artifact set that the write-apply validator expects

## What Passed

Local readiness evidence:

- `codex_dev_workhorse_runner.py` already allowlists `execution_write_apply_candidate`
- `codex_bounded_delegation_dispatcher.py` already routes `execution_write_apply_candidate`
- `codex_execution_write_apply_candidate_runner.py` validates accepted-source packages and enforces:
  - `validation_summary.json`
  - `git_diff.patch`
  - `changed_files.txt`
  - no missing validation artifacts
  - Codex-owned accept/reject semantics

## What Failed On A Real Accepted Source

Validated against:

- accepted proposal-first source run:
  - `documentation/codex/model-routing/execution-direct-or-runs/DEV-WORKHORSE-EXECUTION-GATE-003`

Observed reject reasons:

- missing `delegated_result.md`
- missing `summary.json`
- missing `git_diff.patch`
- missing `changed_files.txt`
- `accepted_for_codex_patch_review is not true`
- source `final_outcome` is not normalized to the write-apply validator expectation

## Meaning

This is good news operationally:

- the next blocker is not “OR cannot do write-candidate work”
- the next blocker is not “we still need a whole new runner”
- the next blocker is not “we need more model-family speculation first”

The next blocker is now an artifact-shape seam between:

- accepted proposal-first execution evidence
- and the derivative write-apply candidate source contract

## Practical Interpretation

We now have:

- accepted mini-doc OR lanes
- accepted quickchange OR lane
- accepted review-first `execution_patch_candidate` lane

But we do not yet have:

- an automatic or normalized bridge that converts an accepted `execution_patch_candidate` run into a write-apply-candidate-ready source package

## Next Smallest Useful Step

Build one bounded source-package bridge for `execution_write_apply_candidate`.

That bridge should take an accepted `execution_patch_candidate` run and emit the exact normalized artifacts required by the write-apply validator:

- `delegated_result.md`
- `summary.json`
- `git_diff.patch`
- `changed_files.txt`
- normalized `validation_summary.json`
- normalized accepted-for-review marker

## Decision

The fastest path forward is:

1. do not reopen mini-doc or quickchange lanes
2. do not jump into live write activation
3. add the accepted-source bridge for `execution_write_apply_candidate`
4. validate it locally against `DEV-WORKHORSE-EXECUTION-GATE-003`
5. only then decide whether a first bounded write-candidate pilot is worth a real run
