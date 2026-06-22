# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING
target_skill: janus-spec-review
recommended_model: 5.4
recommended_reasoning: medium
new_chat: no
complexity_score: 59
confidence: HIGH
dashboard_hint: CAUTION
reason: Existing debug workflow gains one bounded OR consumer path with explicit user choice, strict fallback, and Codex-owned final authority.

## FEATURE IDENTITY
- Feature Name: Erster produktiver OR-Consumer fuer `janus-debug`
- Feature Type: Workflow-Erweiterung fuer einen bestehenden Janus-Skill
- Primary Goal: Den ersten echten alltagstauglichen OR-Pfad in `janus-debug` produktiv nutzbar machen, ohne die bounded Governance und die finale Codex-Kontrolle aufzuweichen.
- Trigger Source: Ein normaler `janus-debug`-Workflow trifft auf einen klar bounded und OR-geeigneten Debug-Fall.
- Primary Persona: Operator, der bei geeigneten Debug-Aufgaben bewusst zwischen Codex-Kontingent und OR-Kosten waehlen will.

## USER VALUE

Der Nutzer kann in passenden Debug-Faellen zwischen Codex und OR waehlen, statt jede Analyse- oder Patch-Vorbereitung lokal mit Codex auszufuehren. Dadurch wird teures Codex-Kontingent nur dort verbraucht, wo es wirklich noetig ist, waehrend OR bounded Vorarbeit uebernehmen kann und Codex die finale Kontrolle behaelt.

## TARGET SURFACE
- Primary Surface: `janus-debug`
- Existing Surface: Ja
- Existence Confirmation: confirmed by user
- In-Scope Surfaces: der bestehende `janus-debug`-Workflow fuer klar bounded OR-geeignete Debug-Faelle, sichtbare Codex-vs-OR-Auswahl, bounded OR-Analyse, bounded OR-Patch-Kandidaten, lokaler Codex-Fallback
- Explicit Non-Surfaces: `janus-test-pipeline`, `janus-documentation-update`, allgemeine Janus-Produktworkflows, globale OR-Freigabe, automatische Skill-uebergreifende Modellwahl, Release- oder Routing-Autoritaet fuer OR

## USER ACTION SURFACE
- Entry Action: In einem klar geeigneten `janus-debug`-Fall erscheint eine explizite Wahl zwischen Codex und OR.
- Required Inputs: die Nutzerauswahl zwischen Codex und OR bei einem eligible Debug-Fall
- Success Feedback: Der Workflow zeigt, dass der bounded OR-Pfad genutzt wurde, welches Ergebnis zurueckkam und dass Codex final akzeptiert, verworfen oder lokal uebernommen hat.
- Failure Feedback: Der Workflow zeigt knapp, dass OR verworfen wurde oder nicht genutzt werden konnte, und faellt direkt auf Codex-only zurueck.
- Cancel / Undo Behavior: Wenn der Nutzer Codex waehlt oder die OR-Voraussetzungen nicht vorliegen, bleibt der Schritt ohne Seiteneffekte lokal bei Codex.

## SYSTEM BEHAVIOR

`janus-debug` behaelt seinen normalen lokalen Codex-Pfad als Standard. Ein OR-Pfad wird nur dann angeboten, wenn der konkrete Debug-Fall klar bounded, reviewbar und OR-geeignet ist.

Die Auswahl zwischen Codex und OR erscheint nicht bei jedem Debug-Fall, sondern nur bei Faellen, die innerhalb der bestehenden bounded OR-Grenzen sicher und sinnvoll bearbeitet werden koennen. Nicht geeignete Faelle bleiben still Codex-only.

Wenn der Nutzer den OR-Pfad waehlt, darf OR bounded Debug-Arbeit uebernehmen. Dazu gehoeren Analyse- und Review-Arbeit sowie bounded Umsetzungsvorschlaege in Form von Patch- oder Fix-Kandidaten innerhalb der erlaubten Grenzen.

Codex bleibt in jedem Fall die letzte autoritative Instanz. Codex prueft das OR-Ergebnis, bewertet dessen Brauchbarkeit fuer den konkreten Debug-Fall und entscheidet final, ob es akzeptiert, lokal weitergefuehrt oder verworfen wird.

