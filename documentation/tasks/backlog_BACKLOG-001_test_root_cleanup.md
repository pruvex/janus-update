# BACKLOG TASK – BACKLOG-001 – Test-Dateien in Root-Verzeichnis aufräumen

## 1. Ziel
Verschiebe alle Test-Dateien aus dem Projekt-Root in die entsprechenden Test-Verzeichnisse (tests/ oder test/).

## 2. Impact-Analyse
- **Basiert auf:** documentation/backlog/BACKLOG.md#BACKLOG-001
- **Beeinflusst:** Projekt-Root (test_cluster_4.py, test_geometrie_check.py, test_logging_fix.py, test_openai_tools.py, test_face.jpg, test_personalities.json), tests/ oder test/ Verzeichnisse
- **Risiko-Einschätzung:** LOW

## 3. Scope
### IN SCOPE
- Verschieben von test_cluster_4.py nach tests/ oder test/
- Verschieben von test_geometrie_check.py nach tests/ oder test/
- Verschieben von test_logging_fix.py nach tests/ oder test/
- Verschieben von test_openai_tools.py nach tests/ oder test/
- Verschieben von test_face.jpg nach tests/ oder test/
- Verschieben von test_personalities.json nach tests/ oder test/
- Prüfung der Test-Abhängigkeiten vor dem Verschieben
- Validierung dass bestehende Tests nach dem Verschieben noch laufen

### OUT OF SCOPE
- Änderung an Test-Logik oder Test-Inhalten
- Umbenennung von Dateien
- Änderung an der Feature-Funktionalität

## 4. Umsetzungsschritte
1. Prüfen ob tests/ oder test/ Verzeichnis existiert und für diese Art von Tests geeignet ist
2. Für jede der 6 Dateien (test_cluster_4.py, test_geometrie_check.py, test_logging_fix.py, test_openai_tools.py, test_face.jpg, test_personalities.json):
   - Prüfen ob Import-Abhängigkeiten oder relative Pfade existieren
   - Datei in das passende Test-Verzeichnis verschieben
   - Wenn nötig, Import-Pfade in der Datei anpassen
3. Tests laufen lassen um sicherzustellen dass keine Abhängigkeiten gebrochen wurden
4. Bestätigen dass keine Feature-Verhaltensänderung eingetreten ist

## 5. Acceptance Criteria
- [ ] Alle 6 Dateien sind aus dem Projekt-Root entfernt
- [ ] Alle 6 Dateien sind in tests/ oder test/ organisiert
- [ ] Bestehende Tests bleiben grün (pytest oder entsprechender Test-Runner)
- [ ] Keine Feature-Verhaltensänderung

## 6. Tests / Validierung
- Manuelles Prüfen dass Dateien im Projekt-Root nicht mehr existieren
- Manuelles Prüfen dass Dateien im Ziel-Verzeichnis existieren
- Ausführen von pytest oder dem relevanten Test-Runner um sicherzustellen dass Tests noch laufen
- Schneller manueller Test der Janus-Hauptfunktion um sicherzustellen dass keine Funktionalität gebrochen wurde

## 7. Model
- **Assigned Model:** SWE 1.6
- **Reason:** Backlog-Handoff für atomaren klaren Fix mit LOW Risiko.
