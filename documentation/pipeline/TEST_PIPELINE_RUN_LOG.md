# Janus Test Pipeline Run Log

Zweck: Dieses Log sammelt kompakte, auswertbare Beobachtungen aus echten Janus Test-&-Optimierungs-Pipeline-Runs. Es ersetzt nicht `SESSION_LOG.md`, Backlog, TestSpec-Artefakte oder Dashboard-Telemetrie. Es dient dazu, nach mehreren vollstaendigen TestRuns wiederkehrende Fehler, Reibungspunkte und Optimierungspotential in TestSkill-Routen, Handoffs, Security-/Privacy-/Prompt-Injection-Gates und Dashboard-Feldern zu erkennen. Es laeuft parallel zum Feature-Pipeline-Log `documentation/pipeline/PIPELINE_RUN_LOG.md` und darf nicht mit diesem vermischt werden.

## Nutzungsregel

- **Eintrag pro TestRun**: Ein TestRun ist ein abgeschlossener oder klar abgebrochener Test-Durchlauf durch die TestSkill-Route TEST SKILL 1 -> TEST SKILL 2 -> TEST SKILL 3 -> TEST SKILL 4 -> TEST SKILL 5.
- **Kurz halten**: Bei sauberem Verlauf reicht ein kompakter Eintrag.
- **Nur beobachtete Fakten**: Keine Vermutungen als Fakten eintragen.
- **Optimierungen sammeln, nicht sofort umbauen**: TestPipeline-Aenderungen erst nach Auswertung mehrerer Runs beschliessen.
- **Security/Privacy/Prompt-Injection immer dokumentieren**: Auch bei PASS muessen die Gates explizit aufgefuehrt werden.
- **Nebenbefunde außerhalb TestScope immer erfassen**: Seitliche Findings duerfen nicht unter den Tisch fallen.

## Run-Template

```md
### TEST-RUN-YYYY-MM-DD-XXX – <CAPABILITY_NAME> – <Titel>

- **TestRun-ID**: TEST-RUN-YYYY-MM-DD-XXX
- **Datum**: YYYY-MM-DD
- **Quelle**: TestSpec | Backlog | Regression | Manuell | Sonstiges
- **Artefakte**: TestSpec, TestPlan, TestResult, Backlog-IDs
- **Getestete Faehigkeit**: <Capability-Name>
- **Pipeline-Route**: <z. B. TEST SKILL 1 -> TEST SKILL 2 -> TEST SKILL 3 -> TEST SKILL 4 -> TEST SKILL 5 -> SKILL 7>
- **Skill-Ergebnisse**:
  - TEST SKILL 1: PASS | BLOCKED | N/A
  - TEST SKILL 2: PASS | BLOCKED | N/A
  - TEST SKILL 3: PASS | PARTIAL | BLOCKED | N/A
  - TEST SKILL 4: PASS | PARTIAL | BLOCKED | N/A
  - TEST SKILL 5: PASS | PASS WITH FOLLOW-UP | RETEST REQUIRED | BLOCKED | N/A
  - SKILL 7: PASS | BLOCKED | N/A
- **Security Gate**:
  - Userdaten sicher: JA | NEIN | UNKLAR
  - Destruktive Aktionen isoliert: JA | NEIN | N/A
  - Prompt-Injection-Risiko geprueft: JA | NEIN
  - Prompt-Injection-Befund: NONE | LOW | MEDIUM | HIGH | CRITICAL
  - Sensitive Daten in Logs vermieden: JA | NEIN | UNKLAR
  - Persistenzrisiko geprueft: JA | NEIN | N/A
  - Security-Gesamtergebnis: PASS | PASS WITH WATCHPOINTS | BLOCKED
- **Provider-/Model-Matrix**:
  - GPT Smallest Viable: <Modell> – <Ergebnis>
  - GPT Default/Quality, falls noetig: <Modell> – <Ergebnis>
  - Gemini Smallest Viable: <Modell> – <Ergebnis>
  - Gemini Default/Quality, falls noetig: <Modell> – <Ergebnis>
  - GPT-5.5 nur falls Eskalation: <Modell> – <Ergebnis>
- **UX-Ergebnis**: <kurz>
- **Intent-/Skill-Routing-Ergebnis**: <kurz>
- **Kosten-/Token-Ergebnis**: <Tokenanzahl / Kosten / Einsparung>
- **Capability-Erklaerfaehigkeit**: PASS | PARTIAL | FAIL | N/A
- **Findings**:
  - <Liste konkreter Befunde>
- **Sofortfixes**:
  - <Liste oder "Keine">
- **Backlog-Follow-ups**:
  - <BACKLOG-IDs oder "Keine">
- **Nebenbefunde ausserhalb TestScope**:
  - <Liste oder "Keine">
- **Optimierungspotential fuer Testpipeline**:
  - <Liste oder "Keine">
- **Abschluss**:
  - Diamond Confidence Score: x/10
  - Production Confidence: y%
  - Gesamtergebnis: PASS | PASS WITH FOLLOW-UP | RETEST REQUIRED | BLOCKED | ABGEBROCHEN
```

