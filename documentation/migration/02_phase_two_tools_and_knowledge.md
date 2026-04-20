# Phase 2 Protokoll: Werkzeuge & Wissen (Janus 2.0)

## Meta
- **Status:** Abgeschlossen ✅
- **Datum:** 28.03.2026
- **Zugehörige Roadmap-Tasks:** 2.1, 2.2

---

## Task 2.1: System-Prompt Upgrade (Der Kernel)
- **Ergebnis:** Kernel **V1.8** (AUTOMATED CONTROL) finalisiert — eine Quelle, keine doppelten Prompt-Blöcke im File.
- **Kern-Logik:** Session-Start (Inventory + Kontingent), 70/30-Pacing, Cursor-Prompt-Engine (@-Refs), Schema-Guard wie Rule 03, Bootstrap `auto_fill_task.js`, Ausnahme 5-Minuten-Regel, `diamond_check.sh` wo vorgesehen.
- **Speicherort (Single Source of Truth):** `documentation/Ai_Studio_Systemprompt.txt`
- **Hinweis:** Es gibt **kein** separates `00_master_prompt.md`; bei Bedarf nur Verweis-Datei anlegen, die auf die `.txt` zeigt (optional).

## Task 2.2: Project Inventory Board
- **Ergebnis:** Kanban-Board als Steuerungseinheit angelegt.
- **Speicherort (Kanban / Diamond-Workflow):** `documentation/04_PROJECT_INVENTORY_AND_STATUS.md`.
- **Nicht verwechseln mit:** `documentation/TECH_PROJECT_INVENTORY.md` — **technische** Projekt-Inventur (Domains/Dateien), anderer Zweck.
- **Initialer Scope:** PDF-Features, Bilder-Bugfix, Chat-UI u. a. im Backlog/Planned erfasst.

## Dokumentation der Werkbank-Installation
Folgende physische Infrastruktur wurde in Phase 2 erfolgreich in das Projekt Janus integriert:

### 1. Cursor-Polizei (.cursor/rules/)
- `01_task_protection.mdc`: Erzwingt Task-Dateien vor Code-Änderung (inkl. 5-Min-Ausnahme).
- `02_learning_loop.mdc`: Automatisiert die Pflege der Lessons Learned.
- `03_schema_lock.mdc`: Schützt die Integrität von Pydantic-Schemas und Modellen.
- `04_completion_gate.mdc`: Definiert harte Kriterien für den Task-Abschluss.

### 2. Automatisierungs-Skripte (scripts/)
- `auto_fill_task.js`: Erzeugt Task-Dateien aus dem Diamond-Template.
- `diamond_check.sh`: Integritäts-Checker für den Workflow.

### 3. Das kollektive Gedächtnis (docs/)
- `lessons_learned.md`: Initialisiert mit dem ersten Stub zur System-Initialisierung.
