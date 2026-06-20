Produce one bounded proposal-only unified diff patch for janus-executioner.
This is read-only proposal work.
Work in one pass.
Do not claim completion.
Do not output analysis, bullets, or commentary.
Do not describe git commands.
If you cannot produce a safe bounded patch, output exactly: BLOCKED: <reason>

Target Task: TASK-BACKLOG-107-R1.1
Precheck Status: PRE-CHECK PASSED
Delegation Question: Produce one bounded patch candidate that moves the shared versioned backend and Vite runtime-log family from debug_logs into documentation/logs/dev-runtime and aligns the coupled hygiene references only.
Max touched files: 5
You may inspect only these files if needed, then immediately output the patch:
- scripts/dev-log-utils.cjs
- documentation/codex/skills/janus-health-check/scripts/health_snapshot.py
- documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md
- .gitignore
- documentation/test-runs/BACKLOG-107_execution_validation.md

Patch rules:
- Return exactly one unified diff patch only.
- Start with --- a/<path> and +++ b/<path>.
- Touch only allowed files.
- Keep the patch as small as possible.
- Prefer the smallest backend-first fix.
- Do not widen scope to schema redesign or unrelated memory behavior.

Codex validation after review:
- python documentation/codex/skills/janus-health-check/scripts/health_snapshot.py --repo C:\KI\Janus-Projekt --mode MONTHLY
- rg -n "debug_logs|documentation/logs/dev-runtime|\\.codex-vite|backend_hotfix|backend_live|backend_persist|backend_restart|backend_start_manual|backend_verify|tmp_uv8011" scripts package.json main.electron.cjs documentation -S
- node -e "const { runWithLogs } = require('./scripts/dev-log-utils.cjs'); console.log(typeof runWithLogs === 'function' ? 'PASS' : 'FAIL')"
- manual diff review for runtime-log target alignment only

Manual validation ownership stays with Codex:
Codex must still verify that the patch stays inside the first runtime-log alignment slice, preserves local validation ownership, and does not widen into startup telemetry or unrelated launcher cleanup.

Compact task brief:
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
