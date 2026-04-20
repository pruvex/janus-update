# Task M-MEM-V2-FINAL: Temporal-Recall & Episodic Memory (Diamond Gold)

## 1. Meta
**Task-ID:** M-MEM-V2-FINAL  
**Priorität:** CRITICAL  
**Story-Points:** 3  
**Zuständig:** Cascade (Kimi)  
**Status:** DONE (2026-04-09)

## 2. Kontext & Ziel
Abschluss des Memory V2.1.0 Diamond Gold Release mit **Episodic Memory** Features:
- Temporal-Recall: Zeitstempel für jede Erinnerung (lokalisiert, menschlich lesbar)
- Ghost-Chat-Awareness: Dedup bevorzugt Origin-Chat-Titel über "Hintergrund-Extraktion"
- Personen-Dedup: Gleiche Person erkannt via Namens-Overlap trotz niedrigem Jaccard
- System Clock: Aktuelle Uhrzeit/Datum im Prompt für Zeit-Fragen

## 3. Anforderungen (Acceptance Criteria)
- [x] Jede MemorySlot enthält `timestamp` und `chat_title`
- [x] Zeitstempel werden in deutscher Lokalzeit angezeigt ("Heute um 14:30", "3. März 2026")
- [x] Der LLM kann auf "Wann hast du das gesagt?" mit exaktem Datum/Uhrzeit antworten
- [x] Identische Fakten aus Ghost-Chats werden dem Origin-Chat zugeordnet
- [x] Personen-Beziehungen werden trotz unterschiedlicher Fakten ("Chris ist Freund" vs "Chris heißt Christoph") als Duplikat erkannt
- [x] Syntax-Checks fehlerfrei

## 4. Änderungs-Set
**Affected Files:**
- `backend/services/memory_budget.py` — Episodic Metadata, Temporal Formatting, Origin-aware Dedup
- `backend/services/chat_orchestrator.py` — Temporal-Recall Directive, System Clock Injection
- `backend/services/memory_extractor.py` — Richtungs-Pflicht für Beziehungen ("des Nutzers")

## 5. Test-Vorgaben
- [x] py_compile: PASSED
- [x] Live-Test: Gemini erkennt Rolf=Nutzer, Chris=Freund (kein Identity-Flip)
- [x] Zeitstempel-Test: Fakten zeigen "Heute um..." oder echtes Datum

## 6. Ergebnis & Audit-Trail
**Files Changed:**
1. `backend/services/memory_budget.py` — Added MemorySlot.timestamp/chat_title, format_temporal_stamp(), _utc_to_local(), Origin-aware dedup with Ghost-Chat inheritance, Personen-Dedup via _extract_proper_names(), _format_slot_line() for episodic context format
2. `backend/services/chat_orchestrator.py` — Added [TEMPORAL-RECALL] directive to system prompt, System Clock injection (AKTUELLES DATUM/UHRZEIT), Identity-Anchor visual block
3. `backend/services/memory_extractor.py` — RELATION-DIRECTION GUARD ensures "des Nutzers" in all relationship facts

**What was done:**
Episodic Memory V2.1.0 Final — Every memory now carries temporal metadata (when + which chat) enabling the LLM to answer "when did I tell you this?" questions. Origin-aware deduplication ensures Ghost-Chat extractions inherit real chat titles. System Clock gives LLM awareness of current time. Identity-Anchor + Richtungs-Pflicht prevent Gemini from flipping user identity with third-party names.

**Test Result:** PASS — Syntax-checks passed, Live-Test with Rolf/Chris/Maggy shows correct identity separation (no flip), temporal stamps render correctly.

**Diamond Gold Certification:** 🚀💎 ACHIEVED

## 7. Debugging-Log
Keine Probleme. Implementation clean.

## 8. Architektur-Notizen
**Episodic Format:**
```
| GESPEICHERT AM: Heute um 19:30 | IM CHAT: 'Neuer Chat' | FAKT: Chris ist Freund des Nutzers
| GESPEICHERT AM: 3. März 2026 um 14:15 | IM CHAT: 'Kennenlern-Gespräch' | FAKT: User heißt Rolf
```

**Origin-Awareness Algorithm:**
1. When near-duplicate detected (Jaccard > 0.70 OR same-person via name overlap)
2. Keep the slot with higher priority (knapsack sort order)
3. BUT adopt: (a) oldest timestamp (lower memory_id), (b) real chat title over ghost title
4. Log: `[KNAPSACK] Ghost-swap: ID=X inherited title 'Real Chat' from ID=Y`

## 9. Beeinflusst
- `documentation/features/epic_memory_v2.md` — Final Diamond Gold release notes
- `WHAT_I_LEARNED.md` — Temporal-Recall Pattern, Episodic Context Pattern
- `01_CENTRAL_TASK_REGISTRY.md` — Epic M-MEM-V2 DONE
- `PROJECT_STATE.md` — Session log entry

## 10. Referenzen
- `live_test_catalog_memory_v2.md` — Test Scenario 19 (E2E)
- `task_fix_036_regression_cleanup.md` — Previous Diamond milestone
