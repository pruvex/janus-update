BACKLOG-105
- Backlog Item: `BACKLOG-105`
- Source: `documentation/backlog/BACKLOG.md`
- Generated At: 2026-06-06

## Task

### BACKLOG-105 Root-Logs aus dem Repo-Root in festen Laufzeitpfad verlagern
- Ziel:
  - Verlagere die Erzeugung wiederkehrender Start-, Debug- und Laufzeit-Logs aus dem Repo-Root in einen klar definierten Zielpfad, damit der Arbeitsbereich sauberer bleibt und der Healthcheck diese Root-Artefakte nicht weiter als Hygiene-Fund meldet.
- Scope:
  - Touch only the local start, debug, or helper scripts and related documentation/config that currently write recurring logs into the repository root.
  - Do not perform a broad repository cleanup, delete unrelated historical artifacts, or change product architecture.
- Files:
  - `scripts/`
  - `documentation/`
  - other directly involved local start/debug script files only if they currently write logs into the repo root
- Steps:
  1. Identify the local scripts or launch paths that currently emit recurring root-level log files such as Vite, backend start, verify, hotfix, or live logs.
  2. Define one consistent target path for these logs and update the relevant scripts to write there instead of into the repository root.
  3. Add or adjust minimal documentation or ignore handling only where needed so the new log path is intentional and understandable.
  4. Verify that the affected scripts no longer default to creating those recurring logs directly in the root.
- Acceptance Criteria:
  - Relevante Start-, Debug- und Laufzeitskripte schreiben ihre wiederkehrenden Logs nicht mehr in den Repo-Root.
  - Es gibt einen klaren und konsistenten Zielpfad fuer diese Logs.
  - Die betroffenen lokalen Script-Pfade sind so angepasst, dass der Root durch diese Logfamilie nicht weiter standardmaessig belastet wird.
- Tests:
  - `rg --files -g "*log*" .`
  - targeted script/config inspection for affected log-output paths
- Model: 5.4
- Reason:
  - Small bounded repo-hygiene fix with local script scope, low risk, and clear acceptance criteria from the monthly healthcheck.
