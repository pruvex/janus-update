TASK-SPEC21
- Source Spec: documentation/SPEC/Spec Done/21_assisted_or_workhorse_mode_for_janus_skills.md
- Backlog Item: N/A
- Feature: Assistierter OR-Arbeitspferd-Modus fuer Janus-Skills
- Generated At: 2026-06-20

## Generated Tasks

### TASK-SPEC21.1 Enforce a locally testable OR eligibility and context-redaction gate for the pilot skills
- Ziel: Vor jedem externen OR-Request eine harte, lokal pruefbare Zulassungs- und Datenminimierungsgrenze erzwingen, damit nur die freigegebenen bounded Klassen in `janus-debug` und `janus-test-pipeline` ueberhaupt OR anbieten koennen.
- Scope: Shared Eligibility-Contract fuer die erste Pilotmenge, explizite Allowlist fuer `debug_hypothesis_review` und `test_result_triage_review`, testbare Kontext-Redaction/Allowlist-Regeln und deterministischer No-Gate-Fallback fuer alle anderen Skills oder Klassen.
- Files:
  - documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py
  - documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
  - documentation/codex/model-routing/scripts/codex_structured_action_request_builder.py
  - documentation/codex/model-routing/tests/
- Steps:
  - Einen gemeinsamen Eligibility-Contract definieren, der im ersten Rollout nur `janus-debug` mit `debug_hypothesis_review` und `janus-test-pipeline` mit `test_result_triage_review` zulaesst.
  - Eine lokal testbare Kontext-Allowlist und Redaction-Regel einziehen, die nur fuer den bounded Schritt noetige Felder an OR weitergeben darf.
  - Nicht freigegebene Skills, nicht freigegebene Task-Klassen oder unzureichend redigierte Pakete deterministisch vor dem OR-Gate blockieren.
  - Reviewbare Status- oder Fehlerausgaenge fuer `OR_NOT_ELIGIBLE`, `OR_CONTEXT_REDACTION_REQUIRED` und `OR_ALLOWED` bereitstellen.
- Acceptance Criteria:
  - Nur die zwei pilotierten bounded Klassen koennen ueber den Shared Contract ueberhaupt OR-eligible werden.
  - Ein Paket mit nicht erlaubten oder nicht redigierten Feldern wird vor dem OR-Request deterministisch blockiert.
  - Alle anderen Janus-Skills und Task-Klassen bleiben Codex-only, ohne implizite OR-Fallback-Logik.
- Tests:
  - Positivtest fuer `debug_hypothesis_review` mit erlaubtem, redigiertem Paket
  - Positivtest fuer `test_result_triage_review` mit erlaubtem, redigiertem Paket
  - Negativtest fuer nicht freigegebene Skill- oder Task-Klasse
  - Negativtest fuer Paket mit verbotenen oder unredigierten Feldern
- Model: 5.4
- Reason: Dieser Slice zieht die sicherheits- und scopekritische Zulassungsgrenze hart ein und setzt die Review-Note in einen lokal validierbaren Contract um.

### TASK-SPEC21.2 Normalize the operator gate with mandatory cost and confidence display
- Ziel: Fuer die zwei zugelassenen bounded Pilotklassen eine einheitliche sichtbare Auswahl `1 = Codex` und `2 = OR-Arbeitspferd` mit verpflichtender Kosten- und Confidence-Anzeige herstellen.
- Scope: Shared Gate-Prompt, skill-uebergreifende Operator-Texte fuer Debug und Test-Triage, Pflichtfelder fuer ausgewaehltes OR-Modell, Kostenprognose und Confidence sowie No-Gate-Verhalten bei fehlenden Pflichtdaten.
- Files:
  - documentation/codex/model-routing/scripts/bounded_or_worker_gate_prompt.py
  - documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
  - documentation/codex/skills/janus-debug/SKILL.md
  - documentation/codex/skills/janus-test-pipeline/SKILL.md
  - documentation/codex/model-routing/tests/
- Steps:
  - Den gemeinsamen Operator-Gate-Text fuer die Pilotklassen auf `1 = Codex` und `2 = OR-Arbeitspferd` normalisieren.
  - Pflichtfelder fuer OR-Modell, voraussichtliche Kosten und Confidence im Gate erzwingen.
  - Fehlende Kosten-, Confidence- oder Eligibility-Daten deterministisch als No-Gate oder Codex-only behandeln.
  - Die Skill-Anleitungen fuer `janus-debug` und `janus-test-pipeline` an den gemeinsamen Gate-Stil und die bounded Pilotgrenze angleichen.
