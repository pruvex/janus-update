# Task: Orchestrator UI - Schema & Kontext-Parser (V1.1)

## 1. Klassifizierung & Ressourcen
- **Kategorie:** B6 (Schema-Design) | **Modell:** Claude 4.6 Sonnet

## 2. Zielsetzung (Gehärtet durch A3-Review)
Implementierung der Parser-Logik unter `tools/orchestrator_ui/parser.py`.
**Strikte Auflage:** Nutze Anker-Regex (Task-Name), um nur die korrekten Checkboxen in den Epic-Dateien zu finden. Keine globalen Ersetzungen!

## 3. Akzeptanz-Kriterien
- [ ] Verzeichnis `tools/orchestrator_ui/` erstellt.
- [ ] Pydantic Modelle für `Registry`, `Epic` und `Task` implementiert.
- [ ] Parser liest `01_CENTRAL_TASK_REGISTRY.md` fehlerfrei.
- [ ] Parser erkennt den `NÄCHSTER BLOCKER` und verknüpft ihn mit der Epic-Checkliste.
- [ ] Unit-Test für Regex-Robustheit (Checkboxes in Code-Blöcken dürfen NICHT gematcht werden).

## 4. Audit-Trail
| Datum | Status | Änderung |
| :--- | :--- | :--- |
| 2026-03-29 | Updated | Opus-Review integriert (Pfad-Änderung & Regex-Anker). |
| 2026-03-29 | ✅ Implementiert | `tools/orchestrator_ui/parser.py` erstellt. 5/5 Unit-Tests grün. Registry + Bug korrekt geparst. Wartet auf UI-VALIDIERT. |
