Produce one bounded proposal-only unified diff patch for janus-executioner.
This is read-only proposal work.
Work in one pass.
Do not claim completion.
Do not output analysis, bullets, or commentary.
Do not describe git commands.
If you cannot produce a safe bounded patch, output exactly: BLOCKED: <reason>

Target Task: BACKLOG-107
Precheck Status: PRE-CHECK PASSED
Delegation Question: Produce one bounded patch candidate that reroutes recurring script-generated root artifacts into intentional target paths without broad repository cleanup or architecture drift.
Max touched files: 9
You may inspect only these files if needed, then immediately output the patch:
- scripts/dev-log-utils.cjs
- scripts/run-backend-dev.cjs
- scripts/run-vite-dev.cjs
- scripts/write-startup-marker.cjs
- package.json
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
- rg -n "backend_hotfix|backend_live|backend_persist|backend_restart|backend_start_manual|backend_verify|tmp_uv8011|startdev\\.log|\\.codex-vite" scripts package.json main.electron.cjs documentation -S
- manual diff review for output-path hardening only

Manual validation ownership stays with Codex:
Codex must still verify that the patch only hardens recurring script output paths, does not widen into repo cleanup, and keeps final validation ownership local.

Compact task brief:
### BACKLOG-107 Script-Output-Pfade haerten, damit Dirty-Tree und Root-Suspicious nicht dauernd nachwachsen
- Ziel:
  - Haerte die relevanten lokalen Start-, Test-, Debug- und Hilfsskript-Pfade so, dass wiederkehrende Nebenprodukte in klar definierte Zielpfade laufen und nicht weiter standardmaessig im Repo-Root oder in anderen unsauberen Streupfaden nachwachsen.
- Scope:
  - Touch only the directly involved local dev, debug, verification, or helper scripts, their minimal supporting utilities/config, and the narrow documentation or ignore rules needed to define intentional output locations.
  - Do not perform a broad repository cleanup, redesign the Janus architecture, or migrate unrelated historical artifacts that are outside the active recurring script-output paths.
- Files:
  - `scripts/`
  - `documentation/codex/`
  - `documentation/backlog/`
  - other directly involved local dev/helper script files only if they currently create recurring root or otherwise suspicious output artifacts
- Steps:
  1. Identify the recurring root or suspicious side-effect artifacts that are still being created by versioned local scripts or helper flows.
  2. Trace those artifacts back to the concrete script output paths and group them by shared target family where a consistent destination can be defined.
  3. Update the affected script paths or supporting utilities so their default outputs land in intentional, stable locations instead of scattered root-level paths.
  4. Add only the minimal documentation or ignore/path-handling updates needed so the new output locations are explicit and maintainable.
  5. Re-run the targeted hygiene evidence and confirm the repeated script-generated root findings are reduced or intentionally reclassified.
- Acceptance Criteria:
  - Wiederkehrende Script-Nebenprodukte haben definierte und konsistente Zielpfade.
  - Die wichtigsten lokalen Dev-Skripte erzeugen keine neuen Root-Artefakte mehr als Standardverhalten.
  - Ein erneuter Healthcheck zeigt weniger wiederkehrende scriptbedingte `root_suspicious`-Funde oder eine gezielte, nachvollziehbare Neueinordnung.
