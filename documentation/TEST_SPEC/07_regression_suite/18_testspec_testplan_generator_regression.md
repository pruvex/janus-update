# JANUS TESTSPEC - DIAMANTSTANDARD v1.0

## TESTSPEC REVIEW EXECUTION ROUTING

target_skill: TEST_SKILL_1
execution_mode: SWE_1_6
complexity_score: 58
confidence: HIGH
dashboard_hint: PRIORITY
security_hint: LOW
reason: Regression covers repeated TestSpec-to-TestPlan oracle drift findings where updated clarification/source patterns were not transferred.

## TEST IDENTITY

- TestSpec Name: 18 TestSpec TestPlan Generator Regression
- Capability Name: Janus Test Pipeline Generator Regression
- Source Input: Regression suite planning; BACKLOG-058, BACKLOG-062, BACKLOG-063 and source-attribution generator fixes.
- Primary Test Goal: Ensure the TestPlan compiler preserves critical oracle semantics from TestSpec into TestPlan and generated runner.
- User Problem: A green or red test run is misleading when the generated TestPlan silently drops updated oracle terms.
- User Value: The skill pipeline remains trustworthy and avoids repeated manual TestPlan corrections.
- Suggested Save Path: documentation/TEST_SPEC/07_regression_suite/18_testspec_testplan_generator_regression.md
- Machine Result Schema: tests/e2e/generator/test-result.schema.json
- Required Result Markdown: documentation/test-results/<test_run_id>_results.md
- Required Result JSON: documentation/test-results/<test_run_id>_results.json

## TEST OBJECTIVE

Validate static pipeline behavior: TestSpec parsing, TestPlan expected-pattern transfer, must-not-contain preservation, clarification/refusal oracle transfer, source-attribution oracle transfer, parallelization metadata and runner generation.

## SCOPE

Generator/compiler static checks, validation schema, generated runner integrity, handover metadata and regression coverage for previously dropped patterns.

## OUT OF SCOPE

Live Janus behavior, provider answer quality, Playwright browser execution and product-code fixes.

## USER EXPERIENCE CONTRACT

- Success Behavior: A TestSpec change appears deterministically in TestPlan and runner artifacts.
- Failure Behavior: Generator blocks with a concrete reason instead of producing a misleading plan.
- Proactive Clarification Behavior: N/A for static generator checks.
- Cancel / Undo Behavior: N/A.
- User-Facing Explanation: Pipeline handover contains enough metadata for next skill execution.

## FUNCTIONAL TEST MATRIX

| TestCase-ID | Scenario | User Prompt / Action | Expected Result | Acceptance Criterion | Criticality |
|-------------|----------|----------------------|-----------------|----------------------|-------------|
| TC-001 | Clarification keywords transfer | Compile spec with clarification terms | TestPlan contains terms | containsAny includes clarification keywords | CRITICAL |
| TC-002 | Refusal keywords transfer | Compile spec with refusal expectations | TestPlan contains refusal terms | "kann nicht"/"nicht erlaubt" style terms preserved | HIGH |
| TC-003 | Source attribution transfer | Compile source-attribution spec | TestPlan contains source patterns | "Quelle"/source-specific patterns preserved | CRITICAL |
| TC-004 | mustNotContain preservation | Compile security spec with forbidden terms | TestPlan preserves forbidden patterns | mustNotContain not dropped | CRITICAL |
| TC-005 | Parallel metadata generation | Compile spec with mixed fit | TestPlan includes parallelization metadata | recommendedWorkers and per-test flags valid | HIGH |
| TC-006 | Runner generation | Generate runner from compiled plan | Runner compiles structurally | Generated file includes serial/parallel describe blocks where applicable | HIGH |

## PROVIDER AND MODEL TEST MATRIX

| Provider | Smallest Viable Model | Required | Quality Model Condition | GPT-5.5 Escalation Condition |
|----------|------------------------|----------|-------------------------|------------------------------|
| Static Generator | N/A | YES | N/A | N/A |
| GPT | N/A | NO | N/A | N/A |
| Gemini | N/A | NO | N/A | N/A |

## SECURITY / PRIVACY / PROMPT-INJECTION GATE

- User Data Involved: NO
- Destructive Operations Possible: NO
- External Content Involved: NO
- Prompt Injection Surface: LOW
- Persistence Involved: Generated test artifacts only
- Test Sandbox Required: YES
- Sensitive Logs Risk: LOW
- Allowed To Proceed: YES

## SECURITY TEST CASES

| SecurityCase-ID | Risk | Test Method | Expected Safe Behavior | Acceptance Criterion |
|-----------------|------|-------------|------------------------|----------------------|
| SEC-001 | Dropped forbidden oracle | Compile security spec | mustNotContain preserved | Forbidden terms remain in TestPlan |
| SEC-002 | Misleading PASS due oracle drift | Compare TestSpec/TestPlan patterns | Drift detected | Missing critical pattern blocks or fails validation |
| SEC-003 | Unsafe generated runner | Inspect generated runner | No destructive hardcoded real paths | Runner uses synthetic/test data only |

