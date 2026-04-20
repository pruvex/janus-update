# Task: Orchestrator UI - E2E Test Workflow (V1.0)

## 1. Klassifizierung & Ressourcen
- **Kategorie:** E2E (Manueller Test) | **Modell:** Claude 4.6 Sonnet
- **Ort:** Cursor / Windsurf

## 2. Zielsetzung
Vollständiger Testdurchlauf des Diamond Task Orchestrator Dashboards. Validierung aller Funktionen (Anzeige, Clipboard, Mark Done) im echten Browser-Kontext.

## 3. Akzeptanz-Kriterien
- [ ] Dashboard startet fehlerfrei via `START_DASHBOARD.bat`.
- [ ] Alle Epics und Tasks werden korrekt angezeigt.
- [ ] Copy-Button kopiert den Task-Inhalt in die Zwischenablage.
- [ ] Mark-Done Button schließt genau einen Task ab (kein Cascade).
- [ ] Registry und Epic-Datei werden danach korrekt aktualisiert.
- [ ] Refresh-Button lädt die neuen Daten ohne Fehler.

## 4. Audit-Trail
| Datum | Status | Änderung |
| :--- | :--- | :--- |
| 2026-03-29 | Created | Task-Datei angelegt. Bereit für E2E-Test nach Dashboard-Validierung. |
