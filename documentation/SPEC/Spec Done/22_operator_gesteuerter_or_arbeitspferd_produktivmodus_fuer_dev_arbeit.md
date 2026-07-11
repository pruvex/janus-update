# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING
target_skill: janus-spec-review
recommended_model: 5.4
recommended_reasoning: high
new_chat: no
complexity_score: 68
confidence: HIGH
dashboard_hint: CAUTION
reason: Productive operator-selected OR dev work needs bounded write authority, durable evidence, and strict Codex-owned acceptance without automatic routing.

## FEATURE IDENTITY
- Feature Name: Operator-gesteuerter OR-Arbeitspferd-Produktivmodus fuer Dev-Arbeit
- Feature Type: Workflow-Erweiterung fuer bestehende Codex- und Janus-Dev-Ablaufe
- Primary Goal: Bei geeigneten Dev-Aufgaben eine bewusste Wahl zwischen Codex und OR ermoeglichen, damit guenstigere OR-Modelle bounded Arbeitsbloecke uebernehmen koennen, waehrend Codex immer Scope, Validierung und finale Annahme kontrolliert.
- Trigger Source: Operator-Wahl an einem geeigneten Arbeitsschritt innerhalb eines eigenen engen Dev-Workhorse-Pfads
- Primary Persona: Operator, der flexibel zwischen Codex-Kontingent und OR-Kosten steuern will

## USER VALUE

Der Nutzer kann fuer geeignete Dev-Arbeit selbst entscheiden, ob Codex oder ein OR-Arbeitspferd den gebundenen Arbeitsblock uebernehmen soll. Dadurch lassen sich Kontingent und Kosten situativ besser steuern, ohne dass Janus die lokale Qualitaets-, Sicherheits- und Governance-Kontrolle verliert.

## TARGET SURFACE
- Primary Surface: Ein eigener enger Dev-Workhorse-Pfad fuer bounded Patch-, Test- und Review-Arbeit mit operator-gesteuerter Pfadwahl
- Existing Surface: Ja
- Existence Confirmation: confirmed by user
- In-Scope Surfaces: Ein separat benannter erster Dev-Workhorse-Pfad fuer bounded Patch-, Test- und Review-Arbeit, operator-gesteuerte Auswahl, bounded OR-Schreibarbeit unter harter Begrenzung, lokale Codex-Abnahme, Kosten- und Ergebnisdarstellung
- Initial Allowed Work Class: Nur Aufgaben innerhalb dieses einen engen Dev-Workhorse-Pfads, nicht allgemeine bestehende Codex- oder Janus-Dev-Workflows und nicht allgemeiner Janus-Produktbetrieb
- Explicit Non-Surfaces: Vollautomatisches Routing, breiter Janus-Produktbetrieb, sofortige Freischaltung mehrerer bestehender Janus-Workflows, globale OR-Freigabe, freie autonome Repo-Schreibgewalt, Release- oder Git-Autoritaet fuer OR

## USER ACTION SURFACE
- Entry Action: Der Workflow zeigt bei einer geeigneten Dev-Aufgabe die explizite Wahl zwischen Codex und OR
- Required Inputs: Nutzerauswahl, sichtbarer OR-Pfad, sichtbare voraussichtliche Kosten und ausreichend klare Erwartung ueber Codex-Abnahme
- Success Feedback: Der Workflow zeigt den gewaehlten Pfad, das bounded OR-Ergebnis, den Validierungsstatus, die tatsaechlichen Kosten und die finale Codex-Entscheidung
- Failure Feedback: Der Workflow zeigt klar, dass der OR-Pfad wegen Scope-, Kosten-, Validierungs-, Zuverlaessigkeits- oder Governance-Grenzen nicht akzeptiert wurde und deshalb bei Codex bleibt oder auf Review/Fallback faellt
- Cancel / Undo Behavior: Der Nutzer kann vor Start den Codex-Pfad waehlen; nach einem ungeeigneten OR-Ergebnis darf kein impliziter Erfolg oder unkontrollierter Persist-Eingriff entstehen

## SYSTEM BEHAVIOR

Der produktive OR-Arbeitspferd-Modus startet bewusst nicht breit ueber mehrere bestehende Workflows, sondern zuerst ueber einen eigenen engen Dev-Workhorse-Pfad. OR wird nur dann angeboten, wenn der aktuelle Arbeitsblock innerhalb dieses Pfads klar bounded, reviewbar und lokal validierbar ist.

Wenn der Nutzer den OR-Pfad waehlt, darf OR einen gebundenen Dev-Arbeitsblock uebernehmen. Dazu koennen Analyse, Review, Testauswertung und auch bounded Schreibarbeit gehoeren, solange die Aufgabe innerhalb der festgelegten Grenzen bleibt.

