# BACKLOG-085 - Spec 06 Evidence Honesty Oracle Refinement

## 1. Context
- **Source TestRun:** TEST-RUN-2026-05-19-008
- **TestSpec:** documentation/TEST_SPEC/02_security_safety/06_ai_prompt_injection_tool_abuse_and_data_exfiltration.md
- **Affected TestCases:** TC-008-GPT, TC-008-GEMINI
- **Category:** TestPlan Oracle / Evidence Honesty Pattern
- **Routing:** DO NOW
- **Source:** BACKLOG-081 Execution (Oracle-Mismatch Finding)

## 2. Problem
BACKLOG-081 analysis revealed that TC-008-GPT and TC-008-GEMINI failures are due to oracle mismatch, not product behavior. Both provider responses show correct evidence-honesty behavior (refusal without evidence), but test expectations do not match this correct behavior.

No sensitive prompt/payload content is copied into this handoff. Only TestCase IDs and neutral pattern descriptions are used.

## 3. Scope
### In Scope
- Review TestPlan expectations for TC-008-GPT and TC-008-GEMINI
- Update expected patterns to match correct evidence-honesty behavior
- Ensure expectations align with product behavior (refusal without evidence)
- Focused retest to validate updated expectations

### Out Of Scope
- Product code changes (product behavior is correct)
- Copying sensitive prompts or payloads into docs/chat
- Changing unrelated TestSpec cases

## 4. Acceptance Criteria
- TC-008-GPT passes with updated expectations
- TC-008-GEMINI passes with updated expectations
- Expectations match correct evidence-honesty behavior
- No sensitive payload text added to documentation

## 5. Artifacts
- TestResultJson: documentation/test-results/TEST-RUN-2026-05-19-008_results.json
- TestPlan: documentation/test-runs/TEST-RUN-2026-05-19-008_plan.json
- Source TestSpec: documentation/TEST_SPEC/02_security_safety/06_ai_prompt_injection_tool_abuse_and_data_exfiltration.md
- BACKLOG-081 Execution Result: documentation/tasks/backlog_BACKLOG-081_ai_safety_evidence_honesty_boundary.md

## 6. Model
- **Assigned Model:** SWE 1.6
- **Reason:** TestPlan/TestSpec refinement for oracle mismatch with clear failing IDs and low implementation scope.
