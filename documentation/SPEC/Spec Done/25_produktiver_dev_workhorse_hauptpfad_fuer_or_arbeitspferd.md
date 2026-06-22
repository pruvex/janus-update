# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING
target_skill: janus-spec-review
recommended_model: 5.4
recommended_reasoning: high
new_chat: no
complexity_score: 72
confidence: HIGH
dashboard_hint: CAUTION
reason: A productive Dev-workhorse path needs bounded write delegation, visible operator control, and strict Codex-owned acceptance without broad OR activation.

## FEATURE IDENTITY
- Feature Name: Produktiver Dev-Workhorse-Hauptpfad fuer OR-Arbeitspferd
- Feature Type: Workflow-Erweiterung fuer bestehende Dev- und OR-Infrastruktur
- Primary Goal: Einen alltagstauglichen produktiven Dev-Workhorse-Hauptpfad schaffen, in dem der Operator pro geeignetem Fall zwischen Codex und OR-Arbeitspferd waehlt, waehrend Codex Scope, Validierung und finale Annahme kontrolliert.
- Trigger Source: Ein geeigneter bounded Dev-Workhorse-Fall innerhalb des dedizierten produktiven Dev-Workhorse-Pfads
- Primary Persona: Operator, der Codex-Kontingent sparen und stattdessen geeignete bounded Workhorse-Arbeit bewusst an OR delegieren will

## USER VALUE

Der Nutzer kann fuer geeignete bounded Dev-Workhorse-Aufgaben aktiv zwischen Codex und OR-Arbeitspferd waehlen, statt alle Umsetzungsarbeit lokal mit Codex zu verbrauchen. Dadurch laesst sich Codex-Kontingent gezielt dort sparen, wo guenstigere OR-Modelle dieselbe klar begrenzte Arbeit uebernehmen koennen, ohne dass die lokale Qualitaets- und Governance-Kontrolle verloren geht.

## TARGET SURFACE
- Primary Surface: dedizierter produktiver Dev-Workhorse-Pfad
- Existing Surface: Ja
- Existence Confirmation: confirmed by user
- In-Scope Surfaces: der bestehende dedizierte Dev-Workhorse-Einstieg mit sichtbarer Wahl zwischen Codex und OR-Arbeitspferd fuer geeignete bounded Schreib- und Umsetzungsarbeit, feste empfohlene OR-Modelle pro Arbeitsklasse, file-first Laufartefakte, lokale Validierung und expliziter Codex-owned Abschluss
- Explicit Non-Surfaces: direkte breite Einhaengung in bestehende Janus-Produktskills, globale OR-Freigabe, automatische Modellwahl per Auto-Router, allgemeine unbounded Repo-Schreibrechte, Produktionsrouting, kanonische Routing-Tabellen-Aktivierung, Git- oder Release-Autoritaet fuer OR

## USER ACTION SURFACE
- Entry Action: Der Operator startet einen geeigneten Dev-Workhorse-Fall und sieht die explizite Wahl `1 = Codex` oder `2 = OR-Arbeitspferd`
- Required Inputs: bewusste Operator-Wahl zwischen Codex und OR-Arbeitspferd bei einem geeigneten bounded Fall
- Success Feedback: Der Workflow zeigt den gewaehlten Pfad, das empfohlene OR-Modell fuer die Arbeitsklasse, die vorab sichtbare Kostenbasis, das gelieferte bounded Ergebnis, den Validierungsstatus und die finale Codex-Entscheidung
- Failure Feedback: Der Workflow zeigt klar, dass der OR-Pfad wegen Eligibility-, Scope-, Kosten-, Validierungs- oder Qualitaetsgrenzen nicht akzeptiert wurde und deshalb bei Codex bleibt oder auf einen lokalen Follow-up-/Reject-Pfad faellt
- Cancel / Undo Behavior: Wenn der Operator Codex waehlt oder die OR-Voraussetzungen nicht vorliegen, bleibt der Ablauf ohne OR-Seiteneffekt lokal bei Codex

## SYSTEM BEHAVIOR

Der produktive OR-Arbeitspferd-Ausbau startet bewusst nicht breit ueber bestehende Janus-Produktskills, sondern ueber genau einen dedizierten Dev-Workhorse-Hauptpfad. Nur dort darf eine sichtbare Wahl zwischen Codex und OR-Arbeitspferd erscheinen.

Der OR-Pfad wird nur angeboten, wenn der aktuelle Dev-Workhorse-Fall klar bounded, reviewbar und lokal validierbar ist. Nicht geeignete Faelle bleiben deterministisch Codex-only.

Wenn der Operator `2 = OR-Arbeitspferd` waehlt, darf OR genau eine geeignete bounded Schreib- oder Umsetzungsaufgabe uebernehmen. Dazu gehoeren Patch-Kandidaten, kleine bounded Code-Aenderungen, generierte Test- oder Hilfsartefakte und vergleichbare Workhorse-Arbeit innerhalb harter Grenzen.

