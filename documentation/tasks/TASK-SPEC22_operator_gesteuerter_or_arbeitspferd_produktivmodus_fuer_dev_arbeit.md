TASK-SPEC22
- Source Spec: documentation/SPEC/Spec Done/22_operator_gesteuerter_or_arbeitspferd_produktivmodus_fuer_dev_arbeit.md
- Backlog Item: N/A
- Feature: Operator-gesteuerter OR-Arbeitspferd-Produktivmodus fuer Dev-Arbeit
- Generated At: 2026-06-20

## Generated Tasks

### TASK-SPEC22.1 Define the dedicated Dev-workhorse path contract and keep all other workflows Codex-only
- Ziel: Einen einzigen produktiven Dev-Workhorse-Einstieg mit harter Eligibility- und Scope-Grenze definieren, damit OR nur fuer diesen einen neuen Pfad angeboten werden kann und nicht implizit in bestehende Janus- oder Codex-Workflows auslaeuft.
- Scope: Ein neuer dedizierter Produktivpfad mit exakt erlaubten bounded Dev-Arbeitsklassen, harter Ablehnung fuer alle anderen Aufrufe, konfigurierter Kosten-/Governance-Grenze und lokaler Testbarkeit der Eligibility-Regeln.
- Files:
  - documentation/codex/model-routing/config/bounded_or_worker_eligibility_2026-06-17.json
  - documentation/codex/model-routing/config/or_task_budget_profiles_2026-06-19.json
  - documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py
  - documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py
- Steps:
  - Einen neuen dedizierten `productive_dev_workhorse_path`-Contract in der Eligibility-Konfiguration anlegen, statt bestehende Skill-Pfade stillschweigend zu erweitern.
  - Fuer den ersten Rollout nur die bounded Dev-Klassen `test_result_triage_review`, `execution_patch_candidate` und `execution_write_apply_candidate` in diesem neuen Pfad erlauben.
  - Governance-, Budget- und Missing-Estimate-Grenzen so verankern, dass ausserhalb des dedizierten Pfads deterministisch `Codex-only` oder `blocked before OR` gilt.
  - Lokale Eligibility-Helfer und Fixtures so erweitern, dass der neue Pfad pruefbar bleibt, ohne bestehende Spec-21-, Quickchange- oder Doku-Pfade umzudefinieren.
- Acceptance Criteria:
  - Nur der neue dedizierte Dev-Workhorse-Pfad kann fuer die drei erlaubten bounded Klassen OR-eligible werden.
  - Alle bestehenden Janus- und Codex-Workflows ausserhalb dieses Pfads bleiben deterministisch Codex-only.
  - Fehlende Path-, Budget- oder Estimate-Voraussetzungen blockieren vor jeder OR-Auswahl.
- Tests:
  - Positivtest fuer einen in-scope `productive_dev_workhorse_path`-Aufruf
  - Negativtest fuer einen bestehenden Workflow ausserhalb des dedizierten Pfads
  - Negativtest fuer eine nicht erlaubte Task-Klasse im dedizierten Pfad
  - Negativtest fuer fehlende Budget- oder Estimate-Voraussetzungen
- Model: 5.4
- Reason: Diese Slice zieht die eigentliche Produktivgrenze ein und verhindert, dass die neue OR-Option unkontrolliert in bestehende Workflows hineinwuchert.
- Closeout: Final Audit PASS ist in `documentation/tasks/TASK-SPEC22.1_final_audit.md` dokumentiert. Der dedizierte `productive_dev_workhorse_path`-Boundary-Contract ist damit task-scharf abgeschlossen und gegen fehlerhafte Kostenwerte fail-closed gehaertet; Spec 22 insgesamt bleibt offen, weil `TASK-SPEC22.2` bis `TASK-SPEC22.4` weiterhin ausstehen.

### TASK-SPEC22.2 Create the operator-invoked Dev-workhorse runner with mandatory Codex-vs-OR gate
- Ziel: Einen neuen dedizierten Runner bereitstellen, der fuer den erlaubten Dev-Workhorse-Pfad die sichtbare Wahl `1 = Codex` oder `2 = OR` inklusive Pflichtanzeige fuer Kosten und Confidence ausgibt.
- Scope: Neuer Entry-Runner, einheitliche Gate-Ausgabe, verpflichtende Estimate-/Confidence-Felder, frueher Abort bei fehlenden Pflichtdaten und kein Wrapper- oder Delegationsstart vor erfolgreichem Gate.
- Files:
  - documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py
  - documentation/codex/model-routing/scripts/bounded_or_worker_gate_prompt.py
  - documentation/codex/model-routing/tests/test_codex_dev_workhorse_runner.py
  - documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md
