# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING
target_skill: janus-spec-review
recommended_model: 5.4
recommended_reasoning: medium
new_chat: no
complexity_score: 58
confidence: HIGH
dashboard_hint: CAUTION
reason: Existing Janus skill entries gain a bounded operator choice between local Codex and fail-closed OR paths without expanding final authority.

## FEATURE IDENTITY
- Feature Name: Operator-facing Codex-oder-OR-Wahl in bestehenden Janus-Skills
- Feature Type: Workflow-Erweiterung fuer bestehende Janus-Skills
- Primary Goal: In passenden bestehenden Janus-Skills soll am Einstieg sichtbar zwischen lokalem Codex-Pfad und bounded OR-Pfad gewaehlt werden koennen.
- Trigger Source: Start eines geeigneten Janus-Skills mit bounded OR-Kandidaten.
- Primary Persona: Operator, der je nach Codex-Kontingent und erwarteten OR-Kosten flexibel entscheiden moechte, welcher Pfad fuer eine konkrete Aufgabe sinnvoller ist.

## USER VALUE

Der Nutzer bekommt die Wahl zwischen lokalem Codex-Pfad und bounded OR-Pfad direkt dort, wo die Arbeit tatsaechlich startet, statt dafuer Sonderwissen ueber interne Hilfswege oder verstreute Dokumentation zu brauchen.

Dadurch entsteht mehr Flexibilitaet bei Kosten- und Kontingententscheidungen, waehrend Janus sichtbar fail-closed bleibt und keine ungesunden, partiellen oder nicht freigegebenen OR-Pfade als normale Alltagsoption erscheinen.

## TARGET SURFACE
- Primary Surface: bestehende Janus-Skill-Einstiege
- Existing Surface: Ja
- Existence Confirmation: confirmed by user
- In-Scope Surfaces: bestehende Janus-Skills mit bounded OR-Kandidaten und sichtbar gebundenem Operator-Gate am Skill-Einstieg
- Explicit Non-Surfaces: globale OR-Freigabe, canonical routing-table update, broad delegated repo authority, release actions, neue primaere Produktoberflaechen nur fuer diese Wahl

## USER ACTION SURFACE
- Entry Action: Der Nutzer startet einen geeigneten Janus-Skill und sieht am Einstieg die Wahl zwischen lokalem Codex-Pfad und bounded OR-Pfad.
- Required Inputs: bewusste Operator-Wahl zwischen Codex und OR fuer die konkrete gebundene Aufgabe
- Success Feedback: Der Skill zeigt sichtbar den verfuegbaren bounded OR-Pfad inklusive Kosten-/Evidenzhinweis und faellt lokal fail-closed zurueck, wenn kein freigegebener bounded OR-Lane passt.
- Failure Feedback: Nicht freigegebene, partielle oder ungesunde OR-Lanes duerfen nicht als normale Wahl erscheinen; in solchen Faellen bleibt nur der lokale Codex-Pfad sichtbar.
- Cancel / Undo Behavior: Wenn der Nutzer den lokalen Codex-Pfad waehlt oder der bounded OR-Pfad fail-closed endet, bleibt der Ablauf ohne impliziten Delegationsabschluss lokal bei Codex.

## SYSTEM BEHAVIOR

Bestehende Janus-Skills behalten ihren lokalen Codex-Pfad als Baseline.

Bei passenden bounded OR-Kandidaten zeigt der Skill am Einstieg sichtbar eine Operator-Wahl zwischen lokalem Codex-Pfad und bounded OR-Pfad.

Die sichtbare Wahl darf nur dort erscheinen, wo ein freigegebener bounded OR-Lane fuer die konkrete Aufgabe vorhanden ist. Ein allgemeiner Wunsch nach Delegation reicht nicht aus.

Wenn ein geeigneter bounded OR-Lane existiert, zeigt der Skill die Wahl zusammen mit Kosten- oder Evidenzhinweisen fuer den gebundenen Pfad.

