# AUDIT PACKAGE

## Scope

- Target Task: `TASK-SPEC24.1`
- Spec: `documentation/SPEC/24_lean_dev_governance_fuer_or_und_workhorse_arbeit.md`
- Task File: `documentation/tasks/TASK-SPEC24_lean_dev_governance_fuer_or_und_workhorse_arbeit.md`
- Precheck: `documentation/tasks/TASK-SPEC24.1_preimplementation_check.md`
- Execution Result: `documentation/tasks/TASK-SPEC24.1_execution_result.md`

## Goal

Codify the approved Lean-Dev governance rule in repo-owned governance artifacts so internal OR- and workhorse-infrastructure work can use a faster bounded mode while Janus product work remains fully strict.

## Changed Files

- `AGENTS.md`
- `documentation/codex/CODEX_WORKFLOW_PLAYBOOK.md`
- `development/README.md`
- `development/DEV_STATE.md`
- `documentation/tasks/TASK-SPEC24.1_AUDIT_PACKAGE.md`
- `documentation/tasks/TASK-SPEC24.1_execution_result.md`

## Validation

- `git diff --check -- AGENTS.md documentation/codex/CODEX_WORKFLOW_PLAYBOOK.md development/README.md development/DEV_STATE.md documentation/tasks/TASK-SPEC24.1_preimplementation_check.md documentation/tasks/TASK-SPEC24.1_AUDIT_PACKAGE.md documentation/tasks/TASK-SPEC24.1_execution_result.md`
- one targeted consistency check that Lean-vs-strict rules match across the four governance files
- one targeted negative check that Janus product work is still explicitly excluded from Lean mode

## Known Risks

- Lean Dev mode must remain strictly limited to internal Dev- and OR-infrastructure work.
- Future slices must not silently extend Lean mode into Janus product work, release work, or security/privacy-sensitive work.

## Audit Focus

- The Lean-vs-strict boundary is explicit and consistent.
- Validation, `CURRENT_STATE`, and sensible Git checkpoints remain mandatory in Lean mode.
- Escalation back to strict mode is explicit for product logic, security/privacy, release/Git, unclear scope, and new productive approvals.
