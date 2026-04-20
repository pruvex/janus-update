# Task: Orchestrator UI - Completion Writer (V1.1)

## 1. Klassifizierung & Ressourcen
- **Kategorie:** C7 (Code-Gen) / B6 (Schema) | **Modell:** Claude 4.6 Sonnet
- **Ort:** Cursor / Windsurf

## 2. Zielsetzung (Gehärtet durch Opus-Review)
Implementierung der Schreib-Logik für den "✅ Mark Done"-Button. Dieser Button soll die Markdown-Dateien sicher (mit Backup und FileLock) aktualisieren.

## 3. Akzeptanz-Kriterien
- [x] Logik in `parser.py`: Funktion `approve_task(epic_name, task_filename)` implementiert.
- [x] **Backup-Schutz:** Erstellt `.bak` der Epic-Datei und Registry vor dem Schreiben.
- [x] **Concurrency-Schutz:** Nutze `filelock`, um Datei-Korruption zu verhindern.
- [x] **Markdown-Manipulation:** Setzt `[x]` beim richtigen Task (Regex-Anker) und aktualisiert den `NÄCHSTER BLOCKER` in der Registry.
- [x] **UI-Integration:** Der Klick auf den Button in `app.py` ruft die neue Logik auf.

## 4. Audit-Trail
| Datum | Status | Änderung |
| :--- | :--- | :--- |
| 2026-03-29 | Planned | Task physisch erstellt. Bereit für Implementierung. |
| 2026-03-29 | ✅ Implementiert | approve_task() mit Backup, FileLock, Registry-Update. Location-Badge + Mark-Done Button aktiv. Wartet auf UI-VALIDIERT. |
