# FEATURE DESIGN SEED - Wikipedia-Routine-Snapshot Polish (Diamond UX)

## SOURCE

- Backlog Item: `BACKLOG-126`
- Entry Point: `QUICKCHANGE_OR_TASK` (bounded — kein Full Spec noetig)
- Source of Truth: `documentation/backlog/BACKLOG.md`
- Session-Evidence: `documentation/codex/HANDOFF_BLOCK2_CALENDAR_WIKIPEDIA_TO_CODEX_2026-07-10.md`

## LATEST DECISION SUMMARY

Feature Name: Wikipedia-Routine-Snapshot Polish
Primary Goal: Bei Kalender+Wikipedia-Routinen die **beste** Nutzer-sichtbare Formulierung speichern und wiedergeben — nicht zufaellig die Tool-Rohfassung des Promotion-Laufs.
User Problem: Erster Lauf (GPT) liefert schoene LLM-Synthese; Promotion-Lauf (Gemini, anderer Chat) speichert Tool-Combo-Text; Routine-Reuse zeigt dann encyclopedia-Style statt Assistenten-Formulierung.
User Value: Wiederholte Berlin-Anfragen fuehlen sich wie der beste erste Lauf an — schnell UND natuerlich.
Primary Target Surface: `calendar_wikipedia_presenter.py`, `workflow_offer_service.py`, `routine_runner.py`
Existing or New Surface: bestehend (Block 2 bereits live)
Success Behavior:
- Snapshot bevorzugt LLM-synthetisierten Wikipedia-Teil, wenn substantiell besser als Tool-Combo
- Gleicher Provider+Chat oder explizite „best text wins“-Policy beim Promotion
- Rebind (z. B. München) weiterhin frische Tool-Kurzfassung
Failure Behavior: Kein Snapshot-Overwrite mit kuerzerem/schlechterem Text; Rebind-Logik unveraendert fail-safe.
Out of Scope: LLM in jedem Routine-Lauf; neue Combo-Familien; Routinen-UI (→ BACKLOG-127 / M5 LU).
Routing Decision: BOUNDED TASK / QUICKCHANGE CLUSTER
Recommended Next Skill: `janus-preimplementation-check` oder `janus-quickchange` nach Scope-Schnitt

## BOUNDED TECHNICAL OPTIONS

1. **Best-text-wins beim Promotion:** `enrich_steps_with_wikipedia_snapshot()` vergleicht `final_text` mit bestehendem Kandidaten-Snapshot, behaelt laengere/bessere LLM-Variante.
2. **Kandidat-Update auf erstem LLM-Lauf:** Erster Hit speichert bereits Snapshot; Promotion merged nur wenn besser.
3. **Provider-Hinweis in Doku:** „Fuer optimalen Snapshot 2× gleicher Provider“ — Doku-only, kein Code.

Empfehlung: Option 1 + 2 kombiniert (kleiner Slice).

## EVIDENCE PATHS

- `backend/services/workflow/calendar_wikipedia_presenter.py`
- `backend/tests/test_calendar_wikipedia_presenter.py`
- Live-Test 2026-07-10: GPT schön → Gemini Promotion → GPT Routine reuse (Tool-Style)

## ACCEPTANCE CRITERIA (DRAFT)

- [ ] Nach 2-Lauf-Lernkette mit unterschiedlichen Providern: Snapshot enthaelt LLM-Qualitaet wenn im ersten Lauf vorhanden
- [ ] Rebind München: weiterhin frischer Tool-Text, kein Berlin-Snapshot
- [ ] Tests fuer best-text-wins und cross-provider promotion
- [ ] Keine Regression Routine-Reuse Kalender-Teil