## Run Log

### TEST-RUN-YYYY-MM-DD-001 – Beispiel – Sauberer Test-Durchlauf

- **TestRun-ID**: TEST-RUN-YYYY-MM-DD-001
- **Datum**: YYYY-MM-DD
- **Quelle**: TestSpec
- **Artefakte**: `documentation/prompts/<TESTSPEC>.md`, `documentation/test-runs/<PLAN>.md`, `documentation/test-results/<RESULTS>.md`
- **Getestete Faehigkeit**: <Capability-Name>
- **Pipeline-Route**: TEST SKILL 1 -> TEST SKILL 2 -> TEST SKILL 3 -> TEST SKILL 4 -> TEST SKILL 5 -> SKILL 7
- **Skill-Ergebnisse**:
  - TEST SKILL 1: PASS
  - TEST SKILL 2: PASS
  - TEST SKILL 3: PASS
  - TEST SKILL 4: PASS
  - TEST SKILL 5: PASS
  - SKILL 7: N/A
- **Security Gate**:
  - Userdaten sicher: JA
  - Destruktive Aktionen isoliert: JA
  - Prompt-Injection-Risiko geprueft: JA
  - Prompt-Injection-Befund: NONE
  - Sensitive Daten in Logs vermieden: JA
  - Persistenzrisiko geprueft: N/A
  - Security-Gesamtergebnis: PASS
- **Provider-/Model-Matrix**:
  - GPT Smallest Viable: gpt-5.4-nano – PASS
  - GPT Default/Quality, falls noetig: N/A
  - Gemini Smallest Viable: gemini-2.0-flash – PASS
  - Gemini Default/Quality, falls noetig: N/A
  - GPT-5.5 nur falls Eskalation: N/A
- **UX-Ergebnis**: Erwartungskonform
- **Intent-/Skill-Routing-Ergebnis**: Korrekt geroutet
- **Kosten-/Token-Ergebnis**: <Tokenanzahl / Kosten / Einsparung>
- **Capability-Erklaerfaehigkeit**: PASS
- **Findings**:
  - Keine
- **Sofortfixes**:
  - Keine
- **Backlog-Follow-ups**:
  - Keine
- **Nebenbefunde ausserhalb TestScope**:
  - Keine
- **Optimierungspotential fuer Testpipeline**:
  - Keine
- **Abschluss**:
  - Diamond Confidence Score: 9/10
  - Production Confidence: 95%
  - Gesamtergebnis: PASS

### TEST-RUN-2026-05-11-005 – Intent Recognition & Tool Routing Engine – SSE-Stream Rendering Fix

