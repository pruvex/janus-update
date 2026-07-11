TASK-SPEC21
- Source Spec: documentation/SPEC/Spec Done/21_assisted_or_workhorse_mode_for_janus_skills.md
- Backlog Item: N/A
- Feature: Assistierter OR-Arbeitspferd-Modus fuer Janus-Skills
- Generated At: 2026-06-26T00:00:00Z

## Generated Tasks

### TASK-SPEC21.1 Implement Eligibility and Redaction Gate for OR Mode
- Ziel: Establish safety boundaries determining when a bounded task qualifies for OpenRouter workhorse mode versus local Codex execution, ensuring sensitive data is redacted before transmission
- Scope: Define eligibility criteria for OR path activation, implement input sanitization and redaction layer, create validation checkpoint that restricts OR access to approved bounded contexts only
- Files:
  - janus/gates/eligibility.py
  - janus/gates/redaction.py
  - config/or_eligibility.yaml
  - janus/security/boundary_validator.py
- Steps:
  - Implement boundedness criteria validator to identify eligible tasks
  - Build redaction engine for sensitive data before OR transmission
  - Create eligibility decision tree with reason codes
  - Integrate validation checkpoint into task initiation flow
  - Add logging for eligibility decisions
- Acceptance Criteria:
  - Only tasks from janus-debug and janus-test-pipeline can pass eligibility gate
  - Sensitive data (API keys, PII) is automatically redacted before OR transmission
  - Eligibility check returns boolean with explicit reason code for rejection
  - Non-bounded tasks are automatically routed to Codex path
  - Redaction is irreversible and logged for audit
- Tests:
  - Unit test: Eligibility passes for approved skills only
  - Unit test: Redaction removes all sensitive patterns
  - Integration test: Blocked skills cannot trigger OR gate
  - Security test: Verify redaction cannot be bypassed
- Model: 5.4
- Reason: Safety boundary must be established first to prevent unauthorized OR usage and data leakage

### TASK-SPEC21.2 Build Operator Choice Gate with Cost and Confidence Display
- Ziel: Create normalized interaction layer presenting clear Codex vs OR choice with predictive cost estimates and confidence metrics before execution commitment
- Scope: Implement the selection interface (1=Codex, 2=OR), cost prediction display, confidence scoring visualization, and operator input handling
- Files:
  - janus/gates/operator_choice.py
  - janus/ui/cost_display.py
  - janus/models/confidence_scorer.py
  - janus/interfaces/selection_prompt.py
- Steps:
  - Implement binary choice prompt with clear 1/2 mapping
  - Integrate cost prediction API for OR path estimation
  - Add confidence scoring algorithm for both execution paths
  - Build input validation and retry logic for invalid selections
  - Ensure display appears only after eligibility confirmation
- Acceptance Criteria:
  - Operator sees explicit '1 = Codex / 2 = OR-Arbeitspferd' choice
  - Predicted cost displayed prominently before OR selection
  - Confidence score visible for both Codex and OR paths
  - Invalid inputs trigger retry without crashing workflow
  - Choice gate blocks execution until operator confirms
- Tests:
  - UI test: Verify correct display of 1/2 options
  - Accuracy test: Cost prediction within 20% of actual
  - Validation test: Reject invalid inputs (0, 3, text)
  - Integration test: Gate appears only for eligible tasks
- Model: 5.4
- Reason: Central decision point requiring transparent cost disclosure and clear UX to prevent accidental expensive OR invocations

### TASK-SPEC21.3 Implement Telemetry, Cost Capture and Fallback Handling
- Ziel: Capture actual OpenRouter costs, execution health metrics, and telemetry post-run, with automatic fallback to manual review on OR gate failures
- Scope: Build telemetry pipeline for OR executions, actual cost tracking, healthcheck validation, failure detection, and fallback workflow activation
- Files:
  - janus/telemetry/or_tracker.py
  - janus/health/cost_validator.py
  - janus/logging/or_audit.py
  - janus/fallback/manual_review.py
- Steps:
  - Implement OR API response parser for actual cost extraction
  - Create telemetry storage schema for bounded OR steps
  - Build healthcheck validator for OR response integrity
  - Implement fallback trigger for failed OR gates
  - Add manual review queue for fallback cases
  - Create post-run cost display component
- Acceptance Criteria:
  - Actual OR cost captured and displayed to operator after run completion
  - Health check validates response integrity and boundedness
  - Telemetry includes latency, token usage, and error codes
  - Failed OR gates automatically trigger fallback to manual review
  - Exactly one bounded OR step is tracked per invocation
  - Fallback workflow preserves context for human operator
- Tests:
  - Integration test: Accurate cost capture from OR API
  - Health test: Detect corrupted or unbounded responses
  - Fallback test: Verify manual review trigger on failure
  - Telemetry test: Complete data capture and storage
  - End-to-end test: Single step enforcement
- Model: 5.4
- Reason: Required for financial auditing, operational monitoring, and ensuring system resilience through fallback mechanisms

### TASK-SPEC21.4 Integrate OR Mode into Approved Skills with Boundary Enforcement
- Ziel: Wire the OR workhorse capability into janus-debug and janus-test-pipeline skills while enforcing strict boundaries to prevent scope widening to other skills
- Scope: Modify approved skills to invoke OR gate, implement skill boundary enforcement ensuring no other janus skills can access OR mode, maintain default Codex path
- Files:
  - skills/janus-debug/or_integration.py
  - skills/janus-test-pipeline/or_integration.py
  - janus/router/skill_boundary.py
  - janus/config/skill_whitelist.yaml
- Steps:
  - Add OR gate invocation points to janus-debug bounded steps
  - Add OR gate invocation points to janus-test-pipeline bounded steps
  - Implement whitelist enforcement at router level
  - Add boundary violation alerts and blocking
  - Ensure Codex remains default path unless OR explicitly chosen
  - Validate no other skills can import or invoke OR modules
- Acceptance Criteria:
  - janus-debug presents OR option for eligible bounded tasks
  - janus-test-pipeline presents OR option for eligible bounded tasks
  - janus-spec-to-task and other skills cannot access OR mode
  - Boundary violation attempts are logged and blocked
  - Integration maintains existing Codex behavior as default
  - No code paths allow OR invocation outside approved skills
- Tests:
  - Integration test: janus-debug full OR workflow
  - Integration test: janus-test-pipeline full OR workflow
  - Security test: Verify other skills blocked at import and runtime
  - Regression test: Codex path unchanged when OR not selected
  - Boundary test: Attempted bypass detection
- Model: 5.4
- Reason: Final integration ensuring the feature remains constrained to approved skills only, preventing scope creep and unauthorized usage

@janus-task-breakdown
Spec: documentation/SPEC/Spec Done/21_assisted_or_workhorse_mode_for_janus_skills.md
Task: documentation/tasks/TASK-SPEC21_assisted_or_workhorse_mode_for_janus_skills.md
Backlog Item: N/A
Target Task: TASK-SPEC21.1
Mode: TASK_REFINEMENT
Execution Model: 5.4
Rules: USE_SPEC_AND_TASK_AS_SOURCE_OF_TRUTH_NO_IMPLEMENTATION_RELEASE_ONE_TARGET_TASK
Expected Output: TASK_REFINED_PLUS_PRECHECK_HANDOFF
