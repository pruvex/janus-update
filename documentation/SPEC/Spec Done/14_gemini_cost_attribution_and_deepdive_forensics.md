# JANUS FEATURE SPEC – DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING

target_skill: SPEC_REVIEW
execution_mode: GPT_5_5
complexity_score: 79
confidence: HIGH
dashboard_hint: CAUTION
reason: Gemini cost attribution, retroactive billing forensics, routing constraints, and DeepDive truthfulness require audit-grade spec review.

## FEATURE IDENTITY

- Feature Name: Gemini Cost Attribution and DeepDive Forensics
- Source Input: Locked LATEST DECISION SUMMARY from Janus feature design
- Primary Goal: Make every external Gemini cost visible, attributable, and explainable inside DeepDive
- User Problem: External Gemini billing is materially higher than Janus internal cost visibility, especially after heavy grounding and websearch test activity
- User Value: The user can trace expensive Gemini usage by anomaly, month, test run, session, and request while identifying safe cost-reduction opportunities without blind quality loss

## USER VALUE

Der Nutzer bekommt eine belastbare Kostenwahrheit statt einer nur teilweise rekonstruierten Sicht. DeepDive wird zur primären Diagnoseoberfläche für externe Gemini-Kosten, inklusive Abweichungen zwischen interner Attribution und externer Billing-Wahrheit.

Zusätzlich soll das Produkt nicht nur Kosten zeigen, sondern Ursachen und vermeidbare Kostentreiber sichtbar machen. Besonders teurer Pro-Verbrauch aus intensiven Grounding- und Websearch-Phasen soll nachvollziehbar und bewertbar werden.

## TARGET SURFACE

- Primary Target Surface: Bestehendes DeepDive / bestehende Kostenansicht
- Existing or New Surface: Existing Surface
- Existence Confirmation: confirmed by user
- User Trigger: Nutzer öffnet DeepDive zur Analyse von Kosten, Billing-Abweichungen oder auffälligem Gemini-Verbrauch
- Success Behavior: DeepDive startet mit einer Auffälligkeitsübersicht und erlaubt Drilldown in Monats-, Testlauf-/Session- und Einzelrequest-Sichten
- Failure Behavior: Wenn Attribution unvollständig ist, zeigt DeepDive die Lücke sichtbar an statt Kosten still zu verlieren
- Explicit Non-Surfaces: Keine neue separate Billing- oder Audit-Ansicht

## USER ACTION SURFACE

- Action Type: Analyse und Drilldown
- Trigger: Öffnen der bestehenden DeepDive-/Kostenansicht
- User Input: Auswahl von Anomalien, Monat, Testlauf, Session oder Einzelrequest
- Immediate Feedback: Auffälligkeiten, Abweichungen, nicht eindeutig attribuierte Kosten und Pro-Kostentreiber werden sofort sichtbar
- Result: Nutzer versteht Ursache, Umfang und potenzielle Einsparhebel einzelner Kostenblöcke
- Cancel / Undo Behavior: Nicht zutreffend, da reine Analyseoberfläche
- Non-Effects: Keine automatische Budget-Sperre und keine neue Pflichtbestätigung für normale Nutzung

## SYSTEM BEHAVIOR

DeepDive zeigt zuerst eine Auffälligkeitsübersicht. Diese priorisiert teure Pro-Blöcke, erkennbare Abweichungen zwischen interner und externer Kostensicht, kritische Attributionslücken und mögliche Einsparpotenziale.

Die reguläre Kostenanalyse ist nach Monat verfügbar, gruppiert primär nach Testlauf oder Session. Von dort aus kann der Nutzer bis auf Einzelrequests herunterbrechen. Versteckte oder indirekte Kosten wie Grounding- oder Websearch-Anteile erscheinen nicht als unsichtbare Nebenwirkung, sondern als gemeinsamer Request-Eintrag mit klarer Komponentenaufschlüsselung.

Jeder externe Gemini-Provider-Call muss in einer persistenten Kosten-/Attributionsspur landen und dadurch grundsätzlich DeepDive-fähig sein. Die Attributionsspur darf provider-neutral modelliert werden, aber dieser Scope verpflichtet nur Gemini, Gemini Grounding und Gemini Websearch. Wenn interne Attribution und externe Billing-Wahrheit nicht exakt übereinstimmen, zeigt DeepDive eine sichtbare Abweichungswarnung mit den Zuständen `intern attribuiert`, `nicht eindeutig attribuiert` und `externe Billing-Summe`.

Auffälliger vermeidbarer Pro-Verbrauch wird aktiv markiert und mit kompaktem Ursachenkontext erklärt. Die Darstellung soll ausdrücklich helfen, Kosten zu senken, ohne pauschal Qualität oder notwendige Sonderfälle zu beschneiden.

