TASK-SPEC21
- Source Spec: documentation/SPEC/Spec Done/21_assisted_or_workhorse_mode_for_janus_skills.md
- Backlog Item: N/A
- Feature: Assistierter OR-Arbeitspferd-Modus fuer Janus-Skills
- Generated At: 2026-06-26T12:00:00Z

## Generated Tasks

### TASK-SPEC21.1 Implement Eligibility Redaction Gate Logic
- Ziel: Ensure bounded eligibility checks before OR delegation
- Scope: Define eligibility criteria and redaction rules for OR worker
- Files:
  - documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py
  - documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
  - documentation/codex/model-routing/scripts/codex_structured_action_request_builder.py
  - documentation/codex/model-routing/tests/
- Steps:
  - Define eligibility rules for bounded OR step
  - Implement redaction logic for sensitive data
  - Integrate eligibility check with dispatcher
- Acceptance Criteria:
  - Eligibility check passes before OR call
  - Redaction applied to sensitive data
  - Visible 1 = Codex / 2 = OR-Arbeitspferd gate
- Tests:
  - tests for eligibility logic
  - tests for redaction output
  - tests for dispatcher integration
- Model: 5.4
- Reason: Required for bounded OR step enforcement

### TASK-SPEC21.2 Normalize Operator Gate Prompts
- Ziel: Standardize prompts for Janus skills (debug/test-pipeline)
- Scope: Adjust prompt templates for operator gate normalization
- Files:
  - documentation/codex/model-routing/scripts/bounded_or_worker_gate_prompt.py
  - documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
  - documentation/codex/skills/janus-debug/SKILL.md
  - documentation/codex/skills/janus-test-pipeline/SKILL.md
  - documentation/codex/model-routing/tests/
- Steps:
  - Review prompt templates for operator gate
  - Normalize operator instructions for Janus skills
  - Update skill SKILL.md references
- Acceptance Criteria:
  - Prompts align with Janus skills
  - No scope widening in prompts
  - Fallback or manual review on failed OR gates
- Tests:
  - tests for prompt generation
  - tests for skill compatibility
  - tests for gate normalization
- Model: 5.4
- Reason: Ensures consistent operator behavior

### TASK-SPEC21.3 Capture Telemetry and Health Check Data
- Ziel: Record OR cost and health status during execution
- Scope: Implement health snapshot capture and cost visibility
- Files:
  - documentation/codex/model-routing/scripts/or_file_first_capture_wrapper.ps1
  - documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
  - documentation/codex/model-routing/scripts/bounded_or_worker_outcome.py
  - documentation/codex/skills/janus-health-check/scripts/health_snapshot.py
  - documentation/codex/model-routing/tests/
- Steps:
  - Integrate health_snapshot.py for telemetry
  - Capture OR cost metrics during run
  - Log health status for visibility
- Acceptance Criteria:
  - Cost visible after run
  - Health snapshot captured
  - Cost and confidence display before choice
- Tests:
  - tests for health capture
  - tests for cost logging
  - tests for telemetry wrapper
- Model: 5.4
- Reason: Supports DoD focus on cost and confidence display

### TASK-SPEC21.4 Integrate Consumer Without Scope Widening
- Ziel: Connect consumer logic to Janus-debug and janus-test-pipeline only
- Scope: Implement consumer integration runners
- Files:
  - documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py
  - documentation/codex/model-routing/scripts/codex_test_result_triage_review_runner.py
  - documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
  - documentation/codex/skills/janus-debug/SKILL.md
  - documentation/codex/skills/janus-test-pipeline/SKILL.md
  - documentation/codex/model-routing/tests/
- Steps:
  - Configure debug hypothesis review runner
  - Configure test result triage review runner
  - Verify scope boundaries for consumer integration
- Acceptance Criteria:
  - No OR path outside allowed skills
  - Consumer integration functional
  - Exactly one bounded OR step
- Tests:
  - tests for consumer integration
  - tests for scope boundaries
  - tests for runner configuration
- Model: 5.4
- Reason: Enforces bounded skill context

@janus-task-breakdown
Spec: documentation/SPEC/Spec Done/21_assisted_or_workhorse_mode_for_janus_skills.md
Task: documentation/tasks/TASK-SPEC21_assisted_or_workhorse_mode_for_janus_skills.md
Backlog Item: N/A
Target Task: TASK-SPEC21.1
Mode: TASK_REFINEMENT
Execution Model: 5.4
Rules: USE_SPEC_AND_TASK_AS_SOURCE_OF_TRUTH_NO_IMPLEMENTATION_RELEASE_ONE_TARGET_TASK
Expected Output: TASK_REFINED_PLUS_PRECHECK_HANDOFF
