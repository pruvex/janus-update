# DEV_STATE

## Project
Janus Dev And OR Infrastructure

## Current Goal
Use the completed DEV-011 evidence-gap plan to convert the highest-priority delegation lanes from no-live planning into lane-by-lane live evidence, with `TASK-EX-002`, `TASK-EX-001`, `TASK-TP-003`, `TASK-DBG-002`, and now `TASK-FD-001` functionally proven or productized in their current bounded forms.

## Active Phase
Post-DEV-011 lane proof consolidation, golden-path cleanup, and next-slice selection

## Current Source Of Truth
- `development/README.md`
- `development/DEV_STATE.md`
- `development/DEV_BACKLOG.md`

## Current Rules
- This area is the Source of Truth for Dev- and OR-infrastructure work.
- Janus remains the Source of Truth for product work and user-facing behavior.
- This area does not claim Janus product, Git, release, production-routing, or final-audit authority.
- Lean Dev mode is allowed only for small and medium bounded internal Dev slices.
- Validation, `documentation/ai/CURRENT_STATE.md`, and sensible Git checkpoints remain mandatory in Lean Dev mode.
- Lean Dev mode ends immediately when product logic, security/privacy, release/Git-governance, unclear scope, or new productive approval becomes involved.

## Open Work
- Decide whether to checkpoint DEV-011 now or keep the repo as-is while continuing bounded routing validation work.
- Treat `feature_design_review` as bounded live-proven for one review-only OR slice and decide whether to productize another unresolved OR lane or move from lane proof toward higher-value workflow integration.
- Treat `debug_repro_investigation`, `test_fixture_worker`, and `execution_write_apply_candidate` as productized-enough reference lanes in their current bounded forms, and spend the next slice on cleanup or a different unresolved lane instead of more proof here.
- Keep `execution_write_apply_candidate` on deterministic local apply as the recommended option-2 worker and stop spending live-run budget on Cursor for that apply step.
- Decide whether EX-001 needs one tiny order-semantic tightening pass or whether its current proof is sufficient and we should move on.
- Decide whether the next value is a small transitional-wording cleanup pass or a move to one of the remaining unresolved lanes.
- Use the evidence-gap plan to choose the next no-live shadow-fixture or explicitly approved live-smoke slice instead of tuning no-evidence lanes by memory.
- Keep execution-lane default tuning deferred until the evidence set is cleaner and less dominated by older experiment variance.
- Keep the separation between Lean Dev work and strict Janus product work explicit in future governance changes.

## Open Risks
- Mixed Dev- and OR-infrastructure topics still exist in Janus artifacts until the migration slice is executed.
- Lean Dev mode must not bleed into Janus product work, release work, or security/privacy-sensitive changes.
- Installed skill working copies under `C:\Users\pruve\.codex\skills` must not become an implicit execution target for Lean-Dev governance slices.
- OpenRouter MCP could distract from the current bounded execution architecture if treated as an execution replacement instead of an information layer.
- The renderer/stub must stay deterministic and local-only in its first slice; live fetches, autonomous execution, and write authority would widen the scope too early.
- The input-prep helper must also stay deterministic and local-only in its first slice; it must not silently grow into live evidence collection or execution orchestration.
- The comparison-artifact helper must not silently widen from archival comparison support into recommendation synthesis, live evaluation, or execution orchestration.
- The new archive-view helper must remain a read-only review surface and must not drift into winner selection, execution triggers, or live routing authority.
- The new calibration helper currently depends on bounded path patterns; future follow-ups must keep that evidence scope explicit and avoid silently treating every historical experiment as equally authoritative.
- Execution-lane evidence is still noisy and spans older transport experiments, so any follow-up tuning there should stay conservative and review-driven rather than auto-applied.
- The new triage and debug defaults are evidence-backed, but they still rely on a relatively small number of historical runs and should be revisited after more productive shared-gate usage.
- `spec_to_task_review` still rests on only one bounded sample even after tuning, so later evidence should confirm the new default before treating it as stable long-term.
- DEV-011 is now closed, but the latest closeout exists only locally until a later approved checkpoint/push happens.
- `debug_repro_investigation` is now live-smoke proven as a bounded no-op/pass case, but the calibration helper does not yet automatically ingest that Cursor evidence.
- `execution_write_apply_candidate` now has strong evidence and routing support for the local deterministic apply surface, but older docs may still describe the historical Cursor/OR apply story and need cleanup over time.
- `execution_patch_candidate` is now live-proven for actual bounded patch generation, but the current shadow assertion is still permissive about line order.
- `test_fixture_worker` now has a clear golden-path doc, but transitional wording in older design/handoff notes still exists elsewhere in the repo.
- `debug_repro_investigation` now has a clear golden-path doc, but transitional wording in older design/handoff notes still exists elsewhere in the repo.
- `feature_design_review` now has one clean bounded live OR proof, but it is still an assist-only review lane and should not be mistaken for final product-decision authority.

## Next Recommended Step
Either move to the next explicitly approved unresolved OR lane, or use the new `feature_design_review` live evidence to decide whether feature-design-class OR assist lanes are productized enough for current needs.

## Last Updated
2026-07-07 16:12 +02:00
