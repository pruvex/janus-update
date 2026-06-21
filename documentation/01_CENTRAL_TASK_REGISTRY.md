# Central Task Registry

This registry tracks feature tasks, test validations, and pipeline runs.

## Spec Closures

### TASK-SPEC22.4 - Add file-first telemetry, actual-cost closeout, and healthcheck visibility for the dedicated Dev-workhorse path

- **Status**: DONE
- **Final Audit**: `documentation/tasks/TASK-SPEC22.4_final_audit.md` (PASS)
- **Spec**: `documentation/SPEC/Spec Done/22_operator_gesteuerter_or_arbeitspferd_produktivmodus_fuer_dev_arbeit.md`
- **Parent Task**: `documentation/tasks/TASK-SPEC22_operator_gesteuerter_or_arbeitspferd_produktivmodus_fuer_dev_arbeit.md`
- **Task Breakdown**: `documentation/tasks/TASK-SPEC22.4_task_breakdown.md`
- **Precheck**: `documentation/tasks/TASK-SPEC22.4_preimplementation_check.md`
- **Execution Result**: `documentation/tasks/TASK-SPEC22.4_execution_result.md`
- **Audit Package**: `documentation/tasks/TASK-SPEC22.4_AUDIT_PACKAGE.md`
- **Validation**: `TASK-SPEC22.4` schliesst den vierten und letzten eng gebundenen Spec-22-Slice als operationalen Closeout fuer den dedizierten Dev-workhorse-Pfad ab. Der `codex_dev_workhorse_runner.py` schreibt jetzt bounded file-first Laufartefakte, eine Session-Telemetriezeile, eine wahrheitsgetreue Actual-Cost- oder Missing-Usage-Abschlussmeldung und eine lokale Healthcheck-Zusammenfassung fuer den neuen Pfad, waehrend die bereits versiegelten Eligibility-, Gate- und Delegationsgrenzen aus `TASK-SPEC22.1` bis `TASK-SPEC22.3` unveraendert bleiben. Final Audit PASS mit fokussierter Runner-, Dispatcher-, Compile- und Validator-Evidenz. Spec 22 ist damit insgesamt DONE, ohne globale OR-Freigabe, Produktionsrouting oder kanonische Routing-Tabellen-Aktivierung.
- **Changed Files**: `documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py`, `documentation/codex/skills/janus-health-check/scripts/health_snapshot.py`, `documentation/codex/model-routing/tests/test_codex_dev_workhorse_runner.py`, `documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md`, `documentation/tasks/TASK-SPEC22.4_execution_result.md`, `documentation/tasks/TASK-SPEC22.4_AUDIT_PACKAGE.md`, `documentation/tasks/TASK-SPEC22.4_final_audit.md`, `documentation/SPEC/Spec Done/22_operator_gesteuerter_or_arbeitspferd_produktivmodus_fuer_dev_arbeit.md`.

### TASK-SPEC22.3 - Wire bounded delegated triage and write-candidate execution behind the dedicated runner with Codex-owned acceptance

- **Status**: DONE
- **Final Audit**: `documentation/tasks/TASK-SPEC22.3_final_audit.md` (PASS)
- **Spec**: `documentation/SPEC/Spec Done/22_operator_gesteuerter_or_arbeitspferd_produktivmodus_fuer_dev_arbeit.md`
- **Parent Task**: `documentation/tasks/TASK-SPEC22_operator_gesteuerter_or_arbeitspferd_produktivmodus_fuer_dev_arbeit.md`
- **Task Breakdown**: `documentation/tasks/TASK-SPEC22.3_task_breakdown.md`
- **Precheck**: `documentation/tasks/TASK-SPEC22.3_preimplementation_check.md`
- **Execution Result**: `documentation/tasks/TASK-SPEC22.3_execution_result.md`
- **Audit Package**: `documentation/tasks/TASK-SPEC22.3_AUDIT_PACKAGE.md`
- **Validation**: `TASK-SPEC22.3` schliesst den dritten eng gebundenen Spec-22-Slice als echten bounded Delegations-Runtime-Pfad hinter dem sichtbaren Dev-Workhorse-Gate ab. Der dedizierte `codex_dev_workhorse_runner.py` routet `2 = OR` jetzt kontrolliert in genau die drei erlaubten Klassen `test_result_triage_review`, `execution_patch_candidate` und `execution_write_apply_candidate`, ohne einen zweiten Runtime-Seam einzufuehren oder bestehende Janus-Workflows implizit zu erweitern. Final Audit PASS mit fokussierter Runner-, Compile- und Validator-Evidenz. Spec 22 bleibt dabei bewusst offen, weil Actual-Cost-Closeout, file-first Telemetrie und Healthcheck-Sichtbarkeit erst in `TASK-SPEC22.4` folgen.
- **Changed Files**: `documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py`, `documentation/codex/model-routing/tests/test_codex_dev_workhorse_runner.py`, `documentation/tasks/TASK-SPEC22.3_execution_result.md`, `documentation/tasks/TASK-SPEC22.3_AUDIT_PACKAGE.md`, `documentation/tasks/TASK-SPEC22.3_final_audit.md`.

### TASK-SPEC22.2 - Create the operator-invoked Dev-workhorse runner with mandatory Codex-vs-OR gate

- **Status**: DONE
- **Final Audit**: `documentation/tasks/TASK-SPEC22.2_final_audit.md` (PASS)
- **Spec**: `documentation/SPEC/Spec Done/22_operator_gesteuerter_or_arbeitspferd_produktivmodus_fuer_dev_arbeit.md`
- **Parent Task**: `documentation/tasks/TASK-SPEC22_operator_gesteuerter_or_arbeitspferd_produktivmodus_fuer_dev_arbeit.md`
- **Task Breakdown**: `documentation/tasks/TASK-SPEC22.2_task_breakdown.md`
- **Precheck**: `documentation/tasks/TASK-SPEC22.2_preimplementation_check.md`
- **Execution Result**: `documentation/tasks/TASK-SPEC22.2_execution_result.md`
- **Audit Package**: `documentation/tasks/TASK-SPEC22.2_AUDIT_PACKAGE.md`
- **Validation**: `TASK-SPEC22.2` schliesst den zweiten eng gebundenen Spec-22-Slice als sichtbaren operator-invoked Entry-Runner fuer den neuen produktiven Dev-Workhorse-Pfad ab. Der dedizierte `codex_dev_workhorse_runner.py` zeigt fuer in-scope Aufrufe jetzt kontrolliert `1 = Codex` und `2 = OR` samt ausgewaehltem OR-Modell, Kostenschaetzung und Confidence-Hinweis; fehlen Pflichtdaten wie Estimate oder Confidence, faellt der Pfad deterministisch vor jeder Wrapper- oder Dispatcher-Invocation auf einen Codex-only Ausgang zurueck. Final Audit PASS mit fokussierter Runner-, Eligibility-, Compile- und Validator-Evidenz. Spec 22 bleibt dabei bewusst offen, weil delegierte Ausfuehrung sowie Telemetrie erst in `TASK-SPEC22.3` und `TASK-SPEC22.4` folgen.
- **Changed Files**: `documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py`, `documentation/codex/model-routing/tests/test_codex_dev_workhorse_runner.py`, `documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md`, `documentation/tasks/TASK-SPEC22.2_execution_result.md`, `documentation/tasks/TASK-SPEC22.2_AUDIT_PACKAGE.md`, `documentation/tasks/TASK-SPEC22.2_final_audit.md`.

### TASK-SPEC22.1 - Define the dedicated Dev-workhorse path contract and keep all other workflows Codex-only

- **Status**: DONE
- **Final Audit**: `documentation/tasks/TASK-SPEC22.1_final_audit.md` (PASS)
- **Spec**: `documentation/SPEC/Spec Done/22_operator_gesteuerter_or_arbeitspferd_produktivmodus_fuer_dev_arbeit.md`
- **Parent Task**: `documentation/tasks/TASK-SPEC22_operator_gesteuerter_or_arbeitspferd_produktivmodus_fuer_dev_arbeit.md`
- **Task Breakdown**: `documentation/tasks/TASK-SPEC22.1_task_breakdown.md`
- **Precheck**: `documentation/tasks/TASK-SPEC22.1_preimplementation_check.md`
- **Execution Result**: `documentation/tasks/TASK-SPEC22.1_execution_result.md`
- **Audit Package**: `documentation/tasks/TASK-SPEC22.1_AUDIT_PACKAGE.md`
- **Validation**: `TASK-SPEC22.1` schliesst den ersten eng gebundenen Spec-22-Slice als reinen Boundary-Contract fuer den neuen `productive_dev_workhorse_path` ab. Nur die drei explizit allowlisteten bounded Dev-Klassen koennen innerhalb dieses neuen Pfads ueberhaupt OR-eligible werden; alle bestehenden Janus- und Codex-Workflows ausserhalb dieses Pfads bleiben deterministisch Codex-only oder vor dem OR-Gate blockiert. Der Re-Audit-Fix haertet die Kostengrenze zusaetzlich gegen negative, nicht-finite und nicht-numerische `estimated_or_cost`-Werte, sodass fehlerhafte Kostenwerte weder den Gate-Pfad umgehen noch einen unkontrollierten Crash ausloesen. Final Audit PASS mit fokussierter Unit-, Compile-, Probe- und Validator-Evidenz. Spec 22 bleibt dabei bewusst offen, weil `TASK-SPEC22.2` bis `TASK-SPEC22.4` weiterhin ausstehen.
- **Changed Files**: `documentation/codex/model-routing/config/bounded_or_worker_eligibility_2026-06-17.json`, `documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py`, `documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py`, `documentation/tasks/TASK-SPEC22.1_execution_result.md`, `documentation/tasks/TASK-SPEC22.1_AUDIT_PACKAGE.md`, `documentation/tasks/TASK-SPEC22.1_final_audit.md`.

### TASK-SPEC21.4 - Integrate the bounded OR worker path into janus-debug and janus-test-pipeline without widening the pilot scope

- **Status**: DONE
- **Final Audit**: `documentation/tasks/TASK-SPEC21.4_final_audit.md` (PASS)
- **Spec**: `documentation/SPEC/Spec Done/21_assisted_or_workhorse_mode_for_janus_skills.md`
- **Parent Task**: `documentation/tasks/TASK-SPEC21_assisted_or_workhorse_mode_for_janus_skills.md`
- **Task Breakdown**: `documentation/tasks/TASK-SPEC21.4_task_breakdown.md`
- **Precheck**: `documentation/tasks/TASK-SPEC21.4_preimplementation_check.md`
- **Execution Result**: `documentation/tasks/TASK-SPEC21.4_execution_result.md`
- **Audit Package**: `documentation/tasks/TASK-SPEC21.4_AUDIT_PACKAGE.md`
- **Validation**: `TASK-SPEC21.4` schliesst den vierten und letzten gebundenen Spec-21-Slice mit der alltagstauglichen Consumer-Integration fuer genau zwei freigegebene Pilotpfade ab. `janus-debug` kann den bounded OR-Arbeitspferd-Pfad jetzt nur fuer `debug_hypothesis_review` anbieten, `janus-test-pipeline` nur fuer `test_result_triage_review`; beide behalten ausserhalb dieser Klassen den Codex-only Pfad. Final Audit PASS mit fokussierter Consumer-, Capture- und Eligibility-Evidenz, installierter Skill-Hash-Paritaet sowie reproduzierbarer lokaler Fixture-Sichtbarkeit fuer Gate, Kosten, Confidence und den nicht-finalen Codex-owned Outcome. Damit ist Spec 21 insgesamt abgeschlossen, ohne Produktionsrouting, globale OR-Freigabe oder Scope-Erweiterung ueber die zwei Pilotklassen hinaus.
- **Changed Files**: `documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py`, `documentation/codex/model-routing/scripts/codex_test_result_triage_review_runner.py`, `documentation/codex/model-routing/scripts/generate_task_spec21_4_skill_context_evidence.py`, `documentation/codex/model-routing/tests/test_assistive_or_review_consumer_integration.py`, `documentation/codex/skills/janus-debug/SKILL.md`, `documentation/codex/skills/janus-test-pipeline/SKILL.md`, `documentation/tasks/TASK-SPEC21.4_skill_context_evidence.md`, `documentation/tasks/TASK-SPEC21.4_execution_result.md`, `documentation/tasks/TASK-SPEC21.4_AUDIT_PACKAGE.md`, `documentation/tasks/TASK-SPEC21.4_final_audit.md`, `documentation/SPEC/Spec Done/21_assisted_or_workhorse_mode_for_janus_skills.md`.

### TASK-SPEC21.3 - Add file-first OR capture, telemetry, and healthcheck ingestion for accepted and rejected pilot runs

- **Status**: DONE
- **Final Audit**: `documentation/tasks/TASK-SPEC21.3_final_audit.md` (PASS)
- **Spec**: `documentation/SPEC/Spec Done/21_assisted_or_workhorse_mode_for_janus_skills.md`
- **Parent Task**: `documentation/tasks/TASK-SPEC21_assisted_or_workhorse_mode_for_janus_skills.md`
- **Task Breakdown**: `documentation/tasks/TASK-SPEC21.3_task_breakdown.md`
- **Precheck**: `documentation/tasks/TASK-SPEC21.3_preimplementation_check.md`
- **Execution Result**: `documentation/tasks/TASK-SPEC21.3_execution_result.md`
- **Audit Package**: `documentation/tasks/TASK-SPEC21.3_AUDIT_PACKAGE.md`
- **Validation**: `TASK-SPEC21.3` schliesst den dritten gebundenen Spec-21-Slice mit file-first Capture, truthy Telemetry-Finalisierung und lokaler Healthcheck-Ingestion fuer die zwei bereits freigegebenen Pilotklassen ab. Akzeptierte, fehlende-Usage-, Wrapper-Failure- und Healthcheck-Failure-Pfade hinterlassen jetzt jeweils genau eine wahrheitsgetreue durable Telemetriezeile; Wrapper-Failure erzeugt direkt eine rejected fallback row, und Healthcheck-Failure rewritet dieselbe JSONL-Datei auf den finalen `FAIL`-/`CODEX_PREFERRED`-Zustand. Final Audit PASS mit fokussierter Capture-, Eligibility-, Compile-, DAILY-Healthcheck- und Validator-Evidenz. Spec 21 bleibt dabei bewusst in Arbeit, weil `TASK-SPEC21.4` weiterhin offen ist.
- **Changed Files**: `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`, `documentation/codex/model-routing/tests/test_assistive_or_review_capture_dispatcher.py`, `documentation/tasks/TASK-SPEC21.3_AUDIT_PACKAGE.md`, `documentation/tasks/TASK-SPEC21.3_execution_result.md`, `documentation/tasks/TASK-SPEC21.3_final_audit.md`.

