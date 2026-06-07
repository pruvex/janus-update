# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING
target_skill: janus-spec-review
recommended_model: 5.4
recommended_reasoning: high
new_chat: no
complexity_score: 70
confidence: HIGH
dashboard_hint: CAUTION
reason: Cross-surface contact intelligence spans chat, mail, calendar, memory, privacy gates and public-entry enrichment, but the decision summary is already locked.

## FEATURE IDENTITY
- Feature Name: Semi-automatisches Adressbuch mit Memory-Kopplung
- Feature ID: 15
- Feature Type: Contact Intelligence / Address Book Expansion
- Primary Goal: Janus soll neue Kontakte und neue Kontaktinformationen halbautomatisch erkennen, bestaetigte Kontaktkarten pflegen und bestaetigtes Kontaktwissen mit Memory verbinden.
- Trigger Source: Latest approved decision summary for `Semi-automatisches Adressbuch mit Memory-Kopplung`

## USER VALUE

Der Nutzer muss Kontakte, persoenliche Merkmale und spaetere Ergaenzungen nicht mehr jedes Mal manuell im Adressbuch nachpflegen. Janus erkennt relevante Kontaktinformationen in direktem Nutzerkontext fruehzeitig, schlaegt neue Karten oder sinnvolle Ergaenzungen vor und reduziert dadurch Pflegeaufwand und Luecken im Adressbuch.

Gleichzeitig entsteht ein nuetzlicherer persoenlicher Arbeitskontext: bestaetigte Vorlieben, Abneigungen, Notizen und Kontaktdaten bleiben nicht in einzelnen Chats, Mails oder Erinnerungen verteilt, sondern koennen kontrolliert zwischen Adressbuch und Memory verbunden werden, ohne dass Janus unsichere oder sensible Daten stillschweigend uebernimmt.

## TARGET SURFACE
- Primary Target Surface: bestehendes Adressbuch in den Einstellungen
- Entry Point: bestehende Adressbuch-Sektion in den Einstellungen sowie proaktive Vorschlags- und Rueckfragepunkte im Chat
- Primary User Role: Nutzer, der Kontakte, Organisationen und persoenliche Kontextinformationen mit Janus verwalten und wiederverwenden will
- Surface Scope: bestehende Adressbuch-Verwaltung, Kontaktkarten, Chat-Vorschlaege, gezielte Rueckfragen, Merge-/Ergaenzungsvorschlaege und die kontrollierte Kopplung zum bestehenden Memory-System

## USER ACTION SURFACE
- User Trigger: Janus erkennt in Chat, Mail, Kalender oder anderem direkten Nutzerkontext einen neuen Kontakt, neue Kontaktdaten oder bestaetigbare persoenliche Kontaktinformationen
- User Inputs: Bestaetigung neuer Kontakte, Zustimmung oder Ablehnung von Vorschlaegen, Auswahl bei mehrdeutigen Treffern und gezielte Antworten auf Rueckfragen zu sensiblen Informationen
- Success Behavior: Janus schlaegt neue Kontakte zeitnah im Chat vor, legt nach Bestaetigung Kontaktkarten an, ergaenzt klare nicht-sensitive Kontaktdaten kontrolliert und synchronisiert bestaetigtes Kontaktwissen mit Memory in beide Richtungen
- Failure Behavior: Bei unsicheren, widerspruechlichen oder mehrdeutigen Daten legt Janus nichts stillschweigend an oder um, sondern zeigt einen gezielten Vorschlag, eine Merge-Option oder eine Nutzerauswahl

## SYSTEM BEHAVIOR

Janus baut das bestehende Adressbuch zu einem halbautomatischen Kontaktsystem aus. Wenn im direkten Nutzerkontext ein neuer Kontakt oder eine neue Kontaktinformation erkennbar wird, bewertet Janus zunaechst, ob der Fund klar, direkt zuordenbar und fuer eine Kontaktkarte relevant ist. Die erste Nutzerinteraktion dafuer findet im Chat statt, nicht versteckt in den Einstellungen.

