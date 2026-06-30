TASK-SPEC27
- Source Spec: documentation/SPEC/27_aider_openrouter_worker_poc_fuer_codex_delegation.md
- Backlog Item: N/A
- Feature: Aider/OpenRouter Worker POC fuer Codex-Delegation
- Generated At: 2026-06-30

## Generated Tasks

### TASK-SPEC27.1 Execute one bounded manual Aider/OpenRouter POC on a harmless docs-only target
- Ziel: Einen einzigen manuellen Aider/OpenRouter-POC-Lauf fuer Janus durchfuehren, der nur eine harmlose Doku-Zielflaeche bearbeitet und danach mit Diff, Report und Check-Ausgabe bewertbar ist.
- Scope: Lokale Vorbereitung und Ausfuehrung eines bounded Worker-POC ohne allgemeinen `janus-worker`-Wrapper, ohne Produktlogik, ohne Git-Aktionen und ohne Ausweitung auf weitere Aufgaben oder Tooling-Schichten.
- Files:
  - development/openrouter-skill-tests/janus-worker-aider-poc/
  - documentation/test-runs/
  - documentation/ai/CURRENT_STATE.md
- Steps:
  - Eine kleine lokale POC-Arbeitsflaeche fuer den manuellen Aider-Lauf anlegen, die den Prompt oder Task-Input, den erlaubten Dateibereich und die Bewertungsregeln fuer genau einen docs-only Lauf festhaelt.
  - Einen harmlosen Doku-Zielbereich bestimmen, der absichtlich keine Janus-Produktlogik, keine Release- oder Governance-Dateien und keine breiten Repo-Aenderungen beruehrt.
  - Aider lokal gegen diesen eng gebundenen Scope ausfuehren oder den Lauf sauber als blockiert dokumentieren, falls `aider` oder OpenRouter-Zugang fehlen.
  - Den Lauf mit nachvollziehbarem Diff, kurzem Worker-Report und Test- oder Check-Ausgabe dokumentieren und anschliessend als praktischen Go/No-Go-POC bewerten.
- Acceptance Criteria:
  - Es existiert genau ein manueller bounded Aider/OpenRouter-POC-Lauf fuer eine harmlose docs-only Aufgabe.
  - Der erlaubte Dateibereich ist vor dem Lauf explizit und klein festgelegt.
  - Der Lauf endet ohne Commit, Push oder sonstige Git-Governance-Aktion.
  - Es liegen ein verwertbarer Diff, ein kurzer Report und eine Check-Ausgabe oder ein klar dokumentierter Blocker vor.
  - Das Ergebnis ist als praktischer Go/No-Go fuer kleine kuenftige Janus-Worker-Aufgaben bewertbar.
- Tests:
  - Verfuegbarkeitscheck fuer `aider`
  - Verfuegbarkeitscheck fuer benoetigte OpenRouter-Umgebungsvariablen oder gleichwertige lokale Konfiguration
  - Ein kleiner lokaler Check, dass nur der erlaubte docs-only Bereich geaendert wurde
  - `git diff --check` auf den durch den POC beruehrten Dateien
- Model: 5.4
- Reason: Der POC soll zuerst den Worker-Mechanismus selbst bewerten und nicht sofort Produktcode oder einen allgemeinen Runner einführen.

@janus-task-breakdown
Spec: documentation/SPEC/27_aider_openrouter_worker_poc_fuer_codex_delegation.md
Task: documentation/tasks/TASK-SPEC27_aider_openrouter_worker_poc_fuer_codex_delegation.md
Backlog Item: N/A
Target Task: TASK-SPEC27.1
Mode: TASK_REFINEMENT
Execution Model: 5.4
Rules: USE_SPEC_AND_TASK_AS_SOURCE_OF_TRUTH_NO_IMPLEMENTATION_RELEASE_ONE_TARGET_TASK
Expected Output: TASK_REFINED_PLUS_PRECHECK_HANDOFF
