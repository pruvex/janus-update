# Task 064: Calendar Mutation Detection

## 1. Ziel & Kontext
Breaking the Calendar Listing Prison. Das System erzwingt calendar.list_events auch dann, wenn der User eine Änderung (Mutation) will. Das Modell kann das Update-Tool technisch nicht erreichen. Ziel: Implementierung von is_calendar_mutation in der Intent-Engine und Aufhebung des tool_choice Zwangs in execution_dispatcher.py, wenn es sich um eine Mutation handelt.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** TASK-062 Intent-to-Selector Gap Fix, TASK-063 Proactive Calendar Updates
- **Beeinflusst:** intent_engine.py, execution_dispatcher.py
- **Risiko-Einschätzung:** LOW (Intent detection improvement + tool_choice logic adjustment)

## 3. Betroffene Dateien
- backend/services/orchestrator/intent_engine.py
- backend/services/orchestrator/execution_dispatcher.py

## 4. Umsetzungsschritte (Diamond-Flow)
- [x] **Phase 1 (Pre-Check):** `/pre-check` ausführen.
- [x] **Phase 2 (Implementierung):**
  - IntentDetectionResult in intent_engine.py um 'is_calendar_mutation' erweitern
  - detect_calendar_mutation_intent Methode in intent_engine.py implementieren (Keywords: bring, ergänze, ergänzen, hinzufügen, mit)
  - is_calendar_mutation in detect_all_intents setzen
  - tool_choice Logik in execution_dispatcher.py anpassen (Force nur bei reinen Queries, nicht bei Mutationen)
- [x] **Phase 3 (Testing):** Regression-Tests laufen lassen
- [x] **Phase 4 (Post-Check):** `/post-impl` ausführen.
- [ ] **Phase 5 (Audit - Optional):** `/opus-audit` bei Bedarf ausführen.

## 5. Test-Vorgaben
- [x] Regression: `python -m pytest backend/tests -q`
- [ ] Targeted: "Bring Dosentomaten bei Aldi mit" sollte calendar.find_and_update_event aufrufen, nicht calendar.list_events erzwingen

## 6. Ergebnis & Audit-Trail
**Files changed:**
- `backend/services/orchestrator/intent_engine.py` - Added is_calendar_mutation field to IntentDetectionResult, implemented detect_calendar_mutation_intent method (keywords: bring, ergänze, ergänzen, hinzufügen, mit), integrated into detect_all_intents
- `backend/services/orchestrator/execution_dispatcher.py` - Adjusted tool_choice logic to skip forcing calendar.list_events when is_calendar_mutation is true (CALENDAR-MUTATION: Skipping calendar.list_events force to allow calendar.find_and_update_event)

**What was done:**
Breaking the Calendar Listing Prison. Added is_calendar_mutation detection to IntentEngineV2 to distinguish between pure calendar queries (listing) and calendar mutations (updates). When is_calendar_mutation is true, the system no longer forces calendar.list_events tool_choice, allowing the model to reach calendar.find_and_update_event for mutation operations.

**Test result:**
Regression tests: 486 passed, 7 warnings (not failures).

## 7. Debugging-Log
Keine Probleme. Implementierung verlief reibungslos ohne Fehler.
