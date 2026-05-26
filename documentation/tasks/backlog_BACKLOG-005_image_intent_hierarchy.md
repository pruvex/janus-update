# BACKLOG TASK – BACKLOG-005 – Bild-Intent hat Vorrang vor Filesystem-Intent bei gemischten Keywords

## 1. Ziel
Filesystem-Intent hat Vorrang vor Bild-Intent bei gemischten Keywords, sodass Filesystem-Tools aufgerufen werden statt system.generate_image.

## 2. Impact-Analyse
- **Basiert auf:** documentation/backlog/BACKLOG.md#BACKLOG-005
- **Beeinflusst:** backend/services/orchestrator/intent_engine.py, backend/services/skill_selector.py
- **Risiko-Einschätzung:** MEDIUM (Intent-Hierarchie-Änderung, betrifft Intent-Engine und Skill-Selector)

## 3. Scope
### IN SCOPE
- Intent-Hierarchie zwischen Filesystem-Intent und Bild-Intent anpassen
- Skill-Selector so ändern, dass Filesystem-Intent Vorrang vor Bild-Intent hat
- Logging für Intent-Hierarchie-Entscheidung hinzufügen
- Unit-Tests für Intent-Hierarchie erstellen

### OUT OF SCOPE
- Änderung an anderen Intent-Typen (Calendar, Shopping, etc.)
- UI-Änderungen
- Änderung an Tool-Ausführung

## 4. Umsetzungsschritte
1. Intent-Engine analysieren: Wie wird Bild-Intent erkannt und wie wird die Intent-Hierarchie bestimmt?
2. Skill-Selector analysieren: Wie wird entschieden, welcher Intent Vorrang hat?
3. Intent-Hierarchie-Logik implementieren: Filesystem-Intent hat Vorrang vor Bild-Intent bei gemischten Keywords
4. Logging für Intent-Hierarchie-Entscheidung hinzufügen
5. Unit-Tests für Intent-Hierarchie erstellen
6. Tests ausführen und grün machen

## 5. Acceptance Criteria
- [ ] Filesystem-Intent hat Vorrang vor Bild-Intent bei gemischten Keywords
- [ ] "Bilder" im Kontext von Dateisystem-Operationen wird nicht als Bild-Intent interpretiert
- [ ] Filesystem-Tools werden aufgerufen bei eindeutigem Filesystem-Kontext
- [ ] Logging zeigt Intent-Hierarchie-Entscheidung

## 6. Tests / Validierung
- Unit-Test: Prompt mit "Bilder" im Filesystem-Kontext wird als Filesystem-Intent erkannt
- Unit-Test: Prompt mit reinem Bild-Kontext wird weiterhin als Bild-Intent erkannt
- Unit-Test: Intent-Hierarchie-Logging korrekt

## 7. Model
- **Assigned Model:** SWE 1.6
- **Reason:** Backlog-Handoff für atomaren klaren Fix mit MEDIUM-Risiko

---

## POST-IMPLEMENTATION AUDIT TRAIL

### Implementation Scope
- **Implemented tasks:** TASK-005
- **Feature status:** DONE
- **Final audit status:** PASS

### Files Changed
- **backend/services/orchestrator/intent_engine.py:** Filesystem-Intent in precedence-Tuple vor Bild-Intent gesetzt
- **backend/services/skill_selector.py:** Filesystem-Intent override Logik implementiert (is_filesystem && is_image → is_image = False)
- **backend/data/capability_registry.json:** Filesystem-Tools zur Capability-Registry hinzugefügt
- **backend/services/filesystem_manager.py:** move_files Ausgabe detaillierter (verschobene Dateien aufgelistet), find_files Parameter recursive hinzugefügt
- **backend/skills/filesystem/find_files.json:** Beschreibung erweitert (move_files nach find_files aufrufen)
- **backend/skills/filesystem/move_files.json:** Beschreibung erweitert (Dateinamen aus find_files extrahieren)
- **backend/tests/unit/test_skill_selector_filesystem_calendar.py:** Unit-Tests für Filesystem-vs-Bild-Intent-Hierarchie
- **backend/tests/integration/test_intent_resolver_filesystem.py:** Integration-Tests für Intent-Resolver
- **documentation/backlog/BACKLOG.md:** BACKLOG-007 Performance-Optimierung erstellt

### What Was Done
Filesystem-Intent hat jetzt Vorrang vor Bild-Intent bei gemischten Keywords. "Bilder" im Kontext von Dateisystem-Operationen wird korrekt als Filesystem-Intent erkannt, nicht als Bild-Intent. Skill-Descriptions für find_files und move_files wurden verbessert, um Tool-Call-Effizienz zu erhöhen.

### Validation Evidence
- **Unit/Integration Tests:** python -m pytest backend/tests/integration/test_intent_resolver_filesystem.py backend/tests/unit/test_skill_selector_filesystem_calendar.py -q — PASS (24 passed in 0.77s)
- **Manual Janus Gemini:** PASS — Prompt "hi, erstell auf dem desktop einen ordener 'Bilder' und verschiebe alles jpg und png dateien vom desktop in diesen ordner" erfolgreich
- **Manual Janus GPT:** PASS — Gleicher Prompt erfolgreich
- **Skill 6:** not needed

### Final Audit Fixes
- None

### Version Bump
- **Old version:** 0.4.17-beta.12
- **New version:** 0.4.17-beta.13
- **Files changed:** package.json, package-lock.json, backend/version.py

### Remaining Risks
- Performance-Unterschiede zwischen Gemini und GPT bei Filesystem-Tasks bleiben (separat als BACKLOG-007 dokumentiert)

---

## DEBUGGING LOG

- Keine Probleme.
