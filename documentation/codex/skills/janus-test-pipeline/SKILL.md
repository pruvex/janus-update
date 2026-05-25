---
name: janus-test-pipeline
description: Route Janus TestSpec, TestPlan, TestRun, live execution, finding triage, and retest audit work through the deterministic Diamond test pipeline. Use when the user asks to compile testspecs, prepare or validate test runs, run live Janus tests, triage test findings, or decide retest/release readiness from test evidence.
---

# Janus Test Pipeline

## Purpose

Use this skill for Janus testing work that starts from `documentation/TEST_SPEC/`, `documentation/test-runs/`, or `documentation/test-results/`.

This skill replaces the old five-stage Test Skill pipeline with one Codex-native router. Keep the pipeline deterministic, evidence-first, and bounded. Do not implement product changes in this skill.

## Hard Rules

- Work on exactly one TestSpec, TestPlan, TestRun, or TestResult set at a time.
- Prefer repository generator scripts over hand-written test artifacts.
- Treat `documentation/test-results/<TEST_RUN_ID>_results.json` as the primary evidence for triage and retest audit.
- Do not patch generated plans, generated runners, or result JSON by hand to make a gate pass.
- Do not implement application fixes here. Route implementation findings to Backlog or `janus-debug`.
- Infrastructure, auth, provider outage, missing credentials, or broken test harness issues are blockers, not product findings.
- Before live external/provider execution, present the preflight evidence and wait for explicit user approval: `OK START LIVE TEST`.
- Use `janus-git-governance` before committing, pushing, tagging, or release branching.

## Mode Router

Choose the smallest mode that matches the user request:

| User intent | Mode | Output |
| --- | --- | --- |
| "Build tests from this TestSpec" | `TESTSPEC_TO_TEST_PLAN` | Validated TestPlan and next precheck handoff |
| "Prepare this TestRun" | `TEST_RUN_PRECHECK` | PASS/BLOCKED precheck and generated runner |
| "Run the live test" | `LIVE_TEST_EXECUTION` | Live execution evidence and result artifacts |
| "What do these failures mean?" | `FINDING_TRIAGE` | Finding classification, Backlog routing, dashboard sync needs |
| "Is this ready after retest?" | `DIAMOND_RETEST_AUDIT` | PASS/PASS WITH FIXES/BLOCKED release-readiness audit |

## Mode: TESTSPEC_TO_TEST_PLAN

Inputs:

- One TestSpec path under `documentation/TEST_SPEC/`.
- Optional target `TEST_RUN_ID`.

Process:

1. Read only the selected TestSpec and nearby registry context needed to identify the feature.
2. Compile with the deterministic compiler:

```powershell
node tests/e2e/generator/compile-testspec-to-testplan.mjs --spec <TestSpec>
```

3. Validate the generated plan if the compiler did not already do so:

```powershell
node tests/e2e/generator/validate-test-plan.mjs --plan <TestPlan>
```

4. Report generated paths, scope, provider/model expectations, and blockers.
5. Handoff to `TEST_RUN_PRECHECK`.

Do not create an alternate manual plan unless the compiler is unavailable or clearly broken. If that happens, stop and route to `janus-debug`.

## Mode: TEST_RUN_PRECHECK

Inputs:

- One TestPlan JSON path.
- Matching TestSpec path if available.
- Target `TEST_RUN_ID`.

Process:

1. Validate the TestPlan:

```powershell
node tests/e2e/generator/validate-test-plan.mjs --plan <TestPlan>
```

2. Generate the live runner:

```powershell
node tests/e2e/generator/generate-live-runner.mjs --plan <TestPlan> --out documentation/test-runs/<TEST_RUN_ID>_generated.spec.js
```

3. Confirm prerequisites:

- providers and keys required by the plan
- app/server startup requirements
- Playwright availability
- result output paths
- no unrelated product edits required

4. Output `PASS`, `PASS WITH WARNINGS`, or `BLOCKED`.

