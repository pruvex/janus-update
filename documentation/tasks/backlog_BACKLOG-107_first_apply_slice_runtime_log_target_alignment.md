TASK-BACKLOG-107-R1
- Source: `documentation/tasks/backlog_BACKLOG-107_script_output_pfade_haerten_und_root_nebenprodukte_reduzieren.md`
- Backlog Item: `BACKLOG-107`
- Feature: First apply slice for recurring dev-runtime log target alignment
- Generated At: 2026-06-16

## Generated Tasks

### TASK-BACKLOG-107-R1.1 Move the shared versioned dev-runtime log family from `debug_logs/` into one intentional repo path
- Ziel:
  - Route the first recurring shared dev-runtime log family used by the versioned backend and Vite launcher helpers into one explicit target path so the root-log hygiene work can start from a small applyable slice.
- Scope:
  - Touch only the shared local dev-runtime log helper and the minimal healthcheck, runbook, ignore, and validation artifacts needed to reflect the new path.
  - Do not widen into startup telemetry, unrelated root cleanup, legacy artifact migration, or launcher families that are not already covered by the shared helper.
- Files:
  - `scripts/dev-log-utils.cjs`
  - `documentation/codex/skills/janus-health-check/scripts/health_snapshot.py`
  - `documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md`
  - `.gitignore`
  - `documentation/test-runs/BACKLOG-107_execution_validation.md`
- Steps:
  1. Change the shared helper that writes versioned backend and Vite runtime logs so the default target path becomes `documentation/logs/dev-runtime/` instead of `debug_logs/`.
  2. Update the healthcheck legacy-log classification text only as needed so it points to the same new intentional path.
  3. Update the runbook and ignore rules so the new log destination is explicit and stable.
  4. Refresh the bounded validation note for this backlog item so it records the first apply slice accurately.
- Acceptance Criteria:
  - The shared helper no longer writes the versioned backend and Vite runtime log family into `debug_logs/`.
  - The intended target path for that family is documented consistently as `documentation/logs/dev-runtime/`.
  - Healthcheck classification text, runbook wording, and ignore rules agree on the same target path.
  - No startup telemetry path, product runtime behavior, or broader repo cleanup logic is changed in this first slice.
- Tests:
  - `python documentation/codex/skills/janus-health-check/scripts/health_snapshot.py --repo C:\KI\Janus-Projekt --mode MONTHLY`
  - `rg -n "debug_logs|documentation/logs/dev-runtime|\\.codex-vite|backend_hotfix|backend_live|backend_persist|backend_restart|backend_start_manual|backend_verify|tmp_uv8011" scripts package.json main.electron.cjs documentation -S`
  - `node -e "const { runWithLogs } = require('./scripts/dev-log-utils.cjs'); console.log(typeof runWithLogs === 'function' ? 'PASS' : 'FAIL')"`
- Model: 5.4
- Reason:
  - This is the smallest meaningful `BACKLOG-107` apply slice: one shared helper plus bounded hygiene artifacts, with clear acceptance and no product-surface risk.

HANDOFF_SCOPE:
- Backlog Item: BACKLOG-107
- Entry Point: PRE_IMPLEMENTATION_VERIFICATION
- Required Artifact: documentation/tasks/backlog_BACKLOG-107_first_apply_slice_runtime_log_target_alignment.md
- Required Next Skill: janus-preimplementation-check
- Evidence Paths:
  - documentation/tasks/backlog_BACKLOG-107_preimplementation_check.md
  - documentation/codex/model-routing/execution-review-runs/BOUNDED-EXECUTION-BACKLOG-107-001/
  - scripts/dev-log-utils.cjs
  - documentation/codex/skills/janus-health-check/scripts/health_snapshot.py
- Dropped Context:
  - broader launcher families not yet normalized
  - startup telemetry path changes
  - broad historical root artifact cleanup outside the shared helper path
