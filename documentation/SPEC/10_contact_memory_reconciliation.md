# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING

target_skill: janus-spec-review
recommended_model: 5.5
recommended_reasoning: high
new_chat: no
complexity_score: 74
confidence: HIGH
dashboard_hint: CAUTION
reason: Persistence sync between Memory and address book needs strict privacy, conflict, and ambiguity rules.

## SPEC REVIEW METADATA

- **Review Status:** APPROVED_WITH_NOTES
- **Complexity Score:** 74
- **Risk:** HIGH
- **Recommended Review Model:** 5.5
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-06-08
- **Review Confidence:** HIGH
- **Review Source:** janus-spec-review

## FEATURE IDENTITY

- Feature Name: Contact-Memory Reconciliation fuer bestehende Adressbuchkontakte
- Primary Goal: Janus haelt bestaetigtes Kontaktwissen zwischen lokalem Memory und bestehenden Adressbuchkontakten konsistent.
- User Problem: Janus erinnert Kontaktfakten im Memory, aber dieselben Fakten fehlen im strukturierten Adressbuchkontakt.
- Routing Decision: 5.5
- Routing Reasoning: high
- Routing Confidence: HIGH
- Dashboard Hint: CAUTION

## USER VALUE

Janus beantwortet Kontaktfragen vollstaendiger und verlaesslicher, weil sichere Kontaktfakten nicht nur als lose Memory-Eintraege existieren, sondern beim passenden bestehenden Adressbuchkontakt sichtbar werden.

Das Adressbuch bleibt die kanonische strukturierte Kontaktansicht, waehrend Memory als Quelle fuer nachziehbare Zusatzfakten dienen darf.

## TARGET SURFACE

- Primary Target Surface: Chat-basierte Kontaktfakten und Kontakt-Recall
- Existing or New Surface: Existing Surface
- Existence Confirmation: confirmed by user
- Included Surfaces: memory.write, Kontakt-Recall, Kontakt-Oeffnung oder Kontakt-Suche
- Excluded Surfaces: Globaler Hintergrundscan, App-Start-Vollabgleich, externe Web-Recherche

## USER ACTION SURFACE

- User Trigger: Der Nutzer nennt einen Kontaktfakt oder fragt nach einem Kontakt, z. B. `Was weisst du ueber Chris Gier?`.
- Action Type: Chat-basierte automatische Synchronisierung bei sicherer Zuordnung.
- Feedback: Janus bestaetigt transparent, wenn ein Fakt im lokalen Gedaechtnis und im Adressbuch vermerkt wurde.
- Confirmation Behavior: Bei Unsicherheit fragt Janus kurz und konkret nach, bevor ins Adressbuch geschrieben wird.
- Cancel / Undo Behavior: Nicht zutreffend: Dieses Feature definiert keine neue Undo-Oberflaeche.

## SYSTEM BEHAVIOR

Wenn ein sicherer, niedrig-riskanter Kontaktfakt neu per direkter Nutzeraeusserung oder bestaetigtem Kontaktwissen entsteht und eindeutig einem bestehenden Adressbuchkontakt zugeordnet werden kann, synchronisiert Janus den Fakt automatisch in das passende strukturierte Kontaktfeld.

Wenn Janus bei Kontakt-Recall, Kontakt-Oeffnung oder Kontakt-Suche sichere Memory-Fakten fuer genau diesen bestehenden Kontakt findet, die im Adressbuch noch fehlen, zieht Janus diese Fakten automatisch nach, sofern der Memory-Ursprung als nutzerbestaetigt oder bereits als bestaetigtes Kontaktwissen gilt.

Wenn Kontakt, Fakt, Zuordnung oder Feldklasse nicht eindeutig ist, fragt Janus kurz konkret nach, statt still zu synchronisieren.

Wenn mehrere Kontakte passen, wird nicht automatisch synchronisiert.

Wenn ein sicherer Memory-Fakt einem bestehenden Adressbuchwert widerspricht, fragt Janus konkret nach und beschreibt beide Werte, statt den Kontakt still zu aendern.

