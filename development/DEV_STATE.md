# DEV_STATE

## Project
Janus Dev And OR Infrastructure

## Current Goal
Choose the next small MCP-helper follow-up after the completed renderer/stub slice.

## Active Phase
DEV-005.1 documentation closeout complete; ready to choose the next MCP-helper follow-up

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
- Decide whether the next MCP-helper follow-up should stay local-only or move toward a slightly richer input-prep helper for assembling the structured recommendation package.
- Keep the separation between Lean Dev work and strict Janus product work explicit in future governance changes.

## Open Risks
- Mixed Dev- and OR-infrastructure topics still exist in Janus artifacts until the migration slice is executed.
- Lean Dev mode must not bleed into Janus product work, release work, or security/privacy-sensitive changes.
- Installed skill working copies under `C:\Users\pruve\.codex\skills` must not become an implicit execution target for Lean-Dev governance slices.
- OpenRouter MCP could distract from the current bounded execution architecture if treated as an execution replacement instead of an information layer.
- The renderer/stub must stay deterministic and local-only in its first slice; live fetches, autonomous execution, and write authority would widen the scope too early.

## Next Recommended Step
Route the next small MCP-helper follow-up. Recommended candidate: a bounded input-prep helper that assembles the renderer package from local evidence fields while still avoiding live fetches, executor changes, production routing, and repo-write delegation.

## Last Updated
2026-07-04 14:20 +02:00