- Steps:
  - Einen neuen dedizierten `codex_dev_workhorse_runner.py` als einzigen produktiven Einstieg fuer diesen Rollout anlegen.
  - Die sichtbare Operator-Auswahl auf `1 = Codex` und `2 = OR` mit Estimate-, Confidence- und Scope-Hinweisen normieren.
  - Den Runner so haerten, dass fehlende Estimate-, Confidence-, Budget- oder Eligibility-Daten vor jeder Wrapper- oder Dispatcher-Invocation abbrechen.
  - Das Dev-Runbook auf genau diesen neuen Einstieg verweisen, ohne bestehende Janus-Skills als bereits produktiv umzuetikettieren.
- Acceptance Criteria:
  - Der dedizierte Runner zeigt fuer in-scope Aufrufe immer eine klare Codex-vs-OR-Auswahl mit Kosten- und Confidence-Hinweis.
  - Fehlende Pflichtdaten fuehren zu einem klaren Abort vor jeder Delegations-Invocation.
  - Das Dev-Runbook beschreibt nur den neuen dedizierten Pfad und nicht eine breite Aktivierung bestehender Skills.
- Tests:
  - Positivtest fuer Gate-Ausgabe mit Estimate- und Confidence-Feldern
  - Negativtest fuer fehlende Estimate-Felder
  - Negativtest fuer fehlende Confidence-Felder
  - Regressionstest fuer lokalen Codex-only Ausgang bei `1`
- Model: 5.4
- Reason: Erst ein sauberer operator-invoked Einstieg macht den Produktivmodus alltagstauglich; ohne diesen Gate-Slice bleibt der Pfad technisch vorhanden, aber operativ nicht kontrollierbar.
- Closeout: Final Audit PASS ist in `documentation/tasks/TASK-SPEC22.2_final_audit.md` dokumentiert. Der dedizierte `codex_dev_workhorse_runner.py` ist damit task-scharf als sichtbarer produktiver Entry-Runner mit kontrollierter `1 = Codex` / `2 = OR`-Auswahl, Pflichtfeldern fuer Estimate und Confidence sowie fail-closed Abort vor jeder Delegations-Invocation abgeschlossen; Spec 22 insgesamt bleibt offen, weil `TASK-SPEC22.3` und `TASK-SPEC22.4` weiterhin ausstehen.

### TASK-SPEC22.3 Wire bounded delegated triage and write-candidate execution behind the dedicated runner with Codex-owned acceptance
- Ziel: Den neuen Dev-Workhorse-Runner an die bestehenden bounded Delegationsbausteine anbinden, sodass Review-, Patch-Candidate- und Write-Apply-Candidate-Laeufe moeglich werden, ohne Codex-Autoritaet ueber Scope, Validierung und Accept-or-Reject zu verlieren.
- Scope: Dispatcher- und Runner-Anbindung fuer die drei erlaubten bounded Klassen, file-cluster- und artifact-basierte Weitergabe, harte Fallback-/Abort-Pfade und keine implizite Uebernahme bestehender Skill-Einstiege.
- Files:
  - documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py
  - documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
  - documentation/codex/model-routing/scripts/codex_test_result_triage_review_runner.py
  - documentation/codex/model-routing/scripts/codex_execution_patch_candidate_runner.py
  - documentation/codex/model-routing/scripts/codex_execution_write_apply_candidate_runner.py
  - documentation/codex/model-routing/tests/test_codex_dev_workhorse_runner.py
- Steps:
  - Den dedizierten Runner an genau die drei erlaubten bounded Klassen anbinden und jede Klasse auf den bereits vorhandenen lokalen Delegationsbaustein mappen.
  - Sicherstellen, dass Review-Ergebnisse, Patch-Kandidaten und Write-Apply-Candidates niemals als final erfolgreich gelten, bevor Codex lokal validiert und akzeptiert hat.
  - Einheitliche Abort-, Manual-Review- und Fallback-Ausgaenge fuer parsebare, unparsebare, cap-verletzende oder scope-escapende Ergebnisse herstellen.
  - Explizit absichern, dass die neuen Mappings nicht bestehende Skill-Einstiege umschreiben oder ihre Scope-Grenzen aendern.
- Acceptance Criteria:
  - Der dedizierte Runner kann genau die drei erlaubten bounded Klassen lokal in den passenden Delegationsbaustein routen.
  - Jedes delegierte Ergebnis endet in einem klaren Codex-owned `accept`, `reject`, `fallback` oder `manual review`-Status.
  - Bestehende Workflows wie `janus-debug`, `janus-test-pipeline`, `janus-executioner` oder `janus-quickchange` erhalten durch diese Slice keinen neuen impliziten Produktiv-OR-Einstieg.
- Tests:
  - Positivtest fuer `test_result_triage_review` ueber den neuen dedizierten Runner
  - Positivtest fuer `execution_patch_candidate` ueber den neuen dedizierten Runner
  - Positivtest fuer `execution_write_apply_candidate` mit accepted-source Gate
  - Negativtest fuer out-of-scope oder scope-escapende Ergebnisfaelle
