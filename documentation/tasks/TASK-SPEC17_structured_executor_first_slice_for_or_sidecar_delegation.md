TASK-SPEC17
- Source Spec: documentation/SPEC/17_structured_executor_first_slice_for_or_sidecar_delegation.md
- Backlog Item: N/A
- Feature: Structured Executor First Slice fuer OR- oder Sidecar-Delegation
- Generated At: 2026-06-15

## Generated Tasks

### TASK-SPEC17.1 Structured action request intake and validation skeleton
- Ziel: Einen lokalen Executor-Einstieg schaffen, der genau eine strukturierte Delegationsanfrage laedt, validiert und als deterministischen bounded Run vorbereitet.
- Scope: Request-Load, Schema-Validation, Run-Verzeichnis, Ergebnisartefakte und saubere Fehlerklassifikation fuer unbekannte oder ungueltige Aktionsarten.
- Files:
  - documentation/codex/model-routing/scripts/codex_structured_action_executor.py
  - documentation/codex/model-routing/schemas/codex_delegated_action_request.schema.json
  - documentation/codex/model-routing/structured-action-fixtures/
  - documentation/codex/model-routing/structured-action-runs/
- Steps:
  - Executor-Einstieg fuer genau eine JSON-Anfrage definieren.
  - Schema-Validierung gegen das bestehende Delegated-Action-Schema anbinden.
  - Deterministisches Run-Verzeichnis mit Request-Kopie, Validierungsresultat, stdout, stderr, Exit-Code und Executor-Summary anlegen.
  - Unbekannte oder verbotene Aktionsarten sauber ablehnen, ohne freie Shell-Ausfuehrung zu versuchen.
- Acceptance Criteria:
  - Der Executor kann eine gueltige strukturierte Anfrage laden und ein bounded Run-Verzeichnis mit Ergebnisartefakten erzeugen.
  - Ungueltige oder unbekannte Anfragen werden deterministisch abgelehnt und erzeugen einen reviewbaren Fehlerstatus.
  - Der Executor fuehrt keine freien Shell-Kommandos aus.
- Tests:
  - Unit-Test fuer gueltige Request-Validierung
  - Unit-Test fuer unbekannte Aktionsart
  - Unit-Test fuer fehlerhafte Schema-Anfrage
  - Fixture-basierter Dry-Run fuer Run-Verzeichnis und Summary-Artefakte
- Model: 5.4
- Reason: Der Slice ist implementierungsnah, aber noch klar begrenzt und repo-lokal.

### TASK-SPEC17.2 Deterministic generator mapping for first janus-test-pipeline path
- Ziel: Den ersten freigegebenen `run_generator`-Pfad fuer bounded `janus-test-pipeline` Delegation deterministisch lokal ausfuehrbar machen.
- Scope: Mapping fuer mindestens einen freigegebenen Generator, feste Argumentvorlage, Eingabeuebergabe, Output-Allowlist und Artefaktpruefung.
- Files:
  - documentation/codex/model-routing/scripts/codex_structured_action_executor.py
  - tests/e2e/generator/compile-testspec-to-testplan.mjs
  - documentation/codex/model-routing/structured-action-fixtures/
  - documentation/codex/model-routing/structured-action-runs/
- Steps:
  - `run_generator` fuer einen ersten freigegebenen `generator_id` an den bekannten lokalen Generator mappen.
  - Nur deklarierte Eingaben und vorab erlaubte Outputs zulassen.
  - stdout, stderr, Exit-Code und Output-Artefaktstatus erfassen.
  - Bei fehlender Mapping-Route oder fehlgeschlagenem Generator einen klaren Fallback-Status fuer Codex-local erzeugen.
- Acceptance Criteria:
  - Ein erlaubter `run_generator`-Request fuehrt den lokal gemappten Generator deterministisch aus.
  - Nur deklarierte Eingaben und erlaubte Outputs werden akzeptiert.
  - Fehlende Mapping-Routen oder Generator-Fehler fuehren nicht zu Shell-Improvisation, sondern zu reviewbarem Fallback.
- Tests:
  - Integrationstest fuer erlaubten `run_generator`
  - Negativtest fuer unbekannten `generator_id`
  - Negativtest fuer nicht erlaubte Output-Pfade
  - Fixture-basierter Executor-Run mit Artefaktpruefung
- Model: 5.4
- Reason: Die Aufgabe verknuepft Delegationslogik mit einem bekannten lokalen Generator und braucht fokussierte Implementierung.

### TASK-SPEC17.3 Deterministic validator path and delegated fallback integration
- Ziel: Den ersten `run_validator`-Pfad plus den unmittelbaren Codex-local-Fallback fuer den bounded Delegationspfad vervollstaendigen.
- Scope: Validator-Mapping, Validierungsstatus, Fallback-Klassifikation und Integration mit dem bestehenden delegated Operator-Pfad fuer bounded `janus-test-pipeline` Schritte.
- Files:
  - documentation/codex/model-routing/scripts/codex_structured_action_executor.py
  - documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
  - documentation/codex/model-routing/scripts/codex_test_result_triage_review_runner.py
  - documentation/codex/model-routing/scripts/codex_structured_action_sidecar_bridge.py
  - documentation/codex/model-routing/structured-action-fixtures/
  - documentation/codex/model-routing/structured-action-runs/
- Steps:
  - `run_validator` fuer einen ersten freigegebenen Validator-Pfad verdrahten.
  - Pass oder Fail sauber im Executor-Summary abbilden.
  - Delegierten bounded `janus-test-pipeline` Pfad so anbinden, dass bei fehlender Route oder fehlgeschlagener lokaler Aktion sofort Codex-local uebernommen werden kann.
  - Reviewbare Hinweise fuer den Operator erzeugen, warum der lokale Fallback aktiv wurde.
- Acceptance Criteria:
  - Ein erlaubter `run_validator`-Request laeuft deterministisch lokal und erzeugt reviewbare Pass- oder Fail-Artefakte.
  - Fehlende Routen oder fehlgeschlagene Validatoren aktivieren den vorgesehenen Codex-local-Fallback.
  - Der bestehende bounded Operator-Pfad bleibt benutzbar und fuehrt keine freie delegierte Shell-Ausfuehrung mehr aus, wenn der strukturierte Executor greift.
- Tests:
  - Integrationstest fuer erlaubten `run_validator`
  - Negativtest fuer Validator-Fehler mit Fallback
  - Integrationstest fuer Dispatcher- oder Bridge-Fallback in den lokalen Pfad
  - Regressionstest, dass bestehende read-only bounded Delegation nicht gebrochen wird
- Model: 5.4
- Reason: Die Aufgabe verbindet den Executor mit dem realen bounded Delegationsfluss und braucht gezielte Integrations- und Regressionstests.
