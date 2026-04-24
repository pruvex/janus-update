# Task 053: Schema-Upgrade für move_files (file_names statt pattern) + Limits

## 1. Ziel & Kontext
Schema-Upgrade für `move_files` Skill: Ersetze den Parameter `pattern` durch `file_names: list[str]`, um exakte Dateinamen statt Glob-Patterns zu verwenden. Erhöhe gleichzeitig die `max_calls_per_turn` Limits für `create_directory` und `move_file` von 10 auf 20 (Defense in Depth).

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** Bestehendes Filesystem-Skill-System, `filesystem_manager.py`
- **Beeinflusst:** Alle Aufrufe von `move_files` müssen zukünftig mit `file_names` statt `pattern` arbeiten
- **Risiko-Einschätzung:** MEDIUM (API-Änderung, aber internes System)

## 3. Betroffene Dateien
- `backend/skills/filesystem/move_files.json`
- `backend/services/filesystem_manager.py` (Funktion `move_files`)
- `backend/skills/filesystem/create_directory.json`
- `backend/skills/filesystem/move_file.json`

## 4. Umsetzungsschritte (Diamond-Flow)
- [x] **Phase 1 (Pre-Check):** N/A – direkte Schema-Änderung
- [x] **Phase 2 (Implementierung):**
  - [x] `move_files.json`: Parameter-Schema mit `file_names: list[str]` hinzufügen
  - [x] `filesystem_manager.py`: `move_files()` auf `file_names`-Liste umstellen
  - [x] `create_directory.json`: `max_calls_per_turn` 10 → 20
  - [x] `move_file.json`: `max_calls_per_turn` 10 → 20
- [ ] **Phase 3 (Testing):** Filesystem-Tests laufen lassen
- [ ] **Phase 4 (Post-Check):** `/post-impl` ausführen
- [ ] **Phase 5 (Audit - Optional):** N/A

## 5. Test-Vorgaben
- [ ] Regression: `python -m pytest backend/tests -q`
- [ ] Targeted: Manuelle Verifikation der `move_files` Funktion

## 6. Ergebnis & Audit-Trail
_Wird automatisch durch /post-impl ausgefüllt._

## 7. Debugging-Log
_Wird bei Bedarf ausgefüllt._