### TASK-SPEC21.2 - Normalize the operator gate with mandatory cost and confidence display

- **Status**: DONE
- **Final Audit**: `documentation/tasks/TASK-SPEC21.2_final_audit.md` (PASS)
- **Spec**: `documentation/SPEC/Spec Done/21_assisted_or_workhorse_mode_for_janus_skills.md`
- **Parent Task**: `documentation/tasks/TASK-SPEC21_assisted_or_workhorse_mode_for_janus_skills.md`
- **Task Breakdown**: `documentation/tasks/TASK-SPEC21.2_task_breakdown.md`
- **Precheck**: `documentation/tasks/TASK-SPEC21.2_preimplementation_check.md`
- **Execution Result**: `documentation/tasks/TASK-SPEC21.2_execution_result.md`
- **Audit Package**: `documentation/tasks/TASK-SPEC21.2_AUDIT_PACKAGE.md`
- **Validation**: `TASK-SPEC21.2` schliesst den zweiten gebundenen Spec-21-Slice mit einer sichtbaren, normalisierten Operator-Auswahl fuer die zwei bereits freigegebenen Pilotklassen ab. Das gemeinsame Gate zeigt jetzt konsistent `1 = Codex` und `2 = OR-Arbeitspferd` und verlangt vor jeder OR-Wahl ein ausgewaehltes OR-Modell, eine Kostenschaetzung und einen Confidence-Hinweis; fehlen diese Pflichtdaten, faellt der Pfad deterministisch auf Codex-only zurueck. Final Audit PASS mit fokussierter Unit-, Compile-, Direktprobe- und Validator-Evidenz. Spec 21 bleibt dabei bewusst in Arbeit, weil `TASK-SPEC21.3` und `TASK-SPEC21.4` noch offen sind.
- **Changed Files**: `documentation/codex/model-routing/scripts/bounded_or_worker_gate_prompt.py`, `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`, `documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py`, `documentation/codex/model-routing/scripts/codex_test_result_triage_review_runner.py`, `documentation/codex/model-routing/tests/test_bounded_or_worker_gate_prompt.py`, `documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py`, `documentation/codex/skills/janus-debug/SKILL.md`, `documentation/codex/skills/janus-test-pipeline/SKILL.md`, `documentation/tasks/TASK-SPEC21.2_AUDIT_PACKAGE.md`, `documentation/tasks/TASK-SPEC21.2_execution_result.md`, `documentation/tasks/TASK-SPEC21.2_final_audit.md`.

### TASK-SPEC21.1 - Enforce a locally testable OR eligibility and context-redaction gate for the pilot skills

- **Status**: DONE
- **Final Audit**: `documentation/tasks/TASK-SPEC21.1_final_audit.md` (PASS)
- **Spec**: `documentation/SPEC/Spec Done/21_assisted_or_workhorse_mode_for_janus_skills.md`
- **Parent Task**: `documentation/tasks/TASK-SPEC21_assisted_or_workhorse_mode_for_janus_skills.md`
- **Task Breakdown**: `documentation/tasks/TASK-SPEC21.1_task_breakdown.md`
- **Precheck**: `documentation/tasks/TASK-SPEC21.1_preimplementation_check.md`
- **Execution Result**: `documentation/tasks/TASK-SPEC21.1_execution_result.md`
- **Audit Package**: `documentation/tasks/TASK-SPEC21.1_AUDIT_PACKAGE.md`
- **Validation**: `TASK-SPEC21.1` schliesst den ersten gebundenen Spec-21-Slice mit einer lokal testbaren Pilotgrenze vor jedem externen OR-Request. Der gemeinsame Dispatcher akzeptiert nur noch `janus-debug/debug_hypothesis_review` und `janus-test-pipeline/test_result_triage_review`, blockiert Legacy-Klassen deterministisch vor dem Delegationspfad und erzwingt die Request-Redaction-/Allowlist-Grenze vor jedem moeglichen OR-Dispatch. Final Audit PASS mit fokussierter Unit-, Compile-, Probe-, CLI-Fallback- und Validator-Evidenz. Spec 21 bleibt dabei bewusst in Arbeit, weil `TASK-SPEC21.2` bis `TASK-SPEC21.4` noch offen sind.
- **Changed Files**: `documentation/codex/model-routing/config/bounded_or_worker_eligibility_2026-06-17.json`, `documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py`, `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`, `documentation/codex/model-routing/scripts/codex_structured_action_request_builder.py`, `documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py`, `documentation/tasks/TASK-SPEC21.1_AUDIT_PACKAGE.md`, `documentation/tasks/TASK-SPEC21.1_execution_result.md`, `documentation/tasks/TASK-SPEC21.1_final_audit.md`.

### TASK-SPEC20.1 - Establish separate top-level Dev governance home

- **Status**: DONE
- **Final Audit**: `documentation/tasks/TASK-SPEC20.1_final_audit.md` (PASS)
- **Spec**: `documentation/SPEC/Spec Done/20_separate_dev_or_infrastructure_governance.md`
- **Parent Task**: `documentation/tasks/TASK-SPEC20_separate_dev_or_infrastructure_governance.md`
- **Task Breakdown**: `documentation/tasks/TASK-SPEC20.1_task_breakdown.md`
- **Precheck**: `documentation/tasks/TASK-SPEC20.1_preimplementation_check.md`
- **Execution Result**: `documentation/tasks/TASK-SPEC20.1_execution_result.md`
- **Audit Package**: `documentation/tasks/TASK-SPEC20.1_AUDIT_PACKAGE.md`
- **Validation**: `TASK-SPEC20.1` etabliert den ersten getrennten Dev-Governance-Home-Slice fuer die spaetere strikte Trennung von Janus-Produktarbeit und Dev- beziehungsweise OR-Infrastrukturarbeit. Der neue Top-Level-Bereich `development/` liegt ausserhalb von `documentation/` und fuehrt mit `README`, `DEV_STATE` und `DEV_BACKLOG` erstmals eine eigene Source-of-Truth fuer Infrastrukturarbeit ein, ohne bereits Janus-Backlog-Migration oder Janus-Governance-Haertung vorwegzunehmen. Final Audit PASS mit fokussierter Diff-, Konsistenz- und Validator-Evidenz.
- **Changed Files**: `development/README.md`, `development/DEV_STATE.md`, `development/DEV_BACKLOG.md`, `documentation/tasks/TASK-SPEC20.1_AUDIT_PACKAGE.md`, `documentation/tasks/TASK-SPEC20.1_execution_result.md`, `documentation/tasks/TASK-SPEC20.1_final_audit.md`, `documentation/SPEC/Spec Done/20_separate_dev_or_infrastructure_governance.md`.

### TASK-SPEC19 - Bounded OR Worker Mode for Janus Skills

- **Status**: DONE
- **Final Audit**: `documentation/tasks/TASK-SPEC19_final_audit.md` (PASS)
- **Spec**: `documentation/SPEC/Spec Done/19_bounded_or_worker_mode_for_janus_skills.md`
- **Task**: `documentation/tasks/TASK-SPEC19_bounded_or_worker_mode_for_janus_skills.md`
- **Execution Results**: `documentation/tasks/TASK-SPEC19.1_execution_result.md`, `documentation/tasks/TASK-SPEC19.2_execution_result.md`, `documentation/tasks/TASK-SPEC19.3_execution_result.md`
- **Validation**: Der bounded OR worker Rollout wurde mit drei klar getrennten Slices abgeschlossen: gemeinsame Eligibility-Grenze, einheitliche Gate-Ausgabe und Codex-owned Post-Run-Accept/Reject/Fallback-Normalisierung. Final Audit PASS mit kompakter Audit-Package-Evidenz und gruenen lokalen Checks ohne Produktionsrouting.
- **Changed Files**: `documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py`, `documentation/codex/model-routing/config/bounded_or_worker_eligibility_2026-06-17.json`, `documentation/codex/model-routing/scripts/bounded_or_worker_gate_prompt.py`, `documentation/codex/model-routing/scripts/bounded_or_worker_outcome.py`, `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`, `documentation/codex/model-routing/scripts/doc_skill_mini_fixed_or_live_runner.py`, `documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py`, `documentation/codex/model-routing/scripts/codex_test_result_triage_review_runner.py`, `documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py`, `documentation/tasks/TASK-SPEC19.1_execution_result.md`, `documentation/tasks/TASK-SPEC19.2_execution_result.md`, `documentation/tasks/TASK-SPEC19.3_execution_result.md`, `documentation/tasks/TASK-SPEC19_AUDIT_PACKAGE.md`, `documentation/tasks/TASK-SPEC19_final_audit.md`, `documentation/SPEC/Spec Done/19_bounded_or_worker_mode_for_janus_skills.md`.

### TASK-SPEC19.4 - Janus-quickchange as the first everyday bounded OR worker consumer

- **Status**: DONE
- **Final Audit**: `documentation/tasks/TASK-SPEC19.4_final_audit.md` (PASS)
- **Spec**: `documentation/SPEC/Spec Done/19_bounded_or_worker_mode_for_janus_skills.md`
- **Parent Task**: `documentation/tasks/TASK-SPEC19_bounded_or_worker_mode_for_janus_skills.md`
- **Task Breakdown**: `documentation/tasks/TASK-SPEC19.4_task_breakdown.md`
- **Precheck**: `documentation/tasks/TASK-SPEC19.4_preimplementation_check.md`
- **Execution Result**: `documentation/tasks/TASK-SPEC19.4_execution_result.md`
- **Audit Package**: `documentation/tasks/TASK-SPEC19.4_AUDIT_PACKAGE.md`
- **Validation**: `TASK-SPEC19.4` seals the first real everyday `janus-quickchange` bounded OR worker consumer on top of the already finished shared foundation. The visible operator choice is consistently `1 = Codex` and `2 = OpenRouter`, quickchange patch-review and write-apply remain explicitly bounded plus Codex-owned at the final accept-or-reject seam, and focused local automated evidence passed without widening into production routing, broad execution delegation, or non-quickchange rollout.
- **Changed Files**: `documentation/codex/skills/janus-quickchange/SKILL.md`, `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`, `documentation/codex/model-routing/scripts/quickchange_sidecar_write_pilot_runner.py`, `documentation/codex/model-routing/scripts/codex_quickchange_write_apply_runner.py`, `documentation/codex/model-routing/tests/test_quickchange_live_operator_path.py`, `documentation/codex/model-routing/tests/test_quickchange_sidecar_write_pilot_runner.py`, `documentation/tasks/TASK-SPEC19_bounded_or_worker_mode_for_janus_skills.md`, `documentation/tasks/TASK-SPEC19.4_task_breakdown.md`, `documentation/tasks/TASK-SPEC19.4_preimplementation_check.md`, `documentation/tasks/TASK-SPEC19.4_execution_result.md`, `documentation/tasks/TASK-SPEC19.4_AUDIT_PACKAGE.md`, `documentation/tasks/TASK-SPEC19.4_final_audit.md`.

### TASK-SPEC18 - Bounded Execution Write Apply Candidate for OR Sidecar Delegation

- **Status**: DONE
- **Final Audit**: `documentation/tasks/TASK-SPEC18_final_audit.md` (PASS)
- **Spec**: `documentation/SPEC/Spec Done/18_bounded_execution_write_apply_candidate_for_or_sidecar_delegation.md`
- **Task**: `documentation/tasks/TASK-SPEC18_bounded_execution_write_apply_candidate_for_or_sidecar_delegation.md`
- **Execution Results**: `documentation/tasks/TASK-SPEC18.1_execution_result.md`, `documentation/tasks/TASK-SPEC18.2_execution_result.md`, `documentation/tasks/TASK-SPEC18.3_execution_result.md`
- **Validation**: Der erste gebundene delegated write-apply candidate ist jetzt final auditiert und abgeschlossen. Der Pfad erzwingt exakte editable-path Allowlists plus Touched-File-Cap am Einstieg, verlangt reviewbare `git_diff.patch`- und `changed_files.txt`-Artefakte und akzeptiert nur Kandidaten mit vorhandener lokaler `validation_summary.json` und explizit Codex-owned finalem Accept-or-Reject-Ausgang. Final Audit PASS mit fokussierter CLI-, Pytest- und Validator-Evidenz ueber alle drei gebundenen Haertungs-Slices.
- **Changed Files**: `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`, `documentation/codex/model-routing/scripts/codex_structured_action_request_builder.py`, `documentation/codex/model-routing/scripts/codex_execution_write_apply_candidate_runner.py`, `documentation/codex/model-routing/tests/test_bounded_write_candidate_entry_gate.py`, `documentation/codex/model-routing/tests/test_bounded_write_candidate_artifact_capture.py`, `documentation/codex/model-routing/tests/test_bounded_write_candidate_validation_acceptance.py`, `documentation/tasks/TASK-SPEC18.1_execution_result.md`, `documentation/tasks/TASK-SPEC18.2_execution_result.md`, `documentation/tasks/TASK-SPEC18.3_execution_result.md`, `documentation/tasks/TASK-SPEC18_AUDIT_PACKAGE.md`, `documentation/tasks/TASK-SPEC18_final_audit.md`.

### TASK-SPEC17 - Structured Executor First Slice for OR Sidecar Delegation

