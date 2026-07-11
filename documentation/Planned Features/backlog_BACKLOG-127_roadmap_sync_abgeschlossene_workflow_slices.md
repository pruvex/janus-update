# TASK SEED - Roadmap-Sync fuer abgeschlossene Workflow-/Block-2-Slices

## SOURCE

- Backlog Item: `BACKLOG-127`
- Entry Point: `DOCUMENTATION_UPDATE`
- Source of Truth: `documentation/backlog/BACKLOG.md`

## LATEST DECISION SUMMARY

Feature Name: Roadmap- und Tracking-Sync fuer bereits gelieferte Slices
Primary Goal: `ROADMAP_EPIC_ORDER.md`, `CURRENT_STATE.md`, `01_CENTRAL_TASK_REGISTRY.md` und Handoffs auf den **echten** Stand bringen — ohne neuen Produktcode.
User Problem: Spec 29 (stilles Lernen), Spec 31 (semantic reuse), Block 2 (Kalender+Wikipedia) und Cursor-Session-Fixes sind live, aber in der Roadmap nur indirekt oder gar nicht als abgeschlossen sichtbar.
User Value: Codex und Operator sehen sofort, was fertig ist und was wirklich als Naechstes dran ist (M4).
Routing Decision: DOCUMENTATION SLICE ONLY
Recommended Next Skill: `janus-documentation-update`

## REQUIRED UPDATES (CHECKLIST)

- [ ] `ROADMAP_EPIC_ORDER.md` §16: Spec-29-Passive-Learning + Spec-31 als DONE/Anhang erwaehnen
- [ ] `ROADMAP_EPIC_ORDER.md`: Block 2 Calendar+Wikipedia als validierter Combo-Pilot (neben Weather/Routing)
- [ ] `01_CENTRAL_TASK_REGISTRY.md`: Eintrag fuer Block-2-Session oder Verweis auf `HANDOFF_BLOCK2_*`
- [ ] `CURRENT_STATE.md`: Kurzabschnitt 2026-07-10 Abend — Block 2 LIVE PASS, Diamond-UX, Snapshot-Modell
- [ ] `SKILL_USAGE_LOG.md`: Cursor-Session-Eintrag
- [ ] Optional: Recall-Follow-up als `BACKLOG-125` / kuenftiges `M2.3` in §0.7 verlinken
- [ ] Optional: `TASK-MEM-M4.1` Precheck-Status gegen echten Code-Stand (`session_search` scaffold) abgleichen

## OUT OF SCOPE

- Kein neuer Feature-Code
- Keine Roadmap-Reihenfolge-Aenderung (M4 bleibt JETZT)

## EVIDENCE PATHS

- `documentation/codex/HANDOFF_BLOCK2_CALENDAR_WIKIPEDIA_TO_CODEX_2026-07-10.md`
- `documentation/codex/model-routing/HANDOFF_ROADMAP_STATUS_TO_CODEX_2026-07-10.md`
- `documentation/tasks/TASK-SPEC31.1_final_audit.md`
- `documentation/tasks/TASK-SPEC31.2_final_audit.md`
- `documentation/tasks/TASK-SPEC29.2_*` (passive learning)
