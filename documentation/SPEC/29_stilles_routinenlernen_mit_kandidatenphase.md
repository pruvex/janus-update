# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING
target_skill: janus-spec-review
recommended_model: 5.4
recommended_reasoning: high
new_chat: no
complexity_score: 68
confidence: HIGH
dashboard_hint: CAUTION
reason: The feature changes routine learning, delayed persistence, passive chat transparency, and settings-based control across chat and routine management surfaces.

## FEATURE IDENTITY
- Feature Name: Stilles Routinenlernen mit Kandidatenphase
- Feature Type: Produkt-Feature fuer stilles Lernen wiederkehrender Chat-Ablaeufe mit spaeter sichtbarer Routine-Verwaltung
- Primary Goal: Wiederkehrende erfolgreiche Mehrschritt-Ablaufe sollen ohne Chat-Unterbrechung zuerst als interner Kandidat und erst nach einem zweiten passenden Erfolg als echte gespeicherte Routine entstehen.
- Trigger Source: `LATEST DECISION SUMMARY` fuer die locked Feature-Entscheidung `Stilles Routinenlernen mit Kandidatenphase`
- Primary Persona: Nutzer, der wiederkehrende Assistenzablaeufe natuerlich im Chat ausfuehrt und spaeter transparent von Routinenunterstuetzung profitiert, ohne vor dem Speichern technisch bestaetigen zu muessen.

## USER VALUE

Janus fuehlt sich weniger wie ein Werkzeug mit internem Fachbegriff und mehr wie ein Assistent an, weil erfolgreiche Wiederholungsmuster im Hintergrund erkannt werden, ohne den Nutzer im ersten Moment mit einer Save-Frage zu unterbrechen.

Die Transparenz bleibt erhalten, weil Janus spaeter knapp im Chat markieren darf, dass eine Routine gespeichert oder genutzt wurde, und weil echte gespeicherte Routinen anschliessend sichtbar in den Einstellungen verwaltet werden koennen.

## TARGET SURFACE
- Primary Surface: bestehender Chat mit passiven Transparenzhinweisen bei Routinen-Speicherung und Routinen-Nutzung
- Existing Surface: Teilweise
- Existence Confirmation: Chat ist bestaetigt; ein Routinen-Bereich in den Einstellungen ist als Produktziel gebunden, aber in diesem Entscheidungsartefakt nicht repo-verifiziert
- In-Scope Surfaces: stille Kandidatenbildung nach einem ersten erfolgreichen Mehrschritt-Ablauf; automatische Umwandlung in gespeicherte Routinen nach einem zweiten passenden erfolgreichen Fall; sichtbare Routinen-Verwaltung in den Einstellungen fuer gespeicherte Routinen
- Explicit Non-Surfaces: Save-Bestaetigung im Chat; Feindesign der Verwaltungsoberflaeche; allgemeines autonomes Lernen ueber alle Skill-Arten; Delegations-, OAuth-, Transport- oder allgemeine Agenten-Architektur

## USER ACTION SURFACE
- Entry Action: Der Nutzer stellt im Chat eine natuerliche Anfrage, die als erfolgreicher Mehrschritt-Ablauf ausgefuehrt wird.
- Required Inputs: mindestens ein echter erfolgreicher wiederkehrender Mehrschritt-Fall; spaeter ein zweiter hinreichend passender erfolgreicher Fall fuer dieselbe Routine-Kategorie
- Success Feedback: Janus zeigt keine Save-Frage beim ersten Fall; bei der spaeteren echten Speicherung oder bei der Nutzung einer gespeicherten Routine erscheint nur ein kurzer passiver Hinweis im Chat; gespeicherte Routinen werden in den Einstellungen sichtbar und verwaltbar.
- Failure Feedback: Wenn keine hinreichend stabile oder passende Wiederholung vorliegt, bleibt der Ablauf ein normaler Chat-Fall ohne Speicherhinweis und ohne neue sichtbare Routine.
- Cancel / Undo Behavior: Nutzer koennen gespeicherte Routinen spaeter in den Einstellungen einsehen, deaktivieren oder loeschen; ein erster unsichtbarer Kandidat erzeugt noch keine sichtbare Nutzeraktion.

## SYSTEM BEHAVIOR

Wenn Janus einen erfolgreichen Mehrschritt-Ablauf im Chat erkennt, der die Lernregeln erfuellt, darf Janus intern einen unsichtbaren Routinen-Kandidaten vormerken. Dieser erste Kandidat darf noch keine sichtbare gespeicherte Routine darstellen und darf keine Save-Bestaetigung im Chat verlangen.

Wenn spaeter ein echter zweiter Nutzerfall erkannt wird, der demselben Kandidaten hinreichend entspricht und erneut erfolgreich abgeschlossen wird, wird der Kandidat automatisch in eine echte gespeicherte Routine umgewandelt. Erst ab diesem Zeitpunkt darf die Routine als normale gespeicherte Routine behandelt, spaeter selbststaendig genutzt und in der Routinen-Verwaltung sichtbar gemacht werden.