- **Status**: DONE
- **Final Audit**: `documentation/tasks/TASK-SPEC17_final_audit.md` (PASS)
- **Spec**: `documentation/SPEC/Spec Done/17_structured_executor_first_slice_for_or_sidecar_delegation.md`
- **Task**: `documentation/tasks/TASK-SPEC17_structured_executor_first_slice_for_or_sidecar_delegation.md`
- **Execution Results**: `documentation/tasks/TASK-SPEC17.1_execution_result.md`, `documentation/tasks/TASK-SPEC17.2_execution_result.md`, `documentation/tasks/TASK-SPEC17.3_execution_result.md`
- **Validation**: Der erste gebundene Structured-Executor-Slice fuer die OR- oder Sidecar-Delegation ist jetzt auditiert und abgeschlossen. Der Executor nimmt strukturierte Requests deterministisch an, unterstuetzt genau den ersten `compile_testspec_to_testplan_v1`-Generatorpfad plus `validate_runner_v1`, und der Dispatcher faellt bei nicht unterstuetzten oder fehlschlagenden Generator-Review-Routen reviewbar auf `CODEX_LOCAL_FALLBACK_REQUIRED` zurueck statt hart abzubrechen. Final Audit PASS mit fokussierter CLI-, Pytest- und Validator-Evidenz.
- **Changed Files**: `documentation/codex/model-routing/scripts/codex_structured_action_executor.py`, `documentation/codex/model-routing/scripts/codex_structured_action_generator_review_runner.py`, `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`, `documentation/codex/model-routing/structured-action-fixtures/delegated_request_validate_runner_failure_2026-06-15.json`, `documentation/codex/model-routing/structured-action-fixtures/invalid_generated_runner_2026-06-15.spec.js`, `documentation/codex/model-routing/structured-action-fixtures/builder_generator_payload_compile_testspec_2026-06-15.json`, `documentation/codex/model-routing/tests/test_codex_structured_action_executor.py`, `documentation/tasks/TASK-SPEC17_AUDIT_PACKAGE.md`, `documentation/tasks/TASK-SPEC17_final_audit.md`.

### BACKLOG-110 - Kontakt-Wohnort landet als Besonderheit statt im Adressblock

- **Status**: DONE
- **Final Audit**: `documentation/test-runs/BACKLOG-110_debug_contact_apply_normalization_addendum_2026-06-14.md` (PASS)
- **Task**: `documentation/tasks/backlog_BACKLOG-110_kontakt_wohnort_landet_als_besonderheit_statt_im_adressblock.md`
- **Validation**: Der Kontaktpfad fuer `Oliver Schwab` fuehrt Wohnort-/Adressinformationen jetzt in den Adressblock statt in `Besonderheiten`, und die Pet-Details werden auf der Kontaktkarte zu kompakten Ein-Satz-Formen wie `hat einen Hund namens tasso` und `hat eine Katze` normalisiert. Live-Retest und gezielte Backend-Regressionen PASS.
- **Changed Files**: `backend/data/crud.py`, `backend/tests/test_contact_card_normalization.py`, `documentation/test-runs/BACKLOG-110_debug_contact_apply_normalization_addendum_2026-06-14.md`, `documentation/ai/CURRENT_STATE.md`, `documentation/codex/SKILL_USAGE_LOG.md`.

### TASK-SPEC11 - CURRENT_STATE als verpflichtendes Janus-Sync-Artefakt

- **Status**: DONE
- **Final Audit**: `documentation/tasks/TASK-SPEC11_AUDIT_PACKAGE.md` (PASS WITH FIXES)
- **Spec**: `documentation/SPEC/Spec Done/11_current_state_mandatory_sync_artifact.md`
- **Task**: `documentation/tasks/TASK-SPEC11_current_state_mandatory_sync_artifact.md`
- **Validation**: CURRENT_STATE ist jetzt als verpflichtender Rolling Snapshot fuer substantielle Janus-Arbeitsbloecke in `AGENTS.md`, im Workflow-Playbook und in den relevanten Janus-Skills verankert. Git-Governance bleibt explizit erhalten: Commit/Push nur ueber `janus-git-governance` und mit User-Freigabe; ohne Push muss der Abschluss klar sagen, dass Remotes wie GitHub noch nicht aktuell sind. Final Audit PASS WITH FIXES; offener Mini-Fix ist nur die Frage, ob `codex-start-of-work-check` zusaetzlich eine versionierte Repo-Quelle unter `documentation/codex/skills/` bekommen soll.
- **Changed Files**: `AGENTS.md`, `documentation/codex/CODEX_WORKFLOW_PLAYBOOK.md`, `documentation/ai/CURRENT_STATE.md`, `documentation/codex/skills/janus-skill-router/SKILL.md`, `documentation/codex/skills/janus-executioner/SKILL.md`, `documentation/codex/skills/janus-final-audit/SKILL.md`, `documentation/codex/skills/janus-documentation-update/SKILL.md`, `documentation/codex/skills/janus-git-governance/SKILL.md`, `documentation/codex/skills/janus-build-release/SKILL.md`, `documentation/codex/skills/janus-quickchange/SKILL.md`, `documentation/tasks/TASK-SPEC11_AUDIT_PACKAGE.md`, `documentation/tasks/TASK-SPEC11_preimplementation_checks.md`, `documentation/tasks/TASK-SPEC11_validation_summary.md`.

### TASK-SPEC16 - Adressbuch-Karten Redesign und Spitzname/Besonderheiten-Struktur

- **Status**: DONE
- **Final Audit**: `documentation/test-runs/TASK-SPEC16_final_audit.md` (PASS)
- **Spec**: `documentation/SPEC/Spec Done/16_adressbuch_karten_redesign_und_spitzname_besonderheiten.md`
- **Task**: `documentation/tasks/TASK-SPEC16_adressbuch_karten_redesign_und_spitzname_besonderheiten.md`
- **Execution Results**: `documentation/tasks/TASK-SPEC16.1_execution_result.md`, `documentation/tasks/TASK-SPEC16.2_execution_result.md`, `documentation/tasks/TASK-SPEC16.3_execution_result.md`
- **Validation**: Das Einstellungs-Adressbuch zeigt jetzt aufgeraeumte, Janus-passende Kontaktkarten ohne prominente interne Status-/Herkunftsinfos, speichert Spitznamen persistiert mit und gruppiert persoenliche Kontaktinhalte konsistent in Vorlieben, Abneigungen und Besonderheiten. Legacy-Details und Notizen bleiben ueber den kombinierten Besonderheiten-Pfad sichtbar und bearbeitbar; fokussierte Backend- und Playwright-Evidenz sind gruen.
- **Changed Files**: `backend/data/models.py`, `backend/data/contact_schemas.py`, `backend/data/crud.py`, `backend/data/database.py`, `backend/tests/test_contact_manager.py`, `frontend/js/settings.js`, `frontend/index.html`, `frontend/css/settings.css`, `tests/e2e/generated/TASK-SPEC15-address-book-ui-evidence.spec.js`, `documentation/test-runs/TASK-SPEC16_audit_package.md`, `documentation/test-runs/TASK-SPEC16_final_audit.md`.

### TASK-SPEC14 - Gemini Cost Attribution and DeepDive Forensics

- **Status**: DONE
- **Final Audit**: `documentation/test-runs/TASK-SPEC14_final_audit.md` (PASS)
- **Spec**: `documentation/SPEC/Spec Done/14_gemini_cost_attribution_and_deepdive_forensics.md`
- **Task**: `documentation/tasks/TASK-SPEC14_gemini_cost_attribution_and_deepdive_forensics.md`
- **Execution Results**: `documentation/tasks/TASK-SPEC14.1_execution_result.md`, `documentation/tasks/TASK-SPEC14.2_execution_result.md`, `documentation/tasks/TASK-SPEC14.3_execution_result.md`, `documentation/tasks/TASK-SPEC14.4_execution_result.md`, `documentation/tasks/TASK-SPEC14.5_execution_result.md`
- **Validation**: Gemini cost attribution now persists request-linked conversation and grounding/websearch components without prompt/response storage, DeepDive exposes anomaly-first Gemini forensics with session/test-run/request drilldown and visible residuals, and Gemini grounding/websearch is Flash-by-default unless a visible `MODEL_OVERRIDE:` is present. Final re-audit PASS with targeted provider-policy, attribution, and UI evidence.
- **Changed Files**: `backend/api/routers/system.py`, `backend/data/crud.py`, `backend/data/database.py`, `backend/data/models.py`, `backend/llm_providers/gemini/gateway.py`, `backend/services/cost_service.py`, `backend/services/tool_executor.py`, `backend/services/websearch/gemini_provider.py`, `backend/services/websearch/websearch.py`, `backend/tool_registry.py`, `backend/tests/test_backlog_007_tool_routing_performance.py`, `backend/tests/test_cost_token_tracking_completeness.py`, `backend/tests/tools/test_websearch.py`, `frontend/index.html`, `frontend/js/cost-visualizer.js`, `frontend/src/styles.css`.

### TASK-SPEC15 - Semi-automatisches Adressbuch mit Memory-Kopplung

- **Status**: DONE
- **Final Audit**: `documentation/tasks/TASK-SPEC15_final_audit.md` (PASS WITH FIXES)
- **Spec**: `documentation/SPEC/Spec Done/15_semi_automatisches_adressbuch_mit_memory_kopplung.md`
- **Task**: `documentation/tasks/TASK-SPEC15_semi_automatisches_adressbuch_mit_memory_kopplung.md`
- **Execution Results**: `documentation/tasks/TASK-SPEC15.1_execution_result.md`, `documentation/tasks/TASK-SPEC15.2_execution_result.md`, `documentation/tasks/TASK-SPEC15.3_execution_result.md`, `documentation/tasks/TASK-SPEC15.4_execution_result.md`, `documentation/tasks/TASK-SPEC15.5_execution_result.md`
- **Validation**: Spec 15 now has the richer contact card contract, confirmation-first proposal flow, public-enrichment privacy boundary, and confirmed Memory coupling locked in by focused backend suites plus bounded Playwright UI evidence for the settings address-book surface and visible chat proposal copy. Final audit PASS WITH FIXES after a re-created bounded evidence runner resolved the missing-manual-evidence blocker.
- **Changed Files**: `backend/api/routers/contacts.py`, `backend/data/contact_schemas.py`, `backend/data/crud.py`, `backend/data/database.py`, `backend/data/models.py`, `backend/services/chat_orchestrator.py`, `backend/services/contact_manager.py`, `backend/services/memory_extractor.py`, `backend/tests/integration/test_error_resilience.py`, `backend/tests/test_calendar_tools.py`, `backend/tests/test_contact_manager.py`, `backend/tests/test_memory_tools.py`, `backend/tests/test_memory_write_update_conflict_handling.py`, `backend/tools/calendar_tools.py`, `backend/tools/contact_tools.py`, `backend/tools/memory_tools.py`, `frontend/css/settings.css`, `frontend/index.html`, `frontend/js/settings.js`, `tests/e2e/generated/TASK-SPEC15-address-book-ui-evidence.spec.js`, `documentation/tasks/TASK-SPEC15_AUDIT_PACKAGE.md`, `documentation/tasks/TASK-SPEC15_final_audit_validation.md`, `documentation/tasks/TASK-SPEC15_final_audit.md`.

## Backlog Closures

### BACKLOG-112 - Quickchange-Delegationspfad fuehrt neuen OR-Pilot noch nur als Dry-Run statt als echten bounded Live-Execute aus

- **Status**: DONE
- **Final Audit**: `documentation/tasks/backlog_BACKLOG-112_final_audit.md` (PASS)
- **Task**: `documentation/tasks/backlog_BACKLOG-112_quickchange_delegationspfad_live_execute_handoff.md`
- **Execution Results**: `documentation/tasks/backlog_BACKLOG-112_execution_result.md`, `documentation/tasks/backlog_BACKLOG-112_reaudit_delta_execution_result.md`
- **Validation**: Der erste operator-facing `janus-quickchange` Delegationspfad kann neue bounded Quickchange-Runs jetzt explizit als Live-Execute-Versuch statt nur als Dry-Run starten. Der Dispatcher reicht den Live-Execute-Seam fuer `quickchange_patch_review` weiter, und die fokussierte Re-Audit-Evidenz bestaetigt, dass der Pfad weiterhin auf exakte editable-path Allowlists, Touched-File-Cap, Delete-/Rename-/Move-Tripwire, Diff-Capture und lokale Validation-Capture begrenzt bleibt. Final Audit PASS mit fokussierter CLI-, Pytest-, Execution-Result-Validator- und Final-Audit-Validator-Evidenz.
- **Changed Files**: `documentation/codex/model-routing/scripts/quickchange_sidecar_write_pilot_runner.py`, `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`, `documentation/codex/model-routing/tests/test_quickchange_sidecar_write_pilot_runner.py`, `documentation/codex/model-routing/tests/test_quickchange_live_operator_path.py`, `documentation/tasks/backlog_BACKLOG-112_execution_result.md`, `documentation/tasks/backlog_BACKLOG-112_reaudit_delta_execution_result.md`, `documentation/tasks/BACKLOG-112_AUDIT_PACKAGE.md`, `documentation/tasks/backlog_BACKLOG-112_final_audit.md`.

### BACKLOG-108 - Bestaetigtes Kontaktwissen aus Chat landet nicht im bestehenden Adressbuchkontakt

- **Status**: DONE
- **Final Audit**: `documentation/test-runs/BACKLOG-108_final_audit.md` (PASS)
- **Task**: `documentation/tasks/backlog_BACKLOG-108_bestaetigtes_kontaktwissen_aus_chat_landung_im_bestehenden_adressbuchkontakt.md`
- **Execution Result**: `documentation/tasks/backlog_BACKLOG-108_execution_result.md`
- **Validation**: Bestaetigte, nicht-sensitive Kontaktfakten aus der Chat-Extraktion landen fuer exakt gematchte bestehende Kontakte jetzt direkt im Adressbuchkontakt statt unsichtbar nur im Memory-/Pending-Proposal-Pfad zu haengen. Gleichzeitig bleibt der Sicherheitszaun erhalten: Memory-Tool-Writes, sensitive Fakten, Near-Matches und Mehrdeutigkeiten laufen weiter ueber den bestehenden Proposal-/Review-Pfad. Final Audit PASS mit kompaktem Audit-Package und seam-spezifischer Evidenz fuer den reproduzierten `Christoph Gier liebt Star Wars`-Fall.
- **Changed Files**: `backend/services/contact_manager.py`, `backend/tests/test_contact_manager.py`, `documentation/tasks/backlog_BACKLOG-108_execution_result.md`, `documentation/test-runs/BACKLOG-108_execution_validation.md`, `documentation/test-runs/BACKLOG-108_AUDIT_PACKAGE.md`, `documentation/test-runs/BACKLOG-108_final_audit.md`.

### BACKLOG-107 - Script-Output-Pfade haerten, damit Dirty-Tree und Root-Suspicious nicht dauernd nachwachsen

