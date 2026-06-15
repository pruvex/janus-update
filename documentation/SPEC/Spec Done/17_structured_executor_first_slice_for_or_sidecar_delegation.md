# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING

target_skill: janus-spec-review
recommended_model: 5.4
recommended_reasoning: medium-high
new_chat: no
complexity_score: 62
confidence: HIGH
dashboard_hint: CAUTION
reason: First structured executor slice changes bounded delegation behavior for janus-test-pipeline but stays within a narrow, reviewable scope.

## SPEC REVIEW METADATA

- **Review Status:** APPROVED_WITH_NOTES
- **Complexity Score:** 62
- **Risk:** HIGH
- **Recommended Review Model:** 5.4
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-06-15
- **Review Confidence:** HIGH
- **Review Source:** janus-spec-review

## FEATURE IDENTITY

- Feature Name: Structured Executor First Slice fuer OR- oder Sidecar-Delegation
- Primary Goal: Delegierte Janus-TestPipeline-Schritte sollen keine freien Shell-Kommandos mehr benoetigen, sondern ueber einen deterministischen lokalen Executor laufen.
- User Problem: Guenstigere OR- oder Sidecar-Modelle koennen die fachliche Arbeit oft leisten, aber freie Windows-Shell-Ausfuehrung ist zu fragil und blockiert verlaessliche Alltagsdelegation.
- Routing Decision: 5.4
- Routing Reasoning: medium-high
- Routing Confidence: HIGH
- Dashboard Hint: CAUTION

## USER VALUE

Janus kann repetitive TestPipeline-Arbeit wirtschaftlicher auslagern, ohne dass der Nutzer Shell-Fehler, PATH-Probleme oder unstabile Delegationslaeufe ausbaden muss.

Codex bleibt die Autoritaet fuer Review, Validierung und Annahme, waehrend guenstigere externe Worker die Analyse- und Auswahlseite uebernehmen koennen.

## TARGET SURFACE

- Primary Target Surface: Bestehender bounded Operator-Gate fuer delegierte `janus-test-pipeline`-Schritte
- Existing or New Surface: Existing Surface with new internal execution path
- Existence Confirmation: confirmed by user
- Included Surfaces: bestehende lokale-vs-delegierte Operator-Wahl, bounded `janus-test-pipeline` Delegation, strukturierte Generator- und Validator-Anfragen
- Excluded Surfaces: neue separate Nutzeroberflaeche, freie Shell-Ausfuehrung, Git- oder Release-Delegation, allgemeine Patch-Autoannahme

## USER ACTION SURFACE

- User Trigger: Der Operator waehlt fuer einen geeigneten bounded `janus-test-pipeline`-Schritt weiterhin den delegierten Pfad.
- Action Type: Delegierter Schritt mit strukturiertem lokalen Executor hinter der bestehenden Gate-Oberflaeche.
- Feedback: Janus zeigt klar, ob ein strukturierter Generator oder Validator erfolgreich ausgefuehrt wurde oder ob auf Codex-local zurueckgefallen wurde.
- Confirmation Behavior: Wenn die strukturierte Mapping-Route vorhanden ist, bestaetigt Janus die deterministische Ausfuehrung mit reviewbaren Artefakten.
- Cancel / Undo Behavior: Nicht zutreffend: Dieses Feature fuehrt keine neue Undo-Oberflaeche ein.

## SYSTEM BEHAVIOR

Wenn der Operator fuer einen geeigneten bounded `janus-test-pipeline`-Schritt den delegierten Pfad waehlt, darf der externe Worker keine freien Shell-Kommandos mehr formulieren muessen.

Stattdessen gibt der delegierte Worker einen strukturierten Aktionswunsch zurueck, der nur vorab erlaubte Generator- oder Validator-Typen fuer den ersten Executor-Slice ausdrueckt.

Wenn die angefragte Aktion einer freigegebenen lokalen Mapping-Route entspricht, fuehrt Janus diese Aktion deterministisch lokal aus und erzeugt reviewbare Ausfuehrungsartefakte.

Wenn kein freigegebenes Mapping existiert, wenn die strukturierte Anfrage ungueltig ist oder wenn die lokale Generator- oder Validator-Ausfuehrung fehlschlaegt, faellt Janus sofort auf Codex-local zurueck und versucht keine freie delegierte Shell-Ausfuehrung.

Der erste Executor-Slice gilt nur fuer bounded `janus-test-pipeline`-Schritte mit Generator- und Validator-Charakter.

