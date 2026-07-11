# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING

target_skill: janus-spec-review
recommended_model: 5.4
recommended_reasoning: medium-high
new_chat: no
complexity_score: 63
confidence: HIGH
dashboard_hint: CAUTION
reason: Bounded delegated write-apply candidate needs strict scope, validation, and Codex acceptance rules without broad write authority.

## SPEC REVIEW METADATA

- **Review Status:** APPROVED_WITH_NOTES
- **Complexity Score:** 63
- **Risk:** HIGH
- **Recommended Review Model:** 5.4
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-06-15
- **Review Confidence:** HIGH
- **Review Source:** janus-spec-review

## FEATURE IDENTITY

- Feature Name: Bounded Execution Write Apply Candidate fuer OR- oder Sidecar-Delegation
- Primary Goal: Einen eng begrenzten write-nahen Delegationspfad schaffen, bei dem OR oder Sidecar innerhalb einer exakten Allowlist einen Aenderungsversuch liefern darf, waehrend Codex Validierung, Annahme oder Ablehnung kontrolliert.
- User Problem: Das vorhandene OR- oder Sidecar-Fundament ist auditiert, uebernimmt aber noch nicht den fuer den Alltag wertvollen Teil echter Aenderungsarbeit innerhalb eines klar begrenzten Codex-Workflows.
- Routing Decision: 5.4
- Routing Reasoning: medium-high
- Routing Confidence: HIGH
- Dashboard Hint: CAUTION

## USER VALUE

Der Nutzer kann spaeter bei passenden Codex-Arbeitsaufgaben zwischen voll lokalem Codex-Pfad und einem bounded delegated write candidate waehlen, ohne die Reviewbarkeit oder Validierungsdisziplin zu verlieren.

Codex-Kontingent kann dadurch bei kleinen, eng gebundenen Aenderungsslices geschont werden, waehrend Codex die fachliche Endkontrolle behaelt.

## TARGET SURFACE

- Primary Target Surface: Bounded Delegationspfad innerhalb von `janus-executioner`
- Existing or New Surface: Existing Surface Extension
- Existence Confirmation: confirmed by user
- Included Surfaces: operator-invoked delegated execution candidate, exact file-cluster allowlist, changed-files capture, diff capture, validation summary, Codex acceptance flow
- Excluded Surfaces: broad repo writes, unrestricted workspace-write, release or Git authority, direct production routing

## USER ACTION SURFACE

- User Trigger: Der Nutzer waehlt in einem vorgeprueften `janus-executioner`-Slice den bounded delegated Pfad statt des rein lokalen Codex-Pfads.
- Action Type: Operator-gesteuerte Auswahl zwischen `Codex` und `Delegated` fuer genau einen gebundenen Zieltask mit exakter Dateigrenze.
- Feedback: Codex zeigt den bounded Gate-Kontext, den Delegationsausgang, die geaenderten Dateien, das Diff und das Validierungsergebnis sichtbar an.
- Confirmation Behavior: Codex behaelt die ausdrueckliche Annahme- oder Ablehnungsentscheidung ueber den delegated Aenderungsversuch.
- Cancel / Undo Behavior: Wenn der delegated Versuch unvollstaendig, ungueltig oder ausserhalb der Allowlist ist, verwirft Codex den delegated Ausgang und fuehrt lokal weiter.

## SYSTEM BEHAVIOR

Wenn ein vorgepruefter `janus-executioner`-Task genau einen gebundenen Zielslice mit exakter Dateigrenze hat, darf der Operator zwischen lokalem Codex-Pfad und bounded delegated write candidate waehlen.

Wenn der Operator den delegated Pfad waehlt, darf OR oder Sidecar den Aenderungsversuch nur innerhalb einer exakten Allowlist und eines vorab festgelegten Touched-File-Caps ausfuehren.

Wenn der delegated Versuch laeuft, muessen immer ein reviewbares Diff, eine Changed-Files-Liste, ein Validierungsergebnis und die Standard-Run-Artefakte entstehen.

Wenn eine Datei ausserhalb der Allowlist beruehrt wird, der Touched-File-Cap ueberschritten wird, Delete-, Rename- oder Move-Aktivitaet auftaucht oder Validierungsartefakte fehlen, wird der delegated Ausgang nicht akzeptiert.

Wenn lokale Validierung fehlschlaegt, markiert Codex den delegated Ausgang als nicht akzeptiert und fuehrt lokal oder manuell weiter.

Wenn der delegated Ausgang alle Gates besteht, bleibt Codex trotzdem Besitzer von Mini-TestPlan, Validierungsinterpretation, manueller Janus-Pruefung und finalem Abschlussstatus.

