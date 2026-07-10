# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING
target_skill: janus-spec-review
recommended_model: 5.4
recommended_reasoning: high
new_chat: no
complexity_score: 61
confidence: HIGH
dashboard_hint: CAUTION
reason: The feature expands saved-routine reuse across semantic matching, parameter rebinding, fail-closed guards, and regression protection for existing routine behavior.

## SPEC REVIEW METADATA

- **Review Status:** APPROVED
- **Complexity Score:** 61
- **Risk:** HIGH
- **Recommended Review Model:** 5.4
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-07-09
- **Review Confidence:** HIGH
- **Review Source:** janus-spec-review

## FEATURE IDENTITY

- Feature Name: Semantisches, parameterisiertes Routine-Reuse fuer mehrschrittige Routinen
- Feature Type: Produkt-Feature fuer die natuerliche Wiederverwendung bestehender gespeicherter Routinen mit frischer Parameterbindung
- Primary Goal: Gespeicherte mehrschrittige Routinen sollen aus natuerlicher Sprache wiederverwendet werden koennen, auch wenn die neue Anfrage neue konkrete Parameter mitbringt.
- Trigger Source: Locked `LATEST DECISION SUMMARY` aus `documentation/Planned Features/backlog_BACKLOG-123_semantisches_parameterisiertes_routine_reuse_mehrschrittige_routinen.md`
- Primary Persona: Nutzer, der wiederkehrende Multi-Step-Aufgaben im normalen Janus-Chat stellt und nicht denselben exakten Routinenamen oder dieselben alten Werte wiederholen will.

## USER VALUE

Janus fuehlt sich bei wiederkehrenden Aufgaben wesentlich hilfreicher an, weil gespeicherte Routinen nicht nur wie starre Makros funktionieren, sondern neue Anfragen mit passenden frischen Werten sinnvoll wiederverwenden koennen.

Der Nutzer muss sich keine Routinenamen merken und keine technische Speicherlogik verstehen, sondern erlebt, dass Janus bekannte mehrschrittige Aufgaben transparent und sicher erneut uebernimmt.

## TARGET SURFACE

- Primary Target Surface: bestehender Chat-basierter Routinenutzungsfluss bei natuerlichen Nutzeranfragen
- Existing or New Surface: Existing Surface
- Existence Confirmation: confirmed by user
- Included Surfaces: automatische Wiederverwendung gespeicherter Routinen; passiver Transparenzhinweis bei Routinenutzung; bestehender gespeicherter Routinebestand
- Excluded Surfaces: neue Routinenverwaltungs-UI; allgemeine Embedding- oder Vektorsuche; freie fuzzy Makro-Automation ohne klare Constraint-Grenzen; unabgesicherte Ausweitung auf alle Skill-Familien in derselben ersten Umsetzung

## USER ACTION SURFACE

- User Trigger: Der Nutzer stellt eine natuerliche Anfrage, die semantisch zu einer bereits gespeicherten mehrschrittigen Routine passt, aber frische konkrete Werte wie Datum, Stadt, Start oder Ziel enthaelt.
- Action Type: automatische und transparente Wiederverwendung einer bestehenden gespeicherten Routine
- Feedback: Janus gibt weiterhin nur einen kurzen passiven Hinweis, dass eine passende gespeicherte Routine genutzt wurde.
- Confirmation Behavior: Nicht zutreffend: Diese Feature-Spec fuehrt keine neue Pflichtbestaetigung fuer normales Reuse ein.
- Cancel / Undo Behavior: Nutzer muessen keine neue Chat-Aktion zum Abbrechen lernen; wenn keine sichere Uebereinstimmung vorliegt, bleibt Janus im normalen Anfragepfad statt eine unpassende alte Routine auszufuehren.

## SYSTEM BEHAVIOR

Wenn eine neue Nutzeranfrage semantisch zu einer bereits gespeicherten mehrschrittigen Routine passt und die benoetigten frischen Parameter sicher aus der Anfrage ableitbar sind, darf Janus diese gespeicherte Routine wiederverwenden, ohne dass der Nutzer den Routinenamen nennen muss.

Beim Reuse muessen die frischen aktuell angefragten Werte Vorrang vor den Werten eines frueheren Routinenlaufs haben. Die gespeicherte Routine dient dabei als wiederverwendbare mehrschrittige Struktur, nicht als starres Replay alter Parameter.

Das Systemverhalten wird als allgemeine Produktfaehigkeit fuer parameterisiertes mehrschrittiges Routine-Reuse definiert, soll aber im ersten Product Slice mindestens die Familie `calendar.list_events + system.routing` sicher abdecken. Der bereits vorhandene `calendar.list_events + system.weather`-Pfad bleibt erhalten und dient als Regression-Referenz.

