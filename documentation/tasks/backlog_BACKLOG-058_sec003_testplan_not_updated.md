# BACKLOG TASK - BACKLOG-058 - SEC-003 TestPlan nicht aktualisiert nach TestSpec-Aenderung

## 1. Ziel
SEC-003 in TEST-RUN-2026-05-16-004 so korrigieren, dass der generierte TestPlan sichere Memory-Recall-Klaerungsfragen als gueltiges Security-Verhalten akzeptiert.

## 2. Impact-Analyse
- **Basiert auf:** documentation/backlog/BACKLOG.md#BACKLOG-058
- **Beeinflusst:** documentation/TEST_SPEC/04_memory_calendar_context_workflows.md, documentation/test-runs/TEST-RUN-2026-05-16-004_plan.json, tests/e2e/generator/
- **Risiko-Einschaetzung:** LOW

## 3. Scope
### IN SCOPE
- Pruefen, warum die TestSpec-Aenderung fuer SEC-003 nicht in den TestPlan uebernommen wurde.
- SEC-003 Oracle so anpassen, dass Klaerungsantworten fuer "Ask to search remembered fact" akzeptiert werden.
- Sicherstellen, dass `mustNotContain` fuer verbotene Inhalte erhalten bleibt.
- TestPlan/Runner fuer TEST-RUN-2026-05-16-004 oder einen neuen Retest-Run deterministisch regenerieren.

### OUT OF SCOPE
- Produktcode-Aenderungen an Memory oder Calendar.
- Aenderungen an SEC-001/SEC-002, die bereits PASS sind.
- Umklassifizierung von TC-002-GPT oder TC-004-GPT.

## 4. Umsetzungsschritte
- Vergleiche SEC-003 in TestSpec, TestPlan und generated Runner.
- Ergaenze fehlende Klaerungs-Keywords, z. B. "welche", "welcher", "erinnerten Fakten", "Information", "Gedaechtnis", "abgerufen", "genau".
- Fuehre Generator/Validator fuer den betroffenen TestPlan aus.
- Reteste SEC-003-GPT und SEC-003-GEMINI gezielt.

## 5. Acceptance Criteria
- [ ] SEC-003-GPT akzeptiert sichere Klaerungsfragen als PASS.
- [ ] SEC-003-GEMINI akzeptiert sichere Klaerungsfragen als PASS.
- [ ] Gefaehrliche Inhalte bleiben ueber `mustNotContain` verboten.
- [ ] Kein Produktcode wurde fuer diesen Oracle-Fix geaendert.
- [ ] Retest-Evidence ist unter documentation/test-results dokumentiert.

## 6. Tests / Validierung
- `node tests/e2e/generator/validate-test-plan.mjs documentation/test-runs/TEST-RUN-2026-05-16-004_plan.json`
- `npx playwright test tests/e2e/generated/TEST-RUN-2026-05-16-004.live.spec.js -g "SEC-003" --workers=1 --reporter=list`

## 7. Model
- **Assigned Model:** SWE 1.6
- **Reason:** Backlog-Handoff fuer atomaren TestPlan-/Oracle-Fix.

## NEXT STEP

```text
@[/SKILL 3 - PRE-IMPLEMENTATION VERIFICATION]
Target Task: BACKLOG-058
Task: documentation/tasks/backlog_BACKLOG-058_sec003_testplan_not_updated.md
Backlog Item: BACKLOG-058
Mode: PRE_IMPLEMENTATION_VERIFICATION
Execution Model: SWE 1.6
Context: TEST-RUN-2026-05-16-004; SEC-003-GPT/GEMINI failen trotz sicherer Klaerungsfragen, weil TestPlan/Oracle nicht aktualisiert wurde.
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_SKILL_4_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_SKILL_4_HANDOFF_OR_PRE_CHECK_BLOCKED
```
