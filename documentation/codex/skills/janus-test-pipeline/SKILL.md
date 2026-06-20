---
name: janus-test-pipeline
description: Route Janus TestSpec, TestPlan, TestRun, live execution, finding triage, and retest audit work through the deterministic Diamond test pipeline. Use when the user asks to compile testspecs, prepare or validate test runs, run live Janus tests, triage test findings, or decide retest/release readiness from test evidence.
---

# Janus Test Pipeline

## Purpose

Use this skill for Janus testing work that starts from `documentation/TEST_SPEC/`, `documentation/test-runs/`, or `documentation/test-results/`.

This skill replaces the old five-stage Test Skill pipeline with one Codex-native router. Keep the pipeline deterministic, evidence-first, and bounded. Do not implement product changes in this skill.
This is primarily a Codex-led evidence skill. ChatGPT should take over only when evidence is unclear, risk is elevated, or an actor/chat boundary needs a compact routing handoff.

## Context Budget

Bind one `TEST_RUN_ID` or one TestSpec at a time and keep the evidence surface narrow.

Prefer:

- one TestSpec
- one TestPlan
- one generated runner
- one `TestResultJson`
- one related Backlog or audit marker only when the mode needs it

Do not reread broad test-run history when the current mode can be decided from the active `TEST_RUN_ID` bundle.

Keep these artifacts separate:

- TestSpec: source-of-truth intent and assertions under `documentation/TEST_SPEC/`
- TestPlan: compiled execution plan under `documentation/test-runs/`
- TestRun: one concrete `TEST_RUN_ID` bundle under `documentation/test-runs/`
- TestResult: execution evidence under `documentation/test-results/`
- Retest evidence: the later `TEST_RUN_ID` bundle used to close a prior blocker

## Hard Rules

- Work on exactly one TestSpec, TestPlan, TestRun, or TestResult set at a time.
- Prefer repository generator scripts over hand-written test artifacts.
- Treat `documentation/test-results/<TEST_RUN_ID>_results.json` as the primary evidence for triage and retest audit.
- Do not patch generated plans, generated runners, or result JSON by hand to make a gate pass.
- Do not implement application fixes here. Route implementation findings to Backlog or `janus-debug`.
- Infrastructure, auth, provider outage, missing credentials, or broken test harness issues are blockers, not product findings.
- Before live external/provider execution, present the preflight evidence and wait for explicit user approval: `OK START LIVE TEST`.
- Use `janus-git-governance` before committing, pushing, tagging, or release branching.
- Do not treat a vague `ok` as permission to start live tests or as a valid handoff substitute.

## Evidence Retention

Version curated TestRun evidence when it is referenced by a TestSpec, Backlog item, final audit, central registry entry, documentation update, or release/audit decision. This includes:

- `documentation/test-runs/<TEST_RUN_ID>_plan.json`
- `documentation/test-runs/<TEST_RUN_ID>_generated.spec.js`
- `documentation/test-runs/<TEST_RUN_ID>_skill*_handover.*`
- `documentation/test-runs/<TEST_RUN_ID>_final_audit.md`
- `documentation/test-results/<TEST_RUN_ID>_results.json`
- `documentation/test-results/<TEST_RUN_ID>_results.md`
- `documentation/test-results/<TEST_RUN_ID>/..._evidence.json`
- `tests/e2e/generated/<TEST_RUN_ID>*.live.spec.js` when it is the executed runner for retained evidence

Do not version raw Playwright report folders, trace bundles, transient terminal logs, local databases, or ad-hoc debug output unless a final audit explicitly cites them and `janus-git-governance` approves the path.

During cleanup, do not delete or ignore `documentation/test-runs/`, `documentation/test-results/`, or `tests/e2e/generated/` wholesale. Group artifacts by `TEST_RUN_ID` and commit or archive each evidence bundle with its related Backlog/Spec/test decision.

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

Use a compact package:

```text
TEST_SCOPE:
- TestSpec:
- Generated Plan:
- Provider Expectations:
- Evidence Paths:
- Dropped Context:
```

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

Use a compact package:

```text
TEST_SCOPE:
- TEST_RUN_ID:
- Plan:
- Runner:
- Prerequisites:
- Evidence Paths:
- Dropped Context:
```

Only allow live test execution when:

- one validated TestPlan is bound
- one generated runner is bound
- one `TEST_RUN_ID` is bound
- prerequisites and evidence output paths are explicit

Otherwise block instead of improvising a run.

## Bounded Generator Review Gate

For eligible bounded generator work inside `TEST_RUN_PRECHECK`, prefer the shared dispatcher as the operator-facing gate when the task is:

- one bound TestPlan
- one bound generated-runner target
- one deterministic generator path
- review-first and evidence-first

This gate is for the validated delegation class `generator_review`.

Binding artifacts:

- `C:\KI\Janus-Projekt\documentation\codex\model-routing\scripts\codex_bounded_delegation_dispatcher.py`
- `C:\KI\Janus-Projekt\documentation\codex\model-routing\scripts\codex_structured_action_generator_review_runner.py`
- `C:\KI\Janus-Projekt\documentation\codex\model-routing\codex_bounded_delegation_dispatcher_canonical_entry_2026-06-14.md`

Use prompt mode first:

