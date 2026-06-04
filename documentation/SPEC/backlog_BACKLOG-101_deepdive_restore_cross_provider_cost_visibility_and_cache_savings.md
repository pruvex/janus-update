# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING
target_skill: janus-spec-review
recommended_model: 5.4
recommended_reasoning: high
new_chat: no
complexity_score: 68
confidence: HIGH
dashboard_hint: CAUTION
reason: Cross-provider DeepDive regression needs bounded product re-integration of GPT, per-model and cache-savings visibility with Spec-14 Gemini forensics.

## FEATURE IDENTITY
- Feature Name: DeepDive Restore Cross-Provider Cost Visibility And Cache Savings
- Feature ID: BACKLOG-101
- Feature Type: Regression Repair / Cost Transparency Improvement
- Primary Goal: Restore the previous DeepDive visibility for GPT/OpenAI, per-model cost breakdown and cache savings without losing the new Gemini forensics from Spec 14
- Trigger Source: Backlog Item `BACKLOG-101`

## USER VALUE

Der Nutzer bekommt wieder eine zusammenhaengende Kostenwahrheit im DeepDive statt einer zu stark Gemini-zentrierten Sicht. Verbrauch fuer GPT/OpenAI und Gemini, Kosten pro Modell und durch Caching eingesparte Tokens/Kosten werden wieder in derselben Diagnoseoberflaeche sichtbar, damit interne DeepDive-Summen und externe Rechnungen nachvollziehbarer bleiben.

## TARGET SURFACE
- Primary Target Surface: Bestehendes DeepDive / bestehende Kostenansicht
- Entry Point: `#cost-summary-widget` und bestehendes Kosten-DeepDive-Modal
- Primary User Role: Nutzer mit aktivem Kostenmonitoring und Billing-Fokus
- Surface Scope: Frontend-DeepDive plus zugehoerige Kostenaggregation, soweit fuer Cross-Provider- und Cache-Sicht noetig

## USER ACTION SURFACE
- User Trigger: Nutzer oeffnet das bestehende DeepDive zur Analyse von Kosten, Modellen, Einsparungen oder Billing-Abweichungen
- User Inputs: Auswahl im bestehenden DeepDive, Drilldown in Provider-, Modell-, Gruppen- und Request-Sichten, Budgetanzeige
- Success Behavior: Nutzer sieht Gemini und GPT/OpenAI in derselben Kostenansicht, erkennt Kosten pro Modell und sieht wieder, wie viel durch Caching eingespart wurde
- Failure Behavior: Wenn einzelne Metriken nicht belastbar berechnet werden koennen, zeigt DeepDive die Luecke sichtbar an statt die betreffende Sicht still zu entfernen

## SYSTEM BEHAVIOR

DeepDive bleibt auf der bestehenden Oberflaeche und behaelt den Spec-14-Forensikfluss fuer Gemini bei, erweitert die Ansicht aber wieder zu einer provideruebergreifenden Kostenoberflaeche. Die Oberflaeche darf nicht nur Gemini-Anomalien priorisieren, sondern muss weiterhin den gesamten fuer den Nutzer relevanten Kostenkontext zeigen.

Provideruebergreifend muessen mindestens Gemini und GPT/OpenAI sichtbar sein. Der Nutzer muss den Verbrauch pro Provider und pro Modell erkennen koennen, ohne die Gemini-Forensik zu verlieren. Die neue Gemini-Sicht auf Attributionsstatus, Komponenten-Split, Restposten und Abweichungen bleibt erhalten, wird aber in eine groessere Kostenuebersicht eingebettet.

Cache- und Savings-Werte muessen im DeepDive wieder sichtbar sein, wenn sie zuvor fuer den Nutzer Teil der Kosteninterpretation waren. DeepDive soll fuer jede dargestellte Kostenebene klar machen, ob der Betrag brutto, netto oder durch Einsparung beeinflusst ist. Wenn Savings oder Modellwerte fuer einen Abschnitt nicht vorliegen, darf die Oberflaeche das nicht simulieren, sondern zeigt den fehlenden Zustand explizit.

Bestehende Gemini-Drilldowns bleiben moeglich, aber die Default-Wahrnehmung des DeepDive darf nicht den Eindruck erzeugen, dass GPT/OpenAI oder Cache-Einsparungen aus dem Kostenbild verschwunden sind. Die Gesamtansicht soll vielmehr erklaeren, wie sich die sichtbaren Kosten ueber Provider, Modelle, Komponenten und Savings zusammensetzen.

## DATA / PERSISTENCE
- Persisted Data: Bestehende Kosten- und Attributionsdaten, inklusive provider, model, token usage, cost entries und Cache-/Savings-nahe Dashboard-Daten
- New Stored Data: Nicht zwingend neue Persistenz; nur soweit noetig, um die frueher sichtbaren DeepDive-Metriken wieder korrekt aggregieren zu koennen
- Read Paths: DeepDive-API, Dashboard-Kosten-API und bestehende Kosten-/Attributionsaggregation
- Write Paths: Nur falls bestehende Kostenaggregation ergaenzt werden muss, um Cross-Provider-, Modell- oder Savings-Sichten belastbar zu liefern

## CONSTRAINTS