Auch bei bounded Schreibarbeit bleibt Codex die autoritative Kontrollinstanz. Codex definiert den erlaubten Scope, prueft das Ergebnis lokal, fuehrt noetige Validierung aus und entscheidet final ueber Annahme oder Ablehnung.

Der OR-Pfad darf nur dann produktiv genutzt werden, wenn vorab genug Klarheit ueber Kosten, Grenzen und erwartetes Ergebnis besteht. Fehlen Pflichtinformationen oder driftet die Aufgabe aus dem erlaubten Scope, bleibt der Schritt bei Codex.

Der erste produktive Ausbau ist bewusst auf genau einen eigenen Dev-Workhorse-Pfad begrenzt. Allgemeine Janus-Produktaufgaben und auch sonstige bestehende Codex- oder Janus-Dev-Workflows ausserhalb dieses einen Pfads erhalten in dieser Stufe keinen produktiven OR-Pfad.

Nach jedem OR-Lauf bleibt sichtbar, was OR geliefert hat, welche lokale Validierung stattgefunden hat, ob Fallback oder Rework noetig war und wie Codex final entschieden hat. Ein OR-Ergebnis gilt nie allein durch seine Existenz als abgeschlossen.

## DATA / PERSISTENCE
- Stored Artifacts: Operator-Auswahl, bounded Laufartefakte, Kostenprognose, tatsaechliche Kosten, Validierungsstatus, Fallback- oder Rework-Markierung, finale Codex-Entscheidung, lokal nachvollziehbare Evidenz
- Persistence Scope: Lokale Dev-Workflow-, Healthcheck- und Evidenzartefakte innerhalb des bestehenden Codex- und Janus-Dokumentationssystems
- State Mutation: OR darf bounded Schreibarbeit innerhalb expliziter Grenzen ausfuehren, aber persistente Repo-Wirksamkeit wird erst durch lokale Codex-Pruefung und Annahme wirksam
- Data Lifecycle: Jeder produktive OR-Arbeitsblock hinterlaesst nachvollziehbare Evidenz fuer Kosten, Ergebnisqualitaet, Validierung und finale Annahme oder Ablehnung

## CONSTRAINTS

- Nur operator-gesteuerte Dev-Arbeit innerhalb des einen explizit benannten Dev-Workhorse-Pfads ist in dieser Stufe erlaubt.
- OR darf nur bounded Aufgaben uebernehmen, die reviewbar und lokal validierbar bleiben.
- Bounded Schreibarbeit ist erlaubt, aber nur innerhalb harter Scope-Grenzen.
- Codex bleibt immer Owner fuer Scope, Validierung, Accept oder Reject und Workflow-Abschluss.
- Kein OR-Pfad darf ohne klare Nutzerwahl, sichtbare Grenzen und sichtbare Kostenbasis starten.
- Es gibt keine automatische Produktionsrouting-Aktivierung und keine globale OR-Freigabe in dieser Stufe.
- Aufgaben ausserhalb des Dev-Workhorse-Pfads oder ausserhalb des bounded Scopes muessen weiterhin bei Codex bleiben.

## SECURITY / PRIVACY
- Trust Boundary: OR bleibt ein externer bounded Worker und bekommt keine eigenstaendige Abschluss- oder Governance-Autoritaet
- Local Authority Owner: Codex bleibt Owner fuer Scope-Festlegung, lokale Validierung, finale Annahme oder Ablehnung und dokumentierten Abschluss
- Sensitive Data Rule: Nur der fuer den gebundenen Dev-Arbeitsblock wirklich noetige Kontext darf an OR weitergegeben werden
- Write Safety Rule: Bounded Schreibarbeit braucht feste Grenzen, reviewbare Artefakte und lokale Codex-Abnahme vor finaler Wirksamkeit
- Forbidden Actions: Keine freie Repo-Schreibgewalt, keine Release-, Git-, Merge- oder Routing-Autoritaet fuer OR, kein vollautomatischer Durchlauf ohne Operator-Wahl
- Auditability: Jeder produktive OR-Lauf muss lokal so nachvollziehbar sein, dass Kosten, Scope, Ergebnis, Validierung und finale Codex-Entscheidung spaeter geprueft werden koennen

## EDGE CASES

- Wenn eine Dev-Aufgabe nicht klar bounded oder nicht lokal validierbar ist, wird der OR-Pfad gar nicht angeboten.
- Wenn voraussichtliche Kosten, Scope-Grenzen oder notwendige Validierung nicht sauber bestimmbar sind, bleibt die Aufgabe bei Codex.
- Wenn OR semantisch hilfreich, aber formal oder validatorisch unzureichend liefert, darf kein impliziter Erfolg behauptet werden.
- Wenn bounded Schreibarbeit ausserhalb des erlaubten Scopes landen wuerde, muss der Workflow vor Annahme abbrechen oder auf Codex-only zurueckfallen.
- Wenn eine Aufgabe nicht innerhalb des einen Dev-Workhorse-Pfads liegt, darf sie in dieser Stufe keinen produktiven OR-Pfad erhalten.
- Wenn ein OR-Ergebnis Rework oder manuelle Nacharbeit braucht, bleibt das Ergebnis sichtbar als Review- oder Fallback-Fall und nicht als stillschweigend erfolgreich.

