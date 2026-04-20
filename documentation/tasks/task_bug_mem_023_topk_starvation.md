---
id: BUG-MEM-023
title: Top-K Starvation Fix (Vector Query Limit)
status: DONE
priority: P1
category: Memory/Bug
assignee: Kimi
---

## 1. Ziel & Kontext
**Problem:** Die Vektorsuche in `get_relevant_facts_as_objects` hat einen Default-Limit von 10. Der Knapsack-Algorithmus kann nur aus diesen 10 Kandidaten wählen, obwohl bessere Matches außerhalb dieses Top-10 existieren könnten.

**Ziel:** Limit auf 50 erhöhen, damit der Knapsack-Algorithmus alle relevanten Kandidaten zur Verfügung hat.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** Memory V2 System, Knapsack-Budget Algorithmus
- **Beeinflusst:** memory_manager.py, Context Selection
- **Risiko-Einschätzung:** P1 — High (Recall Quality)

## 3. Betroffene Dateien (Target)
- `backend/services/memory_manager.py` — `get_relevant_facts_as_objects()` limit Parameter

## 4. Umsetzungsschritte (Diamond-Flow)
- [x] **Phase 1 (Pre-Check):** Task-File erstellt
- [x] **Phase 2 (Fix):** limit 10 → 50
- [x] **Phase 3 (Test):** Syntax-Check PASSED
- [x] **Phase 4 (Post-Impl):** Dokumentation erstellt

## 5. Test-Vorgaben
- [ ] `get_relevant_facts_as_objects` gibt bis zu 50 Kandidaten zurück
- [ ] Knapsack-Algorithmus hat mehr Kandidaten zur Auswahl
- [ ] Recall-Rate für wichtige Fakten verbessert

## 6. Ergebnis & Audit-Trail
**Implementation:** Kimi (Windsurf) — 2026-04-08

**Key Implementation Details:**
```python
def get_relevant_facts_as_objects(db: Session, query: str, limit: int = 50) -> List[ExtractedFact]:
    """
    BUG-MEM-023: Limit von 10 auf 50 erhöht.
    Der Knapsack-Algorithmus regelt das Budget - die Vektorsuche darf die Kandidaten
    nicht vorher künstlich abschneiden!
    """
```

**Files Modified:**
- `backend/services/memory_manager.py` — limit 10 → 50

**Syntax-Check:** ✅ PASSED

## 7. Debugging-Log
**2026-04-08 — Implementation Complete (Kimi)**
- Default limit: 10 → 50
- Docstring aktualisiert mit BUG-MEM-023 Hinweis
- Syntax-Check: ✅ PASSED

**2026-04-08 — /post-impl durch Kimi**
- Task-Dokumentation finalisiert (Diamond-Flow Template)
- PROJECT_STATE.md aktualisiert (Session Log)
- 01_CENTRAL_TASK_REGISTRY.md aktualisiert (Macro-Dashboard)
- Pattern dokumentiert in WHAT_I_LEARNED.md:
  - `## [PATTERN] #MemoryV2 #Retrieval Top-K Vector Query Limit Expansion`
- /post-impl COMPLETE