- Acceptance Criteria:
  - Beide Pilotklassen zeigen denselben klaren Codex-vs-OR-Gate-Stil.
  - Ein OR-Gate ohne Modell-, Kosten- und Confidence-Hinweis wird nicht als regulaere Auswahl ausgegeben.
  - Die Skill-Dokumentation beschreibt OR weiterhin als bounded assist-only und nicht als autonome oder produktionsnahe Routing-Entscheidung.
- Tests:
  - Positivtest fuer Gate-Ausgabe mit Modell, Kosten und Confidence
  - Negativtest fuer fehlende Kosten
  - Negativtest fuer fehlende Confidence
  - Regressionstest fuer unveraenderten Codex-only Ausgang bei No-Gate-Faellen
- Model: 5.4
- Reason: Der Alltagseinstieg in das Feature ist die Operator-Auswahl; sie muss fuer beide Skills konsistent und vertrauenswuerdig sein, bevor Telemetrie oder Runner-Integration Sinn ergeben.
- Closeout: Final Audit PASS ist in `documentation/tasks/TASK-SPEC21.2_final_audit.md` dokumentiert. Die sichtbare Gate-Normalisierung ist damit task-scharf abgeschlossen; Spec 21 insgesamt bleibt offen, weil `TASK-SPEC21.3` und `TASK-SPEC21.4` weiterhin ausstehen.

### TASK-SPEC21.3 Add file-first OR capture, telemetry, and healthcheck ingestion for accepted and rejected pilot runs
- Ziel: Jeden bounded OR-Lauf der Pilotklassen mit file-first Capture, Kosten-/Usage-Erfassung, Validation-Result und lokaler Healthcheck-Ingestion nachvollziehbar machen, ohne Produktionsrouting zu aktivieren.
- Scope: File-first Capture-Artefakte, Telemetrie-Zeile pro Lauf, Accepted/Rejected/Fallback-Klassifikation, Kostenanzeige nach Abschluss und Healthcheck-Summary fuer diese bounded Pilotlaeufe.
- Files:
  - documentation/codex/model-routing/scripts/or_file_first_capture_wrapper.ps1
  - documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
  - documentation/codex/model-routing/scripts/bounded_or_worker_outcome.py
  - documentation/codex/skills/janus-health-check/scripts/health_snapshot.py
  - documentation/codex/model-routing/tests/
- Steps:
  - Den file-first Capture-Pfad fuer bounded OR-Pilotlaeufe an den gemeinsamen Dispatcher anbinden.
  - Kostenprognose, tatsaechliche Kosten, Validation-Result, Fallback-Status und finalen Outcome in eine gemeinsame Telemetrieform bringen.
  - Healthcheck-Ingestion fuer diese bounded Telemetrie so erweitern, dass Reliability-, Cost- und Fallback-Summaries fuer Debug- und Test-Triage-Laeufe lesbar bleiben.
  - Sicherstellen, dass unvollstaendige Capture- oder Usage-Daten nicht als akzeptierter Erfolg erscheinen.
- Acceptance Criteria:
  - Ein akzeptierter oder abgelehnter Pilotlauf erzeugt nachvollziehbare file-first Artefakte und eine gemeinsame Telemetriezeile.
  - Die Abschlussausgabe kann tatsaechliche OR-Kosten anzeigen oder einen dokumentierten Fallback markieren, wenn Usage fehlt.
  - `health_snapshot.py` kann die bounded OR-Telemetrie lesen, ohne bestehende Healthcheck-Pfade zu brechen.
- Tests:
  - Fixture-Test fuer vollstaendige file-first Capture- und Telemetrie-Erzeugung
  - Negativtest fuer fehlende Usage- oder Capture-Daten mit Reject/Fallback-Ausgang
  - Healthcheck-Ingestion-Test gegen bounded OR-Telemetrie
  - Regressionstest fuer bestehenden Healthcheck ohne OR-Eingabe
- Model: 5.4
- Reason: Sichtbare tatsaechliche Kosten und klare Reject/Fallback-Evidenz sind Kernbestandteil der Spec und muessen technisch stabil sein, bevor echte Skill-Nutzung verlässlich werden kann.

