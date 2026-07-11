TASK-INTENT-M0
- Source Roadmap: `documentation/Cursor specs/ROADMAP_EPIC_ORDER.md`
- Source Spec: `documentation/Cursor specs/INTENT_ENGINE_HERMES_INSPIRED_UPGRADE_PLAN.md`
- Backlog Item: `N/A`
- Feature: Intent Phase 0 Benchmark Suite + Baseline Report
- Generated At: 2026-07-07

## Generated Tasks

### TASK-INTENT-M0.1 Build the intent benchmark suite and baseline report without changing routing logic
- Ziel:
  - Erzeuge eine CI-laufbare Benchmark-Suite mit 80+ faellen, die die aktuelle Intent-Engine nur misst und einen baseline-faehigen Report fuer M0 erzeugt.
- Scope:
  - Nur Benchmark-Fixtures, Benchmark-Runner, Benchmark-Tests und den Baseline-Report fuer die bestehende Intent-Engine.
  - Keine Aenderung an Intent-Engine-Logik, Transport, OAuth, OpenRouter-Produktpfad, Delegation, Gate- oder Cursor-Runner-Arbeit.
- Files:
  - `backend/tests/fixtures/intent_benchmark_cases.jsonl`
  - `backend/tests/test_intent_benchmark.py`
  - `backend/scripts/run_intent_benchmark.py`
  - `documentation/test-runs/INTENT_BENCHMARK_BASELINE.md`
- Steps:
  1. Lege einen JSONL-Korpus mit mindestens 80 Benchmark-Cases an und decke die Cluster Contact fact-telling, Contact recall, Pet-owner bridge, Calendar vs shopping sowie die weiteren in Intent-Spec `§4.5` genannten Mindestcluster ab.
  2. Definiere pro Case erwartete Intent-Signale und verbotene Fehlrouten, sodass Contact / Pet / Recall / Calendar separat auswertbar sind.
  3. Implementiere einen lokalen Runner fuer die bestehende Intent-Engine, der pro Cluster und gesamt Accuracy sowie Falllisten fuer Fehlschlaege ausgibt, ohne LLM-Calls auszufuehren.
  4. Ergaenze eine pytest-Suite, die den Korpus validiert, den Runner CI-faehig ausfuehrt und die Mindestcluster-Groessen sowie Report-Erzeugung absichert.
  5. Schreibe den Baseline-Report nach `documentation/test-runs/INTENT_BENCHMARK_BASELINE.md` mit getrennten Teilmengen fuer Contact, Pet, Recall und Calendar.
- Acceptance Criteria:
  - `documentation/test-runs/INTENT_BENCHMARK_BASELINE.md` existiert.
  - Die Benchmark-Suite enthaelt mindestens 80 Faelle und weist Contact / Pet / Recall / Calendar getrennt aus.
  - `python -m pytest backend/tests/test_intent_benchmark.py -q` ist gruen und benoetigt keine externen Provider.
  - `python -m backend.scripts.run_intent_benchmark --write-baseline` erzeugt einen deterministischen lokalen Report auf Basis der aktuellen Intent-Engine.
  - Die Arbeit aendert keine Intent-Engine-Logik.
- Tests:
  - `python -m pytest backend/tests/test_intent_benchmark.py -q`
  - `python -m backend.scripts.run_intent_benchmark --write-baseline`
  - `python -m py_compile backend/scripts/run_intent_benchmark.py backend/tests/test_intent_benchmark.py`
- Model: 5.4
- Reason:
  - Produktnaher, aber eng begrenzter Mess-Slice mit klarer Artefakt- und Testoberflaeche im bestehenden warmen Janus-Kontext.
