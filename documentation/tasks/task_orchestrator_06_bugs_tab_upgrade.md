# Task: Orchestrator UI - Bugs & Audits Tab Upgrade (V1.0)

## 1. Klassifizierung & Ressourcen
- **Kategorie:** C8 (Refactoring) | **Ort:** Cursor / Windsurf
- **Modell:** Claude 4.6 Sonnet

## 2. Zielsetzung
Transformation des Tabs "Bugs & Audits" von einer statischen Liste in eine interaktive Steuerzentrale, identisch zum Epic-Task-System.

## 3. Akzeptanz-Kriterien
- [ ] Parser (`parser.py`) extrahiert Metadaten (Modell, Ort) für isolierte Bugs.
- [ ] UI (`app.py`) zeigt für jeden offenen Bug die Action-Row (Copy, Mark Done, Badges).
- [ ] Schreib-Logik: "Mark Done" setzt den Status in der Registry auf "✅ Erledigt".
- [ ] Konsistenz: Der "NÄCHSTER BLOCKER" Mechanismus funktioniert auch für Prio-Bugs.

## 4. Audit-Trail
| Datum | Status | Änderung |
| :--- | :--- | :--- |
| 2026-03-29 | Planned | Task für UI-Upgrade des Bug-Tabs erstellt. |