Die bestehende DeepDive-Oberflaeche bleibt die einzige Zieloberflaeche. Es darf keine neue parallele Billing- oder Dashboard-Anwendung entstehen. Spec 14 fuer Gemini-Kostenforensik bleibt bindend und darf nicht zurueckgebaut werden.

Die Wiederherstellung der frueheren GPT/OpenAI-, Modell- und Savings-Sicht darf keine weichgezeichnete Kostenlogik einbauen. Wenn Daten fuer eine Sicht nicht vorhanden oder nur teilweise belastbar sind, muss der Nutzer den eingeschraenkten Wahrheitsgrad erkennen koennen.

Diese Arbeit ist kein kompletter Websearch- oder Billing-Neuentwurf. Sie fokussiert auf DeepDive-Transparenz und die richtige Integration bereits vorhandener bzw. erwarteter Kosteninformationen.

## SECURITY / PRIVACY
- User Data Exposure: DeepDive darf weiterhin keine sensiblen Prompt-/Response-Inhalte oder versteckte Nutzerdaten offenlegen
- Sensitive Fields: Promptfragmente, Responsefragmente, verschachtelte Attributionsmetadaten, interne Schluessel oder Secrets bleiben ausgeblendet
- Provider Scope: Mindestens Gemini und GPT/OpenAI muessen dargestellt werden, ohne providerinterne Details zu leaken, die nicht fuer Kostenwahrheit noetig sind
- Audit Requirement: Cost- und Savings-Anzeigen muessen fuer den Nutzer nachvollziehbar sein, ohne ungesicherte oder private Rohdaten direkt sichtbar zu machen

## EDGE CASES

Wenn fuer GPT/OpenAI oder Gemini Kosten vorliegen, aber keine brauchbare Modellzuordnung, zeigt DeepDive die Luecke sichtbar statt die Werte still einer falschen Modellgruppe zuzuordnen.

Wenn Cache-/Savings-Werte nur fuer Teile des Zeitraums oder nur fuer einzelne Provider vorliegen, zeigt DeepDive die Einsparung nur dort, wo sie belastbar ist, und kennzeichnet fehlende Bereiche.

Wenn Gemini-Forensik Restposten oder Abweichungen meldet, darf die wiederhergestellte Gesamtansicht diese Signale nicht ueberdecken oder glattziehen.

Wenn externe Rechnungen und interne DeepDive-Summen weiterhin differieren, soll die kombinierte Ansicht eher mehr Erklaerbarkeit liefern als weniger, insbesondere durch Provider-, Modell- und Savings-Kontext.

## DEFINITION OF DONE
- [ ] Wenn DeepDive geoeffnet wird, dann sind mindestens Gemini und GPT/OpenAI wieder in einer zusammenhaengenden Kostenansicht sichtbar.
- [ ] Wenn Kosten fuer mehrere Modelle vorliegen, dann kann der Nutzer den Verbrauch pro Modell im DeepDive nachvollziehen.
- [ ] Wenn Cache-/Savings-Werte fuer den Zeitraum oder die dargestellte Gruppe vorliegen, dann zeigt DeepDive diese Einsparung wieder sichtbar an.
- [ ] Wenn Gemini-Attributionsstatus, Komponenten-Split oder Restposten vorliegen, dann bleiben diese Informationen in der neuen Gesamtansicht sichtbar.
- [ ] Wenn eine Kosten-, Modell- oder Savings-Sicht fuer einen Bereich nicht belastbar ist, dann zeigt DeepDive dies explizit statt die Information still zu verbergen.

## TEST STRATEGY
- Primary Validation Goal: Nachweis, dass DeepDive wieder provideruebergreifende Kosten, Modellsicht und Cache-Savings zeigt, ohne die Gemini-Forensik aus Spec 14 zu verlieren
- Automated Validation: Fokus auf Aggregations-/API-Regressionen fuer Cross-Provider- und Savings-Daten sowie Frontend-Render-Checks der wiederhergestellten DeepDive-Sicht
- Manual Validation: Sichtpruefung des DeepDive fuer Gemini und GPT/OpenAI, Modellaufschluesselung, Savings-Sicht und Weiterbestehen der Gemini-Anomalie-/Residual-Darstellung
- Regression Areas: `cost-visualizer.js`, DeepDive-API/Antwortstruktur, Kostenaggregation, Modellgruppierung, Cache-/Savings-Anzeige

## OUT OF SCOPE

Kompletter Neuaufbau der Websearch-Qualitaet.

Neue allgemeine Billing-Plattform ausserhalb des bestehenden DeepDive.

Provideruebergreifende Rechnungsimporte oder vollstaendige externe Billing-Synchronisation als separates Produktmodul.

## INTERNAL COMPLEXITY BREAKDOWN

Scope Size: 14
Architectural Risk: 14
State / Persistence Complexity: 12
Cross-System Dependencies: 16
Ambiguity Level: 12
Total Complexity Score: 68
Routing Decision: 5.4
Routing Reasoning: high
Routing Confidence: HIGH
Dashboard Hint: CAUTION

## SPEC REVIEW METADATA

- **Review Status:** APPROVED_WITH_NOTES
- **Complexity Score:** 68
- **Risk:** HIGH
- **Recommended Review Model:** 5.4
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-06-04
- **Review Confidence:** HIGH
- **Review Source:** janus-spec-review
