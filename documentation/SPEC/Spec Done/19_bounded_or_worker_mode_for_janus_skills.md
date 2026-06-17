# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING

target_skill: janus-spec-review
recommended_model: 5.4
recommended_reasoning: medium-high
new_chat: no
complexity_score: 68
confidence: HIGH
dashboard_hint: CAUTION
reason: Cross-skill bounded OR worker mode adds operator gating, validation ownership, and skill-scoped delegation limits without allowing broad autonomous routing.

## SPEC REVIEW METADATA

- **Review Status:** APPROVED_WITH_NOTES
- **Complexity Score:** 68
- **Risk:** HIGH
- **Recommended Review Model:** 5.4
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-06-16
- **Review Confidence:** HIGH
- **Review Source:** janus-spec-review

## SPEC IMPLEMENTATION METADATA

- **Implementation Status:** DONE
- **Final Audit:** PASS
- **Completed At:** 2026-06-17
- **Validation Evidence:** `python -m py_compile documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py documentation/codex/model-routing/scripts/bounded_or_worker_gate_prompt.py documentation/codex/model-routing/scripts/bounded_or_worker_outcome.py documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/model-routing/scripts/doc_skill_mini_fixed_or_live_runner.py documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py documentation/codex/model-routing/scripts/codex_test_result_triage_review_runner.py documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py`: PASS; `python -m pytest documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py -q`: PASS; `python -m pytest documentation/codex/model-routing/tests -q -k "eligibility or fixed_or"`: PASS; `python -m pytest documentation/codex/model-routing/tests -q -k "gate or confidence or cost or codex_only"`: PASS; `python -m pytest documentation/codex/model-routing/tests -q -k "accept or reject or fallback or codex_owned"`: PASS

## FEATURE IDENTITY

- Feature Name: Bounded OR Worker Mode fuer Janus Skills
- Primary Goal: Einen einheitlichen bounded Delegationsmodus schaffen, in dem OpenRouter bei geeigneten Janus-Skills den Hauptarbeitsblock uebernehmen darf, waehrend Codex immer Routing, Review, Validierung und finale Abnahme kontrolliert.
- User Problem: Der Nutzer moechte bei passenden Janus-Aufgaben flexibel zwischen lokalem Codex-Pfad und guenstigerem OpenRouter-Arbeitspferd waehlen koennen, ohne Qualitaets-, Governance- oder Sicherheitsverlust.
- Routing Decision: 5.4
- Routing Reasoning: medium-high
- Routing Confidence: HIGH
- Dashboard Hint: CAUTION

## USER VALUE

Der Nutzer kann Codex-Kontingent gezielt sparen und stattdessen bei geeigneten bounded Aufgaben OpenRouter-Kosten einsetzen, ohne auf die verlassliche Codex-Abnahme zu verzichten.

Der Workflow bleibt alltagstauglich, weil die Auswahl nicht pro Sonderfall neu erfunden wird, sondern als einheitliches Delegations-Gate nur dort erscheint, wo OR wirklich zulaessig und evidenzgestuetzt ist.

## TARGET SURFACE

- Primary Target Surface: Einheitliches skill-uebergreifendes Delegations-Gate vor geeigneten Janus-Skills
- Existing or New Surface: Existing Surface Extension
- Existence Confirmation: confirmed by user
- Included Surfaces: operator-invoked Wahl zwischen `1 = Codex` und `2 = OpenRouter`, bounded OR-Hauptarbeitsblock fuer geeignete Skills, skill-spezifische OR-Eignungspruefung, Codex-Review- und Validierungsabnahme
- Excluded Surfaces: Produktionsrouting, globale OR-Freigabe, automatische OR-Nutzung ohne Gate, broad repo write authority, Release-, Git- oder Final-Audit-Delegation

## USER ACTION SURFACE

- User Trigger: Vor einem geeigneten bounded Janus-Skill erscheint ein einheitliches Delegations-Gate, wenn fuer diesen Skill eine evidenzgestuetzte OR-Option verfuegbar ist.
- Action Type: Explizite Operator-Wahl zwischen lokalem Codex-Pfad und OpenRouter-Pfad fuer genau den aktuellen Skilllauf.
- Feedback: Das Gate zeigt die Codex-Option sowie die OR-Option mit Modell, voraussichtlichen Kosten, Confidence-Hinweis und Boundaries an.
- Confirmation Behavior: Nach einem OR-Lauf prueft Codex das Ergebnis immer aktiv, zeigt Validierungs- und Review-Ausgang sichtbar an und nimmt den Lauf nur danach an.
- Cancel / Undo Behavior: Wenn OR fuer den Skill nicht zulaessig ist, wenn Gates verletzt werden oder wenn die Abnahme scheitert, bleibt der Lauf bei Codex oder faellt sauber auf Codex zurueck.

## SYSTEM BEHAVIOR