If precheck passes and live external calls are involved, ask the user for `OK START LIVE TEST`.

## Mode: LIVE_TEST_EXECUTION

Inputs:

- TestSpec path.
- TestPlan path.
- Generated runner path.
- Approved `TEST_RUN_ID`.

Process:

1. Run deterministic preflight first:

```powershell
node tests/e2e/generator/test-skill3-preflight.mjs --spec <TestSpec> --plan <TestPlan> --run <TEST_RUN_ID>
```

2. If the preflight is not `READY`, stop and classify the blocker.
3. After explicit user approval, run the generated Playwright test:

```powershell
npx playwright test <Runner> --headed --workers=1 --reporter=list
```

4. Preserve raw terminal evidence in the response summary.
5. Verify result files exist and validate them with this skill's helper script when useful:

```powershell
python C:\Users\pruve\.codex\skills\janus-test-pipeline\scripts\validate_test_pipeline_artifacts.py --plan <TestPlan> --result <TestResultJson>
```

Never use PowerShell `curl` aliases for provider checks. Prefer repository scripts or explicit `Invoke-WebRequest` only if the repo has no dedicated helper.

## Mode: FINDING_TRIAGE

Inputs:

- One TestResult JSON path.
- Related TestPlan and TestSpec if available.
- Existing Backlog path.

Process:

1. Validate or plausibilize `TestResultJson` against repository schema and this skill's helper script.
2. Classify each failure:

- `PRODUCT_BUG`
- `SPEC_GAP`
- `TEST_BUG`
- `INFRA_BLOCKER`
- `PROVIDER_BLOCKER`
- `AUTH_BLOCKER`
- `DUPLICATE`
- `NOT_REPRODUCIBLE`

3. For real product/spec/test findings, create or update Backlog items through `janus-backlog-intake`.
4. Use the next Backlog ID only after reading the full current Backlog.
5. Preserve links to TestRun, result JSON, screenshots, logs, and reproduction steps.
6. Mark dashboard sync/documentation update needs explicitly.

Do not implement fixes in this mode.

## Mode: DIAMOND_RETEST_AUDIT

Inputs:

- Retest TestResult JSON.
- Related original finding/Backlog/Spec context.
- Any Final Audit or Debug evidence being closed.

Process:

1. Validate result JSON and compare expected vs actual coverage.
2. Check:

- all required tests executed
- pass/fail/blocker counts are coherent
- security/privacy regressions absent
- provider/model coverage is sufficient for the tested claim
- unresolved blockers are documented
- Backlog and dashboard state can be updated safely

3. Decide:

- `PASS`: evidence is complete and release/documentation update may proceed.
- `PASS WITH FIXES`: only documentation, metadata, or low-risk cleanup remains.
- `BLOCKED`: behavior, evidence, security, infra, or coverage gap remains.

4. Route:

- `PASS` -> `janus-final-audit` or `janus-documentation-update`.
- `PASS WITH FIXES` -> `janus-documentation-update` for non-code cleanup.
- `BLOCKED` -> `janus-debug` or Backlog intake.

## Model And Context Guidance

- Use `5.4 mini` for TestPlan validation, artifact checks, and routine triage.
- Use `5.3 codex` for Playwright execution, local debugging, and script-level investigation.
- Use `5.4` for ambiguous failures, product/spec classification, and retest audit.
- Use `5.5` only for security-sensitive release blockers, provider trust boundaries, or complex audit disputes.
- Start a new chat when entering `LIVE_TEST_EXECUTION` or `DIAMOND_RETEST_AUDIT` with large prior context; bind only TestSpec, TestPlan, TestResult, and current Backlog entries.

## Required Response Shape

For every mode, respond with:

- `Mode`
- `Bound artifacts`
- `Decision`
- `Evidence`
- `Next skill`
- `Model recommendation`

Keep summaries short and point to file paths instead of pasting large artifacts.