Wenn ein OR-Lauf unvollstaendig, zu teuer oder qualitativ unsauber zurueckkommt, faellt der Workflow direkt auf Codex-only zurueck. Der Nutzer soll dabei keinen haengenden Zwischenzustand sehen, sondern einen robusten lokalen Abschluss.

Der produktive Consumer bleibt bewusst eng: genau ein bestehender Janus-Skill, genau ein bounded Debug-Pfad und keine allgemeine OR-Ausweitung ueber weitere Skills oder unbounded Faelle.

## DATA / PERSISTENCE
- Stored Artifacts: bestehende bounded Laufartefakte, Telemetrie-, Kosten-, Validierungs- und Ergebnisnachweise des OR-Pfads
- Persistence Scope: lokale Workflow- und Evidenzartefakte fuer den bounded OR-Consumer innerhalb des vorhandenen Codex- und Janus-Rahmens
- State Mutation: Nicht zutreffend: Die Feature-Entscheidung fuehrt keine neue Endnutzer-Persistenz ein, sondern erweitert den Ausfuehrungspfad eines bestehenden Debug-Workflows.
- Data Lifecycle: Jeder OR-Lauf hinterlaesst nachvollziehbare lokale Evidenz; bei nicht geeignetem oder verworfenem Ergebnis bleibt der Abschluss dennoch eindeutig lokal bei Codex.

## CONSTRAINTS

- `janus-debug` bleibt ausserhalb klar geeigneter Faelle vollstaendig Codex-only.
- Die OR-Auswahl darf nur bei klar bounded und OR-tauglichen Debug-Faellen erscheinen.
- OR darf nur bounded Analyse- und Patch-Kandidaten-Arbeit uebernehmen, nicht aber freie allgemeine Debug-Autoritaet.
- Codex bleibt immer Owner fuer Eligibility, Review, finale Entscheidung und Workflow-Abschluss.
- Schlechte, unvollstaendige oder zu teure OR-Ergebnisse muessen direkt auf Codex-only zurueckfallen.
- Das Feature darf keine globale OR-Freigabe oder stillschweigende Aktivierung in anderen Skills erzeugen.

## SECURITY / PRIVACY
- Trust Boundary: OR bleibt ein externer bounded Worker ohne eigene Abschluss- oder Governance-Autoritaet.
- Local Authority Owner: Codex bleibt Owner fuer Scope, lokale Validierung, finale Akzeptanz oder Verwerfung und den dokumentierten Abschluss.
- Sensitive Data Rule: Nur der fuer den gebundenen Debug-Fall noetige Kontext darf an OR weitergegeben werden.
- Write Safety Rule: Bounded Umsetzungsvorschlaege duerfen nie als automatisch akzeptierte Endaenderung gelten, sondern nur als reviewbare Kandidaten fuer Codex.
- Forbidden Actions: keine globale Skill-Ausweitung, keine Routing-Autoritaet fuer OR, keine Release-, Git- oder Merge-Autoritaet, kein automatischer Erfolg allein durch OR-Rueckgabe
- Auditability: Jeder produktive OR-Debug-Lauf muss lokal so nachvollziehbar sein, dass Auswahl, Ergebnis, Kosten, Validierung und finaler Codex-Abschluss spaeter geprueft werden koennen.

## EDGE CASES

- Wenn ein Debug-Fall nicht klar bounded ist, erscheint keine OR-Auswahl.
- Wenn der Nutzer Codex waehlt, bleibt der gesamte Ablauf lokal.
- Wenn ein OR-Ergebnis unvollstaendig oder qualitativ unsauber ist, faellt der Ablauf direkt auf Codex-only zurueck.
- Wenn ein OR-Ergebnis das Kostenlimit verletzt, wird es nicht als erfolgreicher produktiver Lauf behandelt.
- Wenn ein Debug-Fall zwar technisch OR-faehig, aber fuer den Nutzer nicht sinnvoll delegierbar ist, bleibt der Schritt Codex-only.

## DEFINITION OF DONE

