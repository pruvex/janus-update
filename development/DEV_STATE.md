# DEV_STATE

## Project
Janus Dev And OR Infrastructure

## Current Goal
Close the completed archive-view helper slice cleanly and prepare the next bounded MCP-helper follow-up or checkpoint.

## Active Phase
DEV-008.1 fully documented after final audit PASS; ready for narrow git checkpoint or the next bounded follow-up

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
- Continue the current bounded executor-based rollout for high-value everyday skills.
- Decide whether the next bounded MCP-helper follow-up should improve archive retrieval ergonomics or pause for a governance checkpoint.
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

## Next Recommended Step
Run `janus-git-governance` for a narrow checkpoint covering `DEV-008.1` closeout, or route one new bounded MCP-helper follow-up only after keeping the archive-view slice local-only, deterministic, and read-only.

## Last Updated
2026-07-05 20:50 +02:00
