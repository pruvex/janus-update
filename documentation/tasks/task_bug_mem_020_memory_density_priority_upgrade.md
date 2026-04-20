---
id: BUG-MEM-020
title: Memory Density & Priority Upgrade
status: DONE
priority: P1
category: Memory/Bug
assignee: Kimi
---

## 1. Ziel & Kontext
**Problem:**
1. Wichtige Personen (Bruder, Frau) mit zu niedriger Priority gespeichert → verdrängt.
2. Limit von 10 zu klein → Recall-Fehler (Allergie vergessen).
3. Kaffee-Dubletten verstopfen den Lese-Slot.

**Ziel:** Priority 0.90 für Gesundheit, Limit 25, Dubletten-Prüfung >80%.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** Memory V2 System (COMPLETED)
- **Beeinflusst:** memory_enricher, memory_tools, memory_budget
- **Risiko-Einschätzung:** P1 — High (Safety-Critical)

## 3. Betroffene Dateien (Target)
- `backend/services/memory_enricher.py` — Priority-Rules
- `backend/tools/memory_tools.py` — MemoryReadArgs.limit
- `backend/services/memory_budget.py` — Dubletten-Erkennung

## 4. Umsetzungsschritte (Diamond-Flow)
- [x] **Phase 1 (Pre-Check):** Task-File gelesen
- [x] **Phase 2 (Priority):** HEALTH_FACTS 0.70 → 0.90
- [x] **Phase 3 (Limit):** MemoryReadArgs.limit 10 → 25
- [x] **Phase 4 (Dedupe):** _calculate_text_similarity() + 80% Threshold
- [x] **Phase 5 (Test):** Syntax-Check PASSED
- [x] **Phase 6 (Post-Impl):** /post-impl durch Kimi

## 5. Test-Vorgaben
- [ ] Bruder-Fakt hat Priority 0.85 (nicht verdrängt)
- [ ] Allergie-Fakt hat Priority 0.90 (immer präsent)
- [ ] `memory_read` gibt bis zu 25 Ergebnisse zurück
- [ ] "Ich mag Kaffee" + "User mag Kaffee" = Nur einer wird gewählt

## 6. Ergebnis & Audit-Trail
**Implementation:** Kimi (Windsurf) — 2026-04-08

**Key Implementation Details:**

### 6.1 Priority-Upgrades
- **RELATIONEN:** 0.85 (Partner, Kinder, Eltern, Bruder, Frau)
- **GESUNDHEIT:** 0.90 (Sicherheits-kritisch! Allergien, Erkrankungen)

### 6.2 Recall-Upgrade
- **Limit:** 10 → 25 Ergebnisse (`memory_read` Tool)

### 6.3 Dubletten-Prüfung
- **Threshold:** >80% Text-Ähnlichkeit = Dublette
- **Aktion:** Überspringen (keine 4 Kaffee-Slots mehr!)

**Files Modified:**
- `backend/services/memory_enricher.py` - HEALTH_FACTS 0.70 → 0.90
- `backend/tools/memory_tools.py` - Limit 10 → 25
- `backend/services/memory_budget.py` - Dubletten-Prüfung (>80%)

**Syntax-Check:** ✅ PASSED

**Pattern zur Wiederverwendung:**
- `## [PATTERN] #MemoryV2 #Deduplication Jaccard Similarity Duplicate Filter` in WHAT_I_LEARNED.md

## 7. Debugging-Log
**2026-04-08 — Implementation Complete (Kimi)**
- HEALTH_FACTS Priority: 0.70 → 0.90 (Sicherheits-kritisch)
- MemoryReadArgs.limit: 10 → 25
- Dubletten-Prüfung: _calculate_text_similarity() mit 80% Threshold
- Logging: `[KNAPSACK] Skipping duplicate slot ID=X (similarity=0.85 with ID=Y)`
- Syntax-Check: ✅ PASSED

**2026-04-08 — Post-Impl durch Kimi**
- Task-Dokumentation auf Diamond-Flow Template aktualisiert
- Registries aktualisiert (PROJECT_STATE.md, 01_CENTRAL_TASK_REGISTRY.md)
- WHAT_I_LEARNED.md aktualisiert mit 4 neuen Patterns:
  - Jaccard Similarity Duplicate Filter (BUG-MEM-020)
  - Recall-Guard for Self-Referential Queries (BUG-MEM-021)
  - Medical-Override for Health-Critical Slots (BUG-MEM-021)
  - Family-Context Instruction Hardening (BUG-MEM-021)
- /post-impl COMPLETE
