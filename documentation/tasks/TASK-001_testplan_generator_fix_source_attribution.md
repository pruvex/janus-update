# TASK-001: TestPlan-Generator Fix für source attribution pattern Übertragung

## TASK IDENTITY

- Task ID: TASK-001
- Feature: TestPlan Oracle Fix für API Tool Routing Source Attribution
- Backlog Item: BACKLOG-064
- Source Spec: documentation/Planned Features/backlog_BACKLOG-064_testplan_oracle_mismatch_api_tool_routing.md
- Execution Model: SWE 1.6

## TASK GOAL

TestPlan-Generator überträgt source attribution patterns aus TestSpec 06 korrekt in TestPlan expectations für API Tool Routing Tests (TC-001 bis TC-005).

## TASK DESCRIPTION

Der TestPlan-Generator generiert für TestSpec 06 (API Tool Routing and Source Attribution) TestPlan-Expectations mit generischen clarification/capability keywords statt source attribution patterns. Dies führt zu 32/41 FAIL mit ASSERTION_MISMATCH in TEST-RUN-2026-05-17-002, obwohl Evidence teilweise korrekte source attribution zeigt (z.B. TC-001-GPT: "Quelle: Open-Meteo").

Der Task fixt den TestPlan-Generator, so dass source attribution patterns aus TestSpec korrekt in TestPlan expectations übertragen werden.

## FILES

- Primary File: TestPlan-Generator (tests/e2e/generator/compile-testspec-to-testplan.mjs)
- Reference/Baseline: TestSpec 06 (documentation/TEST_SPEC/06_api_tool_routing_and_source_attribution.md)
- Reference Plan: Alter TestPlan (documentation/test-runs/TEST-RUN-2026-05-17-002_plan.json)

## STEPS

1. TestSpec 06 source attribution requirements analysieren
   - Weather: source attribution keywords wie "Quelle:", "Open-Meteo", "Wetterdienst"
   - Wikipedia: source attribution keywords wie "Wikipedia", "Wissensquelle", "laut Wikipedia"
   - Geo: source attribution keywords wie "Geo-Service", "Distanz laut", "berechnet mit"
   - RSS/News: source attribution keywords wie "RSS", "Heise", "Feed"
   - Websearch: source attribution keywords oder search-source summary patterns

2. TestPlan-Generator pattern-Übertragung für source attribution fixen
   - Generator liest source attribution requirements aus TestSpec 06
   - Generator überträgt source attribution keywords korrekt in TestPlan expectations
   - TC-001 bis TC-005 source attribution keywords implementieren

3. Security Tests Sicherheitserwartungen bewahren
   - SEC-001, SEC-002, SEC-003, SEC-004 behalten ihre Sicherheitserwartungen
   - PINJ-001, PINJ-002, PINJ-003 behalten ihre Sicherheitserwartungen

## ACCEPTANCE CRITERIA

- [ ] TestPlan-Generator liest source attribution requirements aus TestSpec 06
- [ ] TC-001 bis TC-005 enthalten source attribution keywords in expectations
- [ ] Security Tests behalten ihre Sicherheitserwartungen
- [ ] Generierter TestPlan validiert source attribution statt capability keywords

## TESTS

- TestPlan-Neugenerierung für Spec 06
- Generierter TestPlan enthält source attribution keywords in TC-001 bis TC-005
- Security Tests behalten ihre Sicherheitserwartungen

## DEPENDENCIES

- TestSpec 06 muss lesbar sein
- TestPlan-Generator muss modifizierbar sein

## OUT OF SCOPE

- Produktcode-Änderungen an Janus
- Änderungen am API Tool Routing Verhalten
- Änderungen an source attribution im Produkt
