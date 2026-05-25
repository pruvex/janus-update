# BACKLOG-001 Final Audit - Test-Dateien in Root-Verzeichnis aufraeumen

Date: 2026-05-21
Status: PASS

## Scope

BACKLOG-001 was originally completed on 2026-05-07. This audit revalidated the dashboard-active recommendation and closed the remaining root hygiene drift:

- Original BACKLOG-001 files are no longer in the project root and exist under `tests/`.
- Additional tracked root test artifacts were moved to test-owned locations.
- Ignored root log artifact `test-output.log` was removed.
- Backlog parsing was hardened so completed items are not overwritten by following section metadata.

## Changes

- `test_backlog_033_verification.py` moved to `tests/test_backlog_033_verification.py`.
- `test_config.json` moved to `tests/fixtures/test_config.json`.
- `backend/services/backlog/parser.py` closes the current item when a new `##` section starts.
- `janus-dashboard/apps/api/src/index.ts` mirrors the section-boundary parser behavior.
- `tests/test_backlog_parser.py` adds regressions for real dash headings and section-boundary item closure.

## Evidence

- `python -m pytest tests\test_backlog_parser.py -q` -> PASS, 6 passed.
- `python -m pytest tests\test_backlog_033_verification.py -q` -> PASS, 1 passed.
- `python -m py_compile backend\services\backlog\parser.py tests\test_backlog_parser.py` -> PASS.
- Direct parse check: BACKLOG-001 status `DONE`, section `DONE`; backlog counts total=81, active=3, done=78, routing_missing=0.
- `npm run sync:backlog` in `janus-dashboard` -> snapshot synced total=81 active=3 done=78 routing_missing=0.
- `npm run build --workspace apps/api` in `janus-dashboard` -> PASS.
- Root `test*` file scan -> no remaining root test files.
- Dashboard recommendation API no longer recommends BACKLOG-001; next recommendation is BACKLOG-071.

## Verdict

PASS. BACKLOG-001 is diamond-standard complete: root test artifacts are organized, parser/dashboard state is correct, regression tests cover the failure mode, and the dashboard now points to the next active item instead of the completed cleanup task.
