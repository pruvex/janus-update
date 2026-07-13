TASK-M6C.3
- Source Spec: `documentation/SPEC/M6C3_provider_branch_reachability_inventory.md`
- Backlog Item: `N/A`
- Feature: Epic 4 Provider Transport Refactor, Phase C Provider-Branch Reachability Inventory
- Generated At: 2026-07-13

## Generated Tasks

### TASK-M6C.3 Build the bounded provider-branch reachability inventory
- Ziel:
  - Produce one evidence-only inventory that classifies the selected Phase-C provider branches without altering runtime code.
- Scope:
  - Record static callers, branch contracts, and a retained/candidate/needs-runtime-evidence classification for the branches selected by the approved C3 Spec.
  - Treat direct callers as retention evidence.
  - Treat no static caller as `NEEDS_RUNTIME_EVIDENCE`, never as permission to delete.
  - Keep all provider, streaming, normalization, fallback, internal-generation, transport, tool, persistence, UI, and release behavior unchanged.
- Files:
  - `documentation/tasks/TASK-M6C.3_provider_branch_inventory_result.md` (new)
  - `documentation/tasks/TASK-M6C.3_provider_branch_inventory.md`
  - `documentation/ai/CURRENT_STATE.md`
  - `documentation/codex/SKILL_USAGE_LOG.md`
- Steps:
  1. Run deterministic repository scans for the three C3 candidate symbols named by the decision summary.
  2. Record direct callers, provider contract, and conservative classification in the new result artifact.
  3. Validate that the scoped diff changes no product source and record the follow-up boundary for any candidate.
- Acceptance Criteria:
  - Each selected branch has static caller evidence or an explicit no-static-caller result.
  - Directly called branches are classified retained.
  - A no-static-caller branch is classified needs runtime evidence and no deletion is proposed.
  - The task contains no product code or runtime behavior change.
  - The evidence requires no network access or provider credentials.
- Tests:
  - Deterministic `rg` symbol scans recorded in the inventory result.
  - Scoped diff check confirms documentation-only changes.
- Model: 5.6 Terra
- Reason:
  - The user chose the approved evidence-first C3 path, so no code-removal task may be emitted before reachability is recorded.

## Deferred Phase-C Work

- Any code deletion requires a separate decision-locked task, precheck, and validation.
