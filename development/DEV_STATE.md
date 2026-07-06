# DEV_STATE

## Project
Janus Dev And OR Infrastructure

## Current Goal
Prepare a narrow Git-governance checkpoint after the completed DEV-011 documentation closeout.

## Active Phase
DEV-011 documentation update complete; ready for janus-git-governance checkpoint

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
- Run `janus-git-governance` for a narrow checkpoint covering DEV-011 closeout artifacts.
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

## Next Recommended Step
Run `janus-git-governance` for `DEV-011`, then decide deliberately whether to commit this closeout as its own checkpoint.

## Last Updated
2026-07-06 16:08 +02:00
