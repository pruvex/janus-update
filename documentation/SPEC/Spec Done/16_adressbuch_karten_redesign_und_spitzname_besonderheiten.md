# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING
target_skill: janus-spec-review
recommended_model: 5.4
recommended_reasoning: medium
new_chat: no
complexity_score: 51
confidence: HIGH
dashboard_hint: CAUTION
reason: Existing address book surface gains a new persisted nickname field and a clearer card/form structure without broader architecture or privacy changes.

## FEATURE IDENTITY
- Feature Name: Adressbuch-Karten Redesign und Spitzname/Besonderheiten-Struktur
- Feature ID: 16
- Feature Type: Address Book UX Refactor / Contact Structure Extension
- Primary Goal: Das bestehende Adressbuch soll aufgeraeumtere Janus-konforme Kontaktkarten und eine klarere Kontaktstruktur mit Spitzname, Vorlieben, Abneigungen und Besonderheiten erhalten.
- Trigger Source: Latest approved decision summary for `Adressbuch-Karten aufraeumen und Kontaktstruktur erweitern`

## USER VALUE

Der Nutzer soll Kontakte schneller lesen und persoenlich nuetzlicher verwalten koennen. Statt technischer oder interner Statussignale sieht er auf der Kontaktkarte vor allem die Informationen, die im Alltag fuer Wiedererkennung und Umgang wichtig sind.

Durch den neuen Spitznamen und die sauber getrennten Bereiche fuer Vorlieben, Abneigungen und Besonderheiten wird das Adressbuch menschlicher und praktischer. Kontakte lassen sich leichter einordnen, ohne dass wichtige freie Hinweise in einer unklaren Notizflaeche versteckt bleiben.

## TARGET SURFACE
- Primary Target Surface: bestehendes Adressbuch in den Einstellungen
- Entry Point: bestehende Kontaktkarten und bestehender Kontakt-Erstellen/Bearbeiten-Dialog
- Primary User Role: Nutzer, der persoenliche Kontakte und Organisationen in Janus uebersichtlich pflegen will
- Surface Scope: bestehende Kontaktkarten-Darstellung und bestehender Kontaktdialog inklusive sichtbarer Feldstruktur

## USER ACTION SURFACE
- User Trigger: Nutzer oeffnet das Adressbuch, betrachtet Kontaktkarten oder erstellt/bearbeitet einen Kontakt
- User Inputs: voller Name, optionaler Kurz-/Spitzname, Kontaktart, Kategorie, Kontaktdaten sowie getrennte Inhalte fuer Vorlieben, Abneigungen und Besonderheiten
- Success Behavior: Kontaktkarten wirken modern, ruhig und Janus-passend; der volle Name bleibt Hauptzeile, ein vorhandener Spitzname erscheint dezent als Zusatz; Kontaktinformationen sind im Dialog in klar getrennte Abschnitte gegliedert
- Failure Behavior: Bestehende Kontaktinformationen gehen nicht verloren; Kontakte ohne Spitzname oder ohne strukturierte Zusatzinhalte bleiben weiterhin sauber lesbar; technische Status- oder Herkunftsinfos erscheinen nicht wieder prominent auf der Karte

## SYSTEM BEHAVIOR

Das bestehende Adressbuch bleibt die einzige Kontaktoberflaeche, wird aber visuell und strukturell gestrafft. Die Kontaktkarte soll wie eine moderne Janus-Karte wirken: ruhig, fokussiert und auf menschlich relevante Informationen reduziert. Technische oder nur intern sinnvolle Metadaten wie Herkunft, letztes Ergebnis oder vergleichbare Vorschlags-/Sync-Kontexte gehoeren nicht mehr zur primaeren Kartenansicht.

Der volle Kontaktname bleibt die wichtigste sichtbare Identitaet auf der Karte. Wenn ein Kurz- oder Spitzname vorhanden ist, erscheint er lediglich als dezenter Zusatz unterhalb oder direkt am Namen, ohne den offiziellen oder vollstaendigen Namen zu ersetzen.

Die Kontaktkarte gruppiert persoenliche Zusatzinformationen sichtbar nach ihrem Zweck. Vorlieben und Abneigungen bleiben getrennt, damit positive und negative Praeferenzen nicht vermischt werden. Das bisherige Detail-/Notizkonzept wird fachlich zu einem einzigen Bereich `Besonderheiten` zusammengefuehrt. Dort stehen freie, aber alltagsrelevante Eigenschaften oder Hinweise wie vegetarisch, Allergien oder vergleichbare Merkmale.

