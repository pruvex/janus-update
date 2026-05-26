# Task 062: Intent-to-Selector Gap Fix

## 1. Ziel & Kontext
Fixing Intent-to-Selector gap. SkillSelector meldet intent=None (oder nur personal_recall), wodurch calendar.list_events nicht geladen wird. Ziel: Kalender-Keywords schärfen und Sicherheitsnetz einbauen, um sicherzustellen, dass calendar.list_events bei erkanntem Kalender-Intent immer geladen wird.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** TASK-060 Agent Planner Overhaul, TASK-061 SkillSelector Intent-Aware, IntentEngineV2, CapabilityRegistry
- **Beeinflusst:** intent_engine.py, execution_dispatcher.py
- **Risiko-Einschätzung:** LOW (Intent detection improvement + safety net)

## 3. Betroffene Dateien
- backend/services/orchestrator/intent_engine.py
- backend/services/orchestrator/execution_dispatcher.py

## 4. Umsetzungsschritte (Diamond-Flow)
- [x] **Phase 1 (Pre-Check):** `/pre-check` ausführen.
- [x] **Phase 2 (Implementierung):**
  - Kalender-Keywords in intent_engine.py schärfen ("termine", "habe ich", "mittwoch", "was habe ich", "was steht an", "steht an", "meine termine", "meinen termin", "meinen terminen")
  - CapabilityRegistry überprüfen: calendar.list_events ist bereits mandatory bei is_calendar_intent (verifiziert)
  - Sicherheitsnetz in ExecutionDispatcher einbauen: calendar.list_events injizieren, wenn Intent-Verdacht hoch aber Selector leer ausging
- [x] **Phase 3 (Testing):** Regression-Tests laufen lassen
- [x] **Phase 4 (Post-Check):** `/post-impl` ausführen.
- [ ] **Phase 5 (Audit - Optional):** `/opus-audit` bei Bedarf ausführen.

## 5. Test-Vorgaben
- [x] Regression: `python -m pytest backend/tests -q`
- [ ] Targeted: Kalender-Queries mit neuen Keywords testen

## 6. Ergebnis & Audit-Trail
**Files changed:**
- `backend/services/orchestrator/intent_engine.py` - Sharpened calendar keywords (added "habe ich", "was habe ich", "was steht an", "steht an", "meine termine", "meinen termin", "meinen terminen")
- `backend/services/orchestrator/execution_dispatcher.py` - Added safety net to inject calendar.list_events if calendar intent detected but selector returned empty

**What was done:**
Fixed Intent-to-Selector gap. Sharpened calendar keywords in IntentEngineV2 to improve detection of calendar queries like "termine", "habe ich", "mittwoch". Verified CapabilityRegistry already returns calendar.list_events as mandatory for calendar intents. Added safety net in ExecutionDispatcher to inject calendar.list_events if is_calendar_intent is true but relevant_skill_ids is empty or doesn't contain calendar.list_events.

**Test result:**
Regression tests: 483 passed, 7 warnings (not failures).

## 7. Debugging-Log
Keine Probleme. Implementierung verlief reibungslos ohne Fehler.
