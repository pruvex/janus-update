# Task 060: Agent Planner Overhaul

## 1. Ziel & Kontext
Vollständige Harmonisierung von AgentPlanner und SkillSelector mit der IntentEngineV2 und CapabilityRegistry.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** IntentEngineV2, CapabilityRegistry, AgentPlanner, SkillSelector
- **Beeinflusst:** execution_engine.py, chat_orchestrator.py, prompt_registry.py, execution_dispatcher.py
- **Risiko-Einschätzung:** MEDIUM (Core orchestrator changes)

## 3. Betroffene Dateien
- backend/services/orchestrator/prompt_registry.py
- backend/services/orchestrator/execution_dispatcher.py
- backend/data/schemas.py
- backend/services/orchestrator/execution_engine.py
- backend/services/chat_orchestrator.py

## 4. Umsetzungsschritte (Diamond-Flow)
- [x] **Phase 1 (Pre-Check):** `/pre-check` ausführen.
- [x] **Phase 2 (Implementierung):**
  - Einführung von PlannerContext und PlannerProviderProfile in schemas.py
  - Erweiterung von execution_engine.py mit _build_planner_capability_groups, _build_planner_context, _build_planner_provider_profile
  - Integration von capability_registry in OrchestratorExecutionEngine.__init__
  - Update von run_agent_factory zur Verwendung von intent_result, planner_context, provider_profile
  - Verschiebung von capability_registry-Initialisierung in chat_orchestrator.py vor SkillSelector
  - Hinzufügen von Kalender-Guard in execution_dispatcher.py (_CALENDAR_QUERY_TOKENS, _CALENDAR_INCOMPATIBLE_SKILLS, _is_calendar_query)
  - Erweiterung von prompt_registry.py calendar_read_priority mit strikteren VERBOTEN-Regeln
  - Hinzufügen von 14-Tage Wochentag-Kalender in execution_engine.py
- [x] **Phase 3 (Testing):** Regression-Tests laufen lassen
- [x] **Phase 4 (Post-Check):** `/post-impl` ausführen.
- [ ] **Phase 5 (Audit - Optional):** `/opus-audit` bei Bedarf ausführen.

## 5. Test-Vorgaben
- [x] Regression: `python -m pytest backend/tests -q`
- [ ] Targeted: Kalender-Queries testen, forbidden_skill_ids Guard testen

## 6. Ergebnis & Audit-Trail
**Files changed:**
- `backend/services/orchestrator/prompt_registry.py` - Updated calendar_read_priority directive with stricter VERBOTEN rules and 14-day weekday calendar
- `backend/services/orchestrator/execution_dispatcher.py` - Added calendar guard with _CALENDAR_QUERY_TOKENS, _CALENDAR_INCOMPATIBLE_SKILLS, _is_calendar_query function
- `backend/data/schemas.py` - Added PlannerProviderProfile and PlannerContext classes for structured planner handoff
- `backend/services/orchestrator/execution_engine.py` - Added capability_registry parameter, _build_planner_capability_groups, _build_planner_context, _build_planner_provider_profile methods, updated run_agent_factory to use intent_result
- `backend/services/chat_orchestrator.py` - Moved capability_registry initialization before SkillSelector, passed capability_registry to execution_engine, updated run_agent_factory calls to include intent_result

**What was done:**
Harmonized AgentPlanner and SkillSelector with IntentEngineV2 and CapabilityRegistry. Introduced PlannerContext for structured handoff, added calendar guard to purge PDF/image skills for calendar queries, implemented forbidden_skill_ids guard based on intent detection, added 14-day weekday calendar to prevent date guessing.

**Test result:**
Regression tests: 477 passed, 7 warnings (not failures).

## 7. Debugging-Log
Keine Probleme. Implementierung verlief reibungslos ohne Fehler.
