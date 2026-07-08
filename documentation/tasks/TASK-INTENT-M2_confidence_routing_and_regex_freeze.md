TASK-INTENT-M2
- Source Spec: `documentation/Cursor specs/INTENT_ENGINE_HERMES_INSPIRED_UPGRADE_PLAN.md`
- Backlog Item: `N/A`
- Feature: Intent Phase 2 Confidence Routing and Regex Freeze
- Generated At: 2026-07-08

## Generated Tasks

### TASK-INTENT-M2.1 Implement confidence-based intent routing and soften ambiguity hard-blocks
- Ziel:
  - Ersetze den harten Ambiguity-Block fuer mittlere Intent-Sicherheit durch ein kontrolliertes Confidence-Routing, damit Contact/Pet-Facts und Recall-Pfade nicht unnoetig mit `disable_tools=True` abgewuergt werden.
- Scope:
  - Nur Confidence-Routing in Intent-/Dispatcher-Pfad, die direkt benoetigten Tests und die gebundene Evidenz fuer Ambiguity-FP-Reduktion gegen die bestehende M0/M1-Benchmark-Basis.
  - Kein Entity-First-Routing, kein neuer Auxiliary-Classifier-Scope, kein Transport, kein Workflow-Offer und kein Regex-Freeze-Schreibschutz in dieser Slice.
- Files:
  - `backend/services/orchestrator/execution_dispatcher.py`
  - `backend/services/orchestrator/intent_engine.py`
  - `backend/tests/test_intent_confidence_routing.py`
  - `backend/tests/test_calendar_routing_fix.py`
  - `backend/tests/test_intent_benchmark.py`
  - bestehende gezielte Intent-/Routing-Regressionen, falls direkt betroffen
- Steps:
  1. Fuehre einen klaren Confidence-Pfad fuer hohe, mittlere und niedrige Intent-Sicherheit ein, der echte Mehrdeutigkeit weiter blockiert, mittlere Sicherheit aber nicht mehr pauschal in `disable_tools=True` umkippen laesst.
  2. Halte Safety-, Medical-, Consent- und Personal-Recall-Web-Guards unveraendert bindend, auch wenn der neue Confidence-Pfad aktiv ist.
  3. Ergaenze fokussierte Regressionen fuer Contact/Pet/Recall-Faelle, die bisher an Ambiguity-False-Positives haengen, sowie Guardrail-Tests fuer bestehende Calendar-/Weather-/Shopping-Pfade.
  4. Beweise die Ambiguity-FP-Verbesserung ueber den Benchmark-/Test-Pfad gegen die vorhandene M0-Baseline und den M1-Classifier-Stand.
- Acceptance Criteria:
  - Ambiguity False Positives sinken messbar im Rahmen der M2-Zielsetzung (`-30%` bis `-50%`) oder ein belastbarer Blocker ist dokumentiert.
  - Contact/Pet-Fact- und Recall-Faelle mit hoher bzw. ausreichender Sicherheit werden nicht mehr unnoetig durch `disable_tools=True` blockiert.
  - `test_calendar_routing_fix.py` bleibt vollstaendig gruen.
  - Safety-/Medical-/Consent- und Personal-Recall-Web-Guards bleiben unveraendert wirksam.
- Tests:
  - `python -m pytest backend/tests/test_intent_confidence_routing.py -q`
  - `python -m pytest backend/tests/test_calendar_routing_fix.py backend/tests/test_intent_benchmark.py -q`
  - `python -m py_compile backend/services/orchestrator/execution_dispatcher.py backend/services/orchestrator/intent_engine.py`
  - `python -m backend.scripts.run_intent_benchmark --mode m2-proof --output documentation/test-runs/TASK-INTENT-M2.1_confidence_routing_2026-07-08.md`
- Model: 5.4
- Reason:
  - M2 I2 ist der naechste offene produktive Roadmap-Slice und bleibt als klarer Routing-/Guardrail-Block klein genug fuer den normalen 5.4-Workhorse-Pfad.