Wenn fuer eine semantisch aehnliche Anfrage erforderliche Parameter fehlen, ausdruecklich widerspruechlich sind oder nicht verlaesslich extrahiert werden koennen, darf Janus die alte gespeicherte Routine nicht blind mit veralteten Werten ausfuehren. In solchen Faellen faellt Janus fail-closed auf den normalen Anfragepfad zurueck.

Das Matching darf nicht als offenes Aehnlichkeitsspiel verstanden werden. Es muss an klare mehrschrittige Struktur, skill-spezifische Constraint-Familien und einen konservativen Sicherheitsrahmen gebunden bleiben.

## DATA / PERSISTENCE

- Created Data: Nicht zutreffend: Dieses Feature definiert keine neue eigenstaendige Nutzer-Persistenzklasse neben bestehenden gespeicherten Routinen.
- Updated Data: Bestehende gespeicherte Routinen bleiben die Persistenzbasis; geaendert wird das Produktverhalten fuer ihre spaetere Wiederverwendung.
- Deleted Data: Nicht zutreffend: Diese Spec fuehrt keine neue automatische Loeschlogik fuer Routinen ein.
- Runtime Binding: Frische Anfrageparameter werden zur Laufzeit neu an die passende gespeicherte Routinenstruktur gebunden.
- Persistence Boundary: Alte gespeicherte Laufwerte duerfen nicht still als kanonische Wahrheit fuer eine neue abweichende Anfrage behandelt werden.

## CONSTRAINTS

Die erste Umsetzung muss die allgemeine Produktfaehigkeit klar vorbereiten, darf aber den ersten abgesicherten Product Slice auf eine begrenzte Pilotfamilie fokussieren.

Reuse darf nicht auf frei erfundenen, breit unsicheren oder nur oberflaechlich aehnlichen Parametern beruhen.

Das bestehende natuerliche Reuse fuer `calendar.list_events + system.weather` darf nicht regressieren.

Explizite aktuelle Nutzerwerte haben Vorrang vor historischen Routinenwerten.

Fehlende, mehrdeutige oder widerspruechliche Parameter muessen zu fail-closed statt zu heuristischer Altwert-Wiederverwendung fuehren.

## SECURITY / PRIVACY

- Parameter Safety: Janus darf keine alten Werte still weiterverwenden, wenn die neue Anfrage abweichende oder nicht sicher extrahierbare Werte enthaelt.
- Automation Boundary: Das Feature erweitert nur die Wiederverwendung bestehender gespeicherter Routinen und erlaubt keine freie ungesteuerte Automatisierung beliebiger aehnlicher Aufgaben.
- Transparency Rule: Erfolgreiches Reuse bleibt durch einen kurzen passiven Hinweis sichtbar, ohne den Nutzer mit technischen Details oder Pflichtbestaetigungen zu ueberladen.
- Fail-Closed Rule: Bei unsicherer Zuordnung, fehlenden Parametern oder widerspruechlichen Angaben wird keine unpassende gespeicherte Routine ausgefuehrt.
- Privacy Scope: Das Feature fuehrt keine neue externe Datenquelle, keine neue globale Suchflaeche und keine neue ungebundene Persistenz fuer Nutzerinhalte ein.

## EDGE CASES

Wenn mehrere gespeicherte Routinen oberflaechlich zur gleichen Anfragefamilie passen, aber nur eine die benoetigten Parameter konsistent traegt, darf Janus nur diese sichere Routine verwenden.

Wenn eine neue Anfrage dieselbe Skill-Familie hat, aber fachlich andere Parameterbedeutung traegt, darf keine blinde Wiederverwendung erfolgen.

Wenn ein Nutzer nur einen Teil der benoetigten Werte nennt, bleibt Janus im normalen Anfragepfad statt veraltete Werte aus einem frueheren Routinenlauf zu uebernehmen.

Wenn die neue Anfrage ausdruecklich andere Werte als der fruehere gespeicherte Routinenlauf nennt, muessen die neuen Werte gelten oder der Reuse-Pfad wird verworfen.

Wenn eine gespeicherte `calendar.list_events + system.weather`-Routine natuerlich wiederverwendet wird, muss das bestehende Verhalten weiter funktionieren.

Wenn spaeter weitere Multi-Step-Routine-Familien hinzukommen, darf die Produktlogik nicht auf einen einmaligen `calendar+routing`-Sonderfall fest verdrahtet bleiben.

## DEFINITION OF DONE

