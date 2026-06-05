# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING
target_skill: janus-spec-review
recommended_model: 5.4
recommended_reasoning: medium
new_chat: no
complexity_score: 44
confidence: HIGH
dashboard_hint: CAUTION
reason: DeepDive UX refactor stays on one existing surface but changes information architecture, first-view hierarchy and visible detail depth.

## FEATURE IDENTITY
- Feature Name: DeepDive UX Information Architecture Cleanup
- Feature ID: BACKLOG-103
- Feature Type: UX Refactor / Information Architecture Cleanup
- Primary Goal: Make the existing DeepDive a genuinely clear user-facing cost surface through a two-stage information hierarchy
- Trigger Source: Latest approved decision summary for `BACKLOG-103`

## USER VALUE

Der Nutzer soll das DeepDive in wenigen Sekunden verstehen koennen, statt sich durch zu viele Kostenbloecke, Requests und halb-forensische Details zu arbeiten. Die Oberflaeche startet als ruhige Management-Sicht fuer Kosten, Ersparnis und Treiber und zeigt erst nach bewusster Auswahl reduzierte Details.

Dadurch bleibt die Kostensicht handlungsorientiert: zuerst verstehen, was kostet, was spart und wo es relevante Hinweise gibt, danach nur bei Bedarf in Kostenquellen und einzelne Requests einsteigen.

## TARGET SURFACE
- Primary Target Surface: bestehendes DeepDive-Modal der Kostenansicht
- Entry Point: bestehender DeepDive-Entry aus dem Cost Summary Widget
- Primary User Role: Nutzer mit Interesse an Kostenverstaendnis, Budgetkontext und Optimierung
- Surface Scope: nur die bestehende DeepDive-Oberflaeche inklusive ihrer sichtbaren Hierarchie, Standardzustandslogik und Detailtiefe

## USER ACTION SURFACE
- User Trigger: Nutzer oeffnet das DeepDive aus der Kostenansicht
- User Inputs: bestaetigtes Oeffnen des DeepDive sowie bewusste Auswahl einer Kostenquelle fuer reduzierte Details
- Success Behavior: Das DeepDive startet mit einer dashboard-kompakten Management-Sicht und oeffnet Details erst nach bewusster Navigation nach Kostenquelle
- Failure Behavior: Wenn die Kostensicht teilweise unvollstaendig oder nur eingeschraenkt belastbar ist, bleibt die obere Sicht ruhig und zeigt nur einen kompakten Vertrauenshinweis

## SYSTEM BEHAVIOR

Das bestehende DeepDive bleibt als einzige Nutzeroberflaeche erhalten, wird aber klar zweistufig aufgebaut. Beim Oeffnen sieht der Nutzer nicht sofort Requests, Blocklisten und Detailkarten, sondern zuerst eine kompakte Management-Sicht mit Gesamtkosten, Ersparnis, Budgetkontext sowie den wichtigsten Provider- und Modelltreibern.

Die untere Detail-Ebene ist standardmaessig nicht sichtbar. Sie erscheint erst, wenn der Nutzer bewusst eine Kostenquelle auswaehlt. Die erste Navigation fuehrt dabei nicht direkt auf einzelne Requests, sondern zuerst auf Kostenquellen wie Provider, Modelle oder andere gruppierte Kostenurspruenge. Einzelne Requests bleiben moeglich, aber nur als nachgelagerte Vertiefung.

Die obere Sicht bleibt bewusst ruhig. Hinweise auf eingeschraenkte Belastbarkeit oder laufenden Billing-Abgleich werden in einem einzelnen kompakten Vertrauenshinweis zusammengefasst, statt auf viele einzelne Kennzahlen verteilt zu werden.

Die bisherige untere Detailtiefe darf bewusst reduziert werden. Nicht jede bisher sichtbare Detailflaeche muss erhalten bleiben, wenn sie fuer normale Nutzer wenig Mehrwert hat oder die Oberflaeche wieder wie eine Diagnoseansicht wirken laesst.

## DATA / PERSISTENCE
- Persisted Data: bestehende DeepDive-Kosten-, Provider-, Modell- und Savings-Daten bleiben Quelle der Nutzeroberflaeche
- New Stored Data: Nicht zutreffend: diese Arbeit fuehrt keine neue Datenart ein
- Read Paths: bestehende DeepDive-API und aktuelle DeepDive-Datenbasis
- Write Paths: Nicht zutreffend: Fokus liegt auf Darstellung, Hierarchie und reduzierter sichtbarer Detailtiefe

## CONSTRAINTS

Die Arbeit bleibt auf der bestehenden DeepDive-Oberflaeche. Es entsteht keine neue Diagnoseoberflaeche, keine neue Billing-Surface und keine parallele alternative Kostenansicht.

Die erste sichtbare Ebene muss dashboard-kompakt bleiben. Sie darf keine neue Analyse- oder Berichtsflaeche mit vielen Tabellen, langen Listen oder direkter Request-Dichte werden.