Der Kontaktdialog spiegelt dieselbe Struktur wider wie die Karte. Vorlieben, Abneigungen und Besonderheiten erscheinen als klar getrennte Eingabebereiche. Der Nutzer soll nicht zwischen Kartenansicht und Bearbeitungsdialog zwei unterschiedliche Informationsmodelle erleben.

Das neue Spitznamenfeld ist ein eigener persistenter Kontaktbestandteil. Bestehende Kontakte ohne Spitznamen bleiben gueltig und muessen keinen neuen Wert erhalten. Die Umstellung auf `Besonderheiten` darf bestehende Inhalte aus dem frueheren Detail-/Notizbereich nicht unlesbar machen oder verlieren; vorhandene Inhalte muessen weiterhin sichtbar und bearbeitbar bleiben, nur unter der neuen fachlichen Einordnung.

## DATA / PERSISTENCE
- Persisted Data: bestehende Kontaktkarten mit Name, Kontaktart, Kategorie, Kontaktdaten, Vorlieben, Abneigungen und weiteren Kontaktfeldern bleiben erhalten
- New Stored Data: neues persistentes Feld fuer Kurz-/Spitzname als eigener Kontaktbestandteil
- Read Paths: bestehendes Adressbuch und bestehende Kontakt-Detaildaten
- Write Paths: Kontakt-Erstellen/Bearbeiten im bestehenden Adressbuch; bestehendes persoenliches Detailfeld wird fachlich als `Besonderheiten` weitergefuehrt und das bisherige Notizkonzept darin aufgefangen

## CONSTRAINTS

Die Arbeit bleibt auf der bestehenden Adressbuch-Surface. Es entsteht keine zweite Kontaktoberflaeche, kein separates Profilkonzept und keine neue Memory- oder Vorschlagslogik.

Das Redesign darf die Karte optisch modernisieren, aber keine Janus-fremde Stilrichtung einfuehren. Die Karte soll zur bestehenden Janus-UI passen und bewusst aufgeraeumt wirken, statt moeglichst viele Rohdaten gleichzeitig anzuzeigen.

Die neue Struktur darf keine bestaetigten oder bereits gespeicherten Kontaktinformationen verlieren. Bestehende Inhalte aus persoenlichen Details und bisherigen Freitext-Hinweisen muessen bei der Umstellung weiter nutzbar bleiben.

## SECURITY / PRIVACY
- User Data Exposure: Kontaktkarten duerfen nur fuer den Nutzer relevante Informationen prominent zeigen und keine technischen internen Statuswerte als primaeren Karteninhalt hervorheben
- Sensitive Fields: Besonderheiten kann gesundheitsnahe oder persoenliche Hinweise wie Allergien oder Ernaehrung enthalten und bleibt daher Teil des bestehenden privaten Kontaktkontexts
- External Services: Nicht zutreffend: diese Arbeit fuehrt keine neue externe Recherche, keinen neuen Provider und keine neue Systemkopplung ein
- Audit Requirement: Die Umstellung muss nachvollziehbar zwischen neuer sichtbarer Struktur und bestehendem Kontaktbestand trennen, damit weder persoenliche Hinweise verloren gehen noch interne Metadaten versehentlich wieder zur Hauptansicht werden

## EDGE CASES

Wenn ein Kontakt keinen Spitznamen hat, bleibt die Karte vollstaendig und zeigt nur den regulaeren Namen ohne leeren Platzhalter.

Wenn ein Kontakt keine Vorlieben, keine Abneigungen oder keine Besonderheiten hat, duerfen die entsprechenden Bereiche nicht als stoerende Leerbloecke erscheinen.

Wenn bestehende Kontakte Inhalte aus dem bisherigen Detail- oder Notizbereich enthalten, muessen diese unter `Besonderheiten` weiterhin sichtbar und bearbeitbar bleiben, statt zu verschwinden oder unklar verteilt zu werden.

Wenn ein Kontakt eine Organisation statt einer Privatperson ist, muss die Karte weiterhin sinnvoll lesbar sein, auch wenn persoenliche Bereiche teilweise leer bleiben.