Wenn der Fakt bereits im Adressbuch existiert, erzeugt Janus keine Dublette und bestaetigt nicht faelschlich eine neue Aenderung.

Wenn ein Modell nach erfolgreicher Synchronisierung keine stabile Antwort erzeugt, gibt Janus eine deterministische transparente Speicherbestaetigung aus.

## DATA / PERSISTENCE

- Created Data: Keine neuen Nutzeroberflaechen-Daten; bestehende Kontaktfelder duerfen mit sicheren Fakten ergaenzt werden.
- Updated Data: Vorlieben, Abneigungen, Ernaehrungsform/Besonderheiten, Hobbys und einfache Gewohnheiten bestehender Kontakte.
- Deleted Data: Keine automatische Loeschung, ausser fachlich gleichwertige Dubletten oder falsch klassifizierte sichere Werte werden in die richtige Kontaktkategorie ueberfuehrt.
- Remembered Data: Memory-Fakten bleiben als lokale Wissensquelle erhalten.
- Canonical View: Das Adressbuch ist fuer strukturierte Kontaktinformationen die kanonische Ansicht.
- Legacy Memory Handling: Bereits vorhandene sichere Memory-Fakten werden beim naechsten Kontakt-Recall oder Kontakt-Oeffnen/Suchen nachgezogen, wenn ihr Ursprung nutzerbestaetigt oder bestaetigtes Kontaktwissen ist.
- Conflict Handling: Bei Widerspruch zwischen Memory und Adressbuch wird keine stille Aenderung vorgenommen; Janus fragt konkret nach.

## CONSTRAINTS

Auto-Sync gilt nur fuer bestehende Adressbuchkontakte. Das Feature legt keine neuen Kontakte aus Memory-Fakten an.

Auto-Sync darf keine konflikthaften Werte blind ueberschreiben.

Auto-Sync darf keine sensiblen oder riskanten Fakten still in das Adressbuch uebernehmen.

Auto-Sync aus Memory ist nur fuer direkte Nutzerfakten oder bereits bestaetigtes Kontaktwissen erlaubt. Rein modellgenerierte, importierte oder unklare Memory-Fakten fuehren zu einer Rueckfrage oder bleiben unveraendert.

Janus darf unklare Pronomen nur verwenden, wenn der Chat-Kontext eindeutig auf genau einen bestehenden Kontakt zeigt.

Der Sync darf Kontaktfragen nicht in Websuche, RSS, Wikipedia oder allgemeine Personensuche umleiten, wenn lokale Kontaktdaten vorhanden sind.

## SECURITY / PRIVACY

- Sensitive Data Handling: Sensitive Fakten werden nicht still automatisch ins Adressbuch uebernommen.
- Auto-Sync Allowed: Vorlieben, Abneigungen, Ernaehrungsform/Besonderheiten, Hobbys und einfache Gewohnheiten.
- Auto-Sync Forbidden: Adresse, Telefonnummer, Beziehung, Gesundheit, Politik, Religion, Finanzen und konflikthafte Identitaetsdaten.
- Memory Trust Boundary: Automatischer Sync ist nur fuer nutzerbestaetigte Kontaktfakten oder bereits bestaetigtes Kontaktwissen erlaubt.
- External Services: Keine externe Recherche oder Cloud-Abgleich fuer diese Synchronisierung.
- Ambiguity Handling: Bei unklarer Kontaktzuordnung oder unsicherem Fakt fragt Janus konkret nach.
- Conflict Handling: Bei abweichendem bestehenden Adressbuchwert fragt Janus sichtbar nach und nennt Memory-Wert und Adressbuchwert.
- Transparency: Janus sagt sichtbar, wenn ein Fakt sowohl im lokalen Gedaechtnis als auch im Adressbuch vermerkt wurde.

## EDGE CASES

Mehrere Kontakte mit gleichem oder aehnlichem Namen fuehren zu einer Rueckfrage.

Ein Memory-Fakt mit Kontaktname, aber ohne bestehendem Adressbuchkontakt, wird nicht automatisch zu einem neuen Kontakt.

