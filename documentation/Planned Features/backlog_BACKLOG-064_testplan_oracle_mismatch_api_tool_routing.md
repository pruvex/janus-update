# FEATURE SPEC - TestPlan Oracle Fix für API Tool Routing Source Attribution

## SPEC REVIEW EXECUTION ROUTING

target_skill: SKILL_1
execution_mode: SWE_1_6
complexity_score: 35
confidence: HIGH
dashboard_hint: NONE
security_hint: NONE
reason: TestPlan-Generator überträgt source attribution patterns aus TestSpec nicht korrekt in TestPlan expectations für Spec 06 (API Tool Routing and Source Attribution).

## TEST IDENTITY

- Feature Name: TestPlan Oracle Fix für API Tool Routing Source Attribution
- Backlog Item: BACKLOG-064
- Source Input: TestRun TEST-RUN-2026-05-17-002
- Primary Feature Goal: TestPlan-Generator überträgt source attribution patterns aus TestSpec korrekt in TestPlan expectations für API Tool Routing Tests
- User Problem: TestPlan enthält generische clarification/capability keywords statt source attribution patterns, was zu falschen FAIL-Ergebnissen führt
- User Value: API Tool Routing Tests validieren korrekt, ob Janus source attribution liefert, statt capability keywords zu prüfen
- Suggested Save Path: documentation/Planned Features/backlog_BACKLOG-064_testplan_oracle_mismatch_api_tool_routing.md
- Related TestSpec: documentation/TEST_SPEC/06_api_tool_routing_and_source_attribution.md
- Related TestRun: TEST-RUN-2026-05-17-002

## FEATURE OBJECTIVE

TestPlan-Generator muss source attribution patterns aus TestSpec 06 korrekt in TestPlan expectations übertragen, so dass Tests für Weather, Wikipedia, Geo, RSS/News und Websearch source attribution keywords akzeptieren statt generischer clarification/capability keywords.

## SCOPE

Dieses Feature umfasst:
- TestSpec 06: Analyse der source attribution requirements
- TestPlan-Generator: Fix der pattern-Übertragung für source attribution
- TestPlan-Neugenerierung für Spec 06 mit korrekten expectations
- Retest VALIDATION (keine Implementation)

Out of Scope:
- Produktcode-Änderungen an Janus
- Änderungen am API Tool Routing Verhalten
- Änderungen an source attribution im Produkt

## FUNCTIONAL REQUIREMENTS

- FR-1: TestPlan-Generator liest source attribution requirements aus TestSpec 06
- FR-2: TestPlan-Generator überträgt source attribution keywords korrekt in TestPlan expectations
- FR-3: TC-001 (Weather) expectations enthalten source attribution keywords wie "Quelle:", "Open-Meteo", "Wetterdienst"
- FR-4: TC-002 (Wikipedia) expectations enthalten source attribution keywords wie "Wikipedia", "Wissensquelle", "laut Wikipedia"
- FR-5: TC-003 (Geo) expectations enthalten source attribution keywords wie "Geo-Service", "Distanz laut", "berechnet mit"
- FR-6: TC-004 (RSS/News) expectations enthalten source attribution keywords wie "RSS", "Heise", "Feed"
- FR-7: TC-005 (Websearch) expectations enthalten source attribution keywords oder search-source summary patterns
- FR-8: Security/Prompt-Injection Tests behalten ihre Ablehnungs-Keywords bei

## SYSTEM BEHAVIOR

Nach diesem Feature:
- TestPlan für Spec 06 enthält korrekte source attribution expectations
- TestRun für Spec 06 validiert source attribution statt capability keywords
- 32/41 FAIL aus TEST-RUN-2026-05-17-002 werden durch korrekte expectations zu PASS

## CONSTRAINTS

- Keine Produktcode-Änderungen
- TestSpec 06 bleibt unverändert (nur TestPlan-Generator wird angepasst)
- Security/Prompt-Injection Tests müssen ihre Sicherheitserwartungen behalten

## TEST REQUIREMENTS

- TR-1: TestPlan für Spec 06 wird neu generiert
- TR-2: Generierter TestPlan enthält source attribution keywords in TC-001 bis TC-005
- TR-3: Retest TEST-RUN-2026-05-17-003 mit neuem TestPlan zeigt verbesserte PASS-Rate
- TR-4: Security Tests (SEC-001, SEC-002, SEC-003, SEC-004, PINJ-001, PINJ-002, PINJ-003) behalten ihre Sicherheitserwartungen

## ACCEPTANCE CRITERIA

- [ ] TestPlan-Generator überträgt source attribution patterns korrekt
- [ ] TC-001 bis TC-005 enthalten source attribution keywords in expectations
- [ ] Security Tests behalten ihre Sicherheitserwartungen
- [ ] Retest mit neuem TestPlan zeigt source attribution validation
- [ ] Keine Produktcode-Änderungen erforderlich

## BLOCKING CONDITIONS

- [ ] TestSpec 06 ist nicht lesbar
- [ ] TestPlan-Generator ist nicht modifizierbar
- [ ] Retest zeigt neue FAILs durch geänderte expectations

## IMPLEMENTATION NOTES

## FINAL AUDIT / SKILL 7 STATUS

- **Status:** DONE
- **Final Audit:** PASS
- **Final TestRun:** TEST-RUN-2026-05-18-002
- **Result:** 42/42 PASS, 0 failed, 0 blocked, 0 manual gates
- **Evidence:** `documentation/test-results/TEST-RUN-2026-05-18-002_results.json`, `documentation/test-results/TEST-RUN-2026-05-18-002/`
- **Final Audit File:** `documentation/test-runs/BACKLOG-064_final_audit.md`
- **Backlog Items Generated:** Keine
- **Dashboard Sync:** Nicht erforderlich durch Triage; Backlog-Dokumentation wurde synchronisiert.

Dies ist ein TestPipeline-Only Fix. Keine Produktcode-Änderungen. Der Fix liegt im TestPlan-Generator für Spec 06.
