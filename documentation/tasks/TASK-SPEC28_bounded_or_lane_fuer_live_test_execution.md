TASK-SPEC28
- Source Spec: `documentation/SPEC/28_bounded_or_lane_fuer_live_test_execution.md`
- Backlog Item: `BACKLOG-118`
- Feature: Bounded OR Lane fuer LIVE_TEST_EXECUTION
- Generated At: 2026-07-01

## Generated Tasks

### TASK-SPEC28.1 Add bounded eligibility and visible operator gate for local LIVE_TEST_EXECUTION retests
- Status: DONE
- Completed: 2026-07-05
- Ziel:
  - Erweitere den bestehenden `janus-test-pipeline`-Einstieg so, dass nur klar geeignete lokale `LIVE_TEST_EXECUTION`-Slices eine sichtbare Wahl `1 = Codex` / `2 = OR` erhalten.
- Scope:
  - Nur Eligibility-, Sichtbarkeits- und Gate-Integration fuer lokale Live-Retests im bestehenden Testpipeline-Einstieg. Keine OR-Ausfuehrung, keine Auth-Mechanik und keine breite Aktivierung fuer andere Testpfade.
- Files:
  - `documentation/codex/skills/janus-test-pipeline/SKILL.md`
  - `documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py`
  - `documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py`
  - `documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py`
  - `documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py`
- Steps:
  1. Definiere eine fail-closed Eligibility-Regel fuer lokale, bounded `LIVE_TEST_EXECUTION`-Retests.
  2. Binde die sichtbare Codex-vs-OR-Wahl nur an diese eligible Retest-Slices.
  3. Stelle sicher, dass ungeeignete, zu breite oder nicht lokal gebundene Live-Retests weiterhin Codex-only bleiben.
  4. Halte Skill-Wording, Runner-Einstieg und Gate-Ausgabe konsistent.
- Acceptance Criteria:
  - Ein eligible lokaler `LIVE_TEST_EXECUTION`-Retest zeigt die Wahl `1 = Codex` / `2 = OR`.
  - Ein nicht eligible oder zu breiter Live-Retest zeigt keine normale OR-Wahl.
  - Die Sichtbarkeit impliziert weder globale Live-Test-Freigabe noch broad delegated authority.
  - Skill-Text und technischer Gate-Einstieg beschreiben denselben bounded Lane-Fall.
- Tests:
  - `python -m pytest documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py -q`
  - `python -m pytest documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py -q -k "live or gate or eligibility"`
  - `python -m py_compile documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py`
- Model: 5.4
- Reason:
  - Die Sichtbarkeit muss vor jeder Ausfuehrung klar und fail-closed sein; ohne diese Slice wuerde die Lane schon am Einstieg unsauber oder zu breit werden.
- Preimplementation Check: PASS - `documentation/tasks/TASK-SPEC28.1_preimplementation_check.md`
- Execution Result: PASS/HANDOFF - `documentation/tasks/TASK-SPEC28.1_execution_result.md`
- Audit Package: `documentation/tasks/TASK-SPEC28.1_AUDIT_PACKAGE.md`
- Final Audit: PASS - `documentation/tasks/TASK-SPEC28.1_final_audit.md`
- Documentation Update: PASS - `documentation/tasks/TASK-SPEC28.1_documentation_update.md`
- Completion Evidence:
  - `documentation/codex/model-routing/sidecar-runs/TP-LIVE-GATE-AUDIT-PROMPT-001/operator_choice_prompt.json`
  - `documentation/codex/model-routing/sidecar-runs/TP-LIVE-GATE-AUDIT-PROMPT-002/operator_choice_prompt.json`

### TASK-SPEC28.2 Define the bounded local live-retest worker contract, auth handling, and evidence outputs
- Status: DONE
- Completed: 2026-07-05
- Ziel:
  - Schaffe einen bounded Worker-Vertrag fuer lokale Live-Retests inklusive erlaubter Schritte, lokaler Auth-Behandlung und review-faehiger Evidenzartefakte.
- Scope:
  - Nur der bounded Vertragsrahmen fuer `api/health`, Chat-Erzeugung, gebundene Prompt-Laeufe und Evidenzsammlung im lokalen Dev-Pfad. Keine finale PASS/FAIL-Autoritaet und keine generische Shell-Freiheit.
- Files:
  - `documentation/codex/skills/janus-test-pipeline/SKILL.md`
  - `documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py`
  - `documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py`
  - `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`
  - `documentation/codex/model-routing/strong-or-fixtures/`
  - `documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py`
- Steps:
  1. Definiere einen allowlisted Worker-Vertrag fuer lokale Health-/Chat-/Prompt-/Evidenz-Schritte.
  2. Binde den lokalen Dev-API-Auth-/Header-Pfad so ein, dass die Lane technisch funktioniert, ohne versionierte Secrets in Artefakte zu schreiben.
  3. Stelle sicher, dass der Worker nur review-faehige Evidenz und keinen delegierten Abschlussanspruch zurueckgibt.
  4. Halte Dispatcher-, Worker- und Fixture-Vertrag auf denselben bounded Lane-Fall ausgerichtet.
