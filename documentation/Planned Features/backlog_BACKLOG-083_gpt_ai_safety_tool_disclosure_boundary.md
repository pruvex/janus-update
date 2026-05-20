# BACKLOG-083 - GPT AI Safety Tool Disclosure Boundary

## 1. Context
- **Source TestRun:** TEST-RUN-2026-05-19-008
- **TestSpec:** documentation/TEST_SPEC/02_security_safety/06_ai_prompt_injection_tool_abuse_and_data_exfiltration.md
- **Affected TestCases:** INT-001-GPT, TC-009-GPT
- **Category:** GPT safety behavior / tool disclosure control
- **Routing:** DO NOW

## 2. Problem
Two GPT-focused cases fail around AI-safety response boundaries and tool-disclosure control.

No sensitive prompt payloads are copied into this handoff. Use local evidence files only for analysis.

## 3. Scope
### In Scope
- Inspect result/evidence artifacts for INT-001-GPT and TC-009-GPT.
- Determine whether failures are product behavior, TestPlan oracle mismatch, or mixed.
- Harden refusal/clarification/tool-disclosure boundaries where product behavior is too permissive.
- Preserve normal capability-help and tool-routing behavior.

### Out Of Scope
- Broad prompt rewrite.
- Copying sensitive prompts or payloads into docs/chat.
- Changing Gemini behavior unless shared code requires it.

## 4. Acceptance Criteria
- INT-001-GPT passes in focused retest.
- TC-009-GPT passes in focused retest.
- Tool disclosure remains useful for normal capability-help but safe for restricted contexts.
- No sensitive payload text is added to documentation.

## 5. Artifacts
- TestResultJson: documentation/test-results/TEST-RUN-2026-05-19-008_results.json
- TestPlan: documentation/test-runs/TEST-RUN-2026-05-19-008_plan.json
- Source TestSpec: documentation/TEST_SPEC/02_security_safety/06_ai_prompt_injection_tool_abuse_and_data_exfiltration.md

## 6. Model
- **Assigned Model:** SWE 1.6
- **Reason:** Focused GPT safety-boundary work with medium risk and bounded test IDs.
