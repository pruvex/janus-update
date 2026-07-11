# AUDIT PACKAGE

## Scope

- Target Task: `TASK-SPEC25.1`
- Spec: `documentation/SPEC/25_produktiver_dev_workhorse_hauptpfad_fuer_or_arbeitspferd.md`
- Task File: `documentation/tasks/TASK-SPEC25_produktiver_dev_workhorse_hauptpfad_fuer_or_arbeitspferd.md`
- Precheck: `documentation/tasks/TASK-SPEC25.1_preimplementation_check.md`
- Execution Result: `documentation/tasks/TASK-SPEC25.1_execution_result.md`

## Goal

Harden the first productive Dev-workhorse main-path contract so that only the intended bounded write/apply work classes remain eligible and each of those classes carries a fixed recommended OR model before any visible operator gate or productive runtime slice is activated.

## Pipeline Completion Status

- `TASK-SPEC25.1`: implementation COMPLETE - the productive Dev-workhorse contract is now narrowed to the first bounded write/apply classes and requires fixed recommended OR model mappings.
- `TASK-SPEC25.2`: NOT STARTED - visible operator-gate output for fixed model and cost basis remains intentionally untouched.
- `TASK-SPEC25.3`: NOT STARTED - productive runtime wiring and Codex-owned acceptance flow remain intentionally untouched.
- Remaining validation gate: run `janus-final-audit` on this slice only; no production routing, canonical routing-table update, or broad skill activation is included here.

## Changed Files

- `documentation/codex/model-routing/config/bounded_or_worker_eligibility_2026-06-17.json`
- `documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py`
- `documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py`
- `documentation/tasks/TASK-SPEC25.1_AUDIT_PACKAGE.md`
- `documentation/tasks/TASK-SPEC25.1_execution_result.md`

## Validation

- `python -m unittest documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py`
- `python -m py_compile documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py`
- `git diff --check -- documentation/codex/model-routing/config/bounded_or_worker_eligibility_2026-06-17.json documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py`
- `python C:\Users\pruve\.codex\skills\janus-executioner\scripts\validate_execution_result.py documentation/tasks/TASK-SPEC25.1_execution_result.md`

## Known Risks

- This slice is contract-only and intentionally does not prove the visible operator gate or the bounded productive runtime path yet.
- The initial fixed recommended OR model mapping is now pinned for the first productive classes, but any later evidence-based model change must happen in a separate bounded task and review.
- No commit or push has happened for this local execution state yet, so remotes may not contain the latest implementation or `CURRENT_STATE`.

## Blocker Delta Summary

- Removed the older mixed review class from the dedicated productive main path so the contract now reflects bounded write/apply work only.
- Added required fixed recommended OR model mappings for the first productive task classes.
- Added a fail-closed eligibility boundary for missing `selected_or_model` so incomplete productive mappings cannot silently pass.

## Audit Focus

- The dedicated `productive_dev_workhorse_path` must allow only the intended first bounded write/apply classes.
- Each allowed productive class must carry a fixed recommended OR model.
- Missing class or model mapping must block before any productive OR gate can exist.
- Older assist-only or review-oriented pilot families must remain unchanged outside the dedicated productive path.