Patch-Schreiben, allgemeine Codeaenderungen und freie Testdatei-Erzeugung bleiben in diesem ersten Slice ausserhalb des strukturierten Executors.

Codex behaelt in allen Faellen Review-, Validierungs- und Annahmeautoritaet.

## DATA / PERSISTENCE

- Created Data: Executor-Run-Artefakte, Validierungsartefakte und strukturierte Ergebniszusammenfassungen fuer den bounded Delegationslauf
- Updated Data: Bestehende bounded Run-Verzeichnisse und zugehoerige Review-Artefakte fuer den delegierten Schritt
- Deleted Data: Keine automatische Loeschung ausserhalb bestehender bounded Run-/Artefaktpfade
- Remembered Data: Nicht zutreffend: Dieses Feature fuehrt keine neue Nutzer-Memory-Logik ein
- Canonical View: Codex App bleibt die kanonische Review- und Annahmestelle fuer delegierte Ergebnisse
- Fallback Behavior: Bei fehlender Mapping-Route oder fehlgeschlagener lokaler Aktion faellt Janus unmittelbar auf Codex-local zurueck

## CONSTRAINTS

Der erste strukturierte Executor-Slice darf nur bounded `janus-test-pipeline`-Schritte bedienen.

Der delegierte Worker darf keine freien Shell-Befehle, keine PATH-Annahmen und keine Betriebssystem-Zeremonie mehr liefern muessen.

Nur vorab freigegebene strukturierte Generator- und Validator-Aktionen sind erlaubt.

Der strukturierte Executor darf keine Git-, Release- oder Final-Audit-Aufgaben ausfuehren.

Der strukturierte Executor darf keinen neuen allgemeinen Schreibmodus fuer beliebige Dateien aktivieren.

## SECURITY / PRIVACY

- Sensitive Data Handling: Private Logs, Credentials und lokale Datenbanken duerfen nicht unnoetig an externe Worker uebergeben werden.
- External Worker Boundary: Externe Worker duerfen nur bounded Kontextpakete und strukturierte Aktionswuensche verarbeiten.
- Local Execution Boundary: Nur freigegebene lokale Mapping-Routen duerfen ausgefuehrt werden.
- Forbidden Actions: Freie Shell-Ausfuehrung, unbeschraenkte Repo-Schreibrechte, Git-Kommandos, Release-Kommandos, Final-Audit-Entscheidungen
- Validation Authority: Codex App behaelt die Review-, Validierungs- und Annahmeautoritaet fuer jeden delegierten Schritt.
- Fallback Safety: Bei ungueltiger Anfrage oder fehlgeschlagener lokaler Aktion wird sofort auf Codex-local zurueckgefallen statt weiter zu improvisieren.

## EDGE CASES

Wenn ein delegierter Schritt eine Aktionsart anfragt, die im ersten Slice noch nicht freigegeben ist, wird nicht teilweise improvisiert, sondern auf Codex-local zurueckgefallen.

Wenn die strukturierte Anfrage formal gueltig ist, aber auf eine unbekannte Mapping-Route zeigt, wird kein lokaler Shell-Ersatz konstruiert.

Wenn die lokale Generator- oder Validator-Ausfuehrung fehlschlaegt, bleibt das Ergebnis reviewbar dokumentiert und der delegierte Pfad gilt nicht als still erfolgreich.

Wenn ein Schritt echte Patch- oder Schreibautoritaet benoetigt, bleibt er in diesem Slice ausserhalb des strukturierten Executors.

Wenn ein TestPipeline-Schritt keine klare Nachvalidierung durch Codex hat, darf er nicht ueber diesen delegierten Pfad laufen.

## DEFINITION OF DONE

- [ ] Wenn ein geeigneter bounded `janus-test-pipeline`-Schritt delegiert wird, dann benoetigt der externe Worker keine freien Shell-Kommandos mehr.
- [ ] Wenn der delegierte Worker einen erlaubten Generator- oder Validator-Wunsch zurueckgibt, dann fuehrt Janus die Aktion ueber eine freigegebene lokale Mapping-Route deterministisch aus.
- [ ] Wenn keine freigegebene Mapping-Route vorhanden ist, dann faellt Janus sofort auf Codex-local zurueck.
- [ ] Wenn die lokale Generator- oder Validator-Ausfuehrung fehlschlaegt, dann bleibt der Schritt reviewbar dokumentiert und gilt nicht als still erfolgreich.
- [ ] Wenn der delegierte Pfad benutzt wird, dann behaelt Codex App die Review-, Validierungs- und Annahmeautoritaet.
- [ ] Wenn der erste Executor-Slice laeuft, dann bleiben freie Shell-Ausfuehrung, Git-Aktionen, Release-Aktionen und allgemeine Patch-Autoannahme ausserhalb des Scopes.

