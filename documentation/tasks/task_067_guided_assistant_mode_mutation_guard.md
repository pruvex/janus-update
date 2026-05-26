# Task 067: Guided Assistant Mode (Mutation-Guard)

## 1. Ziel & Kontext
Implementierung eines Guided Assistant Mode für Kalender-Mutationen mit User-Confirmation-Flow, um ungewollte Änderungen zu verhindern und die Transparenz zu erhöhen.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** TASK-064 (Mutation Detection), TASK-065 (Contextual Entity Resolver)
- **Beeinflusst:** 
  - backend/services/calendar/calendar_ai_engine.py (Mutation-Proposals)
  - backend/api/routers/calendar.py (State-Management)
  - backend/services/chat_orchestrator.py (User-Confirmation-Flow)
- **Risiko-Einschätzung:** MEDIUM (Eingriff in den kritischen Kalender-Pfad)
- **CU:** 7

## 3. Betroffene Dateien
- backend/services/calendar/calendar_ai_engine.py
- backend/api/routers/calendar.py
- backend/services/chat_orchestrator.py
- backend/data/schemas.py

## 4. Umsetzungsschritte (Diamond-Flow)
- [ ] **Phase 1 (Pre-Check):** `/pre-check` ausführen.
- [ ] **Phase 2 (Implementierung):** Guided Assistant Mode mit User-Confirmation-Flow implementieren
- [ ] **Phase 3 (Testing):** Testen des Mutation-Guards mit verschiedenen Kalender-Szenarien
- [ ] **Phase 4 (Post-Check):** `/post-impl` ausführen.
- [ ] **Phase 5 (Audit - Optional):** `/opus-audit` bei Bedarf ausführen.

## 5. Test-Vorgaben
- [ ] Regression: `python -m pytest backend/tests -q` 
- [ ] Targeted: `python -m pytest backend/tests/test_calendar_modal.py -q`

## 6. Ergebnis & Audit-Trail
_Wird automatisch durch /post-impl ausgefüllt._

## 7. Debugging-Log
_Wird bei Bedarf ausgefüllt._