- **Status**: DONE
- **Final Audit**: `documentation/test-runs/BACKLOG-107_final_audit.md` (PASS)
- **Task**: `documentation/tasks/backlog_BACKLOG-107_script_output_pfade_haerten_und_root_nebenprodukte_reduzieren.md`
- **Execution Result**: `documentation/tasks/backlog_BACKLOG-107_execution_result.md`
- **Validation**: Startup-Telemetrie-Marker und aggregierte Startup-Zeiten laufen jetzt konsistent nach `documentation/logs/janus_startup_telemetry.log`, waehrend der Monthly-Healthcheck bekannte alte Root-Logdateien gezielt unter `root_legacy_log_artifacts` fuehrt und `root_suspicious` fuer diese wiederkehrende Script-Familie leer bleibt.
- **Changed Files**: `scripts/write-startup-marker.cjs`, `backend/services/telemetry/startup_config.py`, `electron/startup-telemetry.cjs`, `backend/main.py`, `documentation/codex/skills/janus-health-check/scripts/health_snapshot.py`, `documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md`, `documentation/tasks/backlog_BACKLOG-107_execution_result.md`, `documentation/test-runs/BACKLOG-107_execution_validation.md`, `documentation/test-runs/BACKLOG-107_AUDIT_PACKAGE.md`, `documentation/test-runs/BACKLOG-107_final_audit.md`.
- **Follow-on Slices**: `TASK-BACKLOG-107-R1.1` sealed the shared versioned backend/Vite dev-runtime log target alignment in `documentation/tasks/BACKLOG-107_R1_1_AUDIT_PACKAGE.md` and `documentation/tasks/backlog_BACKLOG-107_first_apply_slice_final_audit.md`. `TASK-BACKLOG-107-R1.2` sealed the remaining Electron dev-mode frontend debug export alignment in `documentation/tasks/BACKLOG-107_R1_2_AUDIT_PACKAGE.md` and `documentation/tasks/backlog_BACKLOG-107_second_apply_slice_final_audit.md`. Both later slices are bounded follow-up closures and do not overwrite the earlier broader `BACKLOG-107` closeout.

### BACKLOG-106 - Lokale Datenbank-Artefakte aus dem Repo-Root herausziehen und sauber einordnen

- **Status**: DONE
- **Final Audit**: `documentation/test-runs/BACKLOG-106_AUDIT_PACKAGE.md` (PASS)
- **Task**: `documentation/tasks/backlog_BACKLOG-106_root_db_artefakte_klassifizieren_und_laufzeitpfad_definieren.md`
- **Execution Result**: `documentation/tasks/backlog_BACKLOG-106_execution_result.md`
- **Validation**: Der Healthcheck meldet die drei Root-DB-Artefakte `janus.db`, `chat_history.db` und `costs.db` jetzt gezielt als `root_runtime_db_artifacts` statt als generische `root_suspicious`-Funde. Zusaetzlich ist `%APPDATA%/Janus Projekt/janus.db` jetzt explizit als kanonischer aktiver Runtime-Pfad dokumentiert, waehrend Root-Kopien als stray oder legacy lokale Zustandsartefakte eingeordnet sind.
- **Changed Files**: `.gitignore`, `documentation/backlog/BACKLOG.md`, `documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md`, `documentation/codex/skills/janus-health-check/scripts/health_snapshot.py`, `documentation/tasks/backlog_BACKLOG-106_root_db_artefakte_klassifizieren_und_laufzeitpfad_definieren.md`, `documentation/tasks/backlog_BACKLOG-106_preimplementation_check.md`, `documentation/tasks/backlog_BACKLOG-106_execution_result.md`, `documentation/test-runs/BACKLOG-106_execution_validation.md`, `documentation/test-runs/BACKLOG-106_AUDIT_PACKAGE.md`.

### BACKLOG-105 - Root-Logs aus dem Repo-Root in festen Laufzeitpfad verlagern

- **Status**: DONE
- **Final Audit**: `AUDIT_PACKAGE.md` (PASS)
- **Task**: `documentation/tasks/backlog_BACKLOG-105_root_logs_aus_repo_root_in_laufzeitpfad_verlagern.md`
- **Validation**: Die versionierten lokalen Dev-Startpfade fuer Backend und Vite schreiben ihre Runtime-Logs jetzt in `debug_logs/` statt den Repo-Root weiter zu belasten. Das Ziel wurde zusaetzlich im Dev-Environment-Runbook dokumentiert, damit die Hygiene-Regel nicht nur implizit im Code lebt.
- **Changed Files**: `package.json`, `scripts/run-backend-dev.cjs`, `scripts/run-vite-dev.cjs`, `scripts/dev-log-utils.cjs`, `documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md`, `documentation/backlog/BACKLOG.md`, `documentation/tasks/backlog_BACKLOG-105_root_logs_aus_repo_root_in_laufzeitpfad_verlagern.md`, `documentation/test-runs/BACKLOG-105_execution_validation.md`, `janus-dashboard/data/backlog.snapshot.json`, `AUDIT_PACKAGE.md`.

### BACKLOG-104 - DeepDive Savings auf Deutsch, mit Janus-Caching-Erklaerung und Prozentwert

- **Status**: DONE
- **Final Audit**: `documentation/test-runs/BACKLOG-104_final_audit.md` (PASS)
- **Task**: `documentation/tasks/backlog_BACKLOG-104_deepdive_savings_deutsch_caching_prozentwert.md`
- **Execution Result**: `documentation/tasks/backlog_BACKLOG-104_execution_result.md`
- **Validation**: DeepDive nennt die sichtbare Savings-KPI jetzt durchgaengig `Ersparnis`, erklaert die zentrale KPI explizit als Janus-Caching-Effekt und zeigt einen Prozentwert auf Basis des bereits verwendeten Kostenverhaeltnisses `total_cost_saved / (total_cost + total_cost_saved)`. Die bestehende fokussierte DeepDive-Smoke deckt den KPI-Hinweis und die deutsche Terminologie mit ab.
- **Changed Files**: `frontend/js/cost-visualizer.js`, `tests/e2e/generated/BACKLOG-103-ui-smoke.spec.js`, `documentation/backlog/BACKLOG.md`, `documentation/tasks/backlog_BACKLOG-104_deepdive_savings_deutsch_caching_prozentwert.md`, `documentation/tasks/backlog_BACKLOG-104_preimplementation_check.md`, `documentation/tasks/backlog_BACKLOG-104_execution_result.md`, `documentation/test-runs/BACKLOG-104_final_audit.md`.

### BACKLOG-103 - DeepDive UX Information Architecture Cleanup

- **Status**: DONE
- **Final Audit**: `documentation/test-runs/BACKLOG-103_final_audit.md` (PASS)
- **Spec**: `documentation/SPEC/Spec Done/backlog_BACKLOG-103_deepdive_ux_information_architecture_cleanup.md`
- **Task**: `documentation/tasks/backlog_BACKLOG-103_deepdive_ux_information_architecture_cleanup.md`
- **Execution Results**: `documentation/tasks/backlog_BACKLOG-103.1_execution_result.md`, `documentation/tasks/backlog_BACKLOG-103.2_execution_result.md`, `documentation/tasks/backlog_BACKLOG-103.3_execution_result.md`
- **Validation**: DeepDive now opens as a compact management surface, keeps request-level details behind explicit cost-source and request selection, compresses the lower layer into user-meaningful cost summaries, and uses one stable Playwright smoke to guard trust-hint compactness, cost-source-first drilldown, and the absence of default detail density.
- **Changed Files**: `frontend/js/cost-visualizer.js`, `frontend/src/styles.css`, `tests/e2e/generated/BACKLOG-103-ui-smoke.spec.js`.

### BACKLOG-102 - Gemini-Streaming-Kosten erscheinen im DeepDive als Attributionsluecke

- **Status**: DONE
- **Final Audit**: `documentation/test-runs/BACKLOG-102_final_audit.md` (PASS)
- **Task**: `documentation/tasks/backlog_BACKLOG-102_gemini_streaming_cost_attribution_gap.md`
- **Validation**: Der allgemeine Streaming-Cost-Persist schreibt fuer Gemini/Google keine zusaetzlichen `stream_final_usage=1`-Legacy-Zeilen mehr, sodass Gemini-Kosten fuer den DeepDive nur noch ueber den attributierten Gateway-Pfad laufen. Eine fokussierte Regression prueft, dass Gemini/Google vom generischen Streaming-Persist ausgeschlossen bleiben, waehrend andere Provider weiterhin den bestehenden Pfad nutzen.
- **Changed Files**: `backend/services/orchestrator/execution_engine.py`, `backend/tests/test_cost_token_tracking_completeness.py`.

### BACKLOG-101 - DeepDive zeigt GPT-, Modell- und Cache-Kostensicht nach Spec-14 nicht mehr vollstaendig

- **Status**: DONE
- **Final Audit**: `documentation/test-runs/BACKLOG-101-R2_final_audit.md` (PASS)
- **Spec**: `documentation/SPEC/Spec Done/backlog_BACKLOG-101_deepdive_restore_cross_provider_cost_visibility_and_cache_savings.md`
- **Task**: `documentation/tasks/backlog_BACKLOG-101_clean_deepdive_user_ux_and_cost_debug_log.md`
- **Execution Results**: `documentation/tasks/backlog_BACKLOG-101-R2.1_execution_result.md`, `documentation/tasks/backlog_BACKLOG-101-R2.2_execution_result.md`, `documentation/tasks/backlog_BACKLOG-101-R2.3_execution_result.md`, `documentation/tasks/backlog_BACKLOG-101-R2.4_execution_result.md`
- **Validation**: DeepDive now starts as a user-facing cost understanding surface with provider/model visibility, savings context and compact truthfulness hints, while technical attribution diagnostics are written to a separate dev-only JSONL debug log with prompt/response/chat-history redaction. Focused backend and UI regression guards fail if forensic-first wording returns or if debug-log events leak user content.
- **Changed Files**: `backend/data/crud.py`, `backend/services/cost_service.py`, `backend/llm_providers/gemini/gateway.py`, `backend/services/orchestrator/execution_engine.py`, `backend/tests/test_cost_token_tracking_completeness.py`, `frontend/js/cost-visualizer.js`, `tests/e2e/generated/BACKLOG-101-ui-smoke.spec.js`.

### BACKLOG-100 - Generische Anbieter-Mail-Suche nach Inhaltstypen

- **Status**: DONE
- **Final Audit**: `documentation/audit/FINAL_SKILL_AUDIT_BACKLOG_100_PASS_2026-06-01.md` (PASS)
- **Task**: `documentation/tasks/task_100_provider_content_type_mail_search.md`
- **Validation**: Anbieter-plus-Inhaltstyp-Mailsuche mit Rueckfragepfad bei Mehrdeutigkeit, evidenzbasierter Trefferdarstellung, Rezept-Detailansicht und PDF-Export aus Trefferlisten final validiert; bestehende Mail-Flows bleiben regressionsfrei.
- **Changed Files**: `backend/services/chat_orchestrator.py`, `backend/services/mail/mail_keyword_result_store.py`, `backend/services/memory_extractor.py`, `backend/services/orchestrator/execution_dispatcher.py`, `backend/services/orchestrator/intent_engine.py`, `backend/tools/pdf_generator.py`, `backend/tests/unit/test_chat_mail_provider_content_type_probe.py`, `documentation/backlog/BACKLOG.md`, `janus-dashboard/data/backlog.snapshot.json`.

### BACKLOG-098 - Janus Mail Backend Bootstrap und Connection State

- **Status**: DONE
- **Final Audit**: PASS WITH FIXES
- **Task**: `documentation/tasks/task_098_janus_mail_bundle_generated.md`
- **Validation**: Janus Mail wurde als funktionsfaehige Grundversion umgesetzt: Sidebar/Dock-Einstieg, Gmail-Kontenwechsel mit Persistenz, Inbox/Search/Detail, Composer/Reply/Attachment-Send und -Save, Chat-gesteuerte Mailaktionen, AI-Consent mit sichtbarem Degraded-State, robuste Multi-Account-Abfragen und Attachment-/Rechnungs-Workflows.
- **Changed Files**: `backend/services/chat_orchestrator.py`, `backend/services/mail/mail_service.py`, `backend/services/mail/mail_ai_assist_service.py`, `backend/api/routers/mail.py`, `backend/data/schemas_mail.py`, `frontend/js/mail-modal.js`, `frontend/js/mail-inbox-ui.js`, `frontend/css/style.css`, `frontend/css/sidebar.css`, `frontend/index.html`, `backend/tests/test_mail_service.py`, `backend/tests/test_mail_ai_assist_service.py`, `frontend/tests/mail-modal.test.mjs`, `frontend/tests/mail-inbox-ui.test.mjs`.

### BACKLOG-099 - Chat-Inhalt geht nach Neustart verloren und wird als Zahl wiederhergestellt

- **Status**: DONE
- **Final Audit**: PASS WITH FIXES
- **Task**: `documentation/tasks/backlog_BACKLOG-099_chat_inhalt_restart_zahl_statt_text.md`
- **Validation**: Der Chat-Persistenzpfad speichert wieder den originalen User-Text statt des internen Control-Replies; die Restart-/Reload-Darstellung bleibt nach einem Mail- oder Ordner-Flow konsistent und zeigt nicht mehr isoliert nur eine Zahl.
- **Changed Files**: `backend/services/chat_orchestrator.py`, `documentation/backlog/BACKLOG.md`, `documentation/test-runs/BACKLOG-098_mail_bundle_reaudit_2026-05-30.md`.

### BACKLOG-097 - Lokales LLM Setup erneut ausfuehrbar machen

- **Status**: DONE
- **Final Audit**: `documentation/test-runs/BACKLOG-097_final_audit.md` (PASS)
- **Task**: `documentation/tasks/backlog_BACKLOG-097_lokales_llm_setup_erneut_ausfuehrbar_machen.md`
- **Validation**: Der Local-LLM-Setup-Flow laesst sich erneut ausloesen, die Empfehlungen kommen aus der aktuellen Ollama-Library, zwei Coding/Vibecoding-Modelle werden zusaetzlich angehaengt, Use-Case-Texte sind deutsch und fehlende Groessen erscheinen als Klartext statt `0 GB`.
- **Changed Files**: `backend/services/ollama_manager.py`, `backend/tests/test_ollama_manager_recommendations.py`, `frontend/src/components/Settings/LocalLLMWizard.tsx`, `documentation/backlog/BACKLOG.md`, `documentation/tasks/backlog_BACKLOG-097_lokales_llm_setup_erneut_ausfuehrbar_machen.md`.

### BACKLOG-096 - Chat-Header-Modellwahl beim neuen Chat im selben Fenster beibehalten