- Closeout: Final Audit PASS ist in `documentation/tasks/TASK-SPEC21.3_final_audit.md` dokumentiert. File-first Capture, truthy Telemetrie-Finalisierung und lokale Healthcheck-Ingestion sind damit task-scharf abgeschlossen; Spec 21 insgesamt bleibt offen, weil `TASK-SPEC21.4` weiterhin aussteht.

### TASK-SPEC21.4 Integrate the bounded OR worker path into janus-debug and janus-test-pipeline without widening the pilot scope
- Ziel: Die zwei erlaubten bounded Consumer `debug_hypothesis_review` und `test_result_triage_review` an den gemeinsamen Gate-, Capture- und Acceptance-Pfad anbinden, waehrend alle anderen Modi und Skills Codex-only bleiben.
- Scope: Consumer-Integration in die beiden vorhandenen Runner, lokale Fallback- und Manual-Review-Semantik, skill-nahe Operator-Summaries und fokussierte Regression fuer die zwei Pilotpfade.
- Files:
  - documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py
  - documentation/codex/model-routing/scripts/codex_test_result_triage_review_runner.py
  - documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
  - documentation/codex/skills/janus-debug/SKILL.md
  - documentation/codex/skills/janus-test-pipeline/SKILL.md
  - documentation/codex/model-routing/tests/
- Steps:
  - Die Debug-Hypothesis-Review- und Test-Result-Triage-Runner an den gemeinsamen Eligibility-, Gate-, Capture- und Outcome-Pfad anbinden.
  - Sicherstellen, dass Codex in beiden Skills Owner fuer Reproduktion, Validierung, Routingentscheidung und finale Annahme bleibt.
  - Manual-Review- und Fallback-Verhalten fuer truncierte, unparsebare, cap-verletzende oder validatorisch unsichere Ergebnisse vereinheitlichen.
  - Regression absichern, dass andere Debug-/Test-Pipeline-Modi nicht stillschweigend einen OR-Pfad erhalten.
- Acceptance Criteria:
  - `janus-debug` kann OR nur fuer `debug_hypothesis_review` anbieten und behaelt sonst den Codex-only Pfad.
  - `janus-test-pipeline` kann OR nur fuer `test_result_triage_review` anbieten und behaelt sonst den Codex-only Pfad.
  - Akzeptierte, abgelehnte und Manual-Review-Ergebnisse zeigen einen klaren Codex-owned Abschlussstatus mit Modell- und Kostenkontext.
  - Keine andere Janus-Skill- oder Test-Pipeline-Klasse erhaelt durch diese Integration implizit einen OR-Pfad.
- Tests:
  - Positivtest fuer `debug_hypothesis_review` mit sichtbarem Gate und Codex-owned Abschluss
  - Positivtest fuer `test_result_triage_review` mit sichtbarem Gate und Codex-owned Abschluss
  - Negativtest fuer nicht freigegebene Debug- oder Test-Pipeline-Modi
  - Regressionstest fuer lokale Codex-only Pfade ausserhalb der Pilotklassen
- Model: 5.4
- Reason: Dieser Slice bringt die Foundations in genau die zwei freigegebenen Alltagspfade und haelt dabei die Pilotgrenze gegen Scope-Drift explizit geschlossen.
- Closeout: Final Audit PASS ist in `documentation/tasks/TASK-SPEC21.4_final_audit.md` dokumentiert. Die bounded Consumer-Integration ist damit task-scharf abgeschlossen; Spec 21 insgesamt ist DONE und bleibt weiterhin strikt auf `debug_hypothesis_review` und `test_result_triage_review` begrenzt.

@janus-task-breakdown
Spec: documentation/SPEC/Spec Done/21_assisted_or_workhorse_mode_for_janus_skills.md
Task: documentation/tasks/TASK-SPEC21_assisted_or_workhorse_mode_for_janus_skills.md
Backlog Item: N/A
Target Task: TASK-SPEC21.1
Mode: TASK_REFINEMENT
Execution Model: 5.4
Rules: USE_SPEC_AND_TASK_AS_SOURCE_OF_TRUTH_NO_IMPLEMENTATION_RELEASE_ONE_TARGET_TASK
Expected Output: TASK_REFINED_PLUS_PRECHECK_HANDOFF
