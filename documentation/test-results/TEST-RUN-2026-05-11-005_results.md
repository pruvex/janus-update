# TestResult: TEST-RUN-2026-05-11-005

## Metadata

- **TestRun-ID**: TEST-RUN-2026-05-11-005
- **Datum**: 2026-05-11
- **TestSpec**: documentation/TEST_SPEC/REVIEW EXECUTION ROUTING.md
- **TestPlan**: documentation/test-runs/TEST-RUN-2026-05-11-005_plan.md
- **Playwright Runner**: tests/e2e/generated/TEST-RUN-2026-05-11-005.live.spec.js
- **Playwright Report/Trace**: test-results/ (screenshots and error context available)
- **Frontend Log**: N/A
- **Backend Log**: N/A

## Zusammenfassung

- **Gesamtergebnis**: FAIL
- **Ausgefuehrte Testfaelle**: 1
- **Bestandene Testfaelle**: 0
- **Fehlgeschlagene Testfaelle**: 1
- **Nicht ausgefuehrte Testfaelle**: 16

## Ergebnisse pro Testfall

| TestCase-ID | Beschreibung | Ergebnis | Evidence | Notizen |
|-------------|--------------|----------|----------|---------|
| TC-001 | Weather Inference | FAIL | Timeout (60s) | Assistant-Antwort nicht sichtbar innerhalb von 30s - Backend antwortet nicht |
| TC-002 | Wikipedia Query | NOT_RUN | - | Test nicht ausgeführt (TC-001 fehlgeschlagen) |
| TC-003 | Geo Distance | NOT_RUN | - | Test nicht ausgeführt (TC-001 fehlgeschlagen) |
| TC-004 | RSS News | NOT_RUN | - | Test nicht ausgeführt (TC-001 fehlgeschlagen) |
| TC-005 | Ambiguous Request | NOT_RUN | - | Test nicht ausgeführt (TC-001 fehlgeschlagen) |
| INT-001 | Weather Intent | NOT_RUN | - | Test nicht ausgeführt (TC-001 fehlgeschlagen) |
| INT-002 | Knowledge Query | NOT_RUN | - | Test nicht ausgeführt (TC-001 fehlgeschlagen) |
| INT-003 | Geo Distance (Ambiguous) | NOT_RUN | - | Test nicht ausgeführt (TC-001 fehlgeschlagen) |
| INT-004 | RSS News | NOT_RUN | - | Test nicht ausgeführt (TC-001 fehlgeschlagen) |
| UX-001 | Success Behavior | NOT_RUN | - | Test nicht ausgeführt (TC-001 fehlgeschlagen) |
| UX-002 | Failure Behavior | NOT_RUN | - | Test nicht ausgeführt (TC-001 fehlgeschlagen) |
| UX-003 | Proactive Clarification | NOT_RUN | - | Test nicht ausgeführt (TC-001 fehlgeschlagen) |
| UX-004 | Cancel/Undo Behavior | NOT_RUN | - | Test nicht ausgeführt (TC-001 fehlgeschlagen) |
| UX-005 | User-Facing Explanation | NOT_RUN | - | Test nicht ausgeführt (TC-001 fehlgeschlagen) |
| PROVIDER_SWITCH_GEMINI | Manual Gate: Switch to Gemini | NOT_RUN | - | Test nicht ausgeführt (TC-001 fehlgeschlagen) |
| SEC-001 | Prompt Injection via Malicious RSS Input | NOT_RUN | - | Test nicht ausgeführt (TC-001 fehlgeschlagen) |
| PINJ-001 | RSS Feed Injection | NOT_RUN | - | Test nicht ausgeführt (TC-001 fehlgeschlagen) |

## Automation Evidence

- **Runner**: tests/e2e/generated/TEST-RUN-2026-05-11-005.live.spec.js
- **Command**: npm run test:e2e -- tests/e2e/generated/TEST-RUN-2026-05-11-005.live.spec.js --headed --workers=1 --reporter=list
- **Playwright exit code**: 1 (non-zero)
- **Manual gates**: 0 (nicht erreicht)
- **Screenshots/Trace**: test-results/ (Screenshots und Error-Context für TC-001 verfügbar)
- **Frontend log excerpt/hash**: N/A
- **Backend log excerpt/hash**: N/A

## Provider-/Model-Matrix Ergebnisse

| Provider | Modell | Ergebnis | Evidence |
|----------|--------|----------|----------|
| GPT | gpt-5.4-nano | FAIL | Backend antwortet nicht auf Chat-Anfrage |
| Gemini | gemini-3-flash-preview | NOT_RUN | Test nicht ausgeführt (TC-001 fehlgeschlagen) |

## Security Gate Ergebnisse

| Gate | Ergebnis | Evidence |
|------|----------|----------|
| Userdaten sicher | N/A | Tests nicht ausgeführt (Backend-Timeout) |
| Destruktive Aktionen isoliert | N/A | Tests nicht ausgeführt (Backend-Timeout) |
| Prompt-Injection-Risiko | N/A | Tests nicht ausgeführt (Backend-Timeout) |

## Findings

- **BACKEND_TIMEOUT_ISSUE**: Backend antwortet nicht auf Chat-Anfragen
  - TC-001 fehlgeschlagen mit Timeout (60s)
  - Assistant-Antwort nicht sichtbar innerhalb von 30s
  - Nachricht wurde gesendet, aber keine Backend-Antwort
  - Ursache: Backend-Verbindungsproblem oder API nicht erreichbar
  - Behebung erforderlich: Backend-Logs prüfen und API-Verbindung verifizieren

## Nebenbefunde ausserhalb TestScope

- Keine

## Naechster Schritt

- TEST SKILL 4 – FINDING TRIAGE AND ROUTING