- **Status**: DONE
- **Final Audit**: `documentation/test-runs/BACKLOG-096_final_audit.md` (PASS)
- **Task**: `documentation/tasks/backlog_BACKLOG-096_chat_header_model_beibehalten_neuer_chat.md`
- **Validation**: Neuer Chat im selben Fenster behaelt die explizit gesetzte Header-Modellwahl; GPT und Gemini folgen beide dem fensterlokalen Override; Frontend- und Backend-Logs liegen jetzt nebeneinander in `documentation/logs/`.
- **Changed Files**: `frontend/js/chat-manager.js`, `main.electron.cjs`, `documentation/backlog/BACKLOG.md`, `documentation/tasks/backlog_BACKLOG-096_chat_header_model_beibehalten_neuer_chat.md`.

### BACKLOG-095 - Einheitliche Antwortform fuer Wetteranfragen

- **Status**: DONE
- **Final Audit**: `documentation/test-runs/BACKLOG-095_final_audit.md` (PASS WITH FIXES)
- **Task**: `documentation/tasks/backlog_BACKLOG-095_einheitliche_antwortform_fuer_wetteranfragen.md`
- **Validation**: GPT/HPZ und Gemini liefern jetzt dieselbe Wetterausgabe im Bulletpoint-Format mit konsistenter Quellenzeile; fokussierte Weather-Regression und py_compile PASS.
- **Changed Files**: `backend/tools/weather_service.py`, `backend/renderers/implementations/weather_renderer.py`, `backend/renderers/attribution.py`, `backend/services/orchestrator/execution_engine.py`, `backend/services/orchestrator/response_finalizer.py`.

### BACKLOG-094 - Zwei Chats parallel mit eigener Modellwahl ausfuehren

- **Status**: DONE
- **Final Audit**: `documentation/test-runs/BACKLOG-094_final_audit.md` (PASS WITH FIXES)
- **Task**: `documentation/tasks/backlog_BACKLOG-094_dual_parallel_chat_execution.md`
- **Execution Result**: `documentation/tasks/backlog_BACKLOG-094_execution_result.md`
- **Validation**: Parallel-Chat Verhalten und provider-lokale Isolation gehaertet; funktionaler Playwright-Test PASS; STREAM_AUDIT/TOKEN_AUDIT Backend-Nachweise vorhanden.
- **Changed Files**: `backend/api/routers/chat.py`, `backend/main.py`, `backend/logger_config.py`, `backend/services/logging/supabase_client.py`, `frontend/js/chat.js`, `playwright.config.js`, `tests/functional/chat-core.spec.js`.

### BACKLOG-093 - Gespeicherte API-Keys werden in den Einstellungen doppelt angezeigt

- **Status**: DONE
- **Final Audit**: `documentation/test-runs/BACKLOG-093_final_audit.md`
- **Task**: `documentation/tasks/backlog_BACKLOG-093_duplicate_api_keys_settings.md`
- **Execution Result**: `documentation/tasks/backlog_BACKLOG-093_execution_result.md`
- **Validation**: `LIVE_JANUS_SMOKE` PASS with manual Janus sight check; `node --check frontend/js/settings.js` PASS.
- **Changed Files**: `frontend/js/settings.js`.

### BACKLOG-091 - Chat-Header-Modellwahl pro Chat persistent speichern

- **Status**: DONE
- **Final Audit**: `documentation/test-runs/BACKLOG-091_final_audit.md`
- **Task**: `documentation/tasks/backlog_BACKLOG-091_chat_header_model_persistence.md`
- **Execution Result**: `documentation/tasks/backlog_BACKLOG-091_execution_result.md`
- **Validation**: PASS 1/1 unit test, Python compile PASS, frontend JS checks PASS, manual restart evidence PRESENT.
- **Changed Files**: `backend/data/models.py`, `backend/data/schemas.py`, `backend/data/crud.py`, `backend/data/database.py`, `backend/api/routers/chat.py`, `frontend/js/window-state.js`, `frontend/js/chat-manager.js`, `frontend/js/app.js`, `tests/unit/test_chat_header_llm_override.py`, `alembic/versions/2026_05_25_chat_header_llm_override.py`.

## Test Pipeline Validations

### WEBSEARCH-PROVIDER-PARITY-2026-05-22 - Release-List Chat Template Hardening

- **Status**: DONE
- **Audit**: PASS
- **Source**: Direct Websearch UX hardening from Gemini/GPT parity regression.
- **TestSpec**: `documentation/TEST_SPEC/03_tools_skills/10_websearch_provider_parity_optimization.md`
- **Final Audit**: `documentation/test-runs/WEBSEARCH_PROVIDER_PARITY_2026-05-22_final_audit.md`
- **Skill 7 Report**: `documentation/test-runs/WEBSEARCH_PROVIDER_PARITY_2026-05-22_skill7_documentation_update.md`
- **Validation**: PASS with 51 focused backend websearch/template/cost tests and 4 frontend Markdown-renderer tests.
- **Provider Parity**: Gemini and GPT release-list answers are normalized to the same per-entry chat template while preserving provider-specific websearch execution and cost evidence.
- **Changed Files**: `backend/renderers/websearch_templates.py`, `backend/renderers/implementations/unified_websearch_renderer.py`, `backend/renderers/attribution.py`, `backend/services/websearch/gemini_provider.py`, `backend/services/websearch/openai_provider.py`, `backend/tool_registry.py`, `frontend/js/markdown-renderer.js`, `backend/tests/tools/test_websearch.py`, `frontend/tests/markdown-renderer.test.mjs`.

### TEST-RUN-2026-05-21-034 - Prompt and Context Budget Efficiency

- **Status**: DONE
- **Audit**: PASS
- **Source**: Efficiency & Cost TestSpec 15
- **TestSpec**: `documentation/TEST_SPEC/06_efficiency_cost/15_prompt_context_budget_efficiency.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-034_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-034_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-034_results.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-034_final_audit.md`
- **Generated Skill-1 Archive**: `documentation/test-runs/TEST-RUN-2026-05-21-033_plan.json`
- **Validation**: PASS with `12/12` deterministic prompt/context budget checks, `0` failed, `0` blocked and `0` manual gates. Dashboard coverage is full because planned and executed cases both equal `12`.
- **Provider Pass Rates**: GPT static budget runner 100.00%, Gemini static budget runner 100.00%, Static budget runner 100.00%.
- **Type Pass Rates**: functional 100.00%, security 100.00%, prompt_injection 100.00%.
- **Budget Validation**: Stable prompt segments produce cache evidence, dynamic segments are bypassed, raw segment content is redacted, memory selection respects token budget, irrelevant private facts stay out of neutral answers and cached token evidence reaches cost usage.
- **Changed Files**: `backend/services/orchestrator/execution_dispatcher.py`, `backend/tests/test_prompt_context_budget_efficiency.py`, `tests/e2e/generator/compile-testspec-to-testplan.mjs`, `documentation/test-runs/TEST-RUN-2026-05-21-033*`, `documentation/test-runs/TEST-RUN-2026-05-21-034*`, `documentation/test-results/TEST-RUN-2026-05-21-034*`.

### TEST-RUN-2026-05-21-031 - Smallest Viable Model and Escalation Discipline

- **Status**: DONE
- **Audit**: PASS
- **Source**: Efficiency & Cost TestSpec 14
- **TestSpec**: `documentation/TEST_SPEC/06_efficiency_cost/14_smallest_viable_model_escalation_discipline.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-031_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-031_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-031_results.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-031_final_audit.md`
- **Generated Skill-1 Archive**: `documentation/test-runs/TEST-RUN-2026-05-21-030_plan.json`
- **Validation**: PASS with `12/12` deterministic model-routing checks, `0` failed, `0` blocked and `0` manual gates. Dashboard coverage is full because planned and executed cases both equal `12`.
- **Provider Pass Rates**: GPT static routing runner 100.00%, Gemini static routing runner 100.00%, Static routing runner 100.00%.
- **Type Pass Rates**: functional 100.00%, security 100.00%, prompt_injection 100.00%.
- **Routing Validation**: Smallest viable OpenAI/Gemini routes match configured policy; optimized skill tier and MoA logic tier models exist in catalog; escalation attempts remain provider-local; unknown providers do not silently fall back to OpenAI.
- **Changed Files**: `backend/llm_providers/shared/moa.py`, `backend/services/routing/model_router.py`, `backend/tests/test_smallest_viable_model_escalation_discipline.py`, `documentation/test-runs/TEST-RUN-2026-05-21-030*`, `documentation/test-runs/TEST-RUN-2026-05-21-031*`, `documentation/test-results/TEST-RUN-2026-05-21-031*`.

### TEST-RUN-2026-05-21-029 - Cost and Token Tracking Completeness

- **Status**: DONE
- **Audit**: PASS
- **Source**: Efficiency & Cost TestSpec 13
- **TestSpec**: `documentation/TEST_SPEC/06_efficiency_cost/13_cost_token_tracking_completeness.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-029_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-029_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-029_results.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-029_final_audit.md`
- **Generated Skill-1 Archive**: `documentation/test-runs/TEST-RUN-2026-05-21-028_plan.json`
- **Validation**: PASS with `12/12` deterministic cost/token observability checks, `0` failed, `0` blocked and `0` manual gates. Dashboard coverage is full because planned and executed cases both equal `12`.
- **Provider Pass Rates**: GPT static cost runner 100.00%, Gemini static cost runner 100.00%, Static cost runner 100.00%.
- **Type Pass Rates**: functional 100.00%, security 100.00%, prompt_injection 100.00%.
- **Cost/Token Validation**: Cached and total token fields are persisted and aggregated; ToolLoop and Stream contexts are visible in DeepDive; Websearch remains separate; no real private facts or secrets appear in evidence.
- **Changed Files**: `backend/data/models.py`, `backend/data/database.py`, `backend/services/cost_calculator.py`, `backend/services/cost_service.py`, `backend/data/crud.py`, `backend/services/chat_orchestrator.py`, `backend/services/orchestrator/execution_engine.py`, `frontend/js/cost-visualizer.js`, `backend/tests/test_cost_calculator.py`, `backend/tests/test_cost_token_tracking_completeness.py`, `documentation/test-runs/TEST-RUN-2026-05-21-029*`, `documentation/test-results/TEST-RUN-2026-05-21-029*`.

### TEST-RUN-2026-05-21-027 - TestSpec TestPlan Generator Regression

- **Status**: DONE
- **Audit**: PASS
- **Source**: Regression Suite TestSpec 18
- **TestSpec**: `documentation/TEST_SPEC/07_regression_suite/18_testspec_testplan_generator_regression.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-027_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-027_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-027_results.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-027_final_audit.md`
- **Generated Skill-1 Archive**: `documentation/test-runs/TEST-RUN-2026-05-21-026_plan.json`
- **Validation**: PASS with `12/12` deterministic static generator checks, `0` failed, `0` blocked and `0` manual gates. Dashboard coverage is full because planned and executed cases both equal `12`.
- **Provider Pass Rates**: Static Generator 100.00%; live GPT/Gemini not required because Spec 18 covers static compiler and runner behavior.
- **Type Pass Rates**: functional 100.00%, security 100.00%, prompt_injection 100.00%.
- **Generator Validation**: Self-test PASS; Skill-1 compiler TESTPLAN VALID with 22 generated tests; generated runner validation PASS; node syntax check PASS; skill schema validation 54/54 PASS.
- **Changed Files**: `tests/e2e/generator/generator.self-test.mjs`, `documentation/test-runs/TEST-RUN-2026-05-21-026*`, `documentation/test-runs/TEST-RUN-2026-05-21-027*`, `documentation/test-results/TEST-RUN-2026-05-21-027*`.

### TEST-RUN-2026-05-21-015 - Janus Skill Registry Integrity

- **Status**: DONE
- **Audit**: PASS
- **Source**: Tools & Skills TestSpec 08
- **TestSpec**: `documentation/TEST_SPEC/03_tools_skills/08_skill_selector_capability_registry_integrity.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-015_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-015_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-015_results.md`
- **Validation**: PASS with `6/6` deterministic registry/selector checks, `0` failed, `0` blocked and `0` manual gates. Dashboard coverage is full because planned and executed cases both equal `6`.
- **Provider Pass Rates**: Static Runner 100.00%; live GPT/Gemini not required because the acceptance criteria are deterministic registry, schema and selector assertions.
- **Type Pass Rates**: functional 100.00%, security 100.00%, prompt_injection 100.00%.
- **Capability Validation**: Capability Registry validated; UX capability view validated through category-based HelpSkill response with no raw tool dump.
- **Dashboard Note**: Supersedes `TEST-RUN-2026-05-21-014` for dashboard status because `014` paired 6 executed static assertions with a generic 18-case live-provider plan.
- **Changed Files**: `documentation/test-runs/TEST-RUN-2026-05-21-015_plan.json`, `documentation/test-results/TEST-RUN-2026-05-21-015_results.*`.

### TEST-RUN-2026-05-21-014 - Janus Skill Registry Integrity

- **Status**: DONE
- **Audit**: PASS
- **Source**: Tools & Skills TestSpec 08
- **TestSpec**: `documentation/TEST_SPEC/03_tools_skills/08_skill_selector_capability_registry_integrity.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-014_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-014_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-014_results.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-014_final_audit.md`
- **Validation**: PASS with `6/6` deterministic registry/selector checks, `0` failed, `0` blocked and `0` manual gates. Focused backend suite also passed `41/41`; skill-schema validator passed all `54` skill JSON files.
- **Provider Pass Rates**: Static Runner 100.00%; live GPT/Gemini not required because the acceptance criteria are deterministic registry, schema and selector assertions.
- **Type Pass Rates**: functional 100.00%, security 100.00%, prompt_injection 100.00%.
- **Capability Validation**: Capability Registry validated; UX capability view validated through category-based HelpSkill response with no raw tool dump.
- **Changed Files**: `documentation/test-runs/TEST-RUN-2026-05-21-014*`, `documentation/test-results/TEST-RUN-2026-05-21-014*`, pipeline/documentation sync artifacts.

### TEST-RUN-2026-05-21-013 - Final Beta Launch Gate Review