Wenn der Zielslice mehr als einen Dateicluster, mehr als einen Task oder eine neue Architekturentscheidung braucht, ist dieser bounded write candidate nicht zulaessig.

## DATA / PERSISTENCE

- Created Data: Delegationsartefakte wie `summary.json`, `git_diff.patch`, `changed_files.txt`, `validation_summary.json`, `stdout.log`, `stderr.log` und `exit_code.txt`
- Updated Data: Nicht zutreffend: Diese Spec definiert nur den bounded Delegations- und Reviewpfad, nicht eine konkrete Produktdatenmutation
- Deleted Data: Keine automatische Loeschung als regulaerer erfolgreicher Pfad
- Remembered Data: Nicht zutreffend: Keine neue Memory- oder Nutzerpersistenz
- Canonical Review Record: Codex-Review plus die bounded Run-Artefakte sind die kanonische Entscheidungsbasis fuer Annahme oder Ablehnung
- Failure Persistence: Unvollstaendige oder fehlgeschlagene delegated Versuche bleiben als reviewbare bounded Artefakte sichtbar, ohne automatisch als erfolgreiche Task-Erledigung zu zaehlen

## CONSTRAINTS

Der write candidate gilt nur fuer genau einen vorgeprueften Zieltask-Slice.

Der write candidate gilt nur fuer genau einen explizit deklarierten Dateicluster.

Die Allowlist muss vor der delegated Ausfuehrung feststehen und darf nicht dynamisch erweitert werden.

Der Touched-File-Cap muss vor der delegated Ausfuehrung feststehen und darf nicht stillschweigend ueberschritten werden.

Der delegated Pfad darf keine freie Shell-Improvisation, keine Git-Operationen und keine Abschlussclaims fuer Audit, Release oder Task-Fertigstellung erzeugen.

Der delegated Pfad darf keine Delete-, Rename- oder Move-Aktivitaet als normalen Erfolgsweg enthalten.

## SECURITY / PRIVACY

- Write Boundary: Delegated Aenderungen sind nur innerhalb der vorab deklarierten Allowlist erlaubt.
- Forbidden Authority: Kein Git, kein Release, kein Routing-Umschalten, keine Audit-Hoheit, keine broad repo write authority
- Validation Ownership: Codex bleibt Besitzer der Validierungsinterpretation und finalen Annahme- oder Ablehnungsentscheidung.
- Privacy Risk: Nicht zutreffend: Diese Spec fuehrt keinen neuen externen Datenabfluss oder neuen Nutzerdatenpfad ein; sie aendert nur den bounded lokalen Arbeitsmodus.
- Abort Conditions: Allowlist-Verletzung, Touched-File-Cap-Verletzung, Delete-, Rename- oder Move-Aktivitaet, fehlendes Diff, fehlende Validierungsartefakte oder fehlgeschlagene lokale Validierung fuehren zur Ablehnung des delegated Ausgangs.
- Transparency: Codex zeigt fuer den delegated Ausgang sichtbar `changed_files`, `git_diff`, `validation_result` und den finalen Accept-/Reject-Status an.

## EDGE CASES

Ein Zielslice mit mehr als einem Dateicluster ist nicht fuer diesen bounded Pfad geeignet.

Ein Zielslice mit Migration, Provider-Routing-Aenderung, Persistenz-Shape-Aenderung oder Security- beziehungsweise Privacy-Grenze ist nicht fuer den ersten bounded write candidate geeignet.

Ein delegated Ausgang ohne Diff, ohne Changed-Files-Nachweis oder ohne Validierungszusammenfassung ist automatisch unvollstaendig.

Wenn der delegated Ausgang fachlich brauchbar wirkt, aber Validierung fehlt oder unklar ist, darf Codex ihn nicht stillschweigend als akzeptiert behandeln.

Wenn der delegated Ausgang die richtigen Dateien beruehrt, aber der Touched-File-Cap ueberschritten wurde, bleibt das Ergebnis nicht akzeptiert.

Wenn der delegated Ausgang behauptet, der Task sei fertig, auditiert oder releasebereit, ohne dass Codex das bestaetigt hat, gilt das als uebergriffiger Completion-Claim und fuehrt zur Ablehnung.

## DEFINITION OF DONE