- Acceptance Criteria:
  - Der Worker-Vertrag erlaubt nur die fuer den lokalen Live-Retest noetigen bounded Schritte.
  - Lokale Auth-/Header-Unterstuetzung bleibt bounded und leakt keine versionierten Secrets in Repo-Artefakte.
  - Die Rueckgabe an Codex enthaelt review-faehige Evidenz und keinen finalen PASS-/Release-/Routing-Anspruch.
  - Der Vertrag aktiviert keine generische Delegation beliebiger Live-Tests.
- Tests:
  - `python -m pytest documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py -q`
  - `python -m py_compile documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`
  - fixture-based contract check for the bounded local live-retest package
- Model: 5.4
- Reason:
  - Der eigentliche Sicherheits- und Governance-Kern der Lane liegt im Worker- und Evidenzvertrag, nicht nur im sichtbaren Gate.
- Preimplementation Check: PASS - `documentation/tasks/TASK-SPEC28.2_preimplementation_check.md`
- Execution Result: PASS/HANDOFF - `documentation/tasks/TASK-SPEC28.2_execution_result.md`
- Audit Package: `documentation/tasks/TASK-SPEC28.2_AUDIT_PACKAGE.md`
- Final Audit: PASS WITH FIXES - `documentation/tasks/TASK-SPEC28.2_final_audit.md`
- Documentation Update: PASS - `documentation/tasks/TASK-SPEC28.2_documentation_update.md`
- Completion Evidence:
  - `documentation/codex/model-routing/strong-or-fixtures/strong_live_retest_worker_package_2026-07-05.json`
  - `documentation/codex/model-routing/strong-or-fixtures/strong_live_retest_evidence_fixture_2026-07-05.md`
  - `documentation/codex/model-routing/sidecar-runs/TP-LIVE-RETEST-AUDIT-PROMPT-002/operator_choice_prompt.json`

### TASK-SPEC28.3 Add regression coverage and Codex-owned accept/reject handoff for delegated live retests
- Ziel:
  - Sichere die neue Lane mit Regressionen und einem klaren Codex-owned Abschlussmodell ab, damit sichtbare Delegation nicht in implizite Abschlussautoritaet kippt.
- Scope:
  - Nur Regressionen, Review-Handoff und fail-closed Accept/Reject-Verhalten fuer die neue lokale Live-Retest-Lane. Keine neuen Produktfeatures und keine broad Registry-Ausweitung.
- Files:
  - `documentation/codex/model-routing/tests/test_assistive_or_review_consumer_integration.py`
  - `documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py`
  - `documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py`
  - `documentation/codex/skills/janus-test-pipeline/SKILL.md`
  - `documentation/codex/model-routing/or_everyday_operator_registry_summary_2026-06-24.md`
- Steps:
  1. Ergaenze Positiv- und Negativregressionen fuer eligible und nicht eligible lokale Live-Retests.
  2. Sichere ab, dass unvollstaendige Evidenz, fehlende Auth-Voraussetzungen oder zu breite Worker-Pakete fail-closed bei Codex landen.
  3. Halte den sichtbaren Lane-Nachweis und den Codex-owned Accept/Reject-Handoff konsistent.
  4. Stelle sicher, dass die Lane nicht versehentlich als globale OR-Live-Test-Freigabe in Registry- oder Summary-Artefakten auftaucht.
- Acceptance Criteria:
  - Eligible und nicht eligible lokale Live-Retests sind durch Regressionen klar voneinander getrennt.
  - Fehlende oder unsaubere Evidenz fuehrt zu einem lokalen Codex-owned Reject oder Fallback.
  - Die neue Lane behauptet nirgends delegierte finale PASS-/Release-/Routing-Hoheit.
  - Registry-/Summary-Artefakte ueberzeichnen die Lane nicht als globale Live-Test-Freigabe.
- Tests:
  - `python -m pytest documentation/codex/model-routing/tests -q -k "live_retest or accept or reject or fallback"`
  - `python -m pytest documentation/codex/model-routing/tests/test_assistive_or_review_consumer_integration.py -q`
  - `python -m py_compile documentation/codex/model-routing/tests/test_assistive_or_review_consumer_integration.py`
- Model: 5.4
- Reason:
  - Der Nutzerwert der Lane haengt am vertrauenswuerdigen Abschluss; ohne klaren Codex-owned Reject-/Fallback-Schutz waere der sichtbare OR-Live-Retest nur halb abgesichert.

@janus-task-breakdown
Spec: documentation/SPEC/28_bounded_or_lane_fuer_live_test_execution.md
Task: documentation/tasks/TASK-SPEC28_bounded_or_lane_fuer_live_test_execution.md
Backlog Item: BACKLOG-118
Target Task: TASK-SPEC28.1
Mode: TASK_REFINEMENT
Execution Model: 5.4
Rules: USE_SPEC_AND_TASK_AS_SOURCE_OF_TRUTH_NO_IMPLEMENTATION_RELEASE_ONE_TARGET_TASK
Expected Output: TASK_REFINED_PLUS_PRECHECK_HANDOFF