- Closeout:
  - Final Audit PASS ist in `documentation/tasks/TASK-INTENT-M2.1_final_audit.md` dokumentiert. Der erste M2-Slice ist damit task-scharf abgeschlossen: der produktive Intent-/Dispatcher-Pfad arbeitet jetzt mit bounded `routing_confidence`, mittlere Ambiguity wird kontrolliert weich geroutet statt pauschal hart geblockt, und bestehende Safety-/Weather-/Routing-/Realtime-/Mail-Guardrails bleiben erhalten.
  - Der lokale M2.1-Proof in `documentation/test-runs/TASK-INTENT-M2.1_confidence_routing_2026-07-08.md` ist reproduzierbar und zeigt die erwartete Verbesserung gegen die M0-Baseline: insgesamt `81/110 -> 91/110` (`73.6% -> 82.7%`), Contact `55.0% -> 95.0%`, Pet `53.3% -> 73.3%`, Calendar `53.3% -> 66.7%`, Recall unveraendert `80.0% -> 80.0%`.
  - Vor dem Codex-Audit wurde zusaetzlich bounded OpenRouter-Evidence als assist-only Vorreview gesammelt (`WF-INTENT-M2.1-OR-TRIAGE-REVIEW-2026-07-08-001`); die Acceptance Authority blieb explizit lokal bei Codex.
  - `TASK-INTENT-M2.2` bleibt als optionaler Regex-Freeze-Follow-up bewusst offen und darf nicht rueckwirkend in den abgeschlossenen M2.1-Slice hineingelesen werden.

### TASK-INTENT-M2.2 Implement regex freeze guardrails and deprecate new fact-telling pattern growth
- Ziel:
  - Friere weiteres Regex-Wachstum kontrolliert ein und verankere den Prozesspfad, dass neue sprachliche Varianten kuenftig ueber Classifier-/Benchmark-Faelle statt neue Pattern-Listen gelöst werden.
- Scope:
  - Nur Regex-Freeze-Schalter, Kommentare/Tripwires, CI-/Test-Guardrails und direkt benoetigte Deprecation-Hinweise fuer den bestehenden Fact-Telling-/Search-Pattern-Pfad.
  - Keine neue Intent-Logik ausserhalb der Freeze- und Deprecation-Grenzen.
- Files:
  - `backend/services/orchestrator/intent_engine.py`
  - `backend/utils/intent_classifier.py`
  - `backend/tests/test_intent_regex_freeze.py`
  - ggf. kleine validator-/guardrail-nahe Testdateien, falls direkt betroffen
- Steps:
  1. Verankere den Regex-Freeze-Hinweis und die fail-closed Guardrails fuer neue `_FACT_TELLING_PATTERNS`-/aehnliche Pattern-Erweiterungen.
  2. Markiere den alten Search-/Regex-Hilfspfad sauber als deprecation-only, ohne das bestehende Laufzeitverhalten bei deaktivierten Flags zu brechen.
  3. Ergaenze fokussierte Tests, die den Freeze-/Tripwire-Pfad und die weiterhin erlaubten Bugfix-Grenzen klar absichern.
- Acceptance Criteria:
  - Neue Pattern-Wachstumsfaelle werden ueber den Freeze-Pfad sichtbar unterbunden oder eindeutig markiert.
  - Der bestehende Intent-Pfad bleibt bei deaktivierten Freeze-/M2-Flags kompatibel.
  - Die neue Guardrail-Oberflaeche ist lokal testbar und dokumentiert, ohne Produktlogik ausserhalb des Freeze-Scopes zu veraendern.
- Tests:
  - `python -m pytest backend/tests/test_intent_regex_freeze.py -q`
  - `python -m py_compile backend/services/orchestrator/intent_engine.py backend/utils/intent_classifier.py`
- Model: 5.4
- Reason:
  - I3 bleibt laut Spec optional und sollte erst nach dem Confidence-Routing-Kern als separater kleiner Follow-up-Slice freigegeben werden.