Für Gemini Grounding und Websearch gilt produktseitig Flash als Standard. Pro ist dort nicht als stille interne Qualitätseskalation erlaubt, sondern nur bei expliziter Nutzerwahl oder klar sichtbarem manuellem Override.

## DATA / PERSISTENCE

- Persistence Required: YES
- Data Created: Persistente Kosten-/Attributionsbelege pro externem Gemini-Provider-Call
- Data Updated: DeepDive-Aggregationen, Session-/Testlauf-Zuordnungen und Abweichungszustände können nachträglich ergänzt oder präzisiert werden
- Data Deleted: Nicht Teil dieses Scopes
- Source of Truth: Persistente interne Kosten-/Attributionsbelege plus externe Billing-Wahrheit als Vergleichsreferenz
- Historical Behavior: Mai 2026 soll rückwirkend so weit wie möglich forensisch zerlegt werden; nicht sauber zuordenbare Kosten bleiben als sichtbarer Restposten bestehen
- Storage Boundary: Standardmäßig nur Metadaten und kompakter Ursachenkontext, keine vollständigen Prompt-/Antworttexte

## CONSTRAINTS

Der erste Scope enthält keinen harten monatlichen Budget-Kill-Switch.

DeepDive darf unklare oder fehlende Attribution nicht beschönigen. Sichtbare Restposten und Abweichungswarnungen sind verpflichtend, wenn keine vollständige Rückführung möglich ist.

Die Lösung muss Kostenreduktion sichtbar machen, ohne Grounding- oder Websearch-Qualität pauschal herabzusetzen. Vermeidbarer Pro-Verbrauch soll erkennbar sein, aber echte manuelle Overrides oder bewusst gewählte Qualitätspfade dürfen nicht fälschlich als Fehler erscheinen.

Die Produktregel für Gemini Grounding/Websearch ist kostenklar: Flash als Standard, kein stilles internes Auto-Eskalieren auf Pro.

OpenAI und andere Provider bleiben im ersten Scope unverändert, außer dass bestehende Kostenanzeigen und bestehendes Provider-Verhalten nicht regressieren dürfen.

## SECURITY / PRIVACY

- Sensitive Data Involved: YES, weil Kostenbelege Rückschlüsse auf externe Nutzungsereignisse enthalten können
- External Services Involved: YES, Gemini als externer LLM-Provider und externe Billing-Referenzen
- Secrets Required: NO in der DeepDive-Anzeige selbst
- Privacy Impact: Kostenbelege müssen Ursachenanalyse ermöglichen, dürfen aber standardmäßig keine vollständigen Prompt-/Antworttexte speichern
- Security Constraints: Sichtbare Kosten- und Ursachentransparenz ohne unnötige Offenlegung sensitiver Nutzdaten
- Logging Boundary: Persistente Belege speichern nur Metadaten, Modell-, Zeit-, Kosten-, Gruppierungs- und kompakten Ursachenkontext

## EDGE CASES

- Externer Gemini-Call war erfolgreich, aber der persistente Kostenbeleg konnte nicht sauber geschrieben werden; DeepDive muss dies sofort als kritische Lücke markieren
- Rückwirkende Alt-Kosten lassen sich nur teilweise rekonstruieren; der verbleibende Anteil bleibt als `nicht eindeutig attribuiert` sichtbar
- Interne Attribution stimmt nicht exakt mit externer Billing-Wahrheit überein; DeepDive zeigt die Differenz offen an
- Ein Testlauf enthält viele Requests mit hohem Flash-Volumen und relativ kleinem, aber teurem Pro-Anteil; die Analyse muss beides getrennt sichtbar machen
- Manuell gewählter Pro-Einsatz darf nicht mit stiller Auto-Eskalation verwechselt werden
- Versteckte oder indirekte Grounding-Kosten dürfen nicht außerhalb des gemeinsamen Request-Kontexts verloren gehen

## DEFINITION OF DONE

- [ ] Wenn ein externer Gemini-Provider-Call stattfindet, dann erscheint dafür ein persistenter Kosten-/Attributionsbeleg in der DeepDive-Grundlage.
- [ ] Wenn DeepDive geöffnet wird, dann sieht der Nutzer zuerst eine Auffälligkeitsübersicht mit teuren Pro-Blöcken, Abweichungen und Attributionslücken.
- [ ] Wenn der Nutzer einen Kostenblock untersucht, dann kann er von Monat zu Testlauf/Session und weiter bis zum Einzelrequest drillen.
- [ ] Wenn Gemini Grounding- oder Websearch-Kosten vorliegen, dann erscheinen deren Anteile im gemeinsamen Request-Kontext mit klarer Komponentenaufschlüsselung.
- [ ] Wenn interne Summen und externe Billing-Wahrheit auseinanderlaufen, dann zeigt DeepDive eine sichtbare Abweichungswarnung mit intern attribuiertem, nicht eindeutig attribuiertem und externem Gesamtwert.
- [ ] Wenn historische Mai-2026-Kosten nicht vollständig zuordenbar sind, dann zeigt DeepDive den verbleibenden Rest sichtbar als `nicht eindeutig attribuiert`.
- [ ] Wenn Pro-Verbrauch wahrscheinlich vermeidbar war, dann markiert DeepDive diesen Verbrauch aktiv und zeigt einen kompakten Einsparhinweis.
- [ ] Wenn für Gemini Grounding/Websearch kein expliziter Nutzerwunsch oder manueller Override vorliegt, dann wird Pro nicht als stiller Standardpfad verwendet.