## TEST STRATEGY

- Unit Tests: Strukturierte Aktionsvalidierung, Mapping-Aufloesung, erlaubte und verbotene Aktionsarten, Fallback-Entscheidung
- Integration Tests: Delegierter bounded `janus-test-pipeline`-Schritt mit erlaubter Generator-Route, erlaubter Validator-Route und sauberem lokalen Fallback bei fehlender Route
- Negative Tests: Unbekannte Aktionsart, unbekannte Mapping-Route, fehlgeschlagene lokale Aktion, verbotene freie Shell-Ausfuehrung, verbotene Git- oder Release-Aktion
- Manual Test: Operator waehlt im bestehenden bounded Gate den delegierten Pfad fuer einen geeigneten `janus-test-pipeline`-Schritt und prueft den strukturierten lokalen Executor-Fall gegen den Codex-local-Fallback
- Regression Tests: Bisherige bounded Delegationspfade fuer read-only Drafts und bestehende lokale TestPipeline-Pfade bleiben unveraendert nutzbar

## OUT OF SCOPE

Neue sichtbare Operator-Modi.

Allgemeine Patch-Autoannahme.

Breite Code-Schreibdelegation.

Produktionsrouting.

Auto-Router-Ausweitung.

Skill-Ausweitung ueber den ersten bounded `janus-test-pipeline`-Slice hinaus.

## INTERNAL COMPLEXITY BREAKDOWN

- Scope Size: 12
- Architectural Risk: 16
- State / Persistence Complexity: 10
- Cross-System Dependencies: 16
- Ambiguity Level: 8
- Total Complexity Score: 62

## SPEC IMPLEMENTATION METADATA

- **Implementation Status:** DONE
- **Final Audit:** PASS
- **Completed At:** 2026-06-15
- **Audit Package:** `documentation/tasks/TASK-SPEC17_AUDIT_PACKAGE.md`
- **Final Audit Report:** `documentation/tasks/TASK-SPEC17_final_audit.md`
- **Validation Evidence:**
  - `python -m py_compile documentation/codex/model-routing/scripts/codex_structured_action_executor.py documentation/codex/model-routing/scripts/codex_structured_action_generator_review_runner.py documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/model-routing/tests/test_codex_structured_action_executor.py`
  - `python documentation/codex/model-routing/scripts/codex_structured_action_executor.py --request-json documentation/codex/model-routing/structured-action-fixtures/delegated_request_validate_runner_2026-06-14.json`
  - `python documentation/codex/model-routing/scripts/codex_structured_action_executor.py --request-json documentation/codex/model-routing/structured-action-fixtures/delegated_request_validate_runner_failure_2026-06-15.json`
  - `python documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py --task-class generator_review --task-label "TASK-SPEC17.3 validator pass path" --normal-target-model "5.4 medium" --operator-choice delegated --workflow-id BOUNDED-DISPATCH-GENERATOR-SPEC17-3-PASS --generator-manifest documentation/codex/model-routing/structured-action-fixtures/builder_generator_payload_compile_testspec_2026-06-15.json --generator-summary "Run bounded compile-testspec generator plus validator path for TASK-SPEC17.3."`
  - `python documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py --task-class generator_review --task-label "TASK-SPEC17.3 validator fallback path" --normal-target-model "5.4 medium" --operator-choice delegated --workflow-id BOUNDED-DISPATCH-GENERATOR-SPEC17-3-FALLBACK --generator-manifest documentation/codex/model-routing/structured-action-fixtures/builder_generator_payload_2026-06-14.json --generator-summary "Run bounded legacy generator manifest to confirm local fallback when the structured route is no longer supported."`
  - `python documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py --task-class documentation_draft --task-label "TASK-SPEC17.3 read only regression" --normal-target-model "5.4 medium" --operator-choice local --workflow-id BOUNDED-DISPATCH-DOC-SPEC17-3-LOCAL`
  - `python -m pytest documentation/codex/model-routing/tests/test_codex_structured_action_executor.py -q`
