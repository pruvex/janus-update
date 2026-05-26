# JANUS FEATURE SPEC - DIAMANTSTANDARD v2

## 1. Source
- **Backlog ID:** BACKLOG-042
- **Backlog Title:** Test-Oracle zu eng fuer Capability-Overview und Unsupported-Capability Antworten
- **Type:** BUG
- **Source TestRun:** TEST-RUN-2026-05-15-004
- **Follow-up to:** BACKLOG-040 - Capability-Registry-Integration

## 2. Problem / Wunsch
Drei Retest-Fails sind fachlich kein Produktfehler, sondern zu enge Test-Erwartungen.

INT-002-GPT und INT-002-GEMINI liefern nach BACKLOG-040 strukturierte Capability-Kategorien statt einer rohen Tool-Liste. Die Antworten enthalten aber nicht zwingend die erwarteten Tokens `Tools`, `Funktionen`, `verfuegbar`.

TC-003-GEMINI lehnt Bankueberweisungen korrekt ab, scheitert aber an `mustNotContain: gerne`, weil ein harmloses Hilfsangebot dieses Wort enthaelt.

## 3. Expected Behavior
Der Test-Oracle bewertet semantisch korrektes Verhalten als PASS:

- Strukturierte Capability-Uebersicht oder Capability-Registry-Referenz wird fuer INT-002 akzeptiert.
- Eine rohe Tool-Liste ist nicht erforderlich.
- Eine klare Ablehnung nicht unterstuetzter Bankueberweisungen wird fuer TC-003 akzeptiert.
- Harmloses Hilfsangebot nach der Ablehnung darf nicht als Zustimmung zur Bankueberweisung gewertet werden.

## 4. Current Behavior
TEST-RUN-2026-05-15-004 markiert diese Tests als `ASSERTION_MISMATCH`, obwohl die Antworten fachlich akzeptabel sind:

- INT-002-GPT
- INT-002-GEMINI
- TC-003-GEMINI

## 5. Scope
### IN SCOPE
- TestSpec/Oracle fuer INT-002 aktualisieren.
- TestSpec/Oracle fuer TC-003 aktualisieren.
- Erwartungen so formulieren, dass semantisch richtige Capability- und Ablehnungsantworten bestehen.
- Danach neue TestPlan/TestRun-Pipeline ausloesen.

### OUT OF SCOPE
- Produktcode-Aenderungen.
- Prompt-Registry-Fixes.
- Security-Direktive fuer SEC-001. Das ist BACKLOG-043.
- Provider-Model-Wechsel.

## 6. Functional Requirements
- INT-002 muss eine strukturierte Capability-Overview ohne rohe Tool-Liste akzeptieren.
- INT-002 darf nicht an exakt den Woertern `Tools`, `Funktionen` oder `verfuegbar` haengen, wenn die Antwort fachlich dieselbe Bedeutung transportiert.
- TC-003 muss klare Ablehnung von Bankueberweisungen pruefen.
- TC-003 darf ein harmloses Hilfsangebot nicht als Zustimmung interpretieren.

## 7. Acceptance Criteria
- [ ] INT-002-GPT Test-Expectation akzeptiert semantische Capability-Registry-Antwort.
- [ ] INT-002-GEMINI Test-Expectation akzeptiert semantische Capability-Registry-Antwort.
- [ ] TC-003-GEMINI Test-Expectation blockiert echte Zustimmung, erlaubt aber harmloses Hilfsangebot.
- [ ] TestSpec `documentation/TEST_SPEC/01_capability_overview_and_help.md` ist aktualisiert.
- [ ] Neuer TestPlan wird generiert und validiert.
- [ ] Neuer TestRun zeigt keine False-Positive-Fails fuer INT-002 und TC-003 wegen zu enger Oracle-Woerter.

## 8. Evidence
- documentation/test-results/TEST-RUN-2026-05-15-004_results.json
- documentation/test-results/TEST-RUN-2026-05-15-004/INT-002-GPT_evidence.json
- documentation/test-results/TEST-RUN-2026-05-15-004/INT-002-GEMINI_evidence.json
- documentation/test-results/TEST-RUN-2026-05-15-004/TC-003-GEMINI_evidence.json

## 9. Risks
- Zu lockere Expectations koennten echte Capability- oder Security-Regressionen verstecken.
- Oracle-Aenderungen muessen Produktverhalten bewerten, nicht nur Token-Matches entfernen.

## 10. Validation Mapping
- INT-002 semantische Capability-Overview -> aktualisierte TestSpec-Expectation
- TC-003 klare Ablehnung ohne direkte Ausfuehrungszusage -> aktualisierte `mustNotContain`/Ablehnungs-Erwartung
- Neue Erwartungen -> TestPlan-Generator + Validator + Live-Retest

## 12.1 BLOCKING QUESTIONS
Keine blockierenden Fragen offen.

## NEXT STEP

```text
@[/SKILL 1 - SPEC TO TASK COMPILER]
Spec: documentation/Planned Features/backlog_BACKLOG-042_test_oracle_too_narrow.md
Backlog Item: BACKLOG-042
```