Janus darf eine gespeicherte Routine spaeter selbststaendig nutzen, wenn eine passende neue Nutzeranfrage vorliegt. In diesem Fall darf Janus im Chat nur eine kurze transparente Anmerkung geben, dass eine gespeicherte Routine verwendet wurde. Entsprechend darf auch bei der automatischen Umwandlung eines Kandidaten in eine echte Routine nur ein kurzer passiver Speicherhinweis erscheinen.

Fehlgeschlagene, nur teilweise erfolgreiche oder nicht ausreichend passende Ablaufe duerfen keine echte Routine erzeugen.

Wenn fuer einen internen Kandidaten innerhalb von 30 Tagen kein zweiter echter passender erfolgreicher Fall auftritt, verfaellt der Kandidat automatisch und wird nicht dauerhaft angesammelt.

Riskante, sensible oder stark kontextabhaengige Ablaufe bleiben in v1 vollstaendig ausserhalb dieses stillen Lernpfads und duerfen weder als Kandidat noch als automatisch gespeicherte Routine entstehen.

Die explizite bisherige Chat-Unterbrechung vor dem Speichern wird durch dieses Verhalten fuer den in Scope liegenden Routine-Lernpfad ersetzt.

## DATA / PERSISTENCE
- Created Data: interner Routinen-Kandidat nach dem ersten qualifying Erfolg; echte gespeicherte Routine nach dem zweiten passenden erfolgreichen Fall
- Updated Data: Routinen-Metadaten fuer Kandidatenstatus, Umwandlungsstatus, Nutzbarkeit und Sichtbarkeit in der Routinen-Verwaltung
- Deleted Data: gespeicherte Routinen koennen durch Nutzer geloescht werden; Kandidaten duerfen durch Lebensdauer- oder Eignungsregeln verfallen oder entfernt werden
- Persistence Scope: Kandidaten bleiben intern und unsichtbar, bis die Umwandlungsregeln erfuellt sind; echte gespeicherte Routinen sind persistent und in den Einstellungen sichtbar
- Visibility Rule: Nur echte gespeicherte Routinen werden in der sichtbaren Routinen-Verwaltung angezeigt; Kandidaten bleiben unsichtbar
- Accumulation Control: Kandidaten duerfen sich nicht unkontrolliert ansammeln und verfallen automatisch, wenn innerhalb von 30 Tagen kein zweiter echter passender erfolgreicher Fall auftritt

## CONSTRAINTS

Das Feature gilt nur fuer wiederkehrende erfolgreiche Mehrschritt-Ablaufe und nicht fuer beliebige Einzelaktionen oder allgemeines breites Lernen.

Ein erster passender Erfolg erzeugt nur einen Kandidaten, niemals sofort eine sichtbare gespeicherte Routine.

Eine echte gespeicherte Routine darf erst nach einem zweiten echten passenden und erfolgreichen Fall entstehen.

Aehnliche, aber nicht wirklich gleiche Ablaufe duerfen nicht zu frueh zusammengelegt werden.

Riskante, sensible oder stark kontextabhaengige Ablaufe sind in v1 komplett out of scope.

Kandidaten muessen nach 30 Tagen ohne zweite erfolgreiche Bestaetigung automatisch verfallen.

Die Verwaltungsoberflaeche fuer Routinen ist funktional erforderlich, aber ihr visuelles Feindesign ist nicht Teil dieser Spec.

## SECURITY / PRIVACY
- Trust Boundary: stilles Lernen darf keine unkontrollierte oder unsichtbare dauerhafte Automatisierung fuer riskante oder sensible Ablaufe schaffen
- Sensitive Workflow Rule: riskante, sensible oder stark kontextabhaengige Ablaufe duerfen in v1 nicht still gelernt werden und nicht als Kandidat oder gespeicherte Routine entstehen
- User Control Rule: Nutzer muessen echte gespeicherte Routinen einsehen, verwalten, deaktivieren und loeschen koennen
- Transparency Rule: Janus darf nur kurze passive Hinweise im Chat geben, wenn eine gespeicherte Routine angelegt oder verwendet wurde, ohne den Nutzer mit einer Save-Entscheidung zu blockieren
- Hidden State Rule: unsichtbare Kandidaten sind nur als Zwischenstatus erlaubt und duerfen nicht die einzige dauerhafte Existenzform einer nutzbaren Routine sein
- Auditability: der Uebergang von Kandidat zu gespeicherter Routine muss nachvollziehbar an Lernregeln, erfolgreichem zweiten Fall und Kandidaten-Verfall ohne rechtzeitige zweite Bestaetigung gebunden bleiben

## EDGE CASES