Wenn ein Janus-Skill zu den freigegebenen bounded Delegationsklassen gehoert und fuer genau diesen Skill eine evidenzgestuetzte OR-Option vorhanden ist, zeigt Janus vor dem Skilllauf ein einheitliches Delegations-Gate.

Wenn der Nutzer `1 = Codex` waehlt, laeuft der Skill wie bisher voll lokal im normalen Codex-Pfad.

Wenn der Nutzer `2 = OpenRouter` waehlt, darf OR den Hauptarbeitsblock dieses geeigneten bounded Skills uebernehmen, jedoch nur innerhalb der fuer diese Skill-Klasse festgelegten Grenzen.

Wenn der OR-Pfad laeuft, muessen die skill-spezifischen Kontrollgrenzen, die erforderlichen Run-Artefakte, die Validierungsnachweise und die Kosten- beziehungsweise Confidence-Hinweise nachvollziehbar bleiben.

Wenn eine OR-Option fuer den Skill nicht evidenzgestuetzt, nicht zulaessig oder nicht ausreichend begrenzt ist, erscheint kein OR-Gate und der Lauf bleibt im Codex-Pfad.

Wenn ein OR-Ergebnis vorliegt, behaelt Codex immer die aktive Review-, Validierungs- und Abnahmeautoritaet; ein OR-Ergebnis gilt nie stillschweigend als angenommen.

Wenn Validierung fehlt, wenn skill-spezifische Grenzen verletzt werden, wenn das Ergebnis unsicher ist oder wenn Kosten- beziehungsweise Sicherheitsgrenzen gerissen werden, wird der OR-Lauf nicht akzeptiert und Codex uebernimmt oder setzt lokal fort.

Der erste alltagstaugliche OR-Worker-Mode gilt nur fuer klar bounded Skill-Klassen und nicht sofort fuer breite Debug-, Execution-, Release- oder Governance-Arbeit.

## DATA / PERSISTENCE

- Created Data: Operator-Gate-Artefakte, OR-Run-Artefakte, Telemetrie-, Kosten-, Confidence-, Validierungs- und Review-Zusammenfassungen fuer skill-spezifische OR-Laeufe
- Updated Data: Bestehende bounded Run-Verzeichnisse, Skill-spezifische Telemetriepfade und Codex-Review-Artefakte fuer akzeptierte oder abgelehnte OR-Laeufe
- Deleted Data: Keine automatische Loeschung als regulaerer Erfolgsweg
- Remembered Data: Skill-spezifische OR-Eignung, historische Kosten- und Confidence-Werte sowie Review- und Fallback-Evidenz koennen als bounded Betriebsdaten fortgeschrieben werden
- Canonical Review Record: Codex-Review, lokale Validierung und bounded OR-Artefakte bilden gemeinsam die kanonische Entscheidungsbasis fuer Annahme oder Ablehnung
- Failure Persistence: Fehlgeschlagene, abgebrochene oder abgelehnte OR-Laeufe bleiben als bounded Evidenz sichtbar, ohne automatisch als erfolgreich erledigte Skill-Arbeit zu gelten

## CONSTRAINTS

Der OR-Worker-Mode darf nur bei Skills erscheinen, fuer die eine evidenzgestuetzte und explizit zugelassene OR-Option existiert.

Der OR-Worker-Mode darf den Hauptarbeitsblock geeigneter Skills uebernehmen, aber nicht Routing-, Git-, Release-, Final-Audit- oder Produkt-Governance-Autoritaet.

Codex muss nach jedem OR-Lauf immer aktiv pruefen und darf die finale Annahme nicht an OR delegieren.

Der erste alltagstaugliche Rollout darf nur klar bounded Skill-Klassen umfassen.

Der OR-Worker-Mode darf keine globale OR-Freigabe und kein stillschweigendes skill-uebergreifendes Auto-Routing erzeugen.

Die OR-Auswahl darf nur erscheinen, wenn Kosten- und Confidence-Hinweise fuer den konkreten Skilllauf verfuegbar und zulaessig sind.

## SECURITY / PRIVACY

- Sensitive Data Handling: Private Logs, Secrets, Credentials, lokale Datenbanken und unnoetige personenbezogene Rohdaten duerfen nicht automatisch in OR-Kontextpakete gelangen.
- External Worker Boundary: OR darf nur bounded, skill-spezifisch freigegebene Arbeitspakete innerhalb klarer Gates bearbeiten.
- Forbidden Authority: Kein Produktionsrouting, kein kanonisches Routing-Table-Update, keine Git-Autoritaet, keine Release-Autoritaet, keine Final-Audit-Autoritaet, keine globale Freigabe fuer breite Repo-Schreibrechte
- Validation Ownership: Codex bleibt immer Besitzer von Review, Validierung, Accept/Reject und finalem Skill-Abschlussstatus.
- Abort Conditions: Fehlende Evidenz, fehlende Kosten- oder Confidence-Daten, verletzte Skill-Grenzen, fehlende Validierungsartefakte, Sicherheits- oder Kosten-Grenzverletzungen sowie unsichere Ergebnisse fuehren zum Reject oder Fallback.
- Transparency: Das Delegations-Gate und die nachgelagerten Review-Artefakte muessen fuer jeden OR-Lauf den gewaehlten Pfad, das Modell, die Kostenlage, den Validierungsstand und den finalen Accept/Reject-Status sichtbar machen.

