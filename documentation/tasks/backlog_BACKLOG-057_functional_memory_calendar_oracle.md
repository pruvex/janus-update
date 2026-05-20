# BACKLOG TASK - BACKLOG-057 - Functional Memory/Calendar Test Oracle zu eng

Status: DONE
Final Audit: PASS (`documentation/test-runs/BACKLOG-057_final_audit.md`)

## 1. Ziel
Functional-Oracles fuer Memory-/Calendar-Kontext so aktualisieren, dass semantisch korrekte "nicht vorhanden"-Antworten, Klaerungsfragen und sichere Calendar-Fallbacks passend bewertet werden.

## 2. Impact-Analyse
- **Basiert auf:** documentation/backlog/BACKLOG.md#BACKLOG-057
- **Beeinflusst:** documentation/TEST_SPEC/04_memory_calendar_context_workflows.md, documentation/test-runs/TEST-RUN-2026-05-16-003_plan.json, documentation/test-runs/TEST-RUN-2026-05-16-004_plan.json, tests/e2e/generator/
- **Risiko-Einschaetzung:** LOW

## 3. Scope
### IN SCOPE
- Functional-Oracles fuer TC-003-GPT/GEMINI und verwandte Memory-/Calendar-Cases pruefen.
- TC-002-GPT/GEMINI so korrigieren, dass der konkrete Memory-Recall-Wert `Phoenix` als PASS gilt.
- "Keine Information" / "nicht gespeichert" fuer nie gespeicherte Lieblingsfarbe als PASS-Verhalten modellieren.
- Sichere Klaerungs-/Fallback-Antworten fuer Calendar-Abfragen akzeptieren, sofern keine Runtime-Fehler vorliegen.
- `mustNotContain` fuer verbotene Inhalte beibehalten.

### OUT OF SCOPE
- Produktfix fuer TC-002-GPT Placeholder-Halluzination; das ist BACKLOG-059 und ist abgeschlossen.
- TC-004-GPT Runtime-/Infrastructure-Error; eigener Runtime-Finding-Pfad.
- Breite Produktcode-Aenderungen.

## 4. Umsetzungsschritte
- Evidence aus TEST-RUN-2026-05-16-003 und TEST-RUN-2026-05-16-004 vergleichen, insbesondere TC-002-GPT/GEMINI nach BACKLOG-059.
- Functional TestSpec- und TestPlan-Erwartungen fuer Memory-/Calendar-Fallbacks angleichen.
- TestPlan/Runner deterministisch regenerieren.
- Betroffene Functional-Cases gezielt retesten.

## 5. Acceptance Criteria
- [x] TC-002-GPT und TC-002-GEMINI akzeptieren `Phoenix` als korrekte Memory-Recall-Antwort.
- [x] TC-003-GPT und TC-003-GEMINI akzeptieren "keine Information" als korrektes Verhalten fuer nie gespeicherte Lieblingsfarbe.
- [x] Functional-Oracles akzeptieren sichere Klaerungsfragen, aber keine verbotenen Inhalte.
- [x] TC-002-GPT bleibt als Product Bug separiert und wird nicht per Oracle weichgezeichnet.
- [x] TC-004-GPT Runtime-Error bleibt sichtbar und wird nicht als fachlicher PASS kaschiert.

## 6. Tests / Validierung
- `node tests/e2e/generator/validate-test-plan.mjs documentation/test-runs/TEST-RUN-2026-05-16-004_plan.json`
- `npx playwright test tests/e2e/generated/TEST-RUN-2026-05-16-004.live.spec.js -g "TC-003|TC-004" --workers=1 --reporter=list`

## 8. Abschluss / Audit
- TestPlan validation PASS (28 tests).
- Runner regenerated for TEST-RUN-2026-05-16-004.
- Live retest `TC-002` PASS for GPT/GEMINI.
- Live retest `TC-003` PASS for GPT/GEMINI.
- Live retest `PINJ-001-GEMINI` PASS after sequential rerun.
- `TC-004-GEMINI` PASS; `TC-004-GPT` remains FAIL with OpenAI/provider runtime fallback and is tracked separately as BACKLOG-060.

## 7. Model
- **Assigned Model:** SWE 1.6
- **Reason:** Backlog-Handoff fuer atomaren Functional Test-Oracle-Fix.

## NEXT STEP

```text
@[/SKILL 3 - PRE-IMPLEMENTATION VERIFICATION]
Target Task: BACKLOG-057
Task: documentation/tasks/backlog_BACKLOG-057_functional_memory_calendar_oracle.md
Backlog Item: BACKLOG-057
Mode: PRE_IMPLEMENTATION_VERIFICATION
Execution Model: SWE 1.6
Context: TEST-RUN-2026-05-16-003/004; Functional Memory/Calendar-Oracles sind fuer konkrete Memory-Recall-Werte wie Phoenix, sichere "keine Information"- und Klaerungsantworten zu eng.
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_SKILL_4_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_SKILL_4_HANDOFF_OR_PRE_CHECK_BLOCKED
```
