# BACKLOG TASK - BACKLOG-059 - TC-002-GPT Memory-Recall Halluzination bei Projekt-Namensabfrage

## 1. Ziel
GPT Memory-Recall so haerten, dass nach dem Speichern von "Mein Testprojekt heisst Phoenix" beim Recall nicht der Placeholder "Name des Testprojekts" als Fakt ausgegeben wird.

## 2. Impact-Analyse
- **Basiert auf:** documentation/backlog/BACKLOG.md#BACKLOG-059
- **Beeinflusst:** backend/services/orchestrator/, backend/services/chat_orchestrator.py, Memory-/Context-Retrieval-Pfade, TEST-RUN-2026-05-16-004
- **Risiko-Einschaetzung:** MEDIUM

## 3. Scope
### IN SCOPE
- Pruefen, ob TC-001-GPT den Wert "Phoenix" korrekt persistiert oder nur generisch/templated speichert.
- Pruefen, ob TC-002-GPT Memory-Kontext falsch abruft, falsch priorisiert oder Placeholder aus Prompt/Testdaten uebernimmt.
- Placeholder-Guard fuer Antworten wie "Name des Testprojekts" als konkrete Fakten evaluieren.
- Gezielter Retest von TC-001-GPT und TC-002-GPT.

### OUT OF SCOPE
- Breite Memory-Architektur-Refactors.
- Aenderungen an Gemini, sofern TC-002-GEMINI bereits PASS bleibt.
- Test-Oracle-Aufweitung fuer TC-002-GPT; dies ist laut Triage ein Product Bug.

## 4. Umsetzungsschritte
- Evidence fuer TC-001-GPT und TC-002-GPT aus TEST-RUN-2026-05-16-004 auswerten.
- Persistenz- und Retrieval-Pfad fuer den Testprojekt-Fakt identifizieren.
- Precheck klären lassen, welche Dateien/Tests fuer eine sichere Umsetzung notwendig sind.
- Nach Umsetzung gezielt TC-001-GPT/TC-002-GPT retesten und sicherstellen, dass "Phoenix" genannt wird oder ehrlich "keine Information" kommt, aber kein Placeholder-Fakt.

## 5. Acceptance Criteria
- [ ] TC-002-GPT gibt nach erfolgreichem TC-001-GPT den konkreten Projektnamen "Phoenix" aus.
- [ ] TC-002-GPT gibt keinen Placeholder wie "Name des Testprojekts" als Fakt aus.
- [ ] TC-002-GEMINI bleibt PASS.
- [ ] Memory-Recall gibt bei fehlender Evidenz ehrlich "keine Information" statt erfundener Werte aus.
- [ ] Retest-Evidence ist unter documentation/test-results dokumentiert.

## 6. Tests / Validierung
- `npx playwright test tests/e2e/generated/TEST-RUN-2026-05-16-004.live.spec.js -g "TC-001-GPT|TC-002-GPT|TC-002-GEMINI" --workers=1 --reporter=list`
- Falls Produktcode geaendert wird: relevante Python-Syntax-/Unit-Pruefung fuer die betroffenen Backend-Dateien.

## 7. Model
- **Assigned Model:** SWE 1.6
- **Reason:** Backlog-Handoff fuer reproduzierbaren Product Bug mit begrenztem Memory-Recall-Scope.

## NEXT STEP

```text
@[/SKILL 3 - PRE-IMPLEMENTATION VERIFICATION]
Target Task: BACKLOG-059
Task: documentation/tasks/backlog_BACKLOG-059_tc002_gpt_memory_recall_placeholder.md
Backlog Item: BACKLOG-059
Mode: PRE_IMPLEMENTATION_VERIFICATION
Execution Model: SWE 1.6
Context: TEST-RUN-2026-05-16-004; TC-002-GPT halluziniert "Name des Testprojekts" statt "Phoenix" nach TC-001-GPT.
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_SKILL_4_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_SKILL_4_HANDOFF_OR_PRE_CHECK_BLOCKED
```
