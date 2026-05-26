# BACKLOG-060 - TC-004-GPT Calendar Query Runtime Fallback

Status: DONE
Final Audit: PASS (`documentation/test-runs/BACKLOG-060_final_audit.md`)

## Ziel
TC-004-GPT darf bei der Kalenderfrage `Was steht morgen in meinem Testkalender?` keinen Provider-/Runtime-Fallback als Endantwort liefern. Der GPT-Pfad muss entweder eine sichere Kalenderantwort, eine klare Rückfrage oder eine ehrliche "keine Termine/kein Kalender gefunden"-Antwort erzeugen.

## Kontext
- **Quelle:** TEST-RUN-2026-05-16-004
- **Failing Case:** `TC-004-GPT`
- **Passing Comparator:** `TC-004-GEMINI`
- **Evidence:** `documentation/test-results/TEST-RUN-2026-05-16-004/TC-004-GPT_evidence.json`
- **Aktueller Gesamtstand:** TEST-RUN-2026-05-16-004 ist `FAIL` mit `27 passed, 1 failed`.

## Aktuelles Verhalten
`TC-004-GPT` antwortet:

```text
Es ist ein Fehler aufgetreten: Provider: openai | Modell: gpt-5.4-nano. Bitte sende die Anfrage direkt noch einmal; ich versuche es dann mit einem robusten Neuaufbau.
```

Das ist kein Test-Oracle-Problem. BACKLOG-057 hat die Functional-Oracles bereinigt; dieser Fail bleibt absichtlich sichtbar.

## Erwartetes Verhalten
- Calendar-List-Intent wird stabil behandelt.
- GPT liefert Calendar-Listing, "keine Termine gefunden" oder eine gezielte Klärungsfrage.
- Runtime-/Provider-Fehler werden diagnostiziert und nicht als normale finale Assistant-Antwort akzeptiert.
- Keine unsafe Calendar-Mutation.

## Empfohlene Preflight-Fragen
- Tritt der Fehler vor oder nach Tool-Auswahl/Tool-Execution auf?
- Wird `gpt-5.4-nano` im Calendar-Intent mit zu viel Kontext oder ungeeigneten Tools aufgerufen?
- Ist der OpenAI-Gateway-Fallback für diesen Pfad regressiv oder nur ein fehlendes Retry/Degrade-Verhalten?
- Warum besteht `TC-004-GEMINI`, während GPT in den robusten Neuaufbau fällt?

## Validierung
```bash
npx playwright test tests/e2e/generated/TEST-RUN-2026-05-16-004.live.spec.js -g TC-004 --workers=1 --reporter=list
```

Akzeptanz:
- `TC-004-GPT` PASS
- `TC-004-GEMINI` bleibt PASS
- Danach kompletter TEST-RUN-2026-05-16-004 ist Kandidat für 28/28 PASS

## Out of Scope
- Weitere Oracle-Erweiterungen für TC-002/TC-003
- Security-Oracle-Fixes
- Broad Calendar-Architecture-Refactor ohne Preflight-Befund

## NEXT STEP HANDOFF
```text
@[/SKILL 3 - PRE-IMPLEMENTATION VERIFICATION]
Target Task: BACKLOG-060
Task: documentation/tasks/backlog_BACKLOG-060_tc004_gpt_calendar_runtime_error.md
Backlog Item: BACKLOG-060
Mode: PRE_IMPLEMENTATION_VERIFICATION
Execution Model: SWE 1.6
Context: TEST-RUN-2026-05-16-004; TC-004-GPT calendar query returns OpenAI/provider runtime fallback while TC-004-GEMINI passes with a safe clarification. BACKLOG-057 final audit passed and left this as the only remaining failing case.
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_SKILL_4_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_SKILL_4_HANDOFF_OR_PRE_CHECK_BLOCKED
```

## Abschluss
- Root Cause: OpenAI/API-Key/Quota waren nicht defekt; `calendar.list_events` lief erfolgreich. Der Streaming-Finalizer ersetzte ein erfolgreiches Tool-Ergebnis durch dynamischen Provider-Fallback.
- Fix: `execution_engine.py` erkennt dynamische Provider-Fallbacks als generische Stabilitäts-Fallbacks und rekonstruiert nach erfolgreicher Tool-Runde die Antwort aus erfolgreichen Tool-Ergebnissen.
- Validation: `TC-004-GPT` PASS, `TC-004-GEMINI` PASS, TEST-RUN-2026-05-16-004 PASS 28/28.
