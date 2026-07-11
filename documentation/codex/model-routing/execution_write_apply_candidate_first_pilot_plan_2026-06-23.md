# execution_write_apply_candidate First Pilot Plan - 2026-06-23

Status: PILOT PLAN ONLY / NO LIVE WRITE ACTIVATION YET / NO PRODUCTION ROUTING

## Goal

Prepare the first explicitly approvable bounded `execution_write_apply_candidate` pilot now that:

- accepted proposal-first execution evidence exists
- the accepted-source bridge exists
- the derivative write-apply validator accepts the normalized real source package

This plan does not itself approve a live delegated write.

## Proposed Pilot Source

Accepted proposal-first source:

- `documentation/codex/model-routing/execution-direct-or-runs/DEV-WORKHORSE-EXECUTION-GATE-003`

Normalized write-apply source package:

- `documentation/codex/model-routing/execution-write-apply-source-bridges/EXEC-WRITE-APPLY-SOURCE-BRIDGE-001`

Target task binding:

- `BACKLOG-108`

## Why This Is The Best First Pilot

- real prechecked source, not a synthetic fixture
- accepted proposal-first execution evidence already exists
- changed-file set is only:
  - `backend/services/contact_manager.py`
  - `backend/tools/memory_tools.py`
- the source package already passes the derivative write-apply validator locally

## Pilot Boundaries

- exactly one pilot only
- no production routing
- no canonical routing-table update
- no global OR approval
- no delegated final task completion
- no delegated test execution
- Codex remains final accept-or-reject owner

## Pilot Gates

The pilot should be considered runnable only if all remain true at launch time:

- accepted source package validation = `PASS`
- changed files remain exactly the two already normalized files
- no delete / rename / move activity is introduced
- post-run diff capture remains mandatory
- post-run changed-files capture remains mandatory
- local validation capture remains mandatory

## Pilot Acceptance Criteria

Treat the first write-apply pilot as a technical success only if all are true:

- delegated write candidate completes with reviewable artifacts
- touched files remain within:
  - `backend/services/contact_manager.py`
  - `backend/tools/memory_tools.py`
- no allowlist escape occurs
- no touched-file-cap escape occurs
- post-run diff capture exists
- changed-files capture exists
- validation artifacts exist
- Codex can still clearly accept, adapt, or reject locally

## Pilot Abort Rules

Abort or reject immediately if any of these happens:

- changed file escapes allowlist
- changed file count grows beyond the normalized accepted source
- delete / rename / move activity appears
- diff capture is missing
- changed-files capture is missing
- validation artifacts are missing
- the delegated path claims broad authority beyond a bounded write candidate

## Operator Recommendation

If this pilot is explicitly approved later, treat it as:

- `OR_REVIEW_FIRST`

not as:

- `PREFER_OR`

Reason:

- this is the first derivative write-capable pilot, not yet a stable everyday lane

## Suggested Pilot Identity

- workflow id: `EXEC-WRITE-APPLY-PILOT-001`
- class: `execution_write_apply_candidate`
- normal target model: `5.4 medium`
- accepted source run dir:
  - `documentation/codex/model-routing/execution-write-apply-source-bridges/EXEC-WRITE-APPLY-SOURCE-BRIDGE-001`

## Next Step

If you want to move as fast as possible, the next step is not more planning.

The next step is:

- show the bounded operator gate for `execution_write_apply_candidate`
- then wait for one explicit approval before any real delegated write pilot is attempted
