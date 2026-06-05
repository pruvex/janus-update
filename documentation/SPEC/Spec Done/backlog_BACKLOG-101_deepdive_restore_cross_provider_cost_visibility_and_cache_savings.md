# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING
target_skill: janus-spec-review
recommended_model: 5.4
recommended_reasoning: high
new_chat: no
complexity_score: 56
confidence: HIGH
dashboard_hint: CAUTION
reason: DeepDive UX refocus plus debug-log boundary changes cost surfaces, persistence expectations and privacy handling without requiring 5.5 escalation.

## FEATURE IDENTITY
- Feature Name: Clean Cost DeepDive And Cost Tracking Debug Log
- Feature ID: BACKLOG-101
- Feature Type: UX Refocus / Cost Transparency Improvement
- Primary Goal: Make DeepDive a clear user-facing cost understanding surface while moving tracking forensics into a separate developer debug log
- Trigger Source: Latest approved decision summary for `BACKLOG-101`

## USER VALUE

Der Nutzer bekommt eine aufgeraeumte Kostenansicht statt einer forensischen Diagnoseflaeche. DeepDive erklaert wieder, was Kosten verursacht hat, welche Provider und Modelle beteiligt waren, welche Einsparungen durch Caching sichtbar sind und wo sich Optimierung lohnt, ohne den Nutzer mit technischen Trackingdetails zu ueberladen.

Wenn einzelne Kostenanteile nicht vollstaendig belastbar zugeordnet werden koennen, bleibt die Nutzerwahrheit erhalten: DeepDive zeigt einen kompakten, verstaendlichen Hinweis, waehrend die eigentliche Ursachenanalyse in einem separaten Debuglog fuer Entwicklung und Audit landet.

## TARGET SURFACE
- Primary Target Surface: Bestehendes DeepDive / bestehende Kostenansicht
- Entry Point: `#cost-summary-widget` und bestehendes Kosten-DeepDive-Modal
- Primary User Role: Nutzer mit aktivem Kostenmonitoring und Optimierungsinteresse
- Surface Scope: DeepDive-Frontend, DeepDive-Datenaufbereitung und ein separater Dev-Debuglog-Pfad fuer Cost-Tracking-Diagnose

## USER ACTION SURFACE
- User Trigger: Nutzer oeffnet DeepDive, um Kosten, Modelle, Cache-Ersparnis und Optimierungshinweise zu verstehen
- User Inputs: Zeitraum, vorhandene DeepDive-Drilldowns und bestehende Auswahlinteraktionen der Kostenansicht
- Success Behavior: Nutzer sieht eine zusammenhaengende, leicht lesbare Kostenansicht mit Provider-, Modell- und Savings-Kontext statt technischer Forensik
- Failure Behavior: Wenn Kosten- oder Savings-Wahrheit nur teilweise belastbar ist, zeigt DeepDive einen knappen nutzerrelevanten Hinweis statt technische Rohdiagnose

## SYSTEM BEHAVIOR

DeepDive bleibt die bestehende Kostenoberflaeche, wird aber in ihrer Prioritaet neu ausgerichtet: zuerst Nutzerverstaendnis und Kostenoptimierung, nicht technische Tracking-Forensik. Die Standardwahrnehmung der Oberflaeche muss zeigen, wie sich sichtbare Kosten ueber mindestens Gemini und GPT/OpenAI sowie ueber Modelle und Cache-Ersparnis zusammensetzen.

Technische Trackingdiagnose, Attributionsrohzustand, interne Komponentenaufschluesselung, Restpostenursachen, Request-nahe Forensik und andere Entwicklerdetails erscheinen nicht mehr als primaere DeepDive-Inhalte. Diese Informationen werden in ein separates strukturiertes Dev-Debuglog geschrieben, damit Trackingqualitaet weiterhin analysierbar bleibt, ohne die Nutzeroberflaeche zu ueberfrachten.

