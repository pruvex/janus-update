# DEV_BACKLOG

This backlog tracks Dev- and OR-infrastructure work only. It is separate from the Janus product backlog.

## Status Rules

- `NEEDS INFO`: required infrastructure context is missing
- `READY`: clear enough for bounded Dev implementation or governance work
- `IN PROGRESS`: explicitly active in the Dev system
- `DONE`: completed with evidence
- `BLOCKED`: cannot proceed without an external decision or dependency

## Scope Rules

- Include only Dev environment, OR infrastructure, runner, wrapper, telemetry, model-routing support, operator-flow support, and related governance work.
- Do not use this backlog for Janus product features, user-facing behavior, release notes, or product bug prioritization.
- If a Janus product item depends on a Dev item here, Janus keeps only the product context and a slim reference.

## Initial Items

### DEV-001 - Migrate mixed Dev and OR infrastructure topics out of Janus backlog

- **Type:** GOVERNANCE
- **Status:** READY
- **Short Description:** Move existing Dev- and OR-infrastructure topics out of the Janus product backlog into this Dev system without losing product context where a slim Janus reference is still needed.
- **Area:** Backlog governance / migration

### DEV-002 - Harden Janus governance docs to enforce Dev separation

- **Type:** GOVERNANCE
- **Status:** READY
- **Short Description:** Update Janus governance files so future Dev- and OR-infrastructure topics do not drift back into the Janus product system.
- **Area:** Governance hardening