- [ ] Wenn ein `janus-debug`-Fall nicht klar OR-geeignet ist, dann erscheint keine OR-Auswahl und der Ablauf bleibt vollstaendig lokal bei Codex.
- [ ] Wenn ein `janus-debug`-Fall klar OR-geeignet ist, dann erscheint eine explizite Nutzerauswahl zwischen Codex und OR.
- [ ] Wenn der Nutzer in einem geeigneten `janus-debug`-Fall OR waehlt, dann kann OR bounded Analyse- oder Patch-Kandidaten-Arbeit liefern, waehrend Codex die finale Review und Entscheidung behaelt.
- [ ] Wenn ein OR-Ergebnis unvollstaendig, zu teuer oder qualitativ unsauber ist, dann faellt der Ablauf direkt auf Codex-only zurueck.
- [ ] Wenn ein OR-Ergebnis akzeptabel ist, dann bleibt sichtbar, dass Codex den finalen Abschluss verantwortet hat.
- [ ] Wenn der produktive Consumer aktiv ist, dann entsteht dadurch keine implizite OR-Aktivierung in anderen Janus-Skills.

## TEST STRATEGY
- Primary Validation Mode: lokale Workflow-, Eligibility-, Fallback- und Ergebnisvalidierung innerhalb des bestehenden Janus-Debug-Pfads
- Required Evidence: sichtbare Gate-Evidenz fuer geeignete und ungeeignete Faelle, bounded OR-Laufnachweise, Fallback-Nachweise, Codex-owned Abschlussnachweise
- Success Cases: geeigneter Debug-Fall mit sichtbarer Auswahl und erfolgreichem bounded OR-Ergebnis; geeigneter Debug-Fall mit bounded Patch-Kandidat und finalem Codex-Abschluss
- Failure Cases: ungeeigneter Debug-Fall ohne Gate; OR-Lauf mit unvollstaendigem oder qualitativ unsauberem Ergebnis; OR-Lauf mit Kostenverletzung und direktem Codex-Fallback
- Regression Focus: keine implizite Aktivierung in anderen Skills oder anderen Debug-Modi; kein Verlust der finalen Codex-Autoritaet; keine haengenden Zwischenzustaende nach OR-Fehlern

## OUT OF SCOPE

Produktive OR-Aktivierung fuer weitere Janus-Skills, Auto-Router-Entscheidungen, globale Modellsubstitution, parallele Aktivierung mehrerer Consumer, allgemeine Janus-Produktaufgaben, Release- oder Produktionsrouting und jede Form von OR-Autoritaet ueber Git, Merge, Release oder finale Governance-Entscheidungen.

## SPEC REVIEW METADATA

- **Review Status:** APPROVED_WITH_NOTES
- **Complexity Score:** 59
- **Risk:** MEDIUM
- **Recommended Review Model:** 5.4
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-06-21
- **Review Confidence:** HIGH
- **Review Source:** janus-spec-review

## INTERNAL COMPLEXITY BREAKDOWN

- Scope Size: 12/20
- Architectural Risk: 14/20
- State / Persistence Complexity: 8/20
- Cross-System Dependencies: 13/20
- Ambiguity Level: 12/20
- Total Complexity Score: 59/100
- Routing Decision: 5.4
- Routing Reasoning: medium
- Routing Confidence: HIGH
- Dashboard Hint: CAUTION

## SPEC IMPLEMENTATION METADATA

- Implementation Status: DONE
- Final Audit: PASS
- Completion Date: 2026-06-21
- Validation Evidence:
  - `python -m unittest documentation.codex.model-routing.tests.test_assistive_or_review_consumer_integration` PASS (`13` tests)
  - `python -m unittest documentation.codex.model-routing.tests.test_assistive_or_review_capture_dispatcher` PASS (`4` tests)
  - `python -m py_compile documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/model-routing/scripts/bounded_or_worker_outcome.py documentation/codex/model-routing/tests/test_assistive_or_review_consumer_integration.py` PASS
  - direct CLI fixture probe PASS with `selected_path=delegated_assist_only_hypothesis_review` and `self_spawn_detected=false`
  - `python C:\Users\pruve\.codex\skills\janus-final-audit\scripts\validate_final_audit.py documentation/tasks/TASK-SPEC23.2_final_audit.md` PASS
