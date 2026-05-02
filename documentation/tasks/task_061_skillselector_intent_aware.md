# Task 061: SkillSelector Intent-Aware

## 1. Ziel & Kontext
SkillSelector is now Intent-Aware & Policy-Driven. Integration of IntentEngineV2 detection results into SkillSelector.get_relevant_skills() for intent-based skill filtering.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** TASK-060 Agent Planner Overhaul, IntentEngineV2, SkillSelector
- **Beeinflusst:** chat_orchestrator.py
- **Risiko-Einschätzung:** LOW (Follow-up to TASK-060)

## 3. Betroffene Dateien
- backend/services/chat_orchestrator.py

## 4. Umsetzungsschritte (Diamond-Flow)
- [x] **Phase 1 (Pre-Check):** `/pre-check` ausführen.
- [x] **Phase 2 (Implementierung):**
  - Update skill_selector.get_relevant_skills() calls in chat_orchestrator.py to pass intent_result parameter
  - Update wf.relevant_skill_ids call (line 1238)
  - Update wf.all_dynamic_skills call (line 1328)
- [x] **Phase 3 (Testing):** Regression-Tests laufen lassen
- [x] **Phase 4 (Post-Check):** `/post-impl` ausführen.
- [ ] **Phase 5 (Audit - Optional):** `/opus-audit` bei Bedarf ausführen.

## 5. Test-Vorgaben
- [x] Regression: `python -m pytest backend/tests -q`

## 6. Ergebnis & Audit-Trail
**Files changed:**
- `backend/services/chat_orchestrator.py` - Updated skill_selector.get_relevant_skills() calls to pass intent_result parameter (lines 1238, 1328)

**What was done:**
SkillSelector is now Intent-Aware & Policy-Driven. Integrated IntentEngineV2 detection results into SkillSelector.get_relevant_skills() calls in chat_orchestrator.py for intent-based skill filtering. This ensures that the skill selection process respects the detected user intent (e.g., calendar, shopping, personal_recall) to apply appropriate skill filtering policies.

**Test result:**
Regression tests: 479 passed, 7 warnings (not failures).

## 7. Debugging-Log
Keine Probleme. Implementierung verlief reibungslos ohne Fehler.
