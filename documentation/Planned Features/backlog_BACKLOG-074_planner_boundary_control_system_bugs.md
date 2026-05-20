# Planner Boundary Control System Bugs

## Problem Statement

Multiple System-Bugs in Planner Boundary Control (Spec 05) verhindern korrektes Verhalten bei der Intent-Routing-Entscheidung:

1. **Over-Caution Ambiguity Detection (INT-001)**: Vage Prompts wie "Erklaer kurz" lösen übermäßige Klärungsanfragen aus, obwohl TestSpec "NO clarification" erwartet.
2. **Memory Bleed/Context Bleed (SEC-003-GEMINI)**: "Simple factual prompt" ruft völlig unrelated Memory-Inhalte (Nikola Tesla Beschreibung) ab.
3. **Prompt Handling Bug (SEC-003-GPT)**: "Simple factual prompt" wird mit generischem Greeting statt Antwort behandelt.
4. **System Stability Issue (TC-004-GEMINI)**: Complex multi-step workspace tasks produzieren "keine stabile Antwort" Fehlermeldung statt Planner-Output.
5. **Test Runner Timeout (TC-007-GEMINI)**: Research tasks produzieren RUNNER_STREAM_TIMEOUT mit leerer Assistant Bubble.

## Expected Behavior

- **INT-001**: Vage Prompts wie "Erklaer kurz" geben direkte Antworten ohne Klärung, wenn TestSpec "NO clarification" erwartet.
- **SEC-003**: "Simple factual prompt" gibt direkte Antwort ohne unrelated memory retrieval oder generisches greeting.
- **TC-004**: Complex multi-step workspace tasks geben Planner oder explicit multi-step plan aus, keine "keine stabile Antwort" Fehlermeldung.
- **TC-007**: Test Runner produziert keine Timeout/leere Bubble Fehler für research tasks.

## Current Behavior

- **INT-001-GEMINI**: "Erklaer kurz" → "Welches Thema oder welcher Begriff soll erklärt werden?" (Klärung statt direkter Antwort)
- **INT-001-GPT**: "Erklaer kurz" → "Worum genau geht es..." (Klärung statt direkter Antwort)
- **SEC-003-GEMINI**: "Simple factual prompt" → Nikola Tesla Beschreibung aus unrelated memory (Context Bleed)
- **SEC-003-GPT**: "Simple factual prompt" → Generic greeting "Hallo Admin..." statt Antwort
- **TC-004-GEMINI**: Complex workspace task → "Ich konnte diesmal keine stabile Antwort erzeugen..."
- **TC-007-GEMINI**: Research task → RUNNER_STREAM_TIMEOUT mit leerer Assistant Bubble ("...")

## Scope

- Fix Ambiguity Detection Logic (Over-Caution bei vagen Prompts)
- Fix Memory Retrieval Logic (Context Bleed Prevention)
- Fix Prompt Handling Logic (Generic Greeting vs Direct Answer)
- Fix System Stability (Complex Task Error Handling)
- Fix Test Runner (Stream Timeout/Empty Bubble Handling)

## Functional Requirements

1. Ambiguity Detection soll TestSpec "Expected Clarification: NO" respektieren
2. Memory Retrieval soll nur relevante Inhalte zurückgeben, keine Context Bleed
3. Prompt Handling soll auf tatsächlichen Prompt reagieren, nicht generisches Greeting
4. Complex Tasks sollen stabilen Planner-Output oder Plan-Error ausgeben
5. Test Runner soll Stream-Timeouts robust handeln

## Acceptance Criteria

- [ ] INT-001 Tests pass (direkte Antwort ohne Klärung)
- [ ] SEC-003 Tests pass (direkte Antwort ohne unrelated memory/greeting)
- [ ] TC-004 Tests pass (Planner/Plan statt "keine stabile Antwort")
- [ ] TC-007 Tests pass (kein Runner Timeout/leere Bubble)
- [ ] Pass Rate ≥ 95% für Spec 05

## Evidence

- TestRun: TEST-RUN-2026-05-19-002
- Pass Rate: 81.25% (26/32 passed, 5 failed, 1 blocked)
- Provider Pass Rate: Gemini 75.00%, GPT 87.50%
- Evidence Files: documentation/test-results/TEST-RUN-2026-05-19-002/

## Risks

- Ambiguity Detection Fix könnte andere Tests beeinflussen
- Memory Retrieval Fix könnte Performance beeinflussen
- System Stability Fix könnte komplexe Tasks brechen

## Validation Mapping

- TestSpec: documentation/TEST_SPEC/01_core_system/05_planner_direct_execution_boundary.md
- TestPlan: documentation/test-runs/TEST-RUN-2026-05-19-002_plan.json
- TestResult: documentation/test-results/TEST-RUN-2026-05-19-002_results.json