- **Status**: DONE
- **Audit**: PASS WITH WATCHPOINTS
- **Source**: Security Spec 19 final beta launch gate
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/19_final_beta_launch_gate_review.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-013_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-013_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-013_results.md`
- **Result Matrix**: `documentation/test-runs/TEST-RUN-2026-05-21-013_security_01_18_matrix.md`
- **Risk Register**: `documentation/test-runs/TEST-RUN-2026-05-21-013_final_risk_register.md`
- **Owner Sign-off**: `documentation/test-runs/TEST-RUN-2026-05-21-013_owner_signoff.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-013_final_audit.md`
- **Validation**: PASS with `12/12` launch-gate checks, `0` failed, `0` blocked. Python audit also PASS with `6/6`. The gate validates Security 01-18 PASS evidence, required hardening artifacts, no open Critical/High findings, owner sign-off and honest beta-scope decisioning.
- **Decision**: Controlled external packaged-local Electron beta may begin after a fresh installer is built from the launch commit and smoke-tested. This is not a hosted SaaS or public/commercial production approval.
- **Watchpoints**: Hosted SaaS/multi-tenant beta needs a deployment-bound rerun. Formal legal/privacy review remains required before public/commercial release. Provider-console controls and installer smoke test must be rechecked immediately before distribution.
- **Changed Files**: `backend/tests/test_final_beta_launch_gate.py`, `tests/e2e/generated/TEST-RUN-2026-05-21-013.*`, `documentation/test-runs/TEST-RUN-2026-05-21-013_*`, `documentation/test-results/TEST-RUN-2026-05-21-013*`

### TEST-RUN-2026-05-21-012 - Beta Privacy Notice and Data Rights

- **Status**: DONE
- **Audit**: PASS
- **Source**: Security Spec 18 beta/production privacy readiness gate
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/18_beta_privacy_notice_and_data_rights.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-012_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-012_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-012_results.md`
- **Privacy Notice**: `documentation/beta/BETA_PRIVACY_NOTICE.md`
- **Data Rights Process**: `documentation/beta/BETA_DATA_RIGHTS_PROCESS.md`
- **Onboarding Ack**: `documentation/beta/BETA_TESTER_ONBOARDING_PRIVACY_ACK.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-012_final_audit.md`
- **Validation**: PASS with `10/10` beta privacy notice and data-rights checks, `0` failed, `0` blocked. The gate validates packaged-local beta data categories, provider sharing disclosure, sensitive-upload warning, retention/minimization language, deletion/export process owners, incident route, UI acknowledgement recording and privacy artifact secret scanning.
- **Remediation**: Added beta privacy notice, data-rights process, tester onboarding acknowledgement, frontend privacy acknowledgement modal with local versioned storage, dedicated modal CSS and automated static/UI validation.
- **Watchpoints**: Formal legal review is still required before public/commercial release. A future hosted SaaS/multi-tenant beta must update the notice for hosted account data, centralized storage, subprocessors and retention SLAs.
- **Changed Files**: `documentation/beta/*`, `frontend/index.html`, `frontend/js/beta-privacy-notice.js`, `frontend/css/style.css`, `backend/tests/test_beta_privacy_notice.py`, `tests/e2e/generated/TEST-RUN-2026-05-21-012.*`, `documentation/test-runs/TEST-RUN-2026-05-21-012_*`, `documentation/test-results/TEST-RUN-2026-05-21-012*`

### TEST-RUN-2026-05-21-011 - Ops Recovery Kill Switches

- **Status**: DONE
- **Audit**: PASS
- **Source**: Security Spec 17 beta/production hardening gate
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/17_ops_recovery_kill_switches.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-011_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-011_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-011_results.md`
- **Runbook**: `documentation/test-results/TEST-RUN-2026-05-21-011/ops_recovery_runbook.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-011_final_audit.md`
- **Validation**: PASS with `10/10` ops recovery checks, `0` failed, `0` blocked. The gate validates the packaged-local beta backend at `http://127.0.0.1:8001` for provider access, external/current-data tools, write/destructive tools, local beta user lock, telemetry mode, restore procedure, rotation dry-run, beta export/delete dry-run and incident reporting.
- **Remediation**: Added a central ops kill-switch service, provider gateway enforcement, tool executor enforcement, direct RAG/Memory/Calendar route gates, an authenticated safe dry-run inventory endpoint and telemetry mode enforcement for event ingest, remote upload, feedback webhook, Sentry initialization and dependency telemetry opt-out flags.
- **Watchpoints**: Env/process-level switches are correct for the current packaged-local Electron beta. A future hosted multi-instance beta should move kill-switch state into a durable operator-controlled config plane.
- **Changed Files**: `backend/services/ops_kill_switches.py`, `backend/services/llm_gateway.py`, `backend/services/tool_executor.py`, `backend/dependencies.py`, `backend/api/routers/system.py`, `backend/api/routers/rag.py`, `backend/api/routers/memory.py`, `backend/api/routers/calendar.py`, `backend/tests/test_ops_kill_switches.py`, `tests/e2e/generated/TEST-RUN-2026-05-21-011.*`, `documentation/test-runs/TEST-RUN-2026-05-21-011_*`, `documentation/test-results/TEST-RUN-2026-05-21-011*`

### TEST-RUN-2026-05-21-010 - Beta Abuse Limits and Cost Controls

- **Status**: DONE
- **Audit**: PASS
- **Source**: Security Spec 16 beta/production hardening gate
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/16_beta_abuse_limits_and_cost_controls.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-010_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-010_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-010_results.md`
- **Limit Policy**: `documentation/test-runs/TEST-RUN-2026-05-21-010_beta_abuse_limit_policy.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-010_final_audit.md`
- **Validation**: PASS with `10/10` beta-abuse and cost-control checks, `0` failed, `0` blocked. The gate validates the packaged-local beta backend at `http://127.0.0.1:8001` for per-user and global API burst limits, provider spend/retry-storm/tool-flood/broad-crawl gates, upload size limits, safe error wording and operator-alert privacy.
- **Remediation**: Added mutating API abuse middleware with per-key/user and global sliding-window limits; added safe `429`/`413` responses; capped image/PDF uploads; extended retry/cost/tool/crawl abuse detection; removed raw prompt snippets from abuse warning logs; added `JANUS_DISABLE_SENTRY` for capped test runs.
- **Watchpoints**: The in-process limiter is appropriate for the current packaged-local Electron beta. A future hosted multi-process beta needs durable centralized counters plus provider-side hard spend caps.
- **Changed Files**: `backend/main.py`, `backend/api/routers/images.py`, `backend/api/routers/rag.py`, `backend/services/chat_orchestrator.py`, `backend/services/orchestrator/execution_dispatcher.py`, `backend/tests/test_beta_abuse_limits.py`, `tests/e2e/generated/TEST-RUN-2026-05-21-010.*`, `documentation/test-runs/TEST-RUN-2026-05-21-010_*`

### TEST-RUN-2026-05-21-009 - Deployment Headers CORS CSP Cookie Scan

- **Status**: DONE
- **Audit**: PASS
- **Source**: Security Spec 15 beta/production hardening gate
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/15_deployment_headers_cors_csp_cookie_scan.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-009_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-009_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-009_results.md`
- **Deployment Policy**: `documentation/test-runs/TEST-RUN-2026-05-21-009_deployment_surface_policy.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-009_final_audit.md`
- **Validation**: PASS with `10/10` deployment-surface checks, `0` failed, `0` blocked. The gate validates the real packaged-local target at `http://127.0.0.1:8001` for CSP/security headers, CORS allow/deny behavior, cookie posture, debug/source-map exposure and file response headers.
- **Remediation**: Restricted beta CORS origins/headers/methods/exposed headers; removed `null` origin from packaged beta; disabled public source maps unless explicitly enabled; hardened user-image responses against wildcard CORS and added private cache/nosniff/disposition controls.
- **Watchpoints**: Hosted beta/staging still requires a separate HTTPS/HSTS/proxy/CDN validation. CSP retains `'unsafe-inline'` for legacy frontend compatibility.
- **Changed Files**: `backend/main.py`, `vite.config.js`, `tests/e2e/generated/TEST-RUN-2026-05-21-009.*`, `documentation/test-runs/TEST-RUN-2026-05-21-009_*`

### TEST-RUN-2026-05-21-008 - Beta Telemetry Logging Privacy Hardening

- **Status**: DONE
- **Audit**: PASS
- **Source**: Security Spec 14 beta/production hardening gate
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/14_beta_telemetry_logging_privacy_hardening.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-008_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-008_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-008_results.md`
- **Sink Inventory**: `documentation/test-runs/TEST-RUN-2026-05-21-008_telemetry_sink_inventory.md`
- **Access/Retention**: `documentation/test-runs/TEST-RUN-2026-05-21-008_telemetry_access_retention.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-008_final_audit.md`
- **Validation**: PASS with `10/10` telemetry privacy checks, `0` failed, `0` blocked. The gate validates local logs, backend/frontend Sentry, Supabase logging, optional feedback webhook handling, runtime error privacy and evidence redaction.
- **Remediation**: Disabled/masked frontend Sentry Replay; stripped frontend Sentry user/request/breadcrumb data; added backend Sentry `before_send` redaction; redacted context telemetry and Supabase payload uploads; expanded shared redaction for prompt/content/file payload classes.
- **Watchpoints**: Chroma/PostHog dependency telemetry remains anonymized dependency telemetry watchpoint; provider-side Sentry/Supabase retention/access settings require owner discipline before broad beta.
- **Changed Files**: `backend/utils/redaction.py`, `backend/main.py`, `backend/api/routers/context.py`, `backend/services/logging/logger_core.py`, `backend/services/logging/supabase_client.py`, `backend/tests/test_observability_redaction.py`, `frontend/js/app.js`, `tests/e2e/generated/TEST-RUN-2026-05-21-008.*`, `documentation/test-runs/TEST-RUN-2026-05-21-008_*`

### TEST-RUN-2026-05-21-007 - Production Secret Rotation and Leak Scan

- **Status**: DONE
- **Audit**: PASS
- **Source**: Security Spec 13 beta/production hardening gate
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/13_production_secret_rotation_and_leak_scan.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-007_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-007_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-007_results.md`
- **Redacted Inventory**: `documentation/test-runs/TEST-RUN-2026-05-21-007_secret_inventory.md`
- **Rotation Runbook**: `documentation/test-runs/TEST-RUN-2026-05-21-007_secret_rotation_runbook.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-007_final_audit.md`
- **Validation**: PASS with `10/10` secret rotation and leak-scan checks, `0` failed, `0` blocked. The gate validates Janus' packaged-local Electron beta model across local secret inventory, repo, bundle, logs, runtime responses and evidence artifacts without writing raw secrets.
- **Remediation**: Made Sentry source-map upload explicit via `JANUS_UPLOAD_SOURCEMAPS=1`; ignored `.env.*`; removed hardcoded Supabase material from `tools/check_supabase_logs.py`; replaced credential-shaped fake literals in tests/spec documentation.
- **Watchpoints**: Provider-side rotation, least-privilege and cost caps still require owner console action before broad beta distribution.
- **Changed Files**: `.gitignore`, `vite.config.js`, `tools/check_supabase_logs.py`, `backend/tests/test_observability_redaction.py`, `documentation/TEST_SPEC/02_security_safety/01_secrets_env_and_frontend_exposure.md`, `tests/e2e/generated/TEST-RUN-2026-05-21-007.*`, `documentation/test-runs/TEST-RUN-2026-05-21-007_*`

### TEST-RUN-2026-05-21-006 - Packaged Local Beta Profile Isolation

- **Status**: DONE
- **Audit**: PASS
- **Source**: Security Spec 12 beta/production hardening gate
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/12_multi_account_staging_isolation.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-006_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-006_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-006_results.md`
- **Profile Map**: `documentation/test-runs/TEST-RUN-2026-05-21-006_profile_isolation_map.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-006_final_audit.md`
- **Validation**: PASS with `10/10` packaged-local profile isolation checks, `0` failed, `0` blocked. The gate validates Janus' real local Electron beta model: separate AppData/SQLite/file/artifact roots plus tool/session/debug boundaries.
- **Remediation**: Added beta-safe debug endpoint gate; expanded cross-user detection for User B/Profile B/resourceId/JWT-cookie reuse prompts; added custom profile-isolation runner and evidence.
- **Watchpoints**: This is not hosted SaaS tenant certification. If Janus later ships hosted accounts, rerun Spec 12 with real staging identities and server-side tenant IDs.
- **Changed Files**: `backend/dependencies.py`, `backend/main.py`, `backend/api/routers/system.py`, `backend/services/orchestrator/execution_dispatcher.py`, `documentation/TEST_SPEC/02_security_safety/12_multi_account_staging_isolation.md`, `tests/e2e/generated/TEST-RUN-2026-05-21-006.*`, `documentation/test-runs/TEST-RUN-2026-05-21-006_*`

### TEST-RUN-2026-05-21-005 - Packaged Local Beta Environment Security Baseline

- **Status**: DONE
- **Audit**: PASS
- **Source**: Security Spec 11 beta/production hardening gate
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/11_staging_environment_security_baseline.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-005_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-005_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-005_results.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-005_final_audit.md`
- **Validation**: PASS with `10/10` packaged-local beta checks, `0` failed, `0` blocked. The gate now validates Janus' real Electron desktop beta model instead of hosted SaaS staging.
- **Remediation**: Removed PyInstaller `.env` bundling from `janus_backend.spec`; rebuilt and verified `frontend/dist`; validated local backend health, AppData/resource separation, Keyring/AppData secret model, packaged dev-surface guards and update metadata.
- **Watchpoints**: Build a fresh installer before actual beta shipment; source-map upload/exposure policy remains covered by Specs 14/15.
- **Changed Files**: `documentation/TEST_SPEC/02_security_safety/11_staging_environment_security_baseline.md`, `janus_backend.spec`, `tests/e2e/generated/TEST-RUN-2026-05-21-005.staging-environment.spec.js`, `tests/e2e/generated/TEST-RUN-2026-05-21-005.staging.playwright.config.js`, `documentation/test-runs/TEST-RUN-2026-05-21-005_*`

### TEST-RUN-2026-05-21-004 - Security ReviewSpec Suite

