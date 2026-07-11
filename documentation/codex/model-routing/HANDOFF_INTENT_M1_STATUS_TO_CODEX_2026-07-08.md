# Codex Handoff: Intent M1 Status → Next Move (Memory MA/MB)

**Date:** 2026-07-08  
**Source:** Updated Cursor status handoff `HANDOFF_INTENT_M1_STATUS_TO_CURSOR_2026-07-08.md`  
**Status:** READY FOR CODEX

## 1. Was sich geändert hat (kurz)

In `HANDOFF_INTENT_M1_STATUS_TO_CURSOR_2026-07-08.md` wurden zwei Klarstellungen ergänzt:
- Binding-Verweis auf `HANDOFF_DELEGATION_ROUTE_HARDENING_OPERATING_MODEL_2026-07-07.md` (Track A = Memory zuerst).
- Explizites Verbot, für `Memory MA/MB` in die Implementierung über Cursor zu gehen: Cursor nur für bounded review/draft der Memory-Slice-Artefakte, Implementierung bleibt Codex.

Diese Änderungen gelten als Operating-Constraint für die nächste Codex Session (sie verhindern Scope-Widening).

## 2. Current Truth (verbindlich)

- `TASK-INTENT-M1.1`: EXIT PASS
- `TASK-INTENT-M1.2`: EXIT PASS
- `TASK-INTENT-M1.3`: EXIT PASS WITH CAVEAT
- Caveat: Recall blieb `80.0% -> 80.0% (+0.0 pp)` (daher keine Claim „Recall solved“ und keine unrestricted staging-ready Behauptung).

## 3. Files to Trust (konzentriert)

- `documentation/ai/CURRENT_STATE.md`
- `documentation/tasks/TASK-INTENT-M1_auxiliary_action_subject_classifier.md`
- `documentation/tasks/TASK-INTENT-M1.3_final_audit.md`
- `documentation/test-runs/TASK-INTENT-M1.3_benchmark_uplift_2026-07-08.md`
- `documentation/test-runs/INTENT_BENCHMARK_BASELINE.md`
- `documentation/Cursor specs/ROADMAP_EPIC_ORDER.md`
- `documentation/codex/model-routing/HANDOFF_DELEGATION_ROUTE_HARDENING_OPERATING_MODEL_2026-07-07.md`

## 4. Verbindliche No-Go-Regeln

- Kein Transport / OAuth / OpenRouter / Delegation hardening starten aus diesem Handoff.
- Keine M2 Confidence-Routing-Änderungen, bis der Recall-Caveat (wie er behandelt wird) Team-seitig explizit entschieden ist.

## 5. Aufgabe für Codex (nächster sicherer Slice)

**Priorität: Finish `Memory MA/MB`** (Roadmap erlaubt Parallelität zu M1, und es hängt nicht davon ab, Recall als „gelöst“ zu deklarieren).

Danach (parallel oder unmittelbar):
- eine bounded follow-up decision für den Recall gap vorbereiten:
  - entweder dedicated Recall hardening/debug slice
  - oder explizite operator Entscheidung, dass M2 mit dokumentiertem Caveat weitergeht

## 6. Copy-paste Prompt für Codex

```text
Du arbeitest am Janus-Projekt (Branch: develop).

STANDARD: Nur Memory MA/MB als nächsten Schritt umsetzen.

Binding constraints (verbindlich):
- Current milestone: TASK-INTENT-M1.3 PASS WITH CAVEAT (Recall 80% -> 80%, kein „Recall solved“ claim)
- Track A wins: Memory MA/MB zuerst, Hardening nur selten/klein (Operating Model beachten)
- No-Go: kein Transport/OAuth/OpenRouter/Delegation hardening starten
- Keine M2 confidence routing Änderungen, bevor der Recall-Caveat Team-Entscheidung hat

Trust files zuerst:
- documentation/ai/CURRENT_STATE.md
- documentation/tasks/TASK-INTENT-M1_auxiliary_action_subject_classifier.md
- documentation/tasks/TASK-INTENT-M1.3_final_audit.md
- documentation/test-runs/TASK-INTENT-M1.3_benchmark_uplift_2026-07-08.md
- documentation/test-runs/INTENT_BENCHMARK_BASELINE.md
- documentation/Cursor specs/ROADMAP_EPIC_ORDER.md
- documentation/codex/model-routing/HANDOFF_DELEGATION_ROUTE_HARDENING_OPERATING_MODEL_2026-07-07.md

Aufgabe:
- Implementiere Memory MA/MB als genau einen bounded Slice (keine M2 Integration).
- Output: CI-laufbare pytest / py_compile Checks + Update CURRENT_STATE + SKILL_USAGE_LOG Eintrag mit Evidence.
- Wenn Recall-gap follow-up nötig wird: nur Entscheidung/Plan vorbereiten, nicht implementieren.

Stop:
- Nach Memory MA/MB Exit PASS/Blocked (mit Evidence).
```

---

**END OF CODEX HANDOFF**