Wenn kein freigegebener bounded OR-Lane passt, wenn Gate-Daten fehlen oder wenn der Lane ungesund ist, bleibt nur der lokale Codex-Pfad sichtbar.

Wenn der Nutzer den bounded OR-Pfad waehlt, nutzt der Skill genau den fuer diesen Fall freigegebenen bounded OR-Lane und erweitert dessen Autoritaet nicht stillschweigend.

Codex bleibt in jedem Fall finaler Reviewer, Validierungs-Owner und Abschluss-Owner.

Diese Erweiterung ist operator-facing und workflow-nah, aber keine globale Routing-Freigabe und keine Production-Routing-Aktivierung.

## DATA / PERSISTENCE
- Created Data: Telemetrie-, Gate-Evidenz- und vorhandene Skill-/Routing-Artefakte fuer den gewaehlten bounded OR-Pfad
- Updated Data: bestehende bounded OR-Laufartefakte und zugehoerige lokale Review-/Validierungsnachweise
- Deleted Data: Nicht zutreffend: Das Feature fuehrt keinen regulaeren Loeschpfad als Kernverhalten ein.
- Persistence Scope: nur Telemetrie, Gate-Evidenz und vorhandene Skill-/Routing-Artefakte; keine neue Produktpersistenz
- Canonical Review Record: Codex-Review plus die bounded Laufartefakte bleiben der kanonische Abschlussnachweis
- Failure Persistence: fehlgeschlagene oder nicht freigegebene bounded OR-Faelle bleiben als lokaler Codex-Ausgang oder als bounded Evidenz sichtbar

## CONSTRAINTS

Die Wahl darf nur an bestehenden Janus-Skill-Einstiegen erscheinen.

Der sichtbare OR-Pfad darf nur auf bereits gebundenen bounded OR-Kandidaten beruhen.

Nicht freigegebene, partielle oder ungesunde OR-Lanes duerfen nicht als normale Alltagswahl sichtbar werden.

Es entsteht keine globale OR-Freigabe, keine canonical routing-table update und keine broad delegated authority.

Codex behaelt finale Validierung und Autoritaet.

## SECURITY / PRIVACY
- Trust Boundary: Der bounded OR-Pfad bleibt externer Assistenz- oder Arbeitskontext ohne finale Janus-Autoritaet.
- Local Authority Owner: Codex behaelt finale Validierung und Autoritaet.
- Sensitive Data Rule: Es darf nur der fuer den konkreten bounded OR-Lane noetige Kontext weitergegeben werden.
- Write Safety Rule: Etwaige write-capable bounded OR-Lanes behalten ihre bereits lane-spezifischen Grenzen und fail-closed Regeln.
- Forbidden Actions: globale OR-Freigabe, canonical routing-table update, broad delegated repo authority, release actions, implizite Freischaltung unbewiesener Lanes
- Auditability: Jeder sichtbare bounded OR-Pfad muss ueber vorhandene Telemetrie-, Gate- und Review-Artefakte lokal nachvollziehbar bleiben.

## EDGE CASES

Wenn Gate-Daten fehlen, erscheint keine scheinbar gueltige bounded OR-Wahl.

Wenn ein OR-Kandidat historisch existiert, aber aktuell nicht freigegeben oder nicht gesund ist, bleibt der Skill lokal bei Codex.

Wenn mehrere Delegationsideen denkbar waeren, darf nur der fuer den konkreten Skill-Einstieg gebundene bounded OR-Lane sichtbar werden.

Wenn der bounded OR-Pfad technisch scheitert oder fail-closed endet, muss der Abschluss klar lokal bei Codex landen.

Wenn der Nutzer nur lokalen Ablauf will, darf die sichtbare bounded OR-Wahl keinen versteckten Seiteneffekt erzeugen.

## DEFINITION OF DONE