## PROMPT INJECTION TEST CASES

| InjectionCase-ID | Injection Surface | Malicious Input/Data | Expected Safe Behavior | Acceptance Criterion |
|------------------|-------------------|----------------------|------------------------|----------------------|
| PINJ-001 | TestSpec text | Prompt-injection terms in test cases | Treated as test data | Not executed by generator |
| PINJ-002 | Oracle text | Source/refusal keywords include hostile examples | Preserved as data | No generator instruction confusion |

## TEST DATA AND SANDBOX

- Test Data Required: Existing representative TestSpecs plus optional synthetic micro-spec fixture.
- Sandbox Required: YES
- Real User Data Allowed: NO
- Rollback / Recovery: Generated test-run artifacts may be deleted after validation if only used as scratch.
- Destructive Test Isolation: N/A.

## LOGGING AND TELEMETRY PRIVACY

- Required Evidence: Compiler command, TestPlan validation output, generated runner path, pattern transfer checks.
- Backend Log Evidence: N/A.
- Frontend Debug Evidence: N/A.
- Cost / Token Evidence: N/A; static test only.
- Sensitive Data Must Not Include: Real credentials or private chat transcripts.

## MACHINE-READABLE TEST RESULT CONTRACT

- TestResultJson Required: YES
- JSON Schema: tests/e2e/generator/test-result.schema.json
- Markdown Result Path: documentation/test-results/<test_run_id>_results.md
- JSON Result Path: documentation/test-results/<test_run_id>_results.json
- Dashboard Consumption: YES

## AUTOMATION STRATEGY

- Playwright Fit: LOW; live browser is not required.
- Static Generator Fit: HIGH.
- Schema Validation Fit: HIGH.
- Parallelization Fit: HIGH. Static generator checks can run in parallel if each uses a unique output run ID or fixture directory.
- Oracle Design: Exact structural assertions are appropriate for generated JSON fields; no LLM semantic judgment needed.

## ACCEPTANCE CRITERIA

- [x] Clarification keywords from TestSpec appear in generated TestPlan/fixture and generated runner source.
- [x] Refusal keywords from TestSpec appear in generated TestPlan/fixture and generated runner source.
- [x] Source attribution patterns are preserved.
- [x] mustNotContain arrays are preserved.
- [x] Parallelization metadata validates.
- [x] Generated runner is created and structurally valid.

## BLOCKING CONDITIONS

- [x] TestPlan compiler can run.
- [x] Validator schema is available.
- [x] Representative synthetic fixture exists for pattern transfer checks.

## LATEST PIPELINE VALIDATION

- **Latest TestRun**: TEST-RUN-2026-05-21-027
- **Status**: PASS
- **Pass Rate**: 100.00% (12/12)
- **Dashboard Status**: PASS, not partial
- **Generated Skill-1 Archive**: `documentation/test-runs/TEST-RUN-2026-05-21-026_plan.json`
- **Dashboard Plan**: `documentation/test-runs/TEST-RUN-2026-05-21-027_plan.json`
- **Result JSON**: `documentation/test-results/TEST-RUN-2026-05-21-027_results.json`
- **Result Markdown**: `documentation/test-results/TEST-RUN-2026-05-21-027_results.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-027_final_audit.md`
- **Validation Commands**:
  - `node tests\e2e\generator\generator.self-test.mjs` -> PASS.
  - `node tests/e2e/generator/compile-testspec-to-testplan.mjs --spec documentation/TEST_SPEC/07_regression_suite/18_testspec_testplan_generator_regression.md` -> TESTPLAN VALID, TEST-RUN-2026-05-21-026, 22 tests.
  - `node tests\e2e\generator\validate-runner.mjs --plan documentation\test-runs\TEST-RUN-2026-05-21-026_plan.json --runner documentation\test-runs\TEST-RUN-2026-05-21-026_generated.spec.js` -> VALIDATION PASSED.
  - `node --check documentation\test-runs\TEST-RUN-2026-05-21-026_generated.spec.js` -> PASS.
  - `python backend\tools\validate_skill_schemas.py` -> PASS, 54 skill JSON files.
- **Notes**: The generator self-test now includes synthetic oracle-transfer coverage for clarification, refusal, source attribution, `mustNotContain`, prompt-injection-as-data and mixed parallel/serial runner generation.

## INTERNAL TEST COMPLEXITY BREAKDOWN

Scope Size: 16 - Compiler, schema and runner artifacts.
Security Risk: 6 - Static test data only.
Provider Matrix Complexity: 0 - Provider-independent.
Live Test Complexity: 18 - Multiple artifacts, but no live app.
Ambiguity Level: 18 - Needs clear fixture expectations.
Total Complexity Score: 58
Routing Decision: SWE_1_6
Routing Confidence: HIGH
Dashboard Hint: PRIORITY
Security Hint: LOW
