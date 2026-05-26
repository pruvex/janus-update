# Task 065: Contextual Entity Resolver (Calendar Mutations)

## 1. Ziel & Kontext
Der Nutzer beschreibt Kalender-Mutationen mit unpräzisen Titeln (z.B. „Fitnesstudio“ vs. „Sport im Fitnessstudio“). Ziel: Vor dem erzwungenen `calendar.find_and_update_event` gegen den **Kalender-Snapshot** (Memory-Spiegel) ein deterministisches Ranking mit rapidfuzz, Temporal-Pre-Pass bei identischen Titeln, konservative Routing-Hints (`PROCEED` / `FALLBACK_TO_LIST` / `CLARIFY_USER`) und direkter Event-ID-Übergabe ans Tool (kein erneuter Fuzzy-Lauf bei Erfolg).

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** TASK-059 (Kalender-Snapshot), TASK-062–064 (Kalender-Routing/Mutation-Hammer).
- **Beeinflusst:** `execution_dispatcher.py`, `calendar_tools.py`, `schemas.py` (`FindAndUpdateCalendarEventArgs`), Skill-JSON.
- **Risiko-Einschätzung:** MEDIUM (Mutation-Pfad schreibend; Fallbacks konservativ).

## 3. Betroffene Dateien
- `backend/services/orchestrator/entity_resolver.py` (neu)
- `backend/services/orchestrator/execution_dispatcher.py`
- `backend/tools/calendar_tools.py` (`find_and_update_calendar_event` + optional `event_id`)
- `backend/data/schemas.py` (`FindAndUpdateCalendarEventArgs.event_id`)
- `backend/skills/calendar/find_and_update_event.json` (parameter_hints)
- `backend/tests/test_entity_resolver.py` (neu)

## 4. Umsetzungsschritte (Diamond-Flow)
- [x] **Phase 1 (Pre-Check):** `/pre-check` (implizit im Architekt-/Validator-Flow).
- [x] **Phase 2 (Implementierung):** Resolver-Kaskade, Dispatcher-Integration, Tool-Fast-Path, Schema/Skill-Ergänzung.
- [x] **Phase 3 (Testing):** `pytest backend/tests/test_entity_resolver.py` + verwandte Kalender-Tests.
- [x] **Phase 4 (Post-Check):** `/post-impl` ausgeführt.
- [x] **Phase 5 (Guided Mode Final Safety):** Schwenk zu Guided Assistant Mode als finale Sicherheitsmaßnahme. Bei RESOLVED wird event_id + title in action_guidance injiziert, LLM muss zwingend diese Werte verwenden (KEINE Erfindung, KEINE Änderung). Mutation Hammer mit VERBOTEN-Regeln als finaler Check. Status: 🥇 COMPLETE & SEALED.
- [x] **Phase 6 (Deictic Fallback Extension):** Erweiterung um deiktische Referenzen (Pronomen: "ihn", "den", "da"). full_user_text Parameter für vollständige User-Nachricht, orchestrator_context.history für saubere Chat-Historie. Fallback aktiv bei deiktischen Markern ODER sehr kurzen Queries (≤ 2 tokens). Honest Scoring (75.0 statt 100.0). Status: 🥇 COMPLETE & SEALED.

## 5. Test-Vorgaben
- [x] `python -m pytest backend/tests/test_entity_resolver.py -q`
- [x] `python -m pytest backend/tests/test_calendar_routing_fix.py backend/tests/test_entity_resolver.py -q`

## 6. Ergebnis & Audit-Trail
**Files changed (Post-impl):**
- `entity_resolver.py` — TASK-065 Kernlogik (Tokenizer, Temporal Layer, Adaptive Scores, Thresholds).
- `execution_dispatcher.py` — Resolver vor Calendar-Mutation-Hammer; Routing nach `dispatcher_hint`.
- `calendar_tools.py` — `event_id` optional → `events.get()` statt nur Fuzzy-Liste.
- `schemas.py` / `find_and_update_event.json` — optionales Feld `event_id` im Diamond-Contract.
- `test_entity_resolver.py` — 8 deterministische Unit-Tests.

**What was done:**
Smart Entity Resolver ordnet `mutation_target` + `wf.calendar_snapshot` einem Event zu. Bei `RESOLVED` werden `event_title_query` und `event_id` vorbefüllt; bei `AMBIGUOUS`/`WEAK` wird `list_events` erzwungen; bei `NOT_FOUND`/kurzer Query keine Tools bei Mutation (Klärung per LLM-Text).

**Test result:**
- `test_entity_resolver.py`: **8 passed**
- `test_calendar_routing_fix.py` + `test_entity_resolver.py`: **14 passed**

## 7. Debugging-Log
Keine Blocker. Zwei erste Testfälle mussten angepasst werden (`ab` löst Kurzquery nicht aus → `a`; fuzzy-Fragment `Fitnesstudio` landete unter SCHWACH ohne ausreichenden Abstand → `fitnessstudio` als stärkerer Substring).