DeepDive darf nutzerrelevante Wahrheitsgrenzen weiter sichtbar machen, aber nur in verdichteter Form. Wenn ein kleiner Kostenanteil nicht eindeutig zugeordnet werden kann oder eine Teilansicht nur eingeschraenkt belastbar ist, bekommt der Nutzer einen klaren, knappen Hinweis. Die Oberflaeche darf daraus keinen forensischen Untersuchungsfluss machen.

## DATA / PERSISTENCE
- Persisted Data: Bestehende Kosten-, Provider-, Modell- und Savings-Daten bleiben Quelle fuer DeepDive
- New Stored Data: Strukturierte Cost-Tracking-Debugereignisse im Dev-Modus unter `documentation/logs/cost-tracking-debug.jsonl`
- Read Paths: DeepDive-API, bestehende Kostenaggregation und vorhandene Savings-/Provider-Ansichten
- Write Paths: Cost-Tracking-Debuglog im Entwicklungsmodus sowie bestehende Kostenpersistenzpfade, soweit fuer belastbare Nutzeranzeige notwendig

## CONSTRAINTS

DeepDive bleibt die einzige Nutzeroberflaeche fuer diese Arbeit. Der erste Scope fuehrt keine neue Developer-UI, keine parallele Billing-Anwendung und keine Produktpfadlogik fuer Installer oder App-Data ein.

Die Trennung zwischen Nutzeransicht und Debugdiagnose ist verbindlich. Was fuer DeepDive technisch interessant, aber fuer den Nutzer nicht handlungsrelevant ist, gehoert nicht in die Standardoberflaeche.

Die bestehende Kostenwahrheit darf nicht weichgezeichnet werden. Nutzerfreundlichkeit bedeutet Verdichtung, nicht Verschweigen. Wenn Daten fuer einen sichtbaren Abschnitt nicht voll belastbar sind, muss DeepDive dies knapp und ehrlich markieren.

## SECURITY / PRIVACY
- User Data Exposure: DeepDive und Debuglog duerfen keine sensiblen Prompt-, Antwort- oder Nutzinhalte offenlegen
- Sensitive Fields: Keine Prompts, keine Responses, keine Rohinhalte; nur technische Metadaten, Provider-/Modellbezug, Kostenwerte, Attributionstatus, Eventtypen und IDs oder Hashes
- Provider Scope: Mindestens Gemini und GPT/OpenAI muessen in der Nutzeransicht erscheinen, ohne providerinterne Diagnosefelder offenzulegen
- Audit Requirement: Trackingqualitaet muss ueber das Debuglog analysierbar bleiben, waehrend DeepDive fuer Nutzer datensparsam und verstaendlich bleibt

## EDGE CASES

Wenn fuer einen Zeitraum Providerkosten sichtbar sind, aber die Modellzuordnung teilweise fehlt, zeigt DeepDive die Modellluecke knapp an statt Werte falsch zu gruppieren oder die Sicht still zu entfernen.

Wenn Cache- oder Savings-Werte nur fuer Teile des Zeitraums oder einzelne Provider belastbar vorliegen, zeigt DeepDive die Einsparung nur dort, wo sie wahr ist, und markiert fehlende Bereiche verstaendlich.

Wenn ein kleiner Kostenanteil nicht eindeutig attribuiert werden kann, zeigt DeepDive nur einen nutzerrelevanten Hinweis, waehrend die Detailursache ausschliesslich im Debuglog landet.

Wenn im Dev-Modus kein Debuglog geschrieben werden kann, darf dies die normale Nutzeransicht nicht in eine technische Fehleroberflaeche verwandeln.