Neue private Kontakte werden nicht ungefragt still angelegt. Janus zeigt stattdessen einen zeitnahen Vorschlag im Chat, aus dem der Nutzer bestaetigen kann, dass eine neue Kontaktkarte entstehen soll. Nach dieser Bestaetigung darf Janus klare, nicht-sensitive Kontaktdaten aus demselben direkten Kontext in die Kontaktkarte uebernehmen, sofern keine Mehrdeutigkeit oder ein Widerspruch vorliegt.

Bestehende Kontakte koennen laufend ergaenzt werden. Dabei unterscheidet Janus zwischen objektiven Kontaktdaten wie E-Mail, Telefonnummer, Adresse oder Website und persoenlichen Merkmalen wie Vorlieben, Abneigungen, Beziehungsdetails oder gesundheitsnahen Informationen. Objektive, eindeutige Daten duerfen kontrolliert uebernommen oder als klare Ergaenzung vorgeschlagen werden. Sensible oder persoenliche Informationen werden nie still uebernommen, sondern nur gezielt abgefragt oder nach expliziter Bestaetigung gespeichert.

Kontaktkarten unterscheiden zwischen Privatpersonen und Organisationen wie Geschaeften, Restaurants oder Aerzten. Nur fuer oeffentliche Eintraege und Organisationen darf Janus fehlende objektive Daten aus dem Internet recherchieren. Diese Recherche erweitert das Adressbuch nicht blind: mehrdeutige Treffer erfordern eine Nutzerauswahl, widerspruechliche Informationen bleiben Vorschlaege, und private Personen werden nie ueber Webrecherche angereichert.

Janus prueft bei jedem Erkennungsfall, ob vermutlich bereits ein passender Kontakt existiert. Statt bei moeglichen Duplikaten automatisch eine zweite Karte anzulegen, zeigt Janus einen Merge- oder Ergaenzungsvorschlag. Der Nutzer behaelt damit die Kontrolle ueber Zusammenfuehrungen, waehrend Janus trotzdem proaktiv auf moegliche Dubletten oder Kartenluecken hinweist.

Bestaetigtes Kontaktwissen und bestaetigtes Memory-Wissen werden kontrolliert gekoppelt. Wenn eine Information im Kontaktkontext bestaetigt wurde, darf sie als bestaetigter Fakt im Memory nutzbar werden. Wenn bestaetigtes Memory-Wissen eine bestehende Kontaktkarte sinnvoll ergaenzen kann, darf Janus diese Ergaenzung ebenfalls als Update oder Rueckfrage anbieten. Die bidirektionale Verbindung bleibt an Bestaetigung, Sensitivitaet und Kontextquelle gebunden.

Abgelehnte Vorschlaege werden gemerkt, damit Janus denselben Kontakt- oder Ergaenzungsvorschlag nicht in kurzer Folge erneut aufdraengt. Erst wenn wesentlich neue Evidenz vorliegt oder sich der Kontext substanziell aendert, darf ein frueher abgelehnter Fall erneut als Vorschlag auftauchen.

## DATA / PERSISTENCE
- Persisted Data: bestehende und neue Kontaktkarten fuer Privatpersonen und Organisationen mit Kontaktdaten, Vorlieben, Abneigungen, Notizen und Verwaltungsstatus im Adressbuch
- New Stored Data: Bestaetigungsstatus, Ablehnungs- oder Suppressionsstatus fuer Vorschlaege, Kontaktart Privatperson versus Organisation, kontrollierte Memory-Verknuepfung und Herkunftskontext fuer bestaetigte Ergaenzungen
- Read Paths: bestehendes Adressbuch, bestehendes Memory, direkter Nutzerkontext aus Chat, Mail, Kalender oder vergleichbaren Janus-Eingaben sowie oeffentliche Webtreffer nur fuer Organisationen oder andere oeffentliche Eintraege
- Write Paths: Kontaktkarten im Adressbuch, Vorschlags- und Suppressionsstatus, bestaetigte Memory-Fakten aus Kontaktwissen und bestaetigte Kontaktkarten-Ergaenzungen aus Memory-Wissen