## TEST STRATEGY

- Primary Validation Goal: Nachweis, dass jeder externe Gemini-Verbrauch in DeepDive landet und Ursachenanalyse bis zur richtigen Gruppierungsebene möglich ist
- Historical Validation Target: Mai-2026-Billing als Referenzfall für Rückanalyse, Restposten und Abweichungswarnung
- Automated Validation Candidates: Persistenz pro externem Gemini-Call, Aggregation nach Monat/Testlauf/Session, Abweichungswarnung, Anomalie-Markierung, Flash-Standardregel
- Manual Validation: DeepDive-Anomaliefluss, Drilldown-Lesbarkeit, Verständlichkeit von Restposten und Einsparhinweisen
- Regression Areas: Kostenberechnung, Provider-Routing, Grounding-/Websearch-Darstellung, historische Kostenansichten, DeepDive-Performance
- Failure Case Validation: Belegpersistenz schlägt fehl, externe Billing-Daten weichen ab, historische Zuordnung bleibt unvollständig, Pro wird ohne sichtbaren Override genutzt

## OUT OF SCOPE

- Harter monatlicher Budget-Kill-Switch
- Neue separate Billing-/Audit-Oberfläche
- Vollständige Prompt-/Antworttext-Speicherung in Standard-Kostenbelegen
- Stille automatische Qualitätseskalation von Gemini Grounding/Websearch auf Pro
- Beliebige allgemeine Kostenoptimierung außerhalb des Gemini-Attributions- und DeepDive-Kontexts
- Janus-weite Instrumentierung aller externen Provider-Calls
- Änderungen am bestehenden OpenAI-Kosten- oder Routing-Verhalten außerhalb von Regression-Schutz

## INTERNAL COMPLEXITY BREAKDOWN

Scope Size: 17 – neue Kostenwahrheit, Anomalieeinstieg, historische Analyse und Drilldown-Verhalten
Architectural Risk: 17 – Routing-Regeln, externe Billing-Referenz und systemweite Attribution greifen ineinander
State / Persistence Complexity: 18 – persistente Belege pro externem Gemini-Call plus rückwirkende Gruppierung und Restpostenlogik
Cross-System Dependencies: 16 – DeepDive, Kostenservices, Gemini-Providerpfade, Testlauf-/Session-Bezug und Billing-Abgleich
Ambiguity Level: 7 – Provider-Scope ist auf Gemini begrenzt, Ursache/Einsparlogik braucht weiterhin präzise Produktauslegung
Total Complexity Score: 75
Routing Decision: GPT_5_5
Routing Confidence: HIGH
Dashboard Hint: CAUTION

## SPEC REVIEW METADATA

- **Review Status:** APPROVED_WITH_NOTES
- **Complexity Score:** 75
- **Risk:** HIGH
- **Recommended Review Model:** 5.5
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-06-02
- **Review Confidence:** HIGH
- **Review Source:** janus-spec-review

## SPEC IMPLEMENTATION METADATA

- **Implementation Status:** DONE
- **Final Audit:** PASS
- **Completed At:** 2026-06-03
- **Implemented Tasks:** TASK-SPEC14.1, TASK-SPEC14.2, TASK-SPEC14.3, TASK-SPEC14.4, TASK-SPEC14.5
- **Validation Evidence:**
  - `python -m py_compile backend/tool_registry.py backend/services/websearch/websearch.py backend/services/websearch/gemini_provider.py backend/llm_providers/gemini/gateway.py backend/services/tool_executor.py backend/services/cost_service.py backend/tests/tools/test_websearch.py backend/tests/test_backlog_007_tool_routing_performance.py backend/tests/test_cost_token_tracking_completeness.py`
  - `python -m pytest backend/tests/test_cost_token_tracking_completeness.py -q` -> 9 passed
  - `python -m pytest backend/tests/test_backlog_007_tool_routing_performance.py -q` -> 10 passed
  - `python -m pytest backend/tests/tools/test_websearch.py -q` -> 102 passed, 1 warning
  - `python -m pytest backend/tests/test_smallest_viable_model_escalation_discipline.py -q` -> 7 passed
  - `node --check frontend/js/cost-visualizer.js`
- **Final Audit Artifact:** `documentation/test-runs/TASK-SPEC14_final_audit.md`
