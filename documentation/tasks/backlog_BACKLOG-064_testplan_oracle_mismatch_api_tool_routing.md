# BACKLOG TASK – BACKLOG-064 – TestPlan Oracle Fix für API Tool Routing Source Attribution

## 1. Ziel
TestPlan-Generator überträgt source attribution patterns aus TestSpec 06 korrekt in TestPlan expectations, so dass API Tool Routing Tests validieren, ob Janus source attribution liefert, statt capability keywords zu prüfen.

## 2. Impact-Analyse
- **Basiert auf:** documentation/backlog/BACKLOG.md#BACKLOG-064
- **Beeinflusst:** tests/e2e/generator/compile-testspec-to-testplan.mjs, documentation/TEST_SPEC/06_api_tool_routing_and_source_attribution.md
- **Risiko-Einschätzung:** LOW (TestPipeline-Only Fix, keine Produktcode-Änderungen)

## 3. Scope
### IN SCOPE
- Analyse der source attribution requirements in TestSpec 06
- Fix der pattern-Übertragung im TestPlan-Generator für source attribution
- TestPlan-Neugenerierung für Spec 06 mit korrekten expectations
- Validierung durch Retest (keine Produkt-Implementation)

### OUT OF SCOPE
- Produktcode-Änderungen an Janus
- Änderungen am API Tool Routing Verhalten
- Änderungen an source attribution im Produkt

## 4. Umsetzungsschritte
1. TestSpec 06 (documentation/TEST_SPEC/06_api_tool_routing_and_source_attribution.md) analysieren und source attribution requirements extrahieren
2. TestPlan-Generator (tests/e2e/generator/compile-testspec-to-testplan.mjs) untersuchen: aktuelle pattern-Übertragung für source attribution
3. Generator-Branch für Spec 06 source attribution implementieren: Übertragung von source attribution keywords ("Quelle:", "laut", "Wikipedia", "Open-Meteo", "RSS", "Feed", "Geo-Service", "Distanz laut", "berechnet mit", "search-source summary patterns") statt generischer clarification/capability keywords
4. TC-001 (Weather) expectations mit source attribution keywords ausstatten ("Quelle:", "Open-Meteo", "Wetterdienst")
5. TC-002 (Wikipedia) expectations mit source attribution keywords ausstatten ("Wikipedia", "Wissensquelle", "laut Wikipedia")
6. TC-003 (Geo) expectations mit source attribution keywords ausstatten ("Geo-Service", "Distanz laut", "berechnet mit")
7. TC-004 (RSS/News) expectations mit source attribution keywords ausstatten ("RSS", "Heise", "Feed")
8. TC-005 (Websearch) expectations mit source attribution keywords oder search-source summary patterns ausstatten
9. Security/Prompt-Injection Tests (SEC-001, SEC-002, SEC-003, SEC-004, PINJ-001, PINJ-002, PINJ-003) behalten ihre Ablehnungs-Keywords
10. TestPlan für Spec 06 neu generieren mit node tests/e2e/generator/compile-testspec-to-testplan.mjs --spec documentation/TEST_SPEC/06_api_tool_routing_and_source_attribution.md
11. Generierten TestPlan validieren: enthält source attribution keywords in TC-001 bis TC-005; Security Tests behalten Sicherheitserwartungen

## 5. Acceptance Criteria
- [ ] TestPlan-Generator überträgt source attribution patterns korrekt aus TestSpec 06
- [ ] TC-001 bis TC-005 enthalten source attribution keywords in expectations
- [ ] Security Tests behalten ihre Sicherheitserwartungen
- [ ] Generierter TestPlan validiert mit validate-test-plan.mjs
- [ ] Keine Produktcode-Änderungen erforderlich

## 6. Tests / Validierung
- TestPlan-Neugenerierung für Spec 06 mit korrekten source attribution expectations
- Validierung generierter TestPlan mit validate-test-plan.mjs
- Retest TEST-RUN-2026-05-17-003 mit neuem TestPlan zeigt verbesserte PASS-Rate (32/41 FAIL zu PASS erwartet)
- Evidence: documentation/test-runs/TEST-RUN-2026-05-17-003_plan.json, documentation/test-results/TEST-RUN-2026-05-17-003_results.json

## 7. Model
- **Assigned Model:** SWE 1.6
- **Reason:** Backlog-Handoff für TestPipeline-Only Fix mit klar deterministischem Scope (TestPlan-Generator Pattern-Übertragung).
