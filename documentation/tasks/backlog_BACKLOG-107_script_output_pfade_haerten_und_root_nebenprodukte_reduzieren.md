BACKLOG-107
- Backlog Item: `BACKLOG-107`
- Source: `documentation/backlog/BACKLOG.md`
- Generated At: 2026-06-06

## Task

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
- Tests:
  - `python documentation/codex/skills/janus-health-check/scripts/health_snapshot.py --repo C:\KI\Janus-Projekt --mode MONTHLY`
  - `python C:\Users\pruve\.codex\skills\janus-backlog-handoff\scripts\validate_backlog.py C:\KI\Janus-Projekt\documentation\backlog\BACKLOG.md`
  - targeted `rg` inspection for affected output-path references
- Model: 5.4
- Reason:
  - Bounded repo-hygiene and local-tooling hardening pass with clear evidence, medium but controlled scope, and no open product or architecture decision.
