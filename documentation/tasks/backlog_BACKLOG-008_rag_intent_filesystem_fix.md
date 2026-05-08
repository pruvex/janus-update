# BACKLOG TASK – BACKLOG-008 – Filesystem-Intent blockiert RAG-Intent

## 1. Ziel
Filesystem-Intent soll RAG-Intent blockieren, um unnötige Logic-Tier-Upgrades bei reinen Dateisystem-Operationen zu verhindern.

## 2. Impact-Analyse
- **Basiert auf:** documentation/backlog/BACKLOG.md#BACKLOG-008
- **Beeinflusst:** Intent-Engine / RAG-Intent-Detection / Model-Selection
- **Risiko-Einschätzung:** MEDIUM (Intent-Priorisierung beeinflusst Kernverhalten)

## 3. Scope
### IN SCOPE
- Intent-Priorisierung anpassen: Filesystem-Intent blockiert RAG-Intent
- RAG-Intent-Detection präzisieren: nur bei Wissensabfragen (PDFs, Dokumente)
- Log-Output `[INTENT-OVERRIDE] RAG-Intent erkannt` wird nicht mehr bei Filesystem-Operationen getriggert

### OUT OF SCOPE
- Allgemeine RAG-System-Optimierung
- Pfad-Auflösungslogik (separates UX-Problem)
- Model-Selection für andere Intent-Typen

## 4. Umsetzungsschritte
1. Analyse der aktuellen Intent-Priorisierungslogik in der Intent-Engine (ähnlich wie BACKLOG-005 für Filesystem-vs-Bild) und Identifizierung der Stelle, an der RAG-Intent erkannt wird und Logic-Tier-Upgrades auslöst
2. Implementierung einer Filesystem-Intent-Blockade für RAG-Intent (Pattern wie BACKLOG-005: Filesystem-Override-Logik in der Intent-Engine)
3. Validierung durch Test dass RAG-Intent weiterhin bei echten Wissensabfragen getriggert wird

## 5. Acceptance Criteria
- [ ] Filesystem-Intent blockiert RAG-Intent (kein unnötiges Logic-Tier-Upgrade)
- [ ] Filesystem-Operationen werden mit gpt-5.4-nano ausgeführt
- [ ] RAG-Intent wird nur bei tatsächlichen Wissensabfragen getriggert (PDFs, Dokumente)
- [ ] Log zeigt `[INTENT-OVERRIDE] RAG-Intent erkannt` nicht mehr bei reinen Filesystem-Prompts

## 6. Tests / Validierung
- Test mit Filesystem-Prompt ohne RAG-Keywords: "erstell auf dem desktop einen ordner 'Bilder'" → prüfe dass kein Upgrade gpt-5.4-nano → gpt-5.4 erfolgt
- Log-Check auf Model-Selection bei Filesystem-Operationen
- Test mit explizitem Dokumenten-Request: "suche im PDF nach X" → prüfe dass RAG-Intent weiterhin getriggert wird
- Manuellem Test mit Desktop-Ordner-Operation zur Validierung der Pfad-Auflösung

## 7. Model
- **Assigned Model:** SWE 1.6
- **Reason:** Intent-Engine-Integration mit MEDIUM-Risiko, erfordert Verständnis der Intent-Priorisierungsarchitektur und mehrerer betroffener Module

---

## POST-IMPLEMENTATION AUDIT TRAIL

### Implementation Scope
- **Implemented tasks:** TASK-001
- **Feature status:** DONE
- **Final audit status:** PASS WITH FIXES (Skill 6 Debug durchgeführt)

### Files Changed
- **backend/services/orchestrator/execution_dispatcher.py:** Filesystem-Intent-Blockade für RAG-Intent implementiert (Zeilen 191-202)
- **documentation/Planned Features/backlog_BACKLOG-008_rag_intent_filesystem_fix.md:** Spec aktualisiert (Pfad-Auflösung aus Scope entfernt, Hinweis auf BACKLOG-009 hinzugefügt)
- **documentation/backlog/BACKLOG.md:** BACKLOG-008 Akzeptanzkriterien aktualisiert, BACKLOG-009 erstellt

### What Was Done
Filesystem-Intent blockiert jetzt RAG-Intent, um unnötige Logic-Tier-Upgrades bei reinen Dateisystem-Operationen zu verhindern. Die Implementierung folgt dem Pattern von BACKLOG-005 (Filesystem-Intent blockiert Bild-Intent). Skill 6 Debug identifizierte einen Spec-Konflikt: Pfad-Auflösung war Teil der BACKLOG-008 Anforderungen, aber im OUT OF SCOPE deklariert. Dies wurde behoben, indem Pfad-Auflösung als separates BACKLOG-009 ausgelagert wurde.

### Validation Evidence
- **Unit/Integration Tests:** python -m pytest backend/tests/integration/test_intent_resolver_filesystem.py backend/tests/unit/test_intent_filesystem_priority.py -q — PASS
- **Manual Janus test (Skill 6):** BACKLOG-008 funktioniert korrekt ✅ (RAG-Intent unterdrückt, kein Upgrade auf gpt-5.4)
- **Skill 6:** FIXED — Root Cause identifiziert (Spec-Konflikt), Spec aktualisiert, BACKLOG-009 erstellt
- **Backend-Log (Skill 6 Test):** `[FILESYSTEM-OVERRIDE] RAG intent suppressed by filesystem intent` - BACKLOG-008 funktioniert ✅
- **Backend-Log (Skill 6 Test):** gpt-5.4-nano wurde verwendet (kein Upgrade) ✅

### Final Audit Fixes
- **documentation/Planned Features/backlog_BACKLOG-008_rag_intent_filesystem_fix.md:** Pfad-Auflösung aus Expected Behavior und Acceptance Criteria entfernt
- **documentation/Planned Features/backlog_BACKLOG-008_rag_intent_filesystem_fix.md:** Hinweis hinzugefügt, dass Pfad-Auflösung in BACKLOG-009 ausgelagert ist
- **documentation/backlog/BACKLOG.md:** BACKLOG-009 für Pfad-Auflösungs-Problem erstellt

### Skill 7 Version Bump
- **Old version:** 0.4.17-beta.13
- **New version:** 0.4.17-beta.14
- **Mode:** automatic patch prerelease bump
- **Files changed:** package.json, package-lock.json, backend/version.py
- **Validation:** PASS

### Remaining Risks
- Pfad-Auflösungs-Problem (gpt-5.4-nano ist konservativ bei Pfad-Auflösung) ist in BACKLOG-009 ausgelagert

---

## DEBUGGING-LOG
