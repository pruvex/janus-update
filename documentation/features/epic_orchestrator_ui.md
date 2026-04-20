# Epic: Diamond Task Orchestrator UI (Optimiert V1.1)

**Status:** Phase 4 (Optimierter Designplan) | **Reviewer:** Opus (A3-Review integriert)

## 1. Kern-Architektur & Sicherheit
- **Technologie-Stack:** Python 3.11+, Streamlit, `filelock` (für Concurrency-Schutz), `shutil` (für Backups).
- **Ablage-Pfad:** `tools/orchestrator_ui/` (Strikte Trennung vom Janus-Backend).
- **Abhängigkeiten:** Eigene `tools/orchestrator_ui/requirements.txt`.
- **Datenquelle (MVP):** Primär `01_CENTRAL_TASK_REGISTRY.md`, sekundär `documentation/features/epic_xyz.md`. (daily_plan.md ist Future Scope).

## 2. Sicherheits-Vorgaben (Phase 3 Review Auflagen)
- **Robustes Parsing:** Kein blindes `re.sub`. Nutze **kontextgebundenes Regex** mit Zeilen-Matching, das den Task-Namen (`task_xyz.md`) als Anker nutzt, um False Positives zu vermeiden.
- **Race-Condition-Schutz:** Jede schreibende Operation auf Markdown-Dateien MUSS über einen `FileLock` (`filepath + ".lock"`) abgesichert werden.
- **Backup-Routine:** Vor jedem Schreibzugriff MUSS eine Kopie der Zieldatei (`.bak`) erstellt werden.

## 3. Datenfluss & Logik
1. **Registry Parser:** Liest Epics, Status und `NÄCHSTER BLOCKER` aus der Registry.
2. **Epic Parser:** Liest die Checklisten aus den Feature-Dateien.
3. **Task Parser:** Extrahiert Prompts und Modell-Vorgaben aus den spezifischen `task_xyz.md`.
4. **Completion Logic:** Der "Approve"-Button im UI löst das Python-Skript aus, das Backup -> Lock -> Write (Checkbox-Update & Registry-Update) durchführt.

## 4. Master-Task-Liste (Aktualisiert)
- [x] 1. `task_orchestrator_01_schema_and_parser.md` (Pydantic Modelle & Kontext-Regex Parser)
- [x] 2. `task_orchestrator_02_streamlit_ui_layout.md` (Tabelle, Modell-Warnhinweise, Layout)
- [x] 3. `task_orchestrator_03_clipboard_and_action_logic.md` (Clipboard-Handover & Prompt-Extraktion)
- [x] 4. `task_orchestrator_04_completion_writer_with_backup.md` (Write-Logik mit FileLock und Backup-Routine)
- [x] 5. `task_orchestrator_05_e2e_test_workflow.md` (Vollständiger Testdurchlauf inkl. UI-Validierung)