## DEFINITION OF DONE
- [x] Wenn ein Kontakt im Adressbuch angezeigt wird, dann zeigt die Karte keine prominenten Herkunfts-, Ergebnis- oder vergleichbaren internen Statusinformationen mehr als primaeren Karteninhalt.
- [x] Wenn ein Kontakt einen Kurz- oder Spitznamen hat, dann bleibt der volle Name die Hauptzeile und der Spitzname erscheint nur als dezenter Zusatz.
- [x] Wenn ein Kontakt Vorlieben, Abneigungen oder Besonderheiten besitzt, dann erscheinen diese in klar getrennten Bereichen statt in einer unklaren gemischten Freitextstruktur.
- [x] Wenn ein Nutzer einen Kontakt erstellt oder bearbeitet, dann zeigt der Dialog getrennte Eingabebereiche fuer Vorlieben, Abneigungen und Besonderheiten.
- [x] Wenn ein Nutzer einen Kontakt erstellt oder bearbeitet, dann kann ein Kurz-/Spitzname als eigener Kontaktwert gespeichert und wieder geladen werden.
- [x] Wenn ein bestehender Kontakt Inhalte aus frueheren Detail- oder Notizfeldern besitzt, dann bleiben diese nach der Umstellung unter `Besonderheiten` sichtbar und bearbeitbar.
- [x] Wenn ein Kontakt keine optionalen Zusatzinformationen hat, dann bleibt die Karte optisch aufgeraeumt und zeigt keine stoerenden Leerbloecke.

## TEST STRATEGY
- Primary Validation Goal: Nachweis, dass das bestehende Adressbuch eine modernisierte, reduzierte Kartenansicht und eine konsistente neue Kontaktstruktur mit Spitzname und Besonderheiten bietet
- Automated Validation: gezielte Backend- und UI-Regressionschecks fuer Laden, Speichern und Wiederanzeigen des neuen Spitznamenfelds sowie fuer die bestehende Kontaktstruktur nach der Umbenennung zu `Besonderheiten`
- Manual Validation: Sichtpruefung von Kartenlayout, Namenshierarchie, optionalen Leerzustaenden und der Uebereinstimmung zwischen Kartenansicht und Kontaktdialog
- Regression Areas: bestehendes Kontakte-CRUD, Kontaktkarten-Rendering im Adressbuch, Kontakt-Erstellen/Bearbeiten-Dialog, bestehende persoenliche Detail-/Notizinhalte in Kontakten

## OUT OF SCOPE

Neue Memory-Sync-Logik, neue Vorschlagslogik oder Aenderungen an Kontaktvorschlagsstatus.

Neue oeffentliche Recherchelogik oder Aenderungen an der Unterscheidung zwischen Privatpersonen und Organisationen.

Kompletter Neuaufbau des Adressbuchs ausserhalb von Kartenstruktur, Dialogstruktur und der benoetigten Spitznamen-Persistenz.

## INTERNAL COMPLEXITY BREAKDOWN

Scope Size: 11
Architectural Risk: 8
State / Persistence Complexity: 14
Cross-System Dependencies: 9
Ambiguity Level: 9
Total Complexity Score: 51
Routing Decision: 5.4
Routing Reasoning: medium
Routing Confidence: HIGH
Dashboard Hint: CAUTION

## SPEC REVIEW METADATA

- **Review Status:** APPROVED_WITH_NOTES
- **Complexity Score:** 51
- **Risk:** MEDIUM
- **Recommended Review Model:** 5.4
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-06-07
- **Review Confidence:** HIGH
- **Review Source:** janus-spec-review

## SPEC IMPLEMENTATION METADATA

- **Implementation Status:** DONE
- **Final Audit:** PASS
- **Completed At:** 2026-06-07
- **Audit Package:** `documentation/test-runs/TASK-SPEC16_audit_package.md`
- **Final Audit Report:** `documentation/test-runs/TASK-SPEC16_final_audit.md`
- **Validation Evidence:**
  - `python -m py_compile backend/data/models.py backend/data/contact_schemas.py backend/data/crud.py backend/data/database.py`
  - `python -m pytest backend/tests/test_contact_manager.py -q`
  - `node --check frontend/js/settings.js`
  - `npx playwright test tests/e2e/generated/TASK-SPEC15-address-book-ui-evidence.spec.js --headed --workers=1 --reporter=list`
