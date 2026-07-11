TASK-SPEC18
- Source Spec: documentation/SPEC/18_bounded_execution_write_apply_candidate_for_or_sidecar_delegation.md
- Backlog Item: N/A
- Feature: Bounded Execution Write Apply Candidate fuer OR- oder Sidecar-Delegation
- Generated At: 2026-06-15

## Generated Tasks

### TASK-SPEC18.1 Exact write-candidate entry contract and allowlist enforcement
- Ziel: Den ersten bounded write-candidate Einstieg so haerten, dass nur vorgepruefte Zieltasks mit exakter Allowlist, Touched-File-Cap und Codex-owned acceptance contract ueberhaupt in den delegated write-Pfad gelangen.
- Scope: Entry-Contract-Pruefung, Allowlist-Erzwingung, Touched-File-Cap-Vorbereitung, Delete-/Rename-/Move-Tripwire und reviewbarer Reject-Status vor jeder spaeteren delegated Annahme.
- Files:
  - documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
  - documentation/codex/model-routing/scripts/codex_structured_action_request_builder.py
  - documentation/codex/model-routing/structured-action-fixtures/
  - documentation/codex/model-routing/tests/
- Steps:
  - Einen bounded write-candidate Entry-Contract fuer genau einen Zieltask-Slice definieren und lokal erzwingen.
  - Exakte editable-path Allowlist und Touched-File-Cap als Pflichtfelder im delegated Einstieg behandeln.
  - Delete-, Rename- und Move-Tripwire in den candidate Pfad integrieren.
  - Reviewbare Reject- oder Fallback-Zustaende fuer unvollstaendige oder ungueltige write-candidate Eingaben erzeugen.
- Acceptance Criteria:
  - Ein write-candidate Einstieg ohne exakte Allowlist oder ohne Touched-File-Cap wird deterministisch abgelehnt.
  - Delete-, Rename- oder Move-Intent fuehren nicht zu einer delegated Erfolgsroute.
  - Reviewbare Statusartefakte unterscheiden sauber zwischen zulassungsfaehigem und abgelehntem candidate Einstieg.
- Tests:
  - Negativtest fuer fehlende Allowlist
  - Negativtest fuer fehlenden Touched-File-Cap
  - Negativtest fuer Delete-/Rename-/Move-Intent
  - Fixture-basierter Dispatcher- oder Builder-Run mit reviewbarem Reject-Status
- Model: 5.4
- Reason: Die Aufgabe ist implementierungsnah, sicherheitsrelevant und muss den write-candidate Pfad zuerst streng begrenzen, bevor spaetere Diff- oder Apply-Schritte sinnvoll sind.

### TASK-SPEC18.2 Diff and changed-files capture for bounded delegated write candidate
- Ziel: Sicherstellen, dass ein zugelassener delegated write candidate immer ein Diff, eine Changed-Files-Liste und die Standard-Run-Artefakte erzeugt, statt still oder unvollstaendig zu enden.
- Scope: Diff-Capture, Changed-Files-Capture, Artefakt-Vollstaendigkeit und reject-faehige Vollstaendigkeitspruefung fuer delegated write candidates.
- Files:
  - documentation/codex/model-routing/scripts/codex_sidecar_skill_runner.ps1
  - documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
  - documentation/codex/model-routing/structured-action-runs/
  - documentation/codex/model-routing/tests/
- Steps:
  - Den write-candidate Pfad so erweitern, dass `git_diff.patch` und `changed_files.txt` als Pflichtartefakte entstehen.
  - Artefakt-Vollstaendigkeit fuer `summary.json`, `stdout.log`, `stderr.log`, `exit_code.txt`, Diff und Changed-Files pruefen.
  - Fehlende oder leere Review-Artefakte als reject-faehigen delegated Ausgang markieren.
  - Den Operator-Ausgang auf reviewbare Write-Candidate-Felder normalisieren.
- Acceptance Criteria:
  - Ein delegated write candidate ohne Diff oder ohne Changed-Files-Nachweis wird nicht als akzeptierbar behandelt.
  - Die Pflichtartefakte sind fuer den reviewbaren candidate Ausgang konsistent und nachvollziehbar abgelegt.
  - Der Operator-Ausgang zeigt mindestens Status, Changed-Files, Allowlist-Status und finalen Candidate-Ausgang.
- Tests:
  - Integrationstest fuer vollstaendigen delegated write candidate mit Diff plus Changed-Files
  - Negativtest fuer fehlendes Diff
  - Negativtest fuer fehlende Changed-Files-Liste
  - Artefakt-Vollstaendigkeitstest fuer die Pflichtdateien
- Model: 5.4
- Reason: Ohne reviewbares Diff und Changed-Files-Nachweis liefert der delegated write candidate keinen brauchbaren Alltagwert fuer Codex-Abnahme.

### TASK-SPEC18.3 Validation summary and Codex-owned accept-reject flow for delegated write candidate
- Ziel: Den delegated write candidate mit lokaler Validierungszusammenfassung und einem expliziten Codex-owned accept- oder reject-Fluss abschliessen, ohne bereits breite write authority oder Task-Abschluss-Hoheit zu vergeben.
- Scope: Validation-summary Capture, reject bei fehlender oder fehlschlagender Validierung, operator-facing final outcome und Regression gegen bestehende Codex-only Pfade.
- Files:
  - documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
  - documentation/codex/model-routing/scripts/codex_execution_write_apply_candidate_runner.py
  - documentation/codex/model-routing/structured-action-runs/
  - documentation/codex/model-routing/tests/
- Steps:
  - `validation_summary.json` als Pflichtartefakt in den delegated write candidate integrieren.
  - Kandidaten mit fehlender oder fehlschlagender lokaler Validierung deterministisch als nicht akzeptierbar markieren.
  - Den finalen operator-facing candidate Ausgang auf Codex-owned accept oder reject ownership normalisieren.
  - Regression pruefen, dass Codex-only `janus-executioner`-Pfade und bestehende read-only bounded Delegation nicht gebrochen werden.
- Acceptance Criteria:
  - Ein delegated write candidate ohne `validation_summary.json` wird nicht als akzeptierbar behandelt.
  - Fehlgeschlagene lokale Validierung fuehrt zu einem reviewbaren reject- oder fallback-Ausgang statt zu stiller Annahme.
  - Der candidate Ausgang behauptet keine finale Task-Erledigung, Audit- oder Release-Reife ohne Codex-Bestaetigung.
- Tests:
  - Integrationstest fuer delegated write candidate mit vorhandener lokaler Validierungszusammenfassung
  - Negativtest fuer fehlende Validierungszusammenfassung
  - Negativtest fuer fehlschlagende lokale Validierung
  - Regressionstest fuer Codex-only execution path und bestehende read-only bounded delegation
- Model: 5.4
- Reason: Dieser Slice verbindet den delegated write candidate mit der fuer den Alltag entscheidenden Codex-Abnahme-Disziplin, ohne den bounded Scope zu verlieren.