- [ ] Wenn ein vorgepruefter Zielslice genau einen Dateicluster und einen klaren Mini-TestPlan hat, dann kann Codex dafuer sichtbar zwischen lokalem und delegated write-candidate Pfad unterscheiden.
- [ ] Wenn der delegated Pfad gewaehlt wird, dann entstehen immer ein reviewbares Diff, eine Changed-Files-Liste und eine Validierungszusammenfassung.
- [ ] Wenn eine Datei ausserhalb der Allowlist geaendert wird, dann wird der delegated Ausgang nicht akzeptiert.
- [ ] Wenn der Touched-File-Cap ueberschritten wird, dann wird der delegated Ausgang nicht akzeptiert.
- [ ] Wenn Delete-, Rename- oder Move-Aktivitaet auftaucht, dann wird der delegated Ausgang nicht akzeptiert.
- [ ] Wenn Validierungsartefakte fehlen oder lokale Validierung fehlschlaegt, dann verwirft Codex den delegated Ausgang und fuehrt nicht stillschweigend mit ihm weiter.
- [ ] Wenn alle bounded Gates bestehen, dann bleibt Codex trotzdem Besitzer der finalen Annahme- oder Ablehnungsentscheidung.
- [ ] Wenn ein Zielslice mehr als einen Dateicluster oder eine neue Architekturentscheidung braucht, dann ist er fuer den ersten bounded write candidate nicht zulaessig.

## TEST STRATEGY

- Unit Tests: Allowlist-Pruefung, Touched-File-Cap-Pruefung, Delete-/Rename-/Move-Tripwire, Artefakt-Vollstaendigkeit
- Integration Tests: Delegated write candidate innerhalb einer exakten Allowlist mit reviewbarem Diff plus lokaler Validierungszusammenfassung
- Negative Tests: Allowlist-Verletzung, ueberschrittener Touched-File-Cap, fehlendes Diff, fehlende Validierungsartefakte, uebergriffiger Completion-Claim
- Manual Test: Ein spaeterer echter prechecked Mini-Slice mit 1 bis 2 erlaubten Dateien und klarer lokaler Abnahme durch Codex
- Regression Tests: Bestehende Codex-only `janus-executioner`-Pfade und read-only bounded Delegation bleiben unveraendert benutzbar

## OUT OF SCOPE

Breiter Repo-Schreibzugriff durch OR oder Sidecar.

Direkte finale Task-Abschluss-Hoheit fuer delegated Pfade.

Delegierte Test-Ausfuehrung als allgemeiner Ersatz fuer lokale Validierung.

Multi-Task-Ausfuehrung oder mehrere Dateicluster in einem delegated write candidate.

Production Routing, Routing-Tabellen-Updates, Release-Pfade oder Git-Autoritaet.

## INTERNAL COMPLEXITY BREAKDOWN

- Scope Size: 12
- Architectural Risk: 15
- State / Persistence Complexity: 10
- Cross-System Dependencies: 16
- Ambiguity Level: 10
- Total Complexity Score: 63

## SPEC IMPLEMENTATION METADATA

- **Implementation Status:** DONE
- **Final Audit:** PASS
- **Completed At:** 2026-06-15
- **Audit Package:** `documentation/tasks/TASK-SPEC18_AUDIT_PACKAGE.md`
- **Final Audit Report:** `documentation/tasks/TASK-SPEC18_final_audit.md`
- **Validation Evidence:**
  - `python -m py_compile documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/model-routing/scripts/codex_structured_action_request_builder.py`
  - `python -m pytest documentation/codex/model-routing/tests/test_bounded_write_candidate_entry_gate.py -q`
  - `python C:\Users\pruve\.codex\skills\janus-executioner\scripts\validate_execution_result.py documentation/tasks/TASK-SPEC18.1_execution_result.md`
  - `python -m py_compile documentation/codex/model-routing/scripts/codex_execution_write_apply_candidate_runner.py`
  - `python -m pytest documentation/codex/model-routing/tests/test_bounded_write_candidate_artifact_capture.py -q`
  - `python C:\Users\pruve\.codex\skills\janus-executioner\scripts\validate_execution_result.py documentation/tasks/TASK-SPEC18.2_execution_result.md`
  - `python -m py_compile documentation/codex/model-routing/scripts/codex_execution_write_apply_candidate_runner.py documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`
  - `python -m pytest documentation/codex/model-routing/tests/test_bounded_write_candidate_validation_acceptance.py -q`
  - `python documentation/codex/model-routing/tests/test_bounded_write_candidate_validation_acceptance.py`
  - `python C:\Users\pruve\.codex\skills\janus-executioner\scripts\validate_execution_result.py documentation/tasks/TASK-SPEC18.3_execution_result.md`
  - `python C:\Users\pruve\.codex\skills\janus-final-audit\scripts\validate_final_audit.py documentation/tasks/TASK-SPEC18_final_audit.md`