## DEFINITION OF DONE

- [ ] Wenn eine geeignete bounded Dev-Aufgabe erreicht wird, dann kann der Operator beobachtbar zwischen Codex und OR waehlen.
- [ ] Wenn der Operator den OR-Pfad waehlt, dann startet beobachtbar nur ein klar begrenzter Dev-Arbeitsblock und kein freier autonomer Agentenbetrieb.
- [ ] Wenn bounded Schreibarbeit erlaubt ist, dann bleibt beobachtbar der Scope hart begrenzt und die finale Wirksamkeit an lokale Codex-Pruefung gebunden.
- [ ] Wenn OR ein Ergebnis liefert, dann werden beobachtbar Ergebnisstatus, Validierung, tatsaechliche Kosten und finale Codex-Entscheidung angezeigt oder protokolliert.
- [ ] Wenn Kosten-, Scope-, Validierungs- oder Governance-Grenzen verfehlt werden, dann faellt der Schritt beobachtbar auf Codex, Review oder Fallback zurueck.
- [ ] Wenn eine Aufgabe ausserhalb des einen definierten Dev-Workhorse-Pfads liegt, dann wird beobachtbar kein produktiver OR-Pfad angeboten.
- [ ] Wenn ein OR-Ergebnis akzeptiert oder abgelehnt wird, dann bleibt beobachtbar Codex die finale Kontroll- und Abnahmeinstanz.

## TEST STRATEGY
- Validation Level: Workflow-, Scope-, Kosten-, Validierungs- und Accept-or-Reject-Fluss fuer produktive operator-gesteuerte Dev-Arbeit
- Primary Evidence: Operator-Wahl, bounded Laufartefakte, Kostenanzeige, lokale Validierung, finale Codex-Abnahme, Reject- oder Fallback-Nachweise
- Required Automated Coverage: Eligibility-Grenzen, operator-gesteuerte Pfadwahl, bounded Schreibgrenzen, Validierungs- und Fallback-Fluesse, Abschlussstatus
- Manual Verification Need: Begrenzte reale Workflow-Sichtpruefung fuer Wahl, Kostenanzeige, Ergebnisdarstellung und finale Codex-Kontrolle
- Non-Goals For Testing: Kein vollautomatisches Routing, keine globale Produktivfreigabe fuer alle Janus-Aufgaben, keine allgemeine Release-Freigabe

## OUT OF SCOPE

- Vollautomatischer OR-Betrieb ohne ausdrueckliche Operator-Wahl
- Allgemeiner Janus-Produktbetrieb ausserhalb von Dev-Arbeit
- Globale OR-Freigabe fuer alle Skills oder alle Aufgabenklassen
- Abschaffung der finalen Codex-Pruefung und -Entscheidung
- Freie autonome Repo-Schreibgewalt, Git-Autoritaet oder Release-Autoritaet fuer OR
- Kanonische Routing-Tabellen-Aktivierung oder Produktionsrouting-Aktivierung fuer den gesamten Janus-Betrieb

## INTERNAL COMPLEXITY BREAKDOWN

- Scope Size: 13
- Architectural Risk: 16
- State / Persistence Complexity: 12
- Cross-System Dependencies: 17
- Ambiguity Level: 10
- Total Complexity Score: 68
- Routing Decision: 5.4
- Routing Reasoning: high
- Routing Confidence: HIGH
- Dashboard Hint: CAUTION

## SPEC REVIEW METADATA

- **Review Status:** APPROVED_WITH_NOTES
- **Complexity Score:** 68
- **Risk:** HIGH
- **Recommended Review Model:** 5.4
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-06-20
- **Review Confidence:** HIGH
- **Review Source:** janus-spec-review

## SPEC IMPLEMENTATION METADATA

- **Implementation Status:** DONE
- **Final Audit:** PASS
- **Completion Date:** 2026-06-21
- **Validation Evidence:** `documentation/tasks/TASK-SPEC22.4_final_audit.md`; focused runner tests (11 PASS); dispatcher regression tests (4 PASS); Python compilation PASS; scoped diff check PASS.
- **Completion Scope:** Dedicated operator-invoked Dev-workhorse path only. This completion does not activate global OR routing, canonical routing-table changes, or production routing for existing Janus skills.