Die reduzierte Detailsicht darf fuer Nutzer keine wichtige Kostenwahrheit verstecken. Die Oberflaeche darf verdichten und vereinfachen, aber keine relevanten Kosten- oder Savings-Zusammenhaenge verschweigen.

## SECURITY / PRIVACY
- User Data Exposure: DeepDive zeigt weiterhin keine technischen Debug-/Tracking-Rohdetails als primaere Nutzerinformation
- Sensitive Fields: keine Prompts, keine Responses, keine Rohdiagnose, keine Request-nahe Debugdaten als Standardinhalt
- External Services: Nicht zutreffend: diese UX-Arbeit fuehrt keine neue externe Abhaengigkeit ein
- Audit Requirement: Nutzerorientierte Darstellung muss getrennt bleiben von Entwicklerdiagnose und Debuglog-Inhalten

## EDGE CASES

Wenn fuer den Zeitraum keine Kosten vorhanden sind, zeigt das DeepDive einen klaren leeren Management-Zustand statt leerer Detailspalten oder toter Listenbereiche.

Wenn nur teilweise belastbare Daten vorliegen, bleibt die obere Sicht kompakt und zeigt nur einen einzelnen Vertrauenshinweis statt mehrfacher Warnmarker in vielen Kacheln.

Wenn der Nutzer keine Kostenquelle auswaehlt, bleibt die Detail-Ebene geschlossen oder leer statt sofort eine vorausgewaehlte Request-Diagnose zu erzwingen.

Wenn Details reduziert wurden, muss der Nutzer trotzdem noch sinnvoll nachvollziehen koennen, woher relevante Kosten stammen, ohne in eine Entwicklerforensik gedrueckt zu werden.

## DEFINITION OF DONE
- [ ] Wenn das DeepDive geoeffnet wird, dann startet es mit einer dashboard-kompakten Management-Sicht statt mit sofort sichtbarer Request- und Detaildichte.
- [ ] Wenn der Nutzer das DeepDive zum ersten Mal sieht, dann stehen Kosten, Ersparnis, Budgetkontext und wichtigste Treiber sichtbar ueber den Detailinformationen.
- [ ] Wenn Kosten nur teilweise belastbar sind, dann erscheint in der oberen Sicht genau ein kompakter Vertrauenshinweis statt vieler verteilter Warnsignale.
- [ ] Wenn der Nutzer keine Kostenquelle aktiv auswaehlt, dann bleibt die Detail-Ebene geschlossen oder in einem klaren leeren Zustand.
- [ ] Wenn der Nutzer Details oeffnet, dann fuehrt die erste Navigation ueber Kostenquellen und nicht direkt in einzelne Requests.
- [ ] Wenn bisher sichtbare Detailflaechen fuer normale Nutzer keinen klaren Mehrwert haben, dann duerfen sie reduziert oder verdichtet werden, ohne die Kostenwahrheit zu verfremden.

## TEST STRATEGY
- Primary Validation Goal: Nachweis, dass DeepDive als ruhige zweistufige Nutzeroberflaeche funktioniert und nicht mehr wie eine Diagnose- oder Logging-Flaeche startet
- Automated Validation: bestehende UI-Smokes und gezielte Frontend-Regressionschecks fuer oberen Startzustand, sichtbare Management-Sicht, kompakten Vertrauenshinweis und reduzierte Detailaktivierung
- Manual Validation: Sichtpruefung des DeepDive auf Lesbarkeit, Hierarchie, Standardzustand und wahrgenommene Ruhe beim ersten Oeffnen
- Regression Areas: `frontend/js/cost-visualizer.js`, bestehender DeepDive-Renderflow, sichtbare Gruppen-/Request-Standardzustandslogik, UI-Smoke-Evidenz

## OUT OF SCOPE

Neue eigenstaendige Diagnoseoberflaeche fuer Entwickler.

Neue Billing- oder Reporting-Surface ausserhalb des bestehenden DeepDive.

Neue Persistenz- oder Tracking-Mechanik.

Vollstaendige Beibehaltung aller bisherigen sichtbaren Detailbloecke nur aus Rueckwaertskompatibilitaetsgruenden.

## INTERNAL COMPLEXITY BREAKDOWN

Scope Size: 10
Architectural Risk: 8
State / Persistence Complexity: 4
Cross-System Dependencies: 10
Ambiguity Level: 12
Total Complexity Score: 44
Routing Decision: 5.4
Routing Reasoning: medium
Routing Confidence: HIGH
Dashboard Hint: CAUTION

## SPEC REVIEW METADATA

- **Review Status:** APPROVED_WITH_NOTES
- **Complexity Score:** 44
- **Risk:** MEDIUM
- **Recommended Review Model:** 5.4
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-06-05
- **Review Confidence:** HIGH
- **Review Source:** janus-spec-review