Politische Aussagen wie starke Abneigungen gegen Parteien gelten nicht als still auto-sync-faehige Vorliebe oder Abneigung.

Ernaehrungsformen wie Vegetarier oder vegan gelten als Besonderheiten/Details, nicht als normale Vorliebe.

Einfache kombinierte Vorlieben wie `Star Wars und Kimchi` duerfen getrennt gespeichert werden, wenn beide Werte niedrig-riskant sind.

Laengere Phrasen wie `Zeit im Garten` duerfen nicht unnatuerlich in Einzelwoerter zerlegt werden.

Widersprueche zwischen Memory und Adressbuch duerfen nicht still ueberschrieben werden.

Rein modellgenerierte oder importierte Memory-Fakten duerfen nicht automatisch ins Adressbuch uebernommen werden, auch wenn sie lokal eindeutig wirken.

## DEFINITION OF DONE

- [ ] Wenn ein Nutzer einen eindeutigen sicheren Fakt ueber einen bestehenden Kontakt nennt, dann erscheint dieser Fakt im passenden Adressbuchfeld.
- [ ] Wenn Janus den Fakt automatisch synchronisiert, dann bestaetigt Janus transparent die Speicherung im lokalen Gedaechtnis und im Adressbuch.
- [ ] Wenn ein sicherer Memory-Fakt fuer einen bestehenden Kontakt beim Kontakt-Recall fehlt, dann wird er beim naechsten Recall ins Adressbuch nachgezogen.
- [ ] Wenn ein Memory-Fakt nicht nutzerbestaetigt oder kein bestaetigtes Kontaktwissen ist, dann wird er nicht still ins Adressbuch synchronisiert.
- [ ] Wenn mehrere Kontakte passen, dann fragt Janus nach und schreibt nichts still ins Adressbuch.
- [ ] Wenn ein Memory-Fakt einem bestehenden Adressbuchwert widerspricht, dann fragt Janus nach und nennt beide Werte.
- [ ] Wenn ein Fakt sensitiv oder riskant ist, dann wird er nicht still automatisch ins Adressbuch synchronisiert.
- [ ] Wenn ein Fakt bereits im Adressbuch steht, dann entsteht keine Dublette.
- [ ] Wenn eine Ernaehrungsform erkannt wird, dann steht sie unter Besonderheiten/Details und nicht unter Vorlieben.
- [ ] Wenn ein Kontakt-Recall lokale Daten hat, dann fragt Janus nicht, ob der Nutzer sich selbst oder eine andere Person meint.

## TEST STRATEGY

- Unit Tests: Kontaktfakt-Erkennung, sichere Feldklassen, Duplikatvermeidung, Diaet-Klassifizierung, Pronomen-/Alias-Zuordnung.
- Integration Tests: Nutzerbestaetigtes memory.write zu bestehendem Kontakt, Kontakt-Recall zieht alte bestaetigte Memory-Fakten nach, unsichere Zuordnung erzeugt Rueckfrage.
- Negative Tests: Politik, Gesundheit, Adresse, Telefonnummer, Beziehung, modellgenerierte/importierte Memory-Fakten, Konflikte und mehrere Kontaktkandidaten werden nicht still auto-synchronisiert.
- Manual Test: Chris-Gier-Szenario mit bestehenden Memory-Fakten `Star Wars` und `Kimchi` und leerem Adressbuchfeld.
- Regression Tests: Kontakt-Recall bleibt lokal und nutzt keine Web-/RSS-/Wikipedia-Antwort.

## OUT OF SCOPE

Globaler Hintergrundscan.

App-Start-Vollabgleich.

Automatisches Anlegen neuer Kontakte aus Memory.

Automatisches Ueberschreiben konflikthafter Kontaktfelder.

Stille Uebernahme sensibler Daten.

Neue Undo- oder Kontaktverwaltungs-UI.

## INTERNAL COMPLEXITY BREAKDOWN

- Scope Size: 14
- Architectural Risk: 15
- State / Persistence Complexity: 18
- Cross-System Dependencies: 17
- Ambiguity Level: 10
- Total Complexity Score: 74
