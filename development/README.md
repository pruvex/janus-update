# Development Governance Home

## Purpose

This directory is the canonical Source of Truth for Dev- and OR-infrastructure work that supports Janus but is not Janus product work.

It exists to keep Janus product governance, backlog work, and user-facing behavior separate from tooling, runner, model-routing, environment, and operator-workflow infrastructure.

## In Scope

- Dev environment setup, hardening, and local workflow rules
- OpenRouter and delegated-worker infrastructure
- Runner, wrapper, capture, and telemetry support files
- Model-routing support artifacts and experiment governance
- Local operator workflow support that does not itself change Janus product behavior
- Dev-only status tracking and backlog management

## Out Of Scope

- Janus product behavior
- Janus user-facing feature backlog
- Janus release authority
- Janus Git authority
- Janus production routing authority
- Janus final audit authority

## Source Of Truth Rules

- Janus remains the Source of Truth for product work, product bugs, product features, and user-facing behavior.
- `development/` is the Source of Truth for Dev- and OR-infrastructure work.
- If a Janus product item depends on infrastructure tracked here, Janus keeps only the product context and a slim reference to the relevant Dev artifact.
- The same infrastructure topic must not be described in full detail in both Janus documentation and `development/`.

## Starting Artifacts

- `development/DEV_STATE.md` holds the rolling status for active Dev- and OR-infrastructure work.
- `development/DEV_BACKLOG.md` holds the separate Dev backlog.

## Governance Note

This area does not grant broad repo authority or silent control over Janus product decisions.

All product-facing Janus changes still require the normal Janus skill flow, validation, and governance gates.

## Lean Dev Mode

Internal Dev- and OR-infrastructure work may use a leaner delivery mode than Janus product work when all of the following are true:

- the slice does not change Janus product logic
- the slice stays small or medium and clearly bounded
- no security or privacy escalation is involved
- no release or Git-governance risk is involved
- no new productive approval is being decided

Minimum obligations remain:

- validation
- `documentation/ai/CURRENT_STATE.md` for substantial work blocks
- a clean Git checkpoint at sensible delivery boundaries

Lean mode ends immediately if scope drifts, Janus product logic becomes involved, security/privacy is touched, release/Git-governance is touched, or a new productive approval is being decided.

## Current Lean-vs-Strict Entry Map

Current repo-owned internal entrypoints are classified as follows:

- Lean-Dev eligible:
  - `development/README.md`, `development/DEV_STATE.md`, and `development/DEV_BACKLOG.md` when the slice stays on internal Dev-/OR-/workhorse-governance only
  - `documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md` when the slice only operationalizes local Dev workflow, runner, telemetry, capture, or operator support for Dev-only infrastructure
  - `documentation/codex/model-routing/*` and adjacent repo-owned Dev-workhorse support artifacts when the slice remains explicitly Dev-only and does not claim production routing or Janus product authority
- Strict-only:
  - Janus product skills, product backlog work, user-facing behavior, and any Janus runtime logic that affects end users
  - release, publish, tag, merge, and public GitHub/update actions
  - `janus-git-governance` approval steps for commit/push/tag/merge themselves
  - installed skill working copies under `C:\Users\pruve\.codex\skills`
  - production routing, canonical routing-table updates, and new productive approvals

If one slice touches both lists, the slice is strict-only until it is split or re-routed.