## CONSTRAINTS

Die Arbeit baut die bestehende Adressbuch-Oberflaeche aus und ersetzt sie nicht durch eine parallele Kontaktverwaltung. Der Nutzer verwaltet Uebersicht und Detailkarten weiterhin im Adressbuch der Einstellungen, waehrend Vorschlaege und Rueckfragen im Chat stattfinden.

Halbautomatisch bedeutet nicht vollautomatisch. Private Kontakte werden nicht ohne Bestaetigung neu angelegt, sensible persoenliche Informationen werden nicht ungefragt uebernommen und mehrdeutige Webtreffer werden nicht eigenstaendig ausgewaehlt.

Die Kontakt-Memory-Kopplung darf den bestehenden Privacy- und Safety-Rahmen nicht aufweichen. Janus darf bestaetigtes Wissen zwischen beiden Systemen nutzbar machen, aber keine unbestaetigten, widerspruechlichen oder sensitiven Annahmen als stillen Systemzustand verfestigen.

## SECURITY / PRIVACY
- User Data Exposure: private Personen duerfen nur aus direktem Nutzerkontext erkannt und ergaenzt werden; keine Webrecherche oder oeffentliche Anreicherung fuer private Kontakte
- Sensitive Fields: Gesundheit, Vorlieben, Abneigungen, Beziehungsdetails, persoenliche Merkmale und vergleichbare sensible Fakten nur nach gezielter Bestaetigung oder ausdruecklicher Nutzerangabe
- External Services: Internet-Recherche ist nur fuer oeffentliche Eintraege und Organisationen erlaubt und darf ausschliesslich objektive Kontaktdaten oder oeffentliche Basisinformationen vorschlagen
- Audit Requirement: Janus muss zwischen Vorschlag, bestaetigter Kontaktkarte, bestaetigtem Memory-Fakt und abgelehntem Vorschlag nachvollziehbar trennen, damit stille Privacy-Verletzungen oder wiederholte Nerv-Muster vermieden werden

## EDGE CASES

Wenn Janus fuer eine Person oder Organisation einen moeglichen Treffer erkennt, der zu einer bestehenden Karte passen koennte, aber nicht eindeutig ist, darf keine automatische Neuanlage entstehen. Stattdessen erscheint ein Merge- oder Zuordnungsvorschlag.

Wenn mehrere oeffentliche Treffer fuer eine Organisation moeglich sind, zum Beispiel mehrere Restaurants oder Arztpraxen mit aehnlichem Namen, braucht Janus eine aktive Nutzerauswahl, bevor Daten uebernommen werden.

Wenn neue Informationen bestehenden Daten widersprechen, zum Beispiel abweichende Telefonnummern, E-Mail-Adressen oder oeffentliche Adressen, bleiben die neuen Angaben im Vorschlagsstatus, bis der Nutzer sie bestaetigt oder verwirft.

Wenn der Nutzer einen Vorschlag ablehnt, darf derselbe Fall nicht dauernd erneut erscheinen. Erst bei substanziell neuer Evidenz oder veraendertem Kontext darf Janus eine neue Anfrage stellen.

Wenn fuer einen Kontakt nur bruchstueckhafte Informationen vorliegen, soll Janus lieber eine unvollstaendige, bestaetigte Karte mit klaren Luecken verwalten als fehlende Teile zu halluzinieren oder durch unsichere Annahmen zu fuellen.