- Model: 5.4
- Reason: Das ist der eigentliche Arbeitskern des Features; hier entsteht der bounded Produktivwert, waehrend Codex die letzte Verantwortung ueber Validation und Acceptance behaelt.
- Closeout: Final Audit PASS ist in `documentation/tasks/TASK-SPEC22.3_final_audit.md` dokumentiert. Der dedizierte `codex_dev_workhorse_runner.py` ist damit task-scharf als bounded Delegations-Runtime fuer genau `test_result_triage_review`, `execution_patch_candidate` und `execution_write_apply_candidate` abgeschlossen; Codex behaelt dabei explizit die finale Accept-or-Reject-Autoritaet. Spec 22 insgesamt bleibt offen, weil `TASK-SPEC22.4` fuer Actual-Cost-Closeout, file-first Telemetrie und Healthcheck-Sichtbarkeit weiterhin aussteht.

### TASK-SPEC22.4 Add file-first telemetry, actual-cost closeout, and healthcheck visibility for the dedicated Dev-workhorse path
- Ziel: Fuer jeden Lauf des dedizierten Dev-Workhorse-Pfads nachvollziehbar machen, was delegiert wurde, was es gekostet hat, wie validiert wurde und wie Codex final entschieden hat.
- Scope: File-first Capture-Integration, Session-JSONL fuer den neuen Pfad, Anzeige von tatsaechlichen Kosten nach Abschluss, Healthcheck-Ingestion fuer diese neue Pfadfamilie und explizit Dev-only dokumentierter Operator-Closeout.
- Files:
  - documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py
  - documentation/codex/model-routing/scripts/bounded_or_worker_outcome.py
  - documentation/codex/model-routing/scripts/or_file_first_capture_wrapper.ps1
  - documentation/codex/skills/janus-health-check/scripts/health_snapshot.py
  - documentation/codex/model-routing/tests/test_codex_dev_workhorse_runner.py
  - documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md
- Steps:
  - Den dedizierten Runner an file-first Artefakte, Session-JSONL und einheitliche Outcome-Normalisierung anbinden.
  - Nach jedem akzeptierten, abgelehnten oder gefallbackten Lauf die tatsaechlichen OR-Kosten sichtbar in der Operator-Zusammenfassung ausgeben.
  - `health_snapshot.py` so erweitern, dass der neue Dev-Workhorse-Pfad in Reliability-, Cost-, Fallback- und Outcome-Summaries erscheint, ohne bestehende Healthcheck-Pfade zu brechen.
  - Das Dev-Runbook explizit auf Dev-only, operator-invoked, bounded und nicht-produktionsroutingfaehig halten.
- Acceptance Criteria:
  - Jeder Lauf des dedizierten Dev-Workhorse-Pfads erzeugt nachvollziehbare file-first Artefakte und eine Session-Telemetriezeile.
  - Die Abschlussausgabe zeigt tatsaechliche Kosten oder einen expliziten Fallback-/Missing-Usage-Hinweis.
  - Der Janus-Healthcheck kann die neue Dev-Workhorse-Telemetrie lesen, ohne daraus globale OR-Freigabe oder Produktionsrouting abzuleiten.
- Tests:
  - Fixture-Test fuer file-first Artefakterzeugung und Session-JSONL
  - Positivtest fuer sichtbare Actual-Cost-Ausgabe nach Abschluss
  - Negativtest fuer Missing-Usage- oder Missing-Capture-Fallback
  - Healthcheck-Ingestion-Test fuer den neuen Dev-Workhorse-Pfad
- Model: 5.4
- Reason: Ohne sichtbare echte Kosten, nachvollziehbare Artefakte und Healthcheck-Einbindung bleibt der Produktivpfad operativ blind und damit nicht dauerhaft steuerbar.
- Closeout: Final Audit PASS ist in `documentation/tasks/TASK-SPEC22.4_final_audit.md` dokumentiert. File-first Telemetrie, wahrheitsgetreuer Actual-Cost-Closeout und die lokale Healthcheck-Sichtbarkeit fuer den dedizierten Dev-workhorse-Pfad sind damit task-scharf abgeschlossen; Spec 22 insgesamt ist DONE und bleibt weiterhin strikt auf diesen einen Dev-only, operator-invoked Pfad begrenzt.

@janus-task-breakdown
Spec: documentation/SPEC/Spec Done/22_operator_gesteuerter_or_arbeitspferd_produktivmodus_fuer_dev_arbeit.md
Task: documentation/tasks/TASK-SPEC22_operator_gesteuerter_or_arbeitspferd_produktivmodus_fuer_dev_arbeit.md
Backlog Item: N/A
Target Task: TASK-SPEC22.1
Mode: TASK_REFINEMENT
Execution Model: 5.4
Rules: USE_SPEC_AND_TASK_AS_SOURCE_OF_TRUTH_NO_IMPLEMENTATION_RELEASE_ONE_TARGET_TASK
Expected Output: TASK_REFINED_PLUS_PRECHECK_HANDOFF