Das konkrete OR-Modell wird im ersten produktiven Hauptpfad nicht jedes Mal frei gewaehlt, sondern folgt einer festen empfohlenen Zuordnung pro Arbeitsklasse. Die manuelle Wahl des Operators betrifft in dieser Stufe den Pfad Codex versus OR-Arbeitspferd.

Codex bleibt in jedem Fall die letzte autoritative Instanz. Codex definiert den erlaubten Scope, prueft das OR-Ergebnis lokal, fuehrt die notwendige Validierung aus und entscheidet final ueber Accept, lokalen Follow-up oder Reject.

Ein OR-Ergebnis gilt nie allein durch technische Rueckgabe als erfolgreich abgeschlossen. Erst wenn Scope, Kosten, Ergebnisqualitaet und Validierung passen, darf Codex den bounded Lauf als akzeptierten Abschluss behandeln.

Wenn Pflichtinformationen wie Kostenbasis oder Confidence fehlen, wenn der Scope driftet, wenn die Rueckgabe unvollstaendig ist oder wenn die lokale Validierung scheitert, faellt der Ablauf direkt auf einen klaren Codex-owned Ausgang zurueck.

Der erste produktive Hauptpfad bleibt bewusst eng: genau ein dedizierter Dev-Workhorse-Pfad, genau bounded Schreib- und Umsetzungsarbeit und keine breite OR-Ausweitung ueber allgemeine Janus- oder Produktworkflows.

## DATA / PERSISTENCE
- Stored Artifacts: Operator-Auswahl, file-first Laufartefakte, bounded Ergebnisartefakte, Validierungsstatus, Kostenprognose, tatsaechliche Kosten wenn verfuegbar, Fallback- oder Rework-Markierung und finaler Codex-Abschlussstatus
- Persistence Scope: lokale Dev-Workflow-, Telemetrie-, Healthcheck- und Evidenzartefakte innerhalb des bestehenden Codex- und Janus-Dokumentationsrahmens
- State Mutation: OR darf bounded Schreib- und Umsetzungsarbeit innerhalb expliziter Grenzen ausfuehren, aber die finale Repo-Wirksamkeit bleibt an die lokale Codex-Pruefung und Annahme gebunden
- Data Lifecycle: Jeder produktive OR-Arbeitspferd-Lauf hinterlaesst nachvollziehbare lokale Evidenz fuer Pfadwahl, Kosten, Ergebnisqualitaet, Validierung und finale Annahme oder Ablehnung

## CONSTRAINTS

- Nur der dedizierte Dev-Workhorse-Hauptpfad ist in dieser Stufe produktiv OR-faehig.
- OR darf nur bounded Schreib- und Umsetzungsarbeit uebernehmen, die reviewbar und lokal validierbar bleibt.
- Der OR-Pfad darf nur nach ausdruecklicher Operator-Wahl starten.
- Das konkrete OR-Modell folgt in dieser Stufe einer festen empfohlenen Zuordnung pro Arbeitsklasse.
- Codex bleibt immer Owner fuer Scope, Validierung, Accept oder Reject und Workflow-Abschluss.
- Kein OR-Pfad darf stillschweigend globale OR-Freigabe, Produktionsrouting oder breite Skill-Aktivierung erzeugen.
- Aufgaben ausserhalb des dedizierten Dev-Workhorse-Pfads muessen weiterhin bei Codex bleiben.

## SECURITY / PRIVACY
- Trust Boundary: OR bleibt ein externer bounded Worker ohne eigene Abschluss-, Git-, Release-, Routing- oder Governance-Autoritaet
- Local Authority Owner: Codex bleibt Owner fuer Scope-Festlegung, lokale Validierung, finale Annahme oder Ablehnung und dokumentierten Abschluss
- Sensitive Data Rule: Nur der fuer den gebundenen Dev-Workhorse-Fall noetige Kontext darf an OR weitergegeben werden
- Write Safety Rule: Bounded Schreibarbeit braucht feste Grenzen, reviewbare Artefakte und lokale Codex-Abnahme vor finaler Wirksamkeit
- Forbidden Actions: keine freie unbounded Repo-Schreibgewalt, keine Produktionsrouting-Aussagen, keine Git- oder Release-Autoritaet fuer OR, kein automatischer Erfolg allein durch OR-Rueckgabe
- Auditability: Jeder produktive OR-Lauf muss lokal so nachvollziehbar sein, dass Pfadwahl, Kosten, Scope, Ergebnis, Validierung und finale Codex-Entscheidung spaeter geprueft werden koennen

## EDGE CASES

- Wenn ein Dev-Workhorse-Fall nicht klar bounded oder nicht lokal validierbar ist, erscheint keine OR-Auswahl.
- Wenn die vorab noetige Kostenbasis oder Confidence fehlt, bleibt der Schritt bei Codex.
- Wenn eine bounded Schreibaufgabe ueber den erlaubten Scope hinausgehen wuerde, muss der Lauf vor Annahme abbrechen oder auf Codex-only zurueckfallen.
- Wenn OR formal liefert, aber semantisch oder validatorisch unzureichend ist, darf kein impliziter Erfolg behauptet werden.
- Wenn ein Ergebnis Rework oder manuelle Nacharbeit braucht, bleibt es als Review- oder Fallback-Fall sichtbar und nicht als still akzeptierter Abschluss.
- Wenn eine Aufgabe ausserhalb des dedizierten Dev-Workhorse-Pfads liegt, darf sie in dieser Stufe keinen produktiven OR-Pfad erhalten.