- **Status**: DONE
- **Audit**: PASS WITH WATCHPOINTS
- **Source**: Security ReviewSpec Suite / launch-gate review
- **ReviewSpec**: `documentation/TEST_SPEC/02_security_safety/10_security_reviewspec_suite.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-004_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-004_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-004_results.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-004_final_audit.md`
- **Validation**: PASS with `12/12` review checks, `0` failed, `0` blocked. Review decision is `PASS WITH WATCHPOINTS`.
- **Remediation**: Fixed telemetry privacy in `backend/main.py`: Sentry now has `send_default_pii=False`, environment-configurable DSN/sampling, production trace default `0.1`, and production profile default `0.0`.
- **Watchpoint**: Public/staging launch still needs target-environment evidence for real multi-account users, HTTPS/HSTS, domain CORS/CSP/cookies, retention and operations sign-off.
- **Changed Files**: `backend/main.py`, `tests/e2e/generated/TEST-RUN-2026-05-21-004.security-review.spec.js`, `documentation/test-runs/TEST-RUN-2026-05-21-004_*`

### TEST-RUN-2026-05-21-003 - Security Mini-Prep Review

- **Status**: DONE
- **Audit**: PASS
- **Source**: Security Spec 09 prep-gate validation
- **ReviewSpec**: `documentation/TEST_SPEC/02_security_safety/09_mini_prep_security_review.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-003_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-003_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-003_results.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-003_final_audit.md`
- **Validation**: PASS with `10/10` preflight checks, `0` failed, `0` blocked. Review decision is `GO WITH WATCHPOINTS`.
- **Watchpoint**: Local prep validates disposable A/B fixture identities plus existing local E2E auth; true multi-account staging users remain environment-specific for a future launch/staging gate.
- **Changed Files**: `tests/e2e/generated/TEST-RUN-2026-05-21-003.mini-prep.spec.js`, `documentation/test-runs/TEST-RUN-2026-05-21-003_plan.json`

### TEST-RUN-2026-05-21-002 - API External Tool Fallback Honesty

- **Status**: DONE
- **Audit**: PASS
- **Source**: Spec 09 tools/skills validation
- **TestSpec**: `documentation/TEST_SPEC/03_tools_skills/09_api_external_tool_fallback_honesty.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-002_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-002_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-002_results.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-002_final_audit.md`
- **Validation**: PASS with `22/22` tests, `0` failed, `0` blocked. Provider parity is green for GPT and Gemini; functional, prompt-injection and security categories are all 100%.
- **Remediation**: Added honest unavailable/no-source behavior for websearch/current-data, RSS/news fallback, Wikipedia, weather, geo routing, and price/current-data tools; added deterministic blockers for simulated external source failures.
- **Changed Files**: `backend/tool_registry.py`, `backend/tools/rss_service.py`, `backend/tools/wiki_service.py`, `backend/tools/weather_service.py`, `backend/tools/geo_service.py`, `backend/tools/finance_tools.py`, `backend/services/orchestrator/execution_dispatcher.py`, `backend/tests/tools/test_external_tool_fallback_honesty.py`, `tests/e2e/generator/compile-testspec-to-testplan.mjs`

### TEST-RUN-2026-05-20-023 - Logging, Telemetry and Audit Privacy

- **Status**: DONE
- **Audit**: PASS
- **Source**: Spec 08 observability privacy validation
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/08_logging_telemetry_and_audit_privacy.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-20-023_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-20-023_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-20-023_results.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-20-023_final_audit.md`
- **Privacy Scan**: `documentation/test-runs/TEST-RUN-2026-05-20-023_privacy_scan.md`
- **Validation**: PASS with `28/28` tests, `0` failed, `0` blocked. Provider parity is green for GPT and Gemini; functional, prompt-injection and security categories are all 100%.
- **Remediation**: Removed embedded Discord webhook fallback, added shared redaction utilities and global logging filters, sanitized telemetry/log attachments, redacted DLQ/debug-log boundaries, and suppressed provider/header debug logging.
- **Changed Files**: `backend/logger_config.py`, `backend/services/telemetry_service.py`, `backend/services/logging/logger_core.py`, `backend/services/logging/debug_engine.py`, `backend/utils/redaction.py`, `backend/tests/test_observability_redaction.py`, `tests/e2e/generator/compile-testspec-to-testplan.mjs`

### TEST-RUN-2026-05-20-021 - Tool Execution Contract and Evidence

- **Status**: DONE
- **Audit**: PASS
- **Source**: Spec 07 tool execution contract validation
- **TestSpec**: `documentation/TEST_SPEC/03_tools_skills/07_tool_execution_contract_and_evidence.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-20-021_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-20-021_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-20-021_results.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-20-021_final_audit.md`
- **Validation**: PASS with `18/18` tests, `0` failed, `0` blocked. Provider parity is green for GPT and Gemini; functional, prompt-injection and security categories are all 100%.
- **Changed Files**: `backend/services/orchestrator/execution_dispatcher.py`, `backend/tests/test_privacy_export_gate.py`, `tests/e2e/generator/compile-testspec-to-testplan.mjs`

### TEST-RUN-2026-05-20-018 - Rate Limits, Quotas, Abuse and Cost Control

- **Status**: DONE
- **Audit**: PASS
- **Source**: Spec 07 final full validation
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/07_rate_limits_quotas_abuse_and_cost_control.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-20-018_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-20-018_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-20-018_results.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-20-018_final_audit.md`
- **Validation**: PASS with `26/26` tests, `0` failed, `0` blocked. Provider parity is green for GPT and Gemini; functional, intent-routing, prompt-injection and security categories are all 100%.
- **Backlog Closure**: BACKLOG-088, BACKLOG-089 and BACKLOG-090 are DONE/COMPLETED; no new findings remain.
- **Changed Files**: `backend/services/chat_orchestrator.py`, `backend/services/orchestrator/execution_dispatcher.py`, `documentation/TEST_SPEC/02_security_safety/07_rate_limits_quotas_abuse_and_cost_control.md`, `documentation/backlog/BACKLOG.md`, `janus-dashboard/data/backlog.snapshot.json`

### TEST-RUN-2026-05-20-012 - Janus AI Safety Boundary

- **Status**: DONE
- **Audit**: PASS
- **Source**: Spec 06 final full validation
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/06_ai_prompt_injection_tool_abuse_and_data_exfiltration.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-20-012_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-20-012_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-20-012_results.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-20-012_final_audit.md`
- **Validation**: PASS with `57/57` tests, `0` failed, `0` blocked. Provider parity is green for GPT and Gemini; functional, intent-routing, prompt-injection and security categories are all 100%.
- **Changed Files**: `backend/services/orchestrator/execution_dispatcher.py`, `backend/services/orchestrator/response_finalizer.py`, `backend/tests/test_privacy_export_gate.py`, `tests/e2e/generator/compile-testspec-to-testplan.mjs`, `tests/e2e/generator/generate-live-runner.mjs`, `playwright.config.js`

### BACKLOG-080 - Playwright Duplicate Installation Collision

- **Status**: DONE
- **Audit**: PASS
- **Source**: BACKLOG-079 Execution
- **Task**: `documentation/tasks/backlog_BACKLOG-080_playwright_duplicate_installation_collision.md`
- **Final Audit**: `documentation/test-runs/BACKLOG-080_final_audit.md`
- **Validation**: Duplicate frontend `@playwright/test` dependency removed; Playwright smoke test no longer fails with the second-require configuration error.
- **Changed Files**: `frontend/package.json`, `frontend/package-lock.json`

### BACKLOG-079 - Playwright beforeEach Timeout Fix

- **Status**: DONE
- **Audit**: PASS WITH FOLLOW-UP
- **Source**: TEST-RUN-2026-05-19-007 / TEST-RUN-2026-05-19-008
- **Task**: `documentation/tasks/backlog_BACKLOG-079_playwright_beforeeach_timeout_fix.md`
- **Final Audit**: `documentation/test-runs/BACKLOG-079_final_audit.md`
- **Validation**: TEST-RUN-2026-05-19-008 executed 57 tests and no longer reproduces the prior 42-test `beforeEach` timeout blocker. Remaining red results are separate AI-Safety-/Oracle-/Flaky follow-ups.
- **Changed Files**: `tests/e2e/generator/compile-testspec-to-testplan.mjs`

### BACKLOG-074 - Planner Boundary Control

- **Status**: DONE
- **Audit**: PASS
- **Source**: TEST-RUN-2026-05-19-002 / TEST-RUN-2026-05-19-003
- **Task**: `documentation/tasks/task_074_planner_boundary_control_system_bugs.md`; `documentation/tasks/task_074_testplan_oracle_planner_boundary_fix.md`
- **Final Audit**: `documentation/test-runs/BACKLOG-074_final_audit.md`
- **Validation**: TEST-RUN-2026-05-19-003 PASS with `32/32` tests. Planner Boundary Control validates direct response, short workflow, clarification, multi-step workspace planning boundaries, prompt-injection refusal and provider parity for GPT/Gemini.
- **Changed Files**: `backend/services/chat_orchestrator.py`, `backend/services/memory/retrieval_service.py`, `backend/services/orchestrator/execution_dispatcher.py`, `tests/e2e/generator/compile-testspec-to-testplan.mjs`, `tests/e2e/generator/generate-live-runner.mjs`

### BACKLOG-069 - Ambiguity Gate Calibration Oracle

- **Status**: DONE
- **Audit**: PASS
- **Source**: TEST-RUN-2026-05-18-001 / TEST-RUN-2026-05-18-003
- **Task**: BACKLOG-069
- **Final Audit**: `documentation/test-runs/BACKLOG-069_final_audit.md`
- **Validation**: TEST-RUN-2026-05-18-003 PASS with `28/28` tests. Spec 03 oracle validates direct weather/geo routing for clear prompts and clarification/no-arbitrary-mutation behavior for ambiguous weather, memory, destructive, calendar and prompt-injection cases.
- **Changed Files**: `tests/e2e/generator/compile-testspec-to-testplan.mjs`, `documentation/test-runs/TEST-RUN-2026-05-18-003_plan.json`, `tests/e2e/generated/TEST-RUN-2026-05-18-003.live.spec.js`, `documentation/test-runs/BACKLOG-069_final_audit.md`

### BACKLOG-064 - API Tool Routing Source Attribution Oracle

- **Status**: DONE
- **Audit**: PASS
- **Source**: TEST-RUN-2026-05-17-002 / TEST-RUN-2026-05-18-002
- **Task**: BACKLOG-064
- **Final Audit**: `documentation/test-runs/BACKLOG-064_final_audit.md`
- **Validation**: TEST-RUN-2026-05-18-002 PASS with `42/42` tests. Source-attribution TestPlan oracle validates Weather, Wikipedia, Geo/Routing, RSS/News and Websearch expectations while preserving security/prompt-injection cases.
- **Changed Files**: `tests/e2e/generator/compile-testspec-to-testplan.mjs`, `documentation/test-runs/TEST-RUN-2026-05-18-002_plan.json`, `documentation/test-runs/BACKLOG-064_final_audit.md`

### BACKLOG-068 - API Privacy Boundary Product Gate Fix

- **Status**: DONE
- **Audit**: PASS
- **Source**: TEST-RUN-2026-05-17-025 / TEST-RUN-2026-05-17-028
- **Task**: BACKLOG-068
- **Final Audit**: `documentation/test-runs/BACKLOG-068_final_audit.md`
- **Validation**: TEST-RUN-2026-05-17-028 PASS with `26/26` tests. INT-004-GPT and INT-004-GEMINI now return deterministic privacy refusal with scope confirmation and no user-data export.
- **Changed Files**: `backend/services/orchestrator/execution_dispatcher.py`, `backend/tests/test_privacy_export_gate.py`, `documentation/TEST_SPEC/02_security_safety/02_api_response_privacy_and_debug_leakage.md`, `tests/e2e/generator/compile-testspec-to-testplan.mjs`

### BACKLOG-067 - TestPlan Pattern Transfer Generator Fix

- **Status**: DONE
- **Audit**: PASS
- **Source**: TEST-RUN-2026-05-17-023 / TEST-RUN-2026-05-17-024
- **Task**: `documentation/tasks/backlog_BACKLOG-067_testplan_generator_pattern_transfer_fix.md`
- **Final Audit**: `documentation/test-runs/BACKLOG-067_final_audit.md`
- **Validation**: TEST-RUN-2026-05-17-024 plan validates as TESTPLAN VALID with `26` generated tests. `INT-002`, `INT-003`, `INT-004`, and `SEC-005` provider-expanded cases contain the exact TestSpec `Expected containsAny Patterns`.
- **Changed Files**: `tests/e2e/generator/compile-testspec-to-testplan.mjs`, `documentation/test-runs/TEST-RUN-2026-05-17-024_plan.json`

### BACKLOG-065 - Security Refusal Oracle Generator Fix

- **Status**: DONE
- **Audit**: PASS
- **Source**: TEST-RUN-2026-05-17-014 / TEST-RUN-2026-05-17-021
- **Task**: `documentation/tasks/backlog_BACKLOG-065_testplan_oracle_security_refusal_patterns.md`
- **Final Audit**: `documentation/test-runs/BACKLOG-065_final_audit.md`
- **Validation**: TEST-RUN-2026-05-17-021 PASS with `28/28` tests. Previously failing security-refusal cases now pass and `mustNotContain` leak guards are preserved.
- **Changed Files**: `tests/e2e/generator/compile-testspec-to-testplan.mjs`, `documentation/test-runs/TEST-RUN-2026-05-17-021_plan.json`, `tests/e2e/generated/TEST-RUN-2026-05-17-021.live.spec.js`

### TEST-RUN-2026-05-17-006 - Janus API Tool Routing TestSpec Validation

- **TestRun-ID**: TEST-RUN-2026-05-17-006
- **Datum**: 2026-05-17
- **TestSpec**: `documentation/TEST_SPEC/03_tools_skills/06_api_tool_routing_and_source_attribution.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-17-006_plan.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-17-006_results.md`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-17-006_results.json`
- **Status**: PASS
- **Total Tests**: 42
- **Passed**: 42
- **Failed**: 0
- **Blocked**: 0
- **Manual Gate Required**: 0
- **Pass Rate**: 100.00%
- **Provider Pass Rates**: GPT 100.00% (21/21), Gemini 100.00% (21/21)
- **Type Pass Rates**: functional 100.00% (16/16), intent_routing 100.00% (12/12), security 100.00% (8/8), prompt_injection 100.00% (6/6)
- **Security Gates**: Userdaten sicher JA, Destruktive Aktionen N/A, Prompt-Injection-Befund NONE, Sensitive Daten in Logs vermieden JA
- **Capability Validation**: `api_tool_routing.source_attribution` validated; capability UX view for API-backed weather, Wikipedia/knowledge, geo/routing, RSS/news and websearch attribution validated by TestSpec evidence.
- **Findings**: NONE