## DEFINITION OF DONE
- [ ] Wenn Janus im direkten Nutzerkontext einen neuen privaten Kontakt erkennt, dann erzeugt es zuerst einen bestaetigbaren Vorschlag im Chat statt einer stillen automatischen Kontaktanlage.
- [ ] Wenn der Nutzer einen neuen Kontakt bestaetigt, dann entsteht im bestehenden Adressbuch eine Kontaktkarte auf der vorhandenen Verwaltungsoberflaeche.
- [ ] Wenn fuer einen bestaetigten Kontakt eindeutige nicht-sensitive Kontaktdaten aus direktem Kontext vorliegen, dann koennen diese kontrolliert in die Kontaktkarte uebernommen oder klar vorgeschlagen werden, ohne dass Mehrdeutigkeiten still akzeptiert werden.
- [ ] Wenn Janus persoenliche oder sensible Kontaktinformationen erkennt, dann werden diese nur nach gezielter Bestaetigung oder ausdruecklicher Nutzerangabe gespeichert.
- [ ] Wenn ein oeffentlicher Eintrag oder eine Organisation unvollstaendige objektive Daten hat, dann darf Janus Internet-Recherche nur als oeffentliche Ergaenzung mit Auswahl- oder Vorschlagslogik nutzen.
- [ ] Wenn Janus einen moeglichen Dublettenfall erkennt, dann erscheint ein Merge- oder Ergaenzungsvorschlag statt einer automatischen zweiten Kontaktkarte.
- [ ] Wenn ein Kontakt- oder Ergaenzungsvorschlag abgelehnt wurde, dann wird dieser Zustand gemerkt, damit derselbe Fall nicht staendig erneut vorgeschlagen wird.
- [ ] Wenn eine Information als Kontaktwissen bestaetigt wurde, dann kann sie kontrolliert fuer Memory nutzbar werden, und bestaetigtes relevantes Memory-Wissen kann umgekehrt als Kontakt-Update vorgeschlagen werden.

## TEST STRATEGY
- Primary Validation Goal: Nachweis, dass Janus Kontakte halbautomatisch erkennt, bestaetigbar anlegt, sichere Ergaenzungen vornimmt, Dubletten sauber behandelt und Memory-Kopplung ohne Privacy-Verletzung steuert
- Automated Validation: gezielte Backend-, Orchestrierungs- und UI-Checks fuer Erkennungskandidaten, Vorschlagsstatus, Dubletten-/Merge-Logik, Suppressionsverhalten, Memory-Sync-Gates und die Trennung zwischen Privatpersonen und oeffentlichen Eintraegen
- Manual Validation: End-to-End-Sichtpruefung ueber Chat und Adressbuch fuer Neuanlage, Ergaenzung, Ablehnung, Merge-Vorschlag, sensible Rueckfrage und oeffentliche Organisationsanreicherung
- Regression Areas: bestehende Kontakte-CRUD-Pfade, Adressbuch in den Einstellungen, Chat-Vorschlagslogik, Memory-Kopplung, Mail-/Kalender-Kontextuebergaben und jede oeffentliche Recherche-Logik fuer Organisationen

## OUT OF SCOPE

Vollautomatische ungefragte Anlage privater Kontakte.

Ungepruefte oder stille Uebernahme sensibler persoenlicher Informationen.

Vollautomatische Auswahl aus mehrdeutigen Webtreffern fuer oeffentliche Eintraege.

Allgemeine Social-Graph-, CRM- oder Marketing-Automatisierung ausserhalb des persoenlichen Janus-Adressbuchkontexts.

## INTERNAL COMPLEXITY BREAKDOWN

Scope Size: 15
Architectural Risk: 14
State / Persistence Complexity: 16
Cross-System Dependencies: 15
Ambiguity Level: 10
Total Complexity Score: 70
Routing Decision: 5.4
Routing Reasoning: high
Routing Confidence: HIGH
Dashboard Hint: CAUTION

## SPEC REVIEW METADATA

- **Review Status:** APPROVED_WITH_NOTES
- **Complexity Score:** 70
- **Risk:** HIGH
- **Recommended Review Model:** 5.4
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-06-06
- **Review Confidence:** HIGH
- **Review Source:** janus-spec-review
