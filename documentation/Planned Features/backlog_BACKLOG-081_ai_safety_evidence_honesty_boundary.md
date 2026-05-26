# BACKLOG-081 - AI Safety Evidence Honesty Boundary

## 1. Context
- **Source TestRun:** TEST-RUN-2026-05-19-008
- **TestSpec:** documentation/TEST_SPEC/02_security_safety/06_ai_prompt_injection_tool_abuse_and_data_exfiltration.md
- **Affected TestCases:** TC-008-GPT, TC-008-GEMINI
- **Category:** AI Safety behavior / evidence honesty
- **Routing:** DO NOW

## 2. Problem
Two provider variants fail the evidence-honesty boundary. The system must not claim evidence, execution, test success, or tool results without concrete current-turn evidence.

No sensitive prompt payloads are copied into this handoff. Use local evidence files only for analysis.

## 3. Scope
### In Scope
- Inspect result/evidence artifacts for TC-008-GPT and TC-008-GEMINI.
- Determine whether failure is product behavior, oracle mismatch, or both.
- If product behavior: harden evidence-honesty gating before final response.
- If oracle mismatch: route to TestPlan/TestSpec refinement instead of product change.
- Add focused automated checks for the corrected behavior.

### Out Of Scope
- Broad AI Safety refactor.
- Copying sensitive prompts or payloads into docs/chat.
- Changing unrelated TestSpec cases.

## 4. Acceptance Criteria
- TC-008-GPT passes in focused retest.
- TC-008-GEMINI passes in focused retest.
- No success/evidence claim is emitted without concrete evidence.
- No sensitive payload text is added to documentation.

## 5. Artifacts
- TestResultJson: documentation/test-results/TEST-RUN-2026-05-19-008_results.json
- TestPlan: documentation/test-runs/TEST-RUN-2026-05-19-008_plan.json
- Source TestSpec: documentation/TEST_SPEC/02_security_safety/06_ai_prompt_injection_tool_abuse_and_data_exfiltration.md

## 6. Model
- **Assigned Model:** SWE 1.6
- **Reason:** Focused safety-boundary fix with clear failing IDs and medium implementation scope.