## DEFINITION OF DONE
- [ ] Wenn DeepDive geoeffnet wird, dann zeigt es mindestens Gemini und GPT/OpenAI wieder in einer zusammenhaengenden, nutzerorientierten Kostenansicht.
- [ ] Wenn Kosten fuer mehrere Modelle vorliegen, dann kann der Nutzer den Verbrauch pro Modell im DeepDive nachvollziehen.
- [ ] Wenn Cache- oder Savings-Werte fuer den Zeitraum oder die dargestellte Gruppe vorliegen, dann zeigt DeepDive diese Einsparung sichtbar an.
- [ ] Wenn technische Trackingdiagnose fuer Cost-Attribution entsteht, dann erscheint sie nicht als primaerer DeepDive-Inhalt, sondern im separaten Dev-Debuglog.
- [ ] Wenn ein Kostenanteil fuer den Nutzer nicht voll belastbar ist, dann zeigt DeepDive einen knappen nutzerrelevanten Hinweis statt Roh-Forensik.
- [ ] Wenn Cost-Tracking-Debugdaten geschrieben werden, dann enthalten sie keine Prompt-, Antwort- oder Nutzinhalte.

## TEST STRATEGY
- Primary Validation Goal: Nachweis, dass DeepDive wieder als klare Nutzeransicht fuer Kostenverstaendnis und Optimierung funktioniert und technische Trackingdiagnose im Dev-Debuglog getrennt bleibt
- Automated Validation: API- und Aggregationschecks fuer Provider-, Modell- und Savings-Daten sowie Validierung, dass Debugereignisse im Dev-Modus strukturiert und ohne Nutzinhalte geschrieben werden
- Manual Validation: Sichtpruefung des DeepDive auf Lesbarkeit, Priorisierung und reduzierte Komplexitaet sowie Stichprobe des Debuglogs auf Trennschaerfe und Privacy-Grenze
- Regression Areas: `frontend/js/cost-visualizer.js`, DeepDive-API/Antwortstruktur, Kostenaggregation, Savings-Anzeige, Cost-Tracking-Logging

## OUT OF SCOPE

Neue Developer-Debugansicht innerhalb der Janus-Oberflaeche.

Produktions- oder Installer-spezifische Logpfadlogik ausserhalb des Dev-Modus.

Vollstaendige Billing-Plattform, externer Rechnungsimport oder allgemeiner Provider-Audit ausserhalb des DeepDive- und Cost-Tracking-Kontexts.

Speicherung oder Anzeige von Prompt-, Antwort- oder anderen Nutzinhalten fuer Cost-Diagnosezwecke.

## INTERNAL COMPLEXITY BREAKDOWN

Scope Size: 12
Architectural Risk: 11
State / Persistence Complexity: 10
Cross-System Dependencies: 14
Ambiguity Level: 9
Total Complexity Score: 56
Routing Decision: 5.4
Routing Reasoning: high
Routing Confidence: HIGH
Dashboard Hint: CAUTION

## SPEC REVIEW METADATA

- **Review Status:** APPROVED_WITH_NOTES
- **Complexity Score:** 56
- **Risk:** MEDIUM
- **Recommended Review Model:** 5.4
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-06-04
- **Review Confidence:** HIGH
- **Review Source:** janus-spec-review

## SPEC IMPLEMENTATION METADATA

- **Implementation Status:** DONE
- **Final Audit:** PASS
- **Completed At:** 2026-06-05
- **Implementation Track:** TASK-BACKLOG-101-R2.1 through TASK-BACKLOG-101-R2.4
- **Validation Evidence:**
  - `python -m py_compile backend/data/crud.py backend/api/routers/system.py`
  - `python -m py_compile backend/services/orchestrator/execution_engine.py backend/llm_providers/gemini/gateway.py backend/services/cost_service.py`
  - `node --check frontend/js/cost-visualizer.js`
  - `python -m pytest backend/tests/test_cost_token_tracking_completeness.py -q`
  - `npx playwright test tests/e2e/generated/BACKLOG-101-ui-smoke.spec.js --headed --workers=1 --reporter=list`
- **Final Audit Evidence:** `documentation/test-runs/BACKLOG-101-R2_final_audit.md`