## EDGE CASES

Wenn ein Skill grundsaetzlich delegierbar erscheint, aber fuer die konkrete Aufgabe keine belastbare OR-Evidenz oder kein erlaubtes Modell vorhanden ist, erscheint kein OR-Gate.

Wenn ein Skill in mehrere Teilklassen faellt, darf der OR-Worker-Mode nur fuer die bounded und explizit freigegebene Teilklasse erscheinen.

Wenn ein OR-Lauf fachlich brauchbar wirkt, aber lokale Validierung fehlt oder unklar ist, darf Codex ihn nicht still akzeptieren.

Wenn historische OR-Evidenz veraltet, widerspruechlich oder nur fuer eine andere Skill-Variante gueltig ist, bleibt der Skill fuer den OR-Worker-Mode gesperrt, bis neue Evidenz vorliegt.

Wenn ein Skill breite Debug-, Execution-, Release- oder Governance-Autoritaet benoetigt, faellt er ausserhalb des ersten bounded OR-Worker-Rollouts.

Wenn ein OR-Lauf Kosten- oder Confidence-Hinweise nicht verlässlich liefern kann, darf die OR-Option fuer diesen konkreten Lauf nicht als normale Wahl erscheinen.

## DEFINITION OF DONE

- [ ] Wenn ein geeignet freigegebener bounded Skill gestartet wird, dann erscheint sichtbar ein einheitliches Delegations-Gate mit `1 = Codex` und `2 = OpenRouter`.
- [ ] Wenn fuer den konkreten Skill keine evidenzgestuetzte OR-Option vorliegt, dann erscheint kein OR-Gate und der Skill bleibt im Codex-Pfad.
- [ ] Wenn der Nutzer `2 = OpenRouter` waehlt, dann darf OR den Hauptarbeitsblock nur innerhalb der skill-spezifisch festgelegten bounded Grenzen uebernehmen.
- [ ] Wenn ein OR-Lauf abgeschlossen ist, dann prueft Codex das Ergebnis immer aktiv und nimmt es nicht stillschweigend an.
- [ ] Wenn Validierung fehlt, Skill-Grenzen verletzt werden oder das Ergebnis unsicher ist, dann wird der OR-Lauf nicht akzeptiert und faellt sauber auf Codex zurueck.
- [ ] Wenn das Gate eine OR-Option zeigt, dann sind fuer diesen Lauf sichtbare Kosten- und Confidence-Hinweise vorhanden.
- [ ] Wenn der erste alltagstaugliche Rollout aktiv ist, dann umfasst er nur klar bounded Skill-Klassen und keine breite Governance-, Release- oder Final-Audit-Arbeit.

## TEST STRATEGY

- Unit Tests: Skill-Eignungspruefung, Delegations-Gate-Sichtbarkeit, Kosten- und Confidence-Voraussetzungen, Fallback- und Reject-Entscheidungen
- Integration Tests: End-to-end Skilllaeufe mit `Codex`-Wahl, mit `OpenRouter`-Wahl, mit fehlender OR-Eignung und mit skill-spezifischem Reject oder Fallback
- Negative Tests: fehlende Evidenz, fehlende Kosten- oder Confidence-Daten, nicht freigegebene Skill-Klasse, unsicheres OR-Ergebnis, fehlende Validierung, verletzte Sicherheits- oder Kosten-Grenzen
- Manual Test: Operator startet geeignete bounded Skills im echten Workflow, sieht nur bei zugelassener OR-Eignung das Delegations-Gate und beobachtet die sichtbare Codex-Abnahme nach OR-Lauf
- Regression Tests: bestehende Codex-only Skillpfade, bestehende bounded Delegationspfade und nicht delegierbare Janus-Skills bleiben unveraendert sicher nutzbar

## OUT OF SCOPE

Produktionsrouting oder globale OR-Aktivierung.

Kanonisches Routing-Table-Update.

Automatische OR-Nutzung ohne explizites Delegations-Gate.

Breite unbounded Debug-, Execution-, Git-, Release- oder Final-Audit-Delegation.

Eine globale Modellentscheidung, die alle Skills mit demselben OR-Modell bearbeitet.

Die sofortige Ausweitung auf jede Janus-Aufgabe ohne skill-spezifische Evidenz.

## INTERNAL COMPLEXITY BREAKDOWN

- Scope Size: 15
- Architectural Risk: 16
- State / Persistence Complexity: 12
- Cross-System Dependencies: 15
- Ambiguity Level: 10
- Total Complexity Score: 68