- Wenn der erste Ablauf erfolgreich, aber nicht stabil genug oder zu stark kontextabhaengig ist, wird kein Kandidat oder keine spaetere echte Routine erzeugt.
- Wenn ein spaeterer Fall nur oberflaechlich aehnlich wirkt, aber nicht derselben wiederverwendbaren Routine entspricht, bleibt der Kandidat unveraendert oder wird nicht verwendet.
- Wenn zwischen erstem und zweitem Fall sehr viel Zeit vergeht, verfaellt der Kandidat nach 30 Tagen statt unkontrolliert weiter zu bestehen.
- Wenn ein Ablauf teilweise fehlschlaegt oder nur einzelne Schritte erfolgreich sind, entsteht keine echte gespeicherte Routine.
- Wenn fuer eine neue Anfrage keine passende gespeicherte Routine vorliegt, antwortet Janus normal ohne Routinen-Hinweis.
- Wenn ein Ablauf riskant, sensitiv oder stark kontextabhaengig ist, bleibt er in v1 ausserhalb dieses Features.

## DEFINITION OF DONE

- [ ] Wenn ein erster erfolgreicher qualifying Mehrschritt-Ablauf im Chat auftritt, dann wird beobachtbar keine Save-Bestaetigung im Chat verlangt und es entsteht nur ein interner Kandidatenstatus.
- [ ] Wenn spaeter ein zweiter echter passender erfolgreicher Fall fuer denselben Kandidaten auftritt, dann wird beobachtbar eine echte gespeicherte Routine erzeugt.
- [ ] Wenn eine echte gespeicherte Routine erzeugt wurde, dann ist sie beobachtbar in der Routinen-Verwaltung der Einstellungen sichtbar und verwaltbar.
- [ ] Wenn Janus spaeter eine passende gespeicherte Routine selbststaendig nutzt, dann erscheint beobachtbar nur ein kurzer passiver Hinweis im Chat statt einer technischen oder blockierenden Speicherinteraktion.
- [ ] Wenn Aehnlichkeit, Erfolg oder Stabilitaet nicht ausreichen, dann wird beobachtbar keine echte gespeicherte Routine erzeugt.
- [ ] Wenn fuer einen Kandidaten innerhalb von 30 Tagen kein zweiter echter passender erfolgreicher Fall auftritt, dann verfaellt der Kandidat beobachtbar, ohne sich in eine gespeicherte Routine umzuwandeln.
- [ ] Wenn ein Nutzer eine gespeicherte Routine deaktiviert oder loescht, dann kann sie beobachtbar nicht mehr als aktive gespeicherte Routine weiterverwendet werden.
- [ ] Wenn ein Ablauf riskant, sensitiv oder stark kontextabhaengig ist, dann entsteht beobachtbar in v1 weder ein Kandidat noch eine normale stille Routine.

## TEST STRATEGY
- Primary Validation Mode: produktnahe Validierung der Kandidatenbildung, Kandidaten-zu-Routine-Umwandlung, passiven Chat-Transparenz und sichtbaren Routinen-Verwaltung
- Required Evidence: ein erster erfolgreicher Mehrschritt-Fall ohne Save-Prompt; ein zweiter passender erfolgreicher Fall mit nachweisbarer Umwandlung; sichtbare Verwaltungsoberflaeche fuer gespeicherte Routinen; Nachweis fuer Nicht-Speicherung bei unpassenden oder fehlgeschlagenen Faellen
- Success Cases: erster qualifying Fall erzeugt nur Kandidat; zweiter passender Erfolg innerhalb von 30 Tagen erzeugt gespeicherte Routine; spaetere Anfrage nutzt gespeicherte Routine mit kurzem Hinweis; Nutzer kann gespeicherte Routine deaktivieren oder loeschen
- Failure Cases: aehnlicher aber unpassender zweiter Fall; fehlgeschlagener oder teilweiser Ablauf; Kandidat ohne zweite Bestaetigung innerhalb von 30 Tagen; riskanter, sensitiver oder stark kontextabhaengiger Ablauf
- Regression Focus: bisherige explizite Save-Unterbrechung wird fuer den in Scope liegenden Lernpfad ersetzt; normale Chat-Antwort ohne Routine bleibt intakt; keine unsichtbare dauerhafte nutzbare Routine ohne spaetere Sichtbarkeit und Kontrolle; kein stilles Lernen fuer riskante oder stark kontextabhaengige v1-Faelle

## OUT OF SCOPE

UI-Feindesign der Routinen-Verwaltung.

Delegations-, Cursor- oder sonstige Ausfuehrungsarchitektur.

OAuth-, Transport- oder Verbindungsdetails.

Allgemeine Agenten-Architektur ausserhalb dieses Routine-Lernpfads.

Breites autonomes Lernen ueber alle Skill- oder Aufgabenarten hinweg.

## SPEC REVIEW METADATA

- **Review Status:** APPROVED
- **Complexity Score:** 68
- **Risk:** HIGH
- **Recommended Review Model:** 5.4
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-07-09
- **Review Confidence:** HIGH
- **Review Source:** janus-spec-review

## INTERNAL COMPLEXITY BREAKDOWN

- Scope Size: 15
- Architectural Risk: 12
- State / Persistence Complexity: 16
- Cross-System Dependencies: 14
- Ambiguity Level: 11
- Total Complexity Score: 68
- Routing Decision: 5.4
- Routing Reasoning: high
- Routing Confidence: HIGH
- Dashboard Hint: CAUTION
