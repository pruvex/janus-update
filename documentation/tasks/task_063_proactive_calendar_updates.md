# Task 063: Proactive Calendar Updates

## 1. Ziel & Kontext
Automatische Injektion von calendar.find_and_update_event bei Ergänzungen zu bestehenden Terminen. Janus speichert Informationen zwar als Fakt in der Memory-DB, aktualisiert aber nicht den Google-Kalender, weil der Update-Intent nicht scharf genug ist. Ziel: Änderungen am Kalender haben Vorrang vor reinem Memory-Logging.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** TASK-062 Intent-to-Selector Gap Fix, IntentEngineV2, CapabilityRegistry
- **Beeinflusst:** intent_engine.py, capability_registry.py, prompt_registry.py
- **Risiko-Einschätzung:** LOW (Intent detection improvement + mandatory skill addition)

## 3. Betroffene Dateien
- backend/services/orchestrator/intent_engine.py
- backend/services/capability_registry.py
- backend/services/orchestrator/prompt_registry.py

## 4. Umsetzungsschritte (Diamond-Flow)
- [x] **Phase 1 (Pre-Check):** `/pre-check` ausführen.
- [x] **Phase 2 (Implementierung):**
  - Kalender-Update-Keywords in intent_engine.py schärfen ("bring", "ergänze", "ergänzen", "hinzufügen", "mit", "einkaufen", "besorgen", "holen")
  - calendar.find_and_update_event zu mandatory_skills in capability_registry.py für Kalender-Intents hinzufügen
  - Proaktive Mutations-Regel in prompt_registry.py einfügen: "Änderungen am Kalender haben Vorrang vor reinem Memory-Logging"
- [x] **Phase 3 (Testing):** Regression-Tests laufen lassen
- [x] **Phase 4 (Post-Check):** `/post-impl` ausführen.
- [ ] **Phase 5 (Audit - Optional):** `/opus-audit` bei Bedarf ausführen.

## 5. Test-Vorgaben
- [x] Regression: `python -m pytest backend/tests -q`
- [ ] Targeted: "Bring Dosentomaten bei Aldi mit" muss einen Tool-Call auslösen

## 6. Ergebnis & Audit-Trail
**Files changed:**
- `backend/services/orchestrator/intent_engine.py` - Sharpened calendar update keywords (added "bring", "ergänze", "ergänzen", "hinzufügen", "mit")
- `backend/services/capability_registry.py` - Added calendar.find_and_update_event to mandatory skills for calendar intents
- `backend/services/orchestrator/prompt_registry.py` - Added proactive calendar mutation rule: "Änderungen am Kalender haben Vorrang vor reinem Memory-Logging"

**What was done:**
Proactive Calendar Updates implementation. Sharpened calendar update keywords in IntentEngineV2 to detect additions to existing appointments. Added calendar.find_and_update_event as mandatory skill for calendar intents in CapabilityRegistry. Added proactive mutation rule in prompt_registry.py to prioritize calendar updates over pure memory logging.

**Test result:**
Regression tests: 483 passed, 7 warnings (not failures).

## 7. Debugging-Log
Keine Probleme. Implementierung verlief reibungslos ohne Fehler.
