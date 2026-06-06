BACKLOG-106
- Backlog Item: `BACKLOG-106`
- Source: `documentation/backlog/BACKLOG.md`
- Generated At: 2026-06-06

## Task

### BACKLOG-106 Lokale Datenbank-Artefakte aus dem Repo-Root herausziehen und sauber einordnen
- Ziel:
  - Ordne `janus.db`, `chat_history.db` und `costs.db` im Repo-Root sauber ein, definiere den intended Runtime-/Data-Pfad fuer aktive Janus-Datenbanken und reduziere den generischen Healthcheck-Laerm fuer genau diese drei Artefakte.
- Scope:
  - Touch only the targeted healthcheck/reporting path, minimal runtime-data documentation, and ignore handling needed to classify these three database artifacts.
  - Do not perform a broad root cleanup, delete historical local files, change unrelated script output paths, or redesign Janus persistence architecture.
- Files:
  - `documentation/codex/skills/janus-health-check/scripts/`
  - `documentation/codex/`
  - `.gitignore`
  - `documentation/backlog/`
- Steps:
  1. Verify the active Janus runtime database path from code and distinguish it from stray root-level DB files.
  2. Classify `janus.db`, `chat_history.db`, and `costs.db` by role so the healthcheck can report them intentionally instead of as generic suspicious root artifacts.
  3. Add minimal documentation and ignore rules that state the intended local runtime/data path for active DB state.
  4. Re-run the targeted healthcheck snapshot and confirm these DB names no longer appear under the generic `root_suspicious` bucket.
- Acceptance Criteria:
  - `janus.db`, `chat_history.db`, and `costs.db` have an explicit classification with an intended runtime/data-path explanation.
  - The active Janus runtime DB path is documented consistently with the implementation.
  - The targeted healthcheck no longer reports these three DB files as generic `root_suspicious` artifacts.
- Tests:
  - `python documentation/codex/skills/janus-health-check/scripts/health_snapshot.py --repo C:\KI\Janus-Projekt --mode MONTHLY`
  - `python C:\Users\pruve\.codex\skills\janus-backlog-handoff\scripts\validate_backlog.py C:\KI\Janus-Projekt\documentation\backlog\BACKLOG.md`
  - targeted `rg` inspection for runtime DB path references
- Model: 5.4
- Reason:
  - Small bounded repo-hygiene classification pass with low risk, explicit evidence, and no open product or architecture decision.
