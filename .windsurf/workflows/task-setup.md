---
description: Create a new Diamond-OS task file with the mandatory 7-section template
---

## Steps

1. Read `documentation/tasks/` directory and find the highest existing task number.

2. Ask the user for:
   - **Kurzbeschreibung** (slug for filename, e.g. `memory_cache_fix`)
   - **Ziel** (one-sentence goal)
   - **Betroffene Dateien** (list of files, or "TBD")

3. Create file `documentation/tasks/task_<NEXT_NUMBER>_<slug>.md` with this exact template:

```markdown
# Task <NEXT_NUMBER>: <Ziel>

## 1. Ziel & Kontext
<Ziel from user input>

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** [welche bestehenden Systeme/Tasks]
- **Beeinflusst:** [welche anderen Systeme könnten betroffen sein]
- **Risiko-Einschätzung:** [LOW / MEDIUM / HIGH]

## 3. Betroffene Dateien
<file list from user input, or TBD>

## 4. Umsetzungsschritte (Diamond-Flow)
- [ ] **Phase 1 (Pre-Check):** `/pre-check` ausführen.
- [ ] **Phase 2 (Implementierung):** [Haupt-Implementierungsschritte hier eintragen]
- [ ] **Phase 3 (Testing):** [Spezifische Testbefehle hier eintragen]
- [ ] **Phase 4 (Post-Check):** `/post-impl` ausführen.
- [ ] **Phase 5 (Audit - Optional):** `/opus-audit` bei Bedarf ausführen.

## 5. Test-Vorgaben
- [ ] Regression: `python -m pytest backend/tests -q` 
- [ ] Targeted: <specific test command>

## 6. Ergebnis & Audit-Trail
_Wird automatisch durch /post-impl ausgefüllt._

## 7. Debugging-Log
_Wird bei Bedarf ausgefüllt._
```

4. Confirm creation with: `Task-Datei erstellt: documentation/tasks/task_<NR>_<slug>.md`