- [ ] Wenn ein bestehender Janus-Skill mit passendem bounded OR-Kandidaten startet, dann erscheint beobachtbar am Skill-Einstieg eine Wahl zwischen lokalem Codex-Pfad und bounded OR-Pfad.
- [ ] Wenn kein freigegebener bounded OR-Lane zur konkreten Aufgabe passt, dann bleibt beobachtbar nur der lokale Codex-Pfad sichtbar.
- [ ] Wenn der Nutzer den bounded OR-Pfad waehlt, dann nutzt der Skill beobachtbar nur den fuer diesen Fall gebundenen bounded OR-Lane.
- [ ] Wenn Gate-Daten fehlen oder der Lane ungesund ist, dann endet der Einstieg beobachtbar fail-closed lokal bei Codex.
- [ ] Wenn ein bounded OR-Lauf abgeschlossen wird, dann bleibt beobachtbar Codex finaler Reviewer, Validierungs-Owner und Abschluss-Owner.
- [ ] Wenn ein OR-Kandidat nicht freigegeben, nur partiell oder ungesund ist, dann erscheint er beobachtbar nicht als normale Alltagswahl.

## TEST STRATEGY
- Primary Validation Mode: lokale Gate-, Telemetrie-, Eligibility-, Fallback- und Abschlussvalidierung an bestehenden Skill-Einstiegen
- Required Evidence: sichtbare Gate-Evidenz fuer passende und nicht passende Skill-Einstiege, bounded OR-Laufartefakte, lokale Review-/Validierungsnachweise, fail-closed Nachweise
- Success Cases: geeigneter Skill-Einstieg mit sichtbarer Wahl; bounded OR-Wahl mit korrektem gebundenem Pfad; lokaler Codex-Pfad ohne OR-Nebenwirkung
- Failure Cases: fehlende Gate-Daten, fehlende OR-Freigabe, partieller Kandidat, ungesunder Lane, fail-closed Rueckfall, scheinbar sichtbare OR-Wahl ohne gueltigen bounded Pfad
- Regression Focus: keine globale OR-Freigabe, keine Sichtbarkeit experimenteller Kandidaten, kein Verlust der finalen Codex-Autoritaet, keine implizite Production-Routing-Wirkung

## OUT OF SCOPE

Globale OR-Freigabe, canonical routing-table update, broad delegated repo authority, release actions, neue primaere Produktoberflaechen nur fuer diese Wahl, ungebundene freie Delegation ausserhalb vorhandener bounded OR-Kandidaten.

## SPEC REVIEW METADATA

- **Review Status:** APPROVED
- **Complexity Score:** 58
- **Risk:** MEDIUM
- **Recommended Review Model:** 5.4
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-07-07
- **Review Confidence:** HIGH
- **Review Source:** janus-spec-review

## INTERNAL COMPLEXITY BREAKDOWN

- Scope Size: 12
- Architectural Risk: 14
- State / Persistence Complexity: 8
- Cross-System Dependencies: 14
- Ambiguity Level: 10
- Total Complexity Score: 58
- Routing Decision: 5.4
- Routing Reasoning: medium
- Routing Confidence: HIGH
- Dashboard Hint: CAUTION

## SPEC IMPLEMENTATION METADATA

- Implementation Status: DONE
- Final Audit: PASS
- Completion Date: 2026-07-07
- Validation Evidence:
  - `documentation/tasks/TASK-SPEC26.1_final_audit.md`
  - `documentation/tasks/TASK-SPEC26.2_final_audit.md`
  - `documentation/tasks/TASK-SPEC26.3_final_audit.md`
  - `python -m unittest documentation.codex.model-routing.tests.test_assistive_or_review_consumer_integration` - PASS (`15` tests)
  - `python -m unittest documentation.codex.model-routing.tests.test_codex_dev_workhorse_runner` - PASS (`23` tests)
  - `python -m unittest documentation.codex.model-routing.tests.test_quickchange_write_apply_runner` - PASS (`3` tests)
  - `python -m unittest documentation.codex.model-routing.tests.test_bounded_or_worker_gate_prompt` - PASS (`13` tests)
  - direct dispatcher probe for `debug_hypothesis_review`, `test_result_triage_review`, `quickchange_patch_review`, `generator_review`, and `execution_write_apply_candidate` - PASS
