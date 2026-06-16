TASK-BACKLOG-107-R1
- Source: `documentation/tasks/backlog_BACKLOG-107_script_output_pfade_haerten_und_root_nebenprodukte_reduzieren.md`
- Backlog Item: `BACKLOG-107`
- Feature: Second apply slice for remaining frontend debug export runtime-log alignment
- Generated At: 2026-06-16

## Generated Tasks

### TASK-BACKLOG-107-R1.2 Move the Electron frontend debug export from `debug_logs/` into the same intentional dev-runtime log path
- Ziel:
  - Align the remaining Electron-side frontend debug export path with the already accepted `documentation/logs/dev-runtime/` runtime-log destination so one leftover direct `debug_logs/` writer does not keep drifting away from the new shared target family.
- Scope:
  - Touch only the concrete Electron frontend debug export path and the minimal bounded validation note needed to prove the path is now aligned.
  - Do not widen into historical audit packages, broad registry rewrites, startup telemetry, root artifact deletion, or any additional launcher-family cleanup.
- Files:
  - `main.electron.cjs`
  - `documentation/test-runs/BACKLOG-107_execution_validation.md`
- Steps:
  1. Change the dev-mode target path in `debug:write-frontend-log` so frontend debug exports use `documentation/logs/dev-runtime/` instead of `debug_logs/`.
  2. Keep the production-mode `%APPDATA%` path behavior unchanged.
  3. Refresh the bounded validation note so it records this second apply slice accurately.
- Acceptance Criteria:
  - The Electron `debug:write-frontend-log` handler no longer writes dev-mode frontend exports into `debug_logs/`.
  - Dev-mode frontend debug exports use `documentation/logs/dev-runtime/`.
  - Production-mode frontend debug export behavior remains unchanged.
  - No unrelated startup telemetry, backend launcher, or historical documentation cleanup is mixed into this slice.
- Tests:
  - `node --check main.electron.cjs`
  - `rg -n "debug:write-frontend-log|debug_logs|documentation/logs/dev-runtime|frontend_log_" main.electron.cjs documentation/test-runs/BACKLOG-107_execution_validation.md -S`
  - `python documentation/codex/skills/janus-health-check/scripts/health_snapshot.py --repo C:\KI\Janus-Projekt --mode MONTHLY`
- Model: 5.4
- Reason:
  - This is the smallest remaining code-level `BACKLOG-107` path-alignment seam visible from the bounded inspection: one Electron handler plus one current validation artifact, with no need to reopen the broader first slice or historical closeout files.

HANDOFF_SCOPE:
- Backlog Item: BACKLOG-107
- Entry Point: PRE_IMPLEMENTATION_VERIFICATION
- Required Artifact: documentation/tasks/backlog_BACKLOG-107_second_apply_slice_frontend_debug_export_alignment.md
- Required Next Skill: janus-preimplementation-check
- Evidence Paths:
  - documentation/tasks/backlog_BACKLOG-107_first_apply_slice_final_audit.md
  - documentation/tasks/BACKLOG-107_R1_1_AUDIT_PACKAGE.md
  - main.electron.cjs
  - documentation/test-runs/BACKLOG-107_execution_validation.md
- Dropped Context:
  - broader launcher families not yet normalized
  - historical registry or backlog wording that still documents earlier states
  - startup telemetry path changes
