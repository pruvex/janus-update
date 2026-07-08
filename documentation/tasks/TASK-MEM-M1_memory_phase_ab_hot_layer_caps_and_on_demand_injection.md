TASK-MEM-M1
- Source Spec: `documentation/Cursor specs/MEMORY_HERMES_INSPIRED_UPGRADE_PLAN.md`
- Backlog Item: `N/A`
- Feature: Memory Phase A+B Hot-Layer-Caps and On-Demand Injection
- Generated At: 2026-07-08

## Generated Tasks

### TASK-MEM-M1.1 Implement Memory Phase A+B as one bounded guarded retrieval slice
- Ziel:
  - Fuehre Hot-Layer-Caps und On-Demand Memory Injection als einen kleinen, sicheren Memory-V2-Produktionsslice ein, ohne Session-Search, Frozen Core, Intent M2 oder Provider-Transport zu beruehren.
- Scope:
  - Nur Core-Cap-Logik, On-Demand-Gating fuer allgemeine Memory-Injection, benoetigte Observability/Config-Wiring und fokussierte Regressionen fuer die Retrieval-/Orchestrator-Pfade.
  - Kein Session-Search, kein Frozen Core, keine Export-API, keine neuen Provider-/Transportpfade, keine Recall-gap-Implementierung fuer Intent M1.
- Files:
  - `backend/services/memory/retrieval_service.py`
  - `backend/services/memory_budget.py`
  - `backend/services/memory_observability.py`
  - `backend/services/chat_orchestrator.py`
  - `backend/services/orchestrator/intent_engine.py` (nur wenn ein bestehendes Intent-Signal minimal wiederverwendet werden muss)
  - `backend/tests/test_memory_hot_layer_cap.py`
  - `backend/tests/test_memory_on_demand_injection.py`
  - bestehende fokussierte Memory-Regressionen, falls direkt betroffen
- Steps:
  1. Fuehre Flag-gesteuerte Hot-Layer-Caps fuer Core-Memory-Slots ein, inklusive Protected-Tags fuer Health/Medical und einer klaren Drop-Metrik.
  2. Extrahiere ein kleines `should_inject_memory(...)`-Gate fuer personal/recall-nahe Queries und binde es vor der allgemeinen Retrieval-Injection ein.
  3. Halte Health-Injector und bestehende Safety-/Medical-Pfade ausserhalb des neuen allgemeinen Injection-Gates.
  4. Ergaenze fokussierte Unit-/Regressionstests fuer Cap-Verhalten, Protected-Core-Fakten, Flag-off-Paritaet und Wetter-vs-personal Grenzfaelle.
- Acceptance Criteria:
  - `core_always`-Slots bleiben bei aktivem Flag innerhalb des konfigurierten Budgets; Protected Health/Medical-Slots werden nicht verdraengt.
  - Allgemeine Queries wie Wetter/externen Kontext ziehen bei aktivem On-Demand-Flag keine unnoetige Memory-Injection.
  - Personal-/Recall-nahe Queries und Wohnort-/Personen-Hinweise aktivieren Memory weiterhin korrekt.
  - Health-/Medical-Schutzpfade bleiben unveraendert aktiv.
  - Beide Flags defaulten auf `false`, und Flag-`off` behaelt das bisherige Verhalten bei.
- Tests:
  - `python -m pytest backend/tests/test_memory_hot_layer_cap.py -v`
  - `python -m pytest backend/tests/test_memory_on_demand_injection.py -v`
  - `python -m pytest backend/tests/test_memory_diamond.py backend/tests/test_memory_regression.py backend/tests/test_memory_tools.py backend/tests/test_memory_retrieval_relevance_priority.py -q`
  - `python -m py_compile backend/services/memory/retrieval_service.py backend/services/memory_budget.py backend/services/memory_observability.py backend/services/chat_orchestrator.py`
- Model: 5.4
- Reason:
  - Die Roadmap erlaubt MA/MB parallel zu M1, und beide Aenderungen bilden einen kleinen zusammenhaengenden Retrieval-/Injection-Sicherheitsblock, der ohne Session-Search oder Intent-M2-Entscheidungen ausgeliefert werden kann.
- Closeout:
  - Final Audit PASS ist in `documentation/tasks/TASK-MEM-M1.1_final_audit.md` dokumentiert. Die gebuendelte MA/MB-Slice ist damit task-scharf abgeschlossen: allgemeine Memory-Injection wird fuer generische/externe Queries jetzt on-demand gegatet, der Health-/Medical-Pfad bleibt ausserhalb dieser Suppression aktiv, und `core_always`-Memory wird optional ueber einen bounded Hot-Layer-Cap mit geschuetzten `health`-/`medical`-Slots sowie Drop-Metrik begrenzt.
  - Die lokale Evidenz umfasst `py_compile` PASS, fokussierte Pytest-Suiten fuer Hot-Layer-Cap und On-Demand-Injection PASS sowie den erweiterten gebundenen Memory-Regression-Block mit `68 passed`. Die manuelle Janus-Gate-Evidenz auf GPT und Gemini bestaetigt zusaetzlich, dass Wetter-mit-persoenlichem-Scope weiterhin korrekt personalisiert wird und die Nussallergie-/Health-Antwort sicher aktiv bleibt.
  - Session-Search, Frozen Core, USER.md-Export und spaetere Memory-Phasen bleiben bewusst offen und duerfen aus diesem PASS nicht impliziert werden.
