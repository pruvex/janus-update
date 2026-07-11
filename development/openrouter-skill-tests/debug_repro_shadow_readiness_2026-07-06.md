# Debug Repro Shadow Readiness

- Date: `2026-07-06`
- Lane: `debug_repro_investigation`
- Task ID: `TASK-DBG-002`
- Backend focus: `Cursor`
- Scope: no-live shadow readiness validation only

## Inputs Confirmed

- Input package: `documentation/codex/model-routing/fixtures/cursor-shadow-catalog/debug_repro_investigation/input_package.json`
- Worker package: `documentation/codex/model-routing/fixtures/cursor-shadow-catalog/debug_repro_investigation/worker_package.json`
- Allowlist: `documentation/codex/model-routing/fixtures/cursor-shadow-catalog/debug_repro_investigation/allowlist.txt`
- Validation command: `python -m pytest documentation/codex/model-routing/fixtures/cursor-shadow-catalog/debug_repro_investigation/sandbox/test_debug_repro_shadow.py -q`

## Validation Result

- Status: `PASS`
- Pytest result: `1 passed`
- Shadow mismatch state: `resolved in fixture`
- Allowlisted files only:
  - `runner_plan_shadow.json`
  - `executed_runner_shadow.json`
  - `test_debug_repro_shadow.py`

## Readiness Decision

- Ready for next step: `YES`
- Next recommended step: one explicitly approved live Cursor smoke for `TASK-DBG-002`
- Live approval included here: `NO`
- Manifest tuning implied: `NO`
- Production routing implied: `NO`

## Notes

- This validation confirms the shadow package is internally coherent before any live Cursor run.
- The bounded live step should still use the shared `janus_delegate.py` path and remain allowlist-limited.