```powershell
python documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py --task-class generator_review --task-label "<short generator review task>" --normal-target-model "<declared model/reasoning>" --operator-choice prompt --workflow-id <WORKFLOW-ID> --generator-manifest <manifest.json>
```

Expected operator gate:

- `1 = Codex`
- `2 = Delegated`

Meaning here:

- `1` keeps the generator preparation and review fully local in Codex.
- `2` uses delegated intent, but execution still stays deterministic and local through builder, executor, and validator steps.

Boundaries stay strict:

- no production routing
- no canonical routing-table update
- no Git or release authority by delegated path
- no live shell-delegated write path
- Codex App remains final reviewer and acceptance owner

If the user chooses the delegated path:

- if the user chooses `1`, `local`, or `codex`, invoke the dispatcher with `--operator-choice local`
- if the user chooses `2`, `delegated`, or `sidecar`, invoke the dispatcher with `--operator-choice delegated --generator-manifest <manifest.json>`
- keep generator work bound to one deterministic generator family and one validator path

Important:

- this is not a generic sidecar execution mode
- this is not broad test-writing authority
- it remains bounded delegated intent with deterministic local execution
- use it only when the active work is still a narrow generator-review problem inside this skill

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

Summarize only the current run bundle:

```text
TEST_SCOPE:
- TEST_RUN_ID:
- Runner:
- Result Json:
- Evidence Files:
- Dropped Context:
```

Document the execution outcome explicitly as one of:

- `PASS`: evidence supports the tested claim
- `FAIL`: reproducible product/spec/test failure is present
- `FLAKY`: inconsistent outcome across intended identical conditions
- `INCONCLUSIVE`: evidence is missing, contradictory, infra-blocked, or insufficient

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

Do not reread the full Backlog unless a new item number or duplicate check is actually needed.

## Bounded Triage Review Gate

For eligible bounded finding-triage work inside `FINDING_TRIAGE`, prefer the shared dispatcher as the operator-facing gate when the task is:

- one bound `TEST_RUN_ID`
- one existing local result bundle
- one bounded classification question
- review-first and evidence-first

This gate is for the bounded assist-only delegation class `test_result_triage_review`.

Binding artifacts:

- `C:\KI\Janus-Projekt\documentation\codex\model-routing\scripts\codex_bounded_delegation_dispatcher.py`
- `C:\KI\Janus-Projekt\documentation\codex\model-routing\scripts\codex_test_result_triage_review_runner.py`
- `C:\KI\Janus-Projekt\documentation\codex\model-routing\codex_test_result_triage_review_plan_2026-06-14.md`

Use prompt mode first:

```powershell
python documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py --task-class test_result_triage_review --task-label "<short triage review task>" --normal-target-model "<declared model/reasoning>" --operator-choice prompt --workflow-id <WORKFLOW-ID> --test-triage-input-package <input.json> --test-triage-fixture-result <fixture.json>
```

Expected operator gate:

- `1 = Codex`
- `2 = Delegated`

Meaning here:

- `1` keeps finding triage fully local in Codex.
- `2` uses delegated assist-only triage review, but Codex still owns the real classification, rerun decision, Backlog routing, and final evidence interpretation.

Boundaries stay strict:

- no production routing
- no canonical routing-table update
- no delegated live test execution
- no delegated result JSON mutation
- no delegated final PASS or release-readiness decision
- Codex App remains final reviewer and routing owner

If the user chooses the delegated path:

- if the user chooses `1`, `local`, or `codex`, invoke the dispatcher with `--operator-choice local`
- if the user chooses `2`, `delegated`, or `sidecar`, invoke the dispatcher with `--operator-choice delegated --test-triage-input-package <input.json> --test-triage-fixture-result <fixture.json>` in the current local validation path
- keep triage work bound to one result bundle and one bounded classification slice

Important:

- this is not a generic sidecar execution mode
- this is not broad test-result authority
- it remains bounded assist-only review with Codex-owned validation
- use it only when the active work is still a narrow triage problem inside this skill

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

Map retest evidence states as:

- `PASS` -> route to `janus-final-audit`
- `FAIL` -> route to `janus-debug`
- `FLAKY` -> route to `janus-debug`
- `INCONCLUSIVE` -> route to caller review or `janus-debug` depending on the blocker type

For re-audit after a local fix, prefer comparing only:

- prior failing result bundle
- current retest result bundle
- exact blocker closure evidence

Do not reopen unrelated historical runs unless coverage is still ambiguous.

## Model And Context Guidance

- Use `5.4` low for short TestPlan validation, artifact checks, and routine triage when the current `5.4` context is warm or the next step returns to `5.4`.
- Use `5.4 mini` for separated low-risk validation or triage batches only when likely cheaper than staying on warm `5.4`.
- Use `5.4` for Playwright execution, local debugging, and script-level investigation.
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
- `Keep Context`
- `Drop Context`

Keep summaries short and point to file paths instead of pasting large artifacts.

If control moves across actor or chat boundaries, emit exactly one compact fenced `text` block with:

- `NEXT:` and the exact next skill when known
- the bound TestSpec/TestPlan/TestRun/TestResult identity
- the evidence state (`PASS`, `FAIL`, `FLAKY`, or `INCONCLUSIVE`)
- the minimum next action