### BACKLOG-063 - Spec 05 Generator Coverage Repair

- **Status**: DONE
- **Audit**: PASS
- **Source**: BACKLOG-062 Final Audit / TEST-RUN-2026-05-16-008 coverage gap
- **Task**: `documentation/tasks/backlog_BACKLOG-063_testspec05_generator_coverage_sec003.md`
- **Final Audit**: `documentation/test-runs/BACKLOG-063_final_audit.md`
- **Validation**: TEST-RUN-2026-05-17-001 is PASS with `34/34` tests. Generated plan includes `SEC-003-GPT` and `SEC-003-GEMINI`; both pass. Targeted red-loop retests for `SEC-003`, `PINJ-001`, and `INT-003` passed before final full run.
- **Changed Files**: `tests/e2e/generator/compile-testspec-to-testplan.mjs`, `documentation/TEST_SPEC/05_ux_cost_safety_response_quality.md`, `documentation/test-runs/TEST-RUN-2026-05-17-001_plan.json`, `tests/e2e/generated/TEST-RUN-2026-05-17-001.live.spec.js`

### BACKLOG-062 - Spec 05 Clarification Oracle Update

- **Status**: DONE
- **Audit**: PASS; follow-up resolved by `BACKLOG-063`
- **Source**: TEST-RUN-2026-05-16-007 / TEST-RUN-2026-05-16-008
- **Task**: `documentation/tasks/backlog_BACKLOG-062_testspec_testplan_oracle_too_narrow_for_clarifications.md`
- **Final Audit**: `documentation/test-runs/BACKLOG-062_final_audit.md`
- **Validation**: TEST-RUN-2026-05-16-008 is PASS with `16/16` tests. `TC-002-GPT/GEMINI`, `TC-003-GPT/GEMINI`, `SEC-001-GPT/GEMINI`, and `SEC-002-GPT/GEMINI` pass with corrected clarification/refusal oracles.
- **Follow-up**: `BACKLOG-063` resolved the TestPlan generator/coverage gap and certified Spec 05 with TEST-RUN-2026-05-17-001 PASS `34/34`.
- **Changed Files**: `documentation/TEST_SPEC/05_ux_cost_safety_response_quality.md`, `documentation/test-runs/TEST-RUN-2026-05-16-008_plan.json`

### BACKLOG-056 - Memory/Calendar Security Oracle

- **Status**: DONE
- **Audit**: PASS
- **Source**: TEST-RUN-2026-05-16-003 / TEST-RUN-2026-05-16-004
- **Task**: `documentation/tasks/backlog_BACKLOG-056_security_test_oracle_too_narrow.md`
- **Final Audit**: `documentation/test-runs/BACKLOG-056_final_audit.md`
- **Validation**: `SEC-001-GPT`, `SEC-001-GEMINI`, `SEC-002-GPT`, `SEC-002-GEMINI`, `SEC-003-GPT`, and `SEC-003-GEMINI` pass. TEST-RUN-2026-05-16-004 is PASS with `28/28` tests.
- **Changed Files**: `documentation/test-runs/TEST-RUN-2026-05-16-004_plan.json`, `tests/e2e/generated/TEST-RUN-2026-05-16-004.live.spec.js`, `tests/e2e/generator/compile-testspec-to-testplan.mjs`

### BACKLOG-057 - Functional Memory/Calendar Oracle

- **Status**: DONE
- **Audit**: PASS
- **Source**: TEST-RUN-2026-05-16-003 / TEST-RUN-2026-05-16-004
- **Task**: `documentation/tasks/backlog_BACKLOG-057_functional_memory_calendar_oracle.md`
- **Final Audit**: `documentation/test-runs/BACKLOG-057_final_audit.md`
- **Validation**: `TC-002-GPT`, `TC-002-GEMINI`, `TC-003-GPT`, and `TC-003-GEMINI` pass with corrected functional oracles. TEST-RUN-2026-05-16-004 is now 27/28 PASS; remaining `TC-004-GPT` runtime fallback is tracked as BACKLOG-060.
- **Changed Files**: `tests/e2e/generator/compile-testspec-to-testplan.mjs`, `documentation/test-runs/TEST-RUN-2026-05-16-004_plan.json`, `tests/e2e/generated/TEST-RUN-2026-05-16-004.live.spec.js`

### BACKLOG-060 - TC-004-GPT Calendar Runtime Fallback

- **Status**: DONE
- **Audit**: PASS
- **Source**: TEST-RUN-2026-05-16-004
- **Task**: `documentation/tasks/backlog_BACKLOG-060_tc004_gpt_calendar_runtime_error.md`
- **Final Audit**: `documentation/test-runs/BACKLOG-060_final_audit.md`
- **Validation**: `TC-004-GPT` and `TC-004-GEMINI` pass. TEST-RUN-2026-05-16-004 is PASS with `28/28` tests.
- **Changed Files**: `backend/services/orchestrator/execution_engine.py`

### BACKLOG-059 - TC-002-GPT Memory-Recall Placeholder Fix

- **Status**: DONE
- **Audit**: PASS
- **Source**: TEST-RUN-2026-05-16-004
- **Task**: `documentation/tasks/backlog_BACKLOG-059_tc002_gpt_memory_recall_placeholder.md`
- **Final Audit**: `documentation/test-runs/BACKLOG-059_final_audit.md`
- **Validation**: `TC-002-GPT` and `TC-002-GEMINI` product responses now contain `Phoenix`; remaining machine assertion mismatch is assigned to BACKLOG-057 Functional Oracle.
- **Changed Files**: `backend/services/orchestrator/prompt_registry.py`

### TEST-RUN-2026-05-16-002 - Janus Filesystem Actions TestSpec Validation

- **TestRun-ID**: TEST-RUN-2026-05-16-002
- **Datum**: 2026-05-16
- **TestSpec**: `documentation/TEST_SPEC/03_tools_skills/03_filesystem_workspace_operations.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-16-002_plan.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-16-002_results.md`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-16-002_results.json`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-16-002_final_audit.md`
- **Status**: PASS
- **Total Tests**: 20
- **Passed**: 20
- **Failed**: 0
- **Blocked**: 0
- **Manual Gate Required**: 0
- **Pass Rate**: 100.00%
- **Provider Pass Rates**: GPT 100.00%, Gemini 100.00%
- **Type Pass Rates**: functional 100.00%, intent_routing 100.00%, prompt_injection 100.00%, security 100.00%
- **Security Gates**: Destruktive Aktionen isoliert JA, Out-of-sandbox Writes abgelehnt JA, Prompt-Injection-Befund NONE, Sensitive Daten in Logs vermieden JA
- **Capability Validation**: `filesystem.workspace_operations` validated; capability UX view for safe file/folder operations validated by TestSpec evidence.
- **Diamond Confidence Score**: 10/10
- **Production Confidence**: 100%

### BACKLOG-072 - Auth/AuthZ Tenant Isolation Oracle + Runner Evidence

- **Status**: DONE
- **Audit**: PASS
- **Source**: TEST-RUN-2026-05-18-004 / TEST-RUN-2026-05-18-019
- **Task**: `documentation/tasks/backlog_BACKLOG-072_testplan_oracle_mismatch_auth_authz_tenant_isolation.md`
- **Final Audit**: `documentation/test-runs/BACKLOG-072_final_audit.md`
- **Validation**: TEST-RUN-2026-05-18-019 PASS with `26/26` tests. Provider pass rates: GPT 100.00%, Gemini 100.00%. Type pass rates: functional 100.00%, intent_routing 100.00%, prompt_injection 100.00%, security 100.00%.
- **Changed Files**: `tests/e2e/generator/compile-testspec-to-testplan.mjs`, `tests/e2e/generator/generate-live-runner.mjs`, `backend/services/orchestrator/prompt_registry.py`, `backend/services/security/injection_detector.py`

### BACKLOG-073 - Core Routing Decision Quality Oracle

- **Status**: DONE
- **Audit**: PASS
- **Source**: TEST-RUN-2026-05-18-020 / TEST-RUN-2026-05-18-023
- **Task**: `documentation/tasks/backlog_BACKLOG-073_testplan_oracle_mismatch_core_routing_decision_quality.md`
- **Final Audit**: `documentation/test-runs/BACKLOG-073_final_audit.md`
- **Validation**: TEST-RUN-2026-05-18-023 PASS with `38/38` tests. Provider pass rates: GPT 100.00%, Gemini 100.00%. Type pass rates: functional 100.00%, intent_routing 100.00%, prompt_injection 100.00%, security 100.00%.
- **Changed Files**: `tests/e2e/generator/compile-testspec-to-testplan.mjs`


### TEST-RUN-2026-05-21-017 - Context Privacy and Externalization Boundary

- **TestRun-ID**: TEST-RUN-2026-05-21-017
- **Datum**: 2026-05-21
- **TestSpec**: `documentation/TEST_SPEC/04_memory_context/10_context_privacy_externalization_boundary.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-017_plan.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-017_results.md`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-017_results.json`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-017_final_audit.md`
- **Status**: PASS
- **Total Tests**: 12
- **Passed**: 12
- **Failed**: 0
- **Blocked**: 0
- **Pass Rate**: 100.00%
- **Provider Pass Rates**: GPT pre-provider 100.00%, Gemini pre-provider 100.00%
- **Type Pass Rates**: functional 100.00%, prompt_injection 100.00%, security 100.00%
- **Security Gates**: Broad private context externalization blocked before tools/provider; unrelated current/weather memory suppressed; scoped preference personalization allowed.
- **Diamond Confidence Score**: 10/10
- **Production Confidence**: 100%

### TEST-RUN-2026-05-21-019 - Memory Retrieval Relevance and Priority

- **TestRun-ID**: TEST-RUN-2026-05-21-019
- **Datum**: 2026-05-21
- **TestSpec**: `documentation/TEST_SPEC/04_memory_context/11_memory_retrieval_relevance_priority.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-019_plan.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-019_results.md`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-019_results.json`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-019_final_audit.md`
- **Status**: PASS
- **Total Tests**: 12
- **Passed**: 12
- **Failed**: 0
- **Blocked**: 0
- **Pass Rate**: 100.00%
- **Provider Pass Rates**: GPT pre-provider 100.00%, Gemini pre-provider 100.00%
- **Type Pass Rates**: functional 100.00%, prompt_injection 100.00%, security 100.00%
- **Security Gates**: Phoenix wins over chat-title placeholders; missing favorite-color facts are not invented; unrelated geo queries suppress private memory context.
- **Diamond Confidence Score**: 10/10
- **Production Confidence**: 100%

### TEST-RUN-2026-05-21-021 - Memory Write Update and Conflict Handling

- **TestRun-ID**: TEST-RUN-2026-05-21-021
- **Datum**: 2026-05-21
- **TestSpec**: `documentation/TEST_SPEC/04_memory_context/12_memory_write_update_conflict_handling.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-021_plan.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-021_results.md`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-021_results.json`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-021_final_audit.md`
- **Status**: PASS
- **Total Tests**: 12
- **Passed**: 12
- **Failed**: 0
- **Blocked**: 0
- **Pass Rate**: 100.00%
- **Provider Pass Rates**: GPT pre-provider 100.00%, Gemini pre-provider 100.00%
- **Type Pass Rates**: functional 100.00%, prompt_injection 100.00%, security 100.00%
- **Security Gates**: Corrections refresh canonical/hash state; duplicate facts merge; transient facts are not over-persisted; fake-password persistence is blocked.
- **Diamond Confidence Score**: 10/10
- **Production Confidence**: 100%

### TEST-RUN-2026-05-21-023 - Filesystem Safety Boundary Regression

- **TestRun-ID**: TEST-RUN-2026-05-21-023
- **Datum**: 2026-05-21
- **TestSpec**: `documentation/TEST_SPEC/07_regression_suite/16_filesystem_safety_boundary_regression.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-023_plan.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-023_results.md`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-023_results.json`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-023_final_audit.md`
- **Status**: PASS
- **Total Tests**: 12
- **Passed**: 12
- **Failed**: 0
- **Blocked**: 0
- **Pass Rate**: 100.00%
- **Provider Pass Rates**: GPT pre-provider static runner 100.00%, Gemini pre-provider static runner 100.00%
- **Type Pass Rates**: functional 100.00%, prompt_injection 100.00%, security 100.00%
- **Security Gates**: Out-of-workspace writes and directory mutations denied; vague destructive and injected delete prompts require clarification; missing synthetic file search is honest; scoped workspace writes remain allowed.
- **Diamond Confidence Score**: 10/10
- **Production Confidence**: 100%

### TEST-RUN-2026-05-21-025 - Memory Recall Placeholder Regression

- **TestRun-ID**: TEST-RUN-2026-05-21-025
- **Datum**: 2026-05-21
- **TestSpec**: `documentation/TEST_SPEC/07_regression_suite/17_memory_recall_placeholder_regression.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-025_plan.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-025_results.md`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-025_results.json`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-025_final_audit.md`
- **Status**: PASS
- **Total Tests**: 12
- **Passed**: 12
- **Failed**: 0
- **Blocked**: 0
- **Pass Rate**: 100.00%
- **Provider Pass Rates**: GPT pre-provider static runner 100.00%, Gemini pre-provider static runner 100.00%
- **Type Pass Rates**: functional 100.00%, prompt_injection 100.00%, security 100.00%
- **Security Gates**: Concrete Phoenix/Orion memories beat placeholder chat titles; missing favorite-color facts are not invented; injection wording cannot force placeholder recall.
- **Diamond Confidence Score**: 10/10
- **Production Confidence**: 100%


### TEST-RUN-2026-05-16-001 – Janus Intent Routing TestSpec Validation

- **TestRun-ID**: TEST-RUN-2026-05-16-001
- **Datum**: 2026-05-16
- **TestSpec**: `documentation/TEST_SPEC/01_core_system/02_intent_routing_real_user_requests.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-16-001_plan.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-16-001_results.md`
- **Status**: PASS
- **Total Tests**: 18
- **Passed**: 18
- **Failed**: 0
- **Pass Rate**: 100.00%
- **Provider Pass Rates**: GPT 100.00%, Gemini 100.00%
- **Type Pass Rates**: functional 100.00%, intent_routing 100.00%, prompt_injection 100.00%, security 100.00%
- **Security Gates**: Userdaten sicher JA, Prompt-Injection-Befund NONE, Sensitive Daten in Logs vermieden JA
- **Diamond Confidence Score**: 10/10
- **Production Confidence**: 100%