- [ ] Wenn eine natuerliche Anfrage sicher zu einer gespeicherten mehrschrittigen Routine passt und frische Parameter vollstaendig extrahierbar sind, dann fuehrt Janus beobachtbar diese gespeicherte Routine mit den aktuellen Werten aus.
- [ ] Wenn die neue Anfrage andere konkrete Werte als ein frueherer Routinenlauf enthaelt, dann haben beobachtbar die aktuellen Nutzerwerte Vorrang vor alten gespeicherten Laufwerten.
- [ ] Wenn eine Anfrage zur Pilotfamilie `calendar.list_events + system.routing` gehoert und sichere aktuelle Route- und Zeitwerte enthaelt, dann kann Janus beobachtbar die passende gespeicherte Routinenstruktur mit diesen neuen Werten wiederverwenden.
- [ ] Wenn fuer eine semantisch passende Anfrage erforderliche Parameter fehlen, nicht sicher extrahierbar sind oder sich widersprechen, dann fuehrt Janus beobachtbar keine unpassende alte Routine mit Altwerten aus.
- [ ] Wenn eine gespeicherte Routine ueber den semantischen Reuse-Pfad genutzt wird, dann erscheint beobachtbar weiterhin nur ein kurzer transparenter Routinenutzungshinweis.
- [ ] Wenn eine natuerliche Anfrage den bestehenden `calendar.list_events + system.weather`-Reuse-Pfad trifft, dann bleibt dieses beobachtbar funktionsfaehig und regressiert nicht.
- [ ] Wenn mehrere Routinen nur oberflaechlich passen, aber keine sichere eindeutige Wiederverwendung moeglich ist, dann bleibt Janus beobachtbar im normalen Anfragepfad.

## TEST STRATEGY

- Primary Validation Mode: produktnahe Validierung natuerlicher Reuse-Faelle mit frischer Parameterbindung und konservativem Fail-Closed-Verhalten
- Required Evidence: mindestens ein positiver Pilotfall fuer `calendar.list_events + system.routing`; Regressionsnachweis fuer `calendar.list_events + system.weather`; mindestens ein Negativfall mit fehlenden oder widerspruechlichen Parametern
- Success Cases: sichere semantische Wiederverwendung mit frischen Werten; neue Werte schlagen alte gespeicherte Laufwerte; transparenter kurzer Routinenutzungshinweis bleibt erhalten
- Failure Cases: unvollstaendige Parameter; widerspruechliche Parameter; nur oberflaechlich aehnliche Routine; Mehrdeutigkeit zwischen mehreren Routinen
- Regression Focus: bestehender Wetter-Reuse-Pfad bleibt intakt; normale Nicht-Routine-Anfragen werden nicht aggressiv fehlgematcht; alte gespeicherte Werte werden nicht unsicher weitergetragen

## OUT OF SCOPE

- Embedding- oder Vektor-basierte freie Routinenaehnlichkeit ueber das gesamte Produkt
- Neue UI fuer Routinenverwaltung oder Routinenbearbeitung
- Allgemeine freie Wiederverwendung aller Multi-Step-Skill-Kombinationen ohne separate Evidenz und Produktfreigabe
- Aufgabenzerlegung, Implementierungsdetails, konkrete API- oder Datenbankschemata

## INTERNAL COMPLEXITY BREAKDOWN

- Scope Size: 13
- Architectural Risk: 12
- State / Persistence Complexity: 13
- Cross-System Dependencies: 13
- Ambiguity Level: 10
- Total Complexity Score: 61
- Routing Decision: 5.4
- Routing Reasoning: high
- Routing Confidence: HIGH
- Dashboard Hint: CAUTION

## SPEC IMPLEMENTATION METADATA

- Implementation Status: DONE
- Final Audit: PASS
- Completion Date: 2026-07-10
- Validation Evidence:
  - `documentation/tasks/TASK-SPEC31.1_final_audit.md`
  - `documentation/tasks/TASK-SPEC31.2_final_audit.md`
  - `python -m pytest backend/tests/test_routine_runner.py -v` - PASS (`19` tests)
  - `python -m pytest backend/tests/test_workflow_offer_service.py -v` - PASS (`18` tests)
  - `python -m pytest backend/tests/unit/test_chat_orchestrator_routine_execution.py -v` - PASS (`3` tests on slice 31.1)
  - `python -m py_compile backend/services/orchestrator/intent_engine.py backend/services/workflow/routine_runner.py backend/services/chat_orchestrator.py backend/tests/test_workflow_offer_service.py backend/tests/test_routine_runner.py` - PASS
  - live Janus GPT/Gemini evidence via `documentation/tasks/TASK-SPEC31.1_execution_result.md` and `documentation/tasks/TASK-SPEC31.2_execution_result.md`
- Implementation Note: Spec 31 is sealed as a two-slice product delivery. The first slice introduced general semantic multi-step routine reuse plus the first safe `calendar.list_events + system.routing` pilot and preserved the short passive routine-used hint; the second slice hardened the same path with fail-closed handling for missing, conflicting, and superficially ambiguous parameters while keeping the existing `calendar.list_events + system.weather` path intact.