- **TestRun-ID**: TEST-RUN-2026-05-11-005-RETEST-003
- **Datum**: 2026-05-12
- **Quelle**: TestSpec
- **Artefakte**: `documentation/TEST_SPEC/REVIEW EXECUTION ROUTING.md`, `documentation/test-runs/TEST-RUN-2026-05-11-005_plan.md`, `documentation/test-runs/TEST-RUN-2026-05-11-005_plan.json`, `documentation/test-results/TEST-RUN-2026-05-11-005-RETEST-003_results.md`
- **Getestete Faehigkeit**: Intent Recognition & Tool Routing Engine
- **Pipeline-Route**: TEST SKILL 1 -> TEST SKILL 2 -> TEST SKILL 3 -> TEST SKILL 4 -> TEST SKILL 5 -> SKILL 7
- **Skill-Ergebnisse**:
  - TEST SKILL 1: PASS
  - TEST SKILL 2: PASS
  - TEST SKILL 3: PASS (nach Bugfix)
  - TEST SKILL 4: PASS
  - TEST SKILL 5: PARTIAL (nur TC-001 verifiziert)
  - SKILL 7: N/A
- **Security Gate**:
  - Userdaten sicher: JA
  - Destruktive Aktionen isoliert: JA
  - Prompt-Injection-Risiko geprueft: N/A (Security-Tests nicht ausgeführt)
  - Prompt-Injection-Befund: N/A
  - Sensitive Daten in Logs vermieden: JA
  - Persistenzrisiko geprueft: N/A
  - Security-Gesamtergebnis: PASS (für ausgeführte Tests)
- **Provider-/Model-Matrix**:
  - GPT Smallest Viable: gpt-5.4-nano – PASS (TC-001)
  - GPT Default/Quality, falls noetig: N/A
  - Gemini Smallest Viable: gemini-3-flash-preview – NOT_RUN
  - Gemini Default/Quality, falls noetig: N/A
  - GPT-5.5 nur falls Eskalation: N/A
- **UX-Ergebnis**: SSE-Stream rendering erfolgreich mit reanchor-Logik
- **Intent-/Skill-Routing-Ergebnis**: Weather-Intent korrekt erkannt und geroutet
- **Kosten-/Token-Ergebnis**: OpenAI API Cost 0.002000€ für gpt-5.4-nano (conversation)
- **Capability-Erklaerfaehigkeit**: PASS (für TC-001)
- **Findings**:
  - RESOLVED: Ghost-Bubble-Bug (DOM Wipe während SSE-Stream) – reanchor-Logik in chat.js implementiert
  - RESOLVED: Race-Condition in Test-Strategy – Promise.all Pattern in generate-live-runner.mjs
  - RESOLVED: Button-Overlay Interference – DOM-Level click() via evaluate()
- **Sofortfixes**:
  - chat.js: reanchorBubbleIfDetached() Funktion für DOM-Resilience
  - generate-live-runner.mjs: Promise.all race-free send, pressSequentially, enhanced diagnostics
  - strategy-registry.json: chat_button_click_send_v1 Beschreibung aktualisiert
- **Backlog-Follow-ups**:
  - Keine
- **Nebenbefunde ausserhalb TestScope**:
  - Keine
- **Optimierungspotential fuer Testpipeline**:
  - Vollständiger Testlauf aller 17 Testfälle erforderlich für Diamond-Zertifizierung
  - Gemini-Provider muss getestet werden
  - Security-Tests (SEC-001, PINJ-001) müssen ausgeführt werden
- **Abschluss**:
  - Diamond Confidence Score: 3.9/10
  - Production Confidence: 39%
  - Gesamtergebnis: PARTIAL (nur TC-001 verifiziert, unzureichende Coverage)

## Auswertungsbereich

Dieser Bereich wird nach mehreren echten TestRuns gepflegt, z. B. nach 5-10 Runs oder nach einigen Arbeitstagen.

### Beobachtete Muster

- Noch keine Auswertung.

### Haeufige Blocker

- Noch keine Auswertung.

### Security-/Privacy-Muster

- Noch keine Auswertung.

### Prompt-Injection-Muster

- Noch keine Auswertung.

### Provider-/Model-Stabilitaet

- Noch keine Auswertung.

### Kosten-/Token-Muster

- Noch keine Auswertung.

### Skill-Handoff-Qualitaet

- Noch keine Auswertung.

### Dashboard-/Backlog-Routing-Qualitaet

- Noch keine Auswertung.

### Beschlossene Optimierungen

- Noch keine Beschluesse.

### Offene Optimierungsideen

- Noch keine Ideen.
