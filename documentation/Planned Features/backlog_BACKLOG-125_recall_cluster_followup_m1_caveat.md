# FEATURE DESIGN SEED - Recall-Cluster Follow-up (M1 Caveat +0 pp)

## SOURCE

- Backlog Item: `BACKLOG-125`
- Entry Point: `TASK_PIPELINE_START` (bounded Intent slice, kein Full-Spec noetig wenn Precheck eng bleibt)
- Source of Truth: `documentation/backlog/BACKLOG.md`
- Roadmap-Bezug: `ROADMAP_EPIC_ORDER.md` §0.7 Prio 3, M1 Exit Caveat

## LATEST DECISION SUMMARY

Feature Name: Recall-Cluster Follow-up fuer Intent M1
Primary Goal: Den dokumentierten Recall-Flatspot (`80.0% -> 80.0%`, +0 pp) gezielt schliessen, ohne das bestehende Confidence-Routing oder Domänen-Veto zu regressieren.
User Problem: Personal-Recall-Anfragen (Kontakte, Haustiere, „Wer ist…“, „Wie heisst…“) profitieren vom Auxiliary Classifier kaum; Nutzer erleben das wie Provider- oder Memory-Bugs.
User Value: Janus erinnert sich zuverlaessiger an persoenliche Fakten und antwortet konsistenter auf Recall-Fragen.
Primary Target Surface: `intent_engine.py`, `intent_aux_classifier.py`, Recall-Benchmark-Teilmenge
Existing or New Surface: bestehend
Success Behavior: Recall-Benchmark-Teilmenge steigt messbar gegen M0-Baseline (Ziel laut Intent-Spec: ≥ +12 pp fuer Contact/Pet/Recall-Cluster, mindestens Recall nicht mehr flat).
Failure Behavior: Keine Regression bei Calendar, Medical, External/Web, Workflow-Routing.
Out of Scope: Hermes-4-Klassen-Intent-Collapse; Entity-First M5 I4 (separates Backlog moeglich); Transport/OAuth/Memory M4.
Routing Decision: BOUNDED TASK SLICE
Routing Reason: Roadmap erwaehnt Recall nur als Caveat, nicht als formalen Meilenstein — dieser Backlog-Eintrag formalisiert den Slice.
Recommended Next Skill: `janus-preimplementation-check`

## BOUNDED PRODUCT DECISIONS

- Slice bleibt auf Recall/Personal-Cluster begrenzt.
- Benchmark-Proof ist Pflicht vor Staging-Flag-Flip.
- Kein Regex-Wachstum als Ersatz — lieber Classifier/Confidence-Feintuning oder Entity-Resolver-Hook.

## EVIDENCE PATHS

- `documentation/test-runs/INTENT_BENCHMARK_BASELINE.md`
- `documentation/Cursor specs/INTENT_ENGINE_HERMES_INSPIRED_UPGRADE_PLAN.md` §12
- `documentation/Cursor specs/ROADMAP_EPIC_ORDER.md` (Recall Caveat)
- `backend/services/orchestrator/intent_engine.py`
- `backend/services/orchestrator/intent_aux_classifier.py` (falls vorhanden)

## ACCEPTANCE CRITERIA (DRAFT)

- [ ] Recall-Teilmenge Benchmark: messbarer Uplift vs. M0 (Ziel ≥ +8 pp minimum, Stretch +12 pp)
- [ ] Contact/Pet-Recall Live-Retest: dokumentierte PASS-Faelle
- [ ] Keine Regression: Calendar, Medical, Workflow-Combo-Routing
- [ ] Roadmap §0.7 Prio 3 als erledigt markierbar oder in M2.3/I6 formalisiert
