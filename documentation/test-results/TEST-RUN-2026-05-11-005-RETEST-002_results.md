# TestResult: TEST-RUN-2026-05-11-005-RETEST-002

## Metadata

- **TestRun-ID**: TEST-RUN-2026-05-11-005-RETEST-002
- **Source TestRun**: TEST-RUN-2026-05-11-005-RETEST-001
- **Datum**: 2026-05-11
- **TestSpec**: documentation/TEST_SPEC/REVIEW EXECUTION ROUTING.md
- **TestPlan**: documentation/test-runs/TEST-RUN-2026-05-11-005_plan.md
- **Previous TestResult**: documentation/test-results/TEST-RUN-2026-05-11-005-RETEST-001_results.md
- **Playwright Runner**: tests/e2e/generated/TEST-RUN-2026-05-11-005.live.spec.js
- **Playwright Report/Trace**: test-results/ (screenshots and error context available)
- **Frontend Log**: N/A
- **Backend Log**: N/A

## Zusammenfassung

- **Gesamtergebnis**: FAIL
- **Ausgefuehrte Testfaelle**: 2
- **Bestandene Testfaelle**: 1
- **Fehlgeschlagene Testfaelle**: 1
- **Nicht ausgefuehrte Testfaelle**: 15

## Ergebnisse pro Testfall

| TestCase-ID | Beschreibung | Ergebnis | Evidence | Notizen |
|-------------|--------------|----------|----------|---------|
| TC-001 | Weather Inference | PASS | Response in 23.9s | Backend antwortete erfolgreich auf Weather-Query |
| TC-002 | Wikipedia Query | FAIL | Timeout (30s) | Assistant-Antwort nicht sichtbar innerhalb von 30s - Backend antwortet intermittierend |
| TC-003 | Geo Distance | NOT_RUN | - | Test nicht ausgeführt (TC-002 fehlgeschlagen) |
| TC-004 | RSS News | NOT_RUN | - | Test nicht ausgeführt (TC-002 fehlgeschlagen) |
| TC-005 | Ambiguous Request | NOT_RUN | - | Test nicht ausgeführt (TC-002 fehlgeschlagen) |
| INT-001 | Weather Intent | NOT_RUN | - | Test nicht ausgeführt (TC-002 fehlgeschlagen) |
| INT-002 | Knowledge Query | NOT_RUN | - | Test nicht ausgeführt (TC-002 fehlgeschlagen) |
| INT-003 | Geo Distance (Ambiguous) | NOT_RUN | - | Test nicht ausgeführt (TC-002 fehlgeschlagen) |
| INT-004 | RSS News | NOT_RUN | - | Test nicht ausgeführt (TC-002 fehlgeschlagen) |
| UX-001 | Success Behavior | NOT_RUN | - | Test nicht ausgeführt (TC-002 fehlgeschlagen) |
| UX-002 | Failure Behavior | NOT_RUN | - | Test nicht ausgeführt (TC-002 fehlgeschlagen) |
| UX-003 | Proactive Clarification | NOT_RUN | - | Test nicht ausgeführt (TC-002 fehlgeschlagen) |
| UX-004 | Cancel/Undo Behavior | NOT_RUN | - | Test nicht ausgeführt (TC-002 fehlgeschlagen) |
| UX-005 | User-Facing Explanation | NOT_RUN | - | Test nicht ausgeführt (TC-002 fehlgeschlagen) |
| PROVIDER_SWITCH_GEMINI | Manual Gate: Switch to Gemini | NOT_RUN | - | Test nicht ausgeführt (TC-002 fehlgeschlagen) |
| SEC-001 | Prompt Injection via Malicious RSS Input | NOT_RUN | - | Test nicht ausgeführt (TC-002 fehlgeschlagen) |
| PINJ-001 | RSS Feed Injection | NOT_RUN | - | Test nicht ausgeführt (TC-002 fehlgeschlagen) |

## Automation Evidence

- **Runner**: tests/e2e/generated/TEST-RUN-2026-05-11-005.live.spec.js
- **Command**: npm run test:e2e -- tests/e2e/generated/TEST-RUN-2026-05-11-005.live.spec.js --headed --workers=1 --reporter=list
- **Playwright exit code**: 1 (non-zero)
- **Manual gates**: 0 (nicht erreicht)
- **Screenshots/Trace**: test-results/ (Screenshots und Error-Context für TC-002 verfügbar)
- **Frontend log excerpt/hash**: N/A
- **Backend log excerpt/hash**: N/A

## Backend Restart Applied

- **Action**: Backend komplett neu gestartet nach Config-Änderung
- **Status**: SUCCESS
- **Config**: jwt_secret_key und api_key vorhanden
- **Secrets exposed**: NEIN

## Provider-/Model-Matrix Ergebnisse

| Provider | Modell | Ergebnis | Evidence |
|----------|--------|----------|----------|
| GPT | gpt-5.4-nano | PARTIAL | TC-001 PASS, TC-002 FAIL (Intermittierendes Backend-Timeout) |
| Gemini | gemini-3-flash-preview | NOT_RUN | Test nicht ausgeführt (TC-002 fehlgeschlagen) |

## Security Gate Ergebnisse

| Gate | Ergebnis | Evidence |
|------|----------|----------|
| Userdaten sicher | N/A | Tests nicht vollständig ausgeführt |
| Destruktive Aktionen isoliert | N/A | Tests nicht vollständig ausgeführt |
| Prompt-Injection-Risiko | N/A | Tests nicht vollständig ausgeführt |

## Findings

- **INTERMITTENT_BACKEND_TIMEOUT**: Backend antwortet intermittierend auf Chat-Anfragen
  - TC-001: PASS (23.9s) - Backend antwortete erfolgreich
  - TC-002: FAIL (50.5s) - Timeout nach 30s, keine Backend-Antwort
  - Backend wurde neu gestartet nach Config-Änderung
  - Config korrekt geladen (jwt_secret_key und api_key vorhanden)
  - Backend-Health-Check: OK (200)
  - Ursache: Backend antwortet auf erste Anfrage, aber nicht auf zweite (intermittierendes Problem)
  - Behebung erforderlich: Backend-Logs auf Fehler bei aufeinanderfolgenden Anfragen prüfen, möglicherweise Rate-Limit oder Connection-Pool-Problem

## Nebenbefunde ausserhalb TestScope

- Keine

## Naechster Schritt

- TEST SKILL 4 – FINDING TRIAGE AND ROUTING