## DEFINITION OF DONE

- [x] Wenn ein geeigneter bounded Dev-Workhorse-Fall erreicht wird, dann kann der Operator beobachtbar zwischen Codex und OR-Arbeitspferd waehlen.
- [x] Wenn der Operator den OR-Pfad waehlt, dann startet beobachtbar nur ein klar begrenzter bounded Schreib- oder Umsetzungsblock und kein freier autonomer Agentenbetrieb.
- [x] Wenn bounded Schreibarbeit erlaubt ist, dann bleibt beobachtbar der Scope hart begrenzt und die finale Wirksamkeit an lokale Codex-Pruefung gebunden.
- [x] Wenn OR ein Ergebnis liefert, dann werden beobachtbar Ergebnisstatus, Validierung, Kosten und finale Codex-Entscheidung angezeigt oder protokolliert.
- [x] Wenn Kosten-, Scope-, Validierungs- oder Qualitaetsgrenzen verfehlt werden, dann faellt der Schritt beobachtbar auf einen lokalen Codex-owned Ausgang zurueck.
- [x] Wenn eine Aufgabe ausserhalb des dedizierten Dev-Workhorse-Pfads liegt, dann wird beobachtbar kein produktiver OR-Pfad angeboten.
- [x] Wenn ein OR-Ergebnis akzeptiert oder abgelehnt wird, dann bleibt beobachtbar Codex die finale Kontroll- und Abnahmeinstanz.

## TEST STRATEGY
- Primary Validation Mode: lokale Workflow-, Eligibility-, Scope-, Kosten-, Validierungs- und Accept-or-Reject-Pruefung fuer den dedizierten produktiven Dev-Workhorse-Pfad
- Required Evidence: sichtbare Operator-Wahl, bounded Laufartefakte, Kostenanzeige, lokale Validierung, finale Codex-Abnahme, Reject- oder Fallback-Nachweise
- Success Cases: geeigneter bounded Dev-Workhorse-Fall mit sichtbarer Wahl und akzeptiertem OR-Ergebnis; geeigneter bounded Schreibfall mit klarer Scope-Einhaltung und finalem Codex-Abschluss
- Failure Cases: nicht geeigneter Fall ohne Gate; fehlende Kostenbasis oder Confidence; Scope-Verletzung; unvollstaendige oder qualitativ unsaubere Rueckgabe; lokale Validierung FAIL
- Regression Focus: keine breite Aktivierung ausserhalb des dedizierten Dev-Workhorse-Pfads; kein Verlust der finalen Codex-Autoritaet; keine still akzeptierten OR-Ergebnisse; keine unbounded Schreibausweitung

## OUT OF SCOPE

Direkte breite Einhaengung in bestehende Janus-Produktskills, globale OR-Freigabe fuer alle Aufgabenklassen, automatische Modellwahl per Auto-Router im ersten produktiven Pfad, Abschaffung der finalen Codex-Pruefung, freie autonome Repo-Schreibgewalt, Git- oder Release-Autoritaet fuer OR, Produktionsrouting und kanonische Routing-Tabellen-Aktivierung.

## SPEC REVIEW METADATA

- **Review Status:** APPROVED_WITH_NOTES
- **Complexity Score:** 72
- **Risk:** HIGH
- **Recommended Review Model:** 5.5
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-06-22
- **Review Confidence:** HIGH
- **Review Source:** janus-spec-review

## INTERNAL COMPLEXITY BREAKDOWN

- Scope Size: 14
- Architectural Risk: 17
- State / Persistence Complexity: 13
- Cross-System Dependencies: 17
- Ambiguity Level: 11
- Total Complexity Score: 72
- Routing Decision: 5.4
- Routing Reasoning: high
- Routing Confidence: HIGH
- Dashboard Hint: CAUTION

## SPEC IMPLEMENTATION METADATA

- Implementation Status: DONE
- Final Audit: PASS
- Completion Date: 2026-06-22
- Validation Evidence:
  - `documentation/tasks/TASK-SPEC25.1_final_audit.md`
  - `documentation/tasks/TASK-SPEC25.2_final_audit.md`
  - `documentation/tasks/TASK-SPEC25.3_final_audit.md`
  - `python -m unittest documentation.codex.model-routing.tests.test_codex_dev_workhorse_runner` - PASS (`19` tests)
  - `python -m unittest documentation.codex.model-routing.tests.test_bounded_or_worker_eligibility` - PASS (`31` tests)
  - configuration-change seam probe - PASS (`gate=model/A`, `dispatcher=model/A`, `telemetry=model/A`)
