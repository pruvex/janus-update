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

## Tri-Modal Delegate Entry

Operator-facing entry for the current tri-modal rollout:

- `1 = Codex`
- `2 = Cursor`
- `3 = OpenRouter`

Use the shared delegate entry first for the bounded test-pipeline lanes that are live in the manifest:

- `generator_review`
- `test_fixture_worker`
- `test_result_triage_review`

Prompt-mode entry:

```powershell
python documentation/codex/model-routing/scripts/janus_delegate.py --lane <generator_review|test_fixture_worker|test_result_triage_review> --workflow-id <WORKFLOW-ID> --operator-choice prompt --input-package-json <input-package.json> --allowlist-file <allowlist.txt> --estimated-codex-saved-tokens <n> --estimated-delegation-overhead-tokens <n>
```

Notes:

- `test_fixture_worker` is the current bounded write-capable Cursor lane
- `generator_review` and `test_result_triage_review` remain review-first lanes
- default behavior stays plan-only; explicit live Cursor execution requires separate operator approval and `--execute-live-cursor`
- `live_test_execution` and `diamond_retest_audit` remain Codex-only even though the surrounding skill now exposes tri-modal gates for other bounded lanes
- visible delegated choice should appear only for the already approved bounded lane that matches the active slice; non-approved or fail-closed test slices stay local in Codex

After the first shared live Cursor shadow wave, treat Cursor as the primary bounded worker for `test_fixture_worker`. The older `1 = Codex / 2 = OpenRouter` helper wording that still appears below applies only to explicit legacy review/helper paths such as `generator_review` or specialized OR validation, not to the main everyday test worker surface.

Reference everyday proof for this lane:

- `C:\KI\Janus-Projekt\documentation\codex\model-routing\TEST_FIXTURE_WORKER_GOLDEN_PATH_2026-07-06.md`

Reference live evidence:

- `WF-CURSOR-LIVE-SMOKE-003`
- `WF-CURSOR-SHADOW-TEST-LIVE-001`
- `WF-CURSOR-SHADOW-TEST-LIVE-002`

## Bounded Generator Review Gate

For eligible bounded generator work inside `TEST_RUN_PRECHECK`, prefer the shared dispatcher as the operator-facing gate when the task is:

- one bound TestPlan
- one bound generated-runner target
- one deterministic generator path
- review-first and evidence-first

This gate is for the validated delegation class `generator_review`.

Current visibility state:

- `generator_review` is now `VISIBLE_APPROVED` under the shared existing-skill visibility contract for this bounded lane.
- if this older direct helper path is used instead of the shared tri-modal entry above, its local operator gate may be shown as `1 = Codex / 2 = OpenRouter`, while Codex remains final reviewer and acceptance owner.

Binding artifacts:

- `C:\KI\Janus-Projekt\documentation\codex\model-routing\scripts\codex_bounded_delegation_dispatcher.py`
- `C:\KI\Janus-Projekt\documentation\codex\model-routing\scripts\codex_structured_action_generator_review_runner.py`
- `C:\KI\Janus-Projekt\documentation\codex\model-routing\codex_bounded_delegation_dispatcher_canonical_entry_2026-06-14.md`

Use the real operator-facing helper for this lane first:

```powershell
python documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py --testspec-path <TestSpec> --test-run-id <TEST_RUN_ID> --normal-target-model "5.6 Terra medium" --operator-choice prompt --workflow-id <WORKFLOW-ID>
```

Internal delegated meaning:

- generator preparation and review stay deterministic and local through the structured local executor plus validator steps.
- even with visible operator choice, this remains a bounded review-first lane rather than broad delegated test-authoring authority.
- the visible gate should read `1 = Codex` and `2 = OpenRouter`, but the current technical delegated path is the bounded structured local executor surface, not broad free-form repo authority.

Boundaries stay strict:

- no production routing
- no canonical routing-table update
- no Git or release authority by delegated path
- no live shell-delegated write path
- Codex App remains final reviewer and acceptance owner

If the user chooses the delegated path:

- if the user chooses `1`, `local`, or `codex`, invoke the helper with `--operator-choice local`
- if the user chooses `2`, `or`, `delegated`, or `sidecar`, invoke the helper with `--operator-choice 2 --execute-live`
- keep generator work bound to one deterministic generator family and one validator path
- use the helper's generated `operator_choice_prompt.json`, `summary.json`, `validation_summary.json`, and post-validation artifacts as the review bundle for this lane

Important:

- this is not a generic sidecar execution mode
- this is not broad test-writing authority
- it remains bounded delegated intent with deterministic local execution
- use it only when the active work is still a narrow generator-review problem inside this skill

## Strong OR Test Worker Gate

For eligible bounded test work that goes beyond generator review, show a normal operator-facing gate when the slice is:

- one bound TestSpec/TestRun or one bounded test target
- one isolated worker package with explicit `workspace_files`, `pre_commands`, and `post_commands`
- no production app data mutation unless the package and user approval explicitly bind it
- no secrets in the package and no unbounded repository context
- positive expected Codex-token ROI after package preparation and Codex review overhead

Use this lane for work like:

- write or adjust one bounded test artifact
- run the allowed test command multiple times by listing repeated command specs in the package
- summarize the run outcomes and changed files for Codex review

Binding artifacts:

- `C:\KI\Janus-Projekt\documentation\codex\model-routing\scripts\test_pipeline_sidecar_write_pilot_runner.py`
- `C:\KI\Janus-Projekt\documentation\codex\model-routing\scripts\isolated_aider_workspace_runner.py`

Preferred strong OR model for this lane:

- `moonshotai/kimi-k2.5`

Prompt-mode gate example:

```powershell
python documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py --testspec-path <TestSpec-or-N/A> --test-run-id <TEST_RUN_ID> --normal-target-model "5.6 Terra medium" --operator-choice prompt --workflow-id <WORKFLOW-ID> --sidecar-model moonshotai/kimi-k2.5 --isolated-aider-package-json <worker-package.json> --estimated-or-cost <estimated-cost> --cost-estimate-confidence-percent <confidence>
```

If the user chooses the delegated path:

- invoke the helper with `--operator-choice 2` and the same `--isolated-aider-package-json`
- keep the package allowlist as the authority boundary
- treat repeated runs as explicit package command specs, not as open-ended shell freedom
- review `operator_summary.json`, `test_output.log`, `worker_report.md`, changed files, and copy-back files before accepting anything

Boundaries:

- no delegated final PASS, release readiness, Backlog routing, Git, or product decision
- no broad live shell authority
- no edits outside package allowlist
- no command outside package `pre_commands` / `post_commands`
- Codex remains final reviewer, validator, and acceptance owner

This lane exists because the earlier small-model proposal path was too narrow for the intended savings target. It should now be treated as a legacy/specialized OpenRouter helper path beside the Cursor-first shared delegate rollout, and used only when a bounded test-writing/execution bundle is large enough to justify explicit OR validation rather than the normal Cursor worker path.

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
3. Before showing any normal OR choice, classify the live slice fail-closed:

- `local_bounded_retest` -> visible `1 = Codex` / `2 = OpenRouter` gate may be shown
- `local_broad_retest` -> no normal OR gate
- `non_local_live_test` -> no normal OR gate
- `not_a_retest` -> no normal OR gate

Prompt the bounded visibility gate with:

```powershell
python documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py --mode LIVE_TEST_EXECUTION --testspec-path <TestSpec-or-N/A> --test-run-id <TEST_RUN_ID> --normal-target-model "5.6 Terra medium" --operator-choice prompt --workflow-id <WORKFLOW-ID> --live-test-scope <local_bounded_retest|local_broad_retest|non_local_live_test|not_a_retest> --sidecar-model moonshotai/kimi-k2.5
```

Meaning in this first slice:

- only `local_bounded_retest` may expose the visible `2 = OpenRouter` choice
- the visible gate is backed by a bounded worker package only when `--isolated-aider-package-json <worker-package.json>` is supplied
- the worker package may reference a runtime-only local auth/header requirement, but must not serialize real secret values into versioned artifacts
- delegated evidence is reviewable by Codex and must not claim final PASS, release, Git, routing, or task-completion authority
- incomplete delegated evidence, missing auth prerequisites, over-broad worker packages, scope drift, or missing review-bundle files must fail closed to a Codex-owned reject-and-fallback outcome
- Codex remains the final live execution reviewer and acceptance owner
4. After explicit user approval, run the generated Playwright test:

```powershell
npx playwright test <Runner> --headed --workers=1 --reporter=list
```

5. Preserve raw terminal evidence in the response summary.
6. Verify result files exist and validate them with this skill's helper script when useful:

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
- net Codex-token ROI is positive after counting Codex briefing, orchestration, review, and handoff overhead

This gate is for the bounded assist-only delegation class `test_result_triage_review`.

Binding artifacts:

- `C:\KI\Janus-Projekt\documentation\codex\model-routing\scripts\codex_bounded_delegation_dispatcher.py`
- `C:\KI\Janus-Projekt\documentation\codex\model-routing\scripts\codex_test_result_triage_review_runner.py`
- `C:\KI\Janus-Projekt\documentation\codex\model-routing\codex_test_result_triage_review_plan_2026-06-14.md`

Use prompt mode first:

```powershell
python documentation/codex/model-routing/scripts/codex_test_result_triage_review_runner.py --task-label "<short triage review task>" --normal-target-model "<declared model/reasoning>" --operator-choice prompt --workflow-id <WORKFLOW-ID> --estimated-or-cost <estimated-cost> --cost-estimate-confidence-percent <confidence> --estimated-codex-saved-tokens <n> --estimated-codex-or-overhead-tokens <n> --minimum-net-codex-saved-tokens <n> --input-package-json <input.json>
```

Expected local gate for that legacy helper path:

- `1 = Codex`
- `2 = OpenRouter`

Meaning here:

- `1` keeps finding triage fully local in Codex.
- `2` uses the bounded OpenRouter lane for an assist-only triage review, but Codex behaelt die reale Klassifikation, die Rerun-Entscheidung, das Backlog-Routing und die finale Evidenzinterpretation.

Productive role:

- Use OpenRouter when the result bundle and evidence snippets are large enough that external triage review will save meaningful Codex work.
- OpenRouter may cluster failures, suggest likely classification, identify next local verifier/retest, and prepare compact `janus-debug`, `janus-backlog-intake`, or `janus-executioner` handoff language.
- OpenRouter must not run Playwright, mutate result JSON, declare final PASS, or decide release readiness.
- Keep tiny or obvious triage steps on Codex when OpenRouter briefing/review would cost more than classifying the result locally.

Current preferred OR candidate for this bounded lane:

- `qwen/qwen3-coder-30b-a3b-instruct`

Boundaries stay strict:

- no production routing
- no canonical routing-table update
- no delegated live test execution
- no delegated result JSON mutation
- no delegated final PASS or release-readiness decision
- Codex App remains final reviewer and routing owner

If the user chooses the delegated path:

- if the user chooses `1`, `local`, or `codex`, invoke the dispatcher with `--operator-choice local`
- if the user chooses `2`, `delegated`, or `sidecar`, enter through `codex_test_result_triage_review_runner.run_consumer_flow(...)` so the bounded package, ROI gate, operator gate, and dispatcher path stay aligned
- if the productive gate or ROI gate rejects the slice, do not show an OR choice; keep the step deterministically Codex-only
- keep triage work bound to one result bundle and one bounded classification slice

Consumer integration path for everyday `janus-test-pipeline` work:

- build one redacted package with `codex_test_result_triage_review_runner.build_consumer_input_package(...)`
- enter the operator gate through `codex_test_result_triage_review_runner.run_consumer_flow(...)`
- keep any delegated result bounded to assist-only classification review, with Codex still owning rerun choice, Backlog routing, and final evidence interpretation

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

- Use `5.6 Terra` low for short TestPlan validation, artifact checks, and routine triage when the current `5.6 Terra` context is warm or the next step returns to `5.6 Terra`.
- Use `5.6 Luna` for separated low-risk validation or triage batches only when likely cheaper than staying on warm `5.6 Terra`.
- Use `5.6 Terra` for Playwright execution, local debugging, and script-level investigation.
- Use `5.6 Terra` for ambiguous failures, product/spec classification, and retest audit.
- Use `5.6 Sol` only for security-sensitive release blockers, provider trust boundaries, or complex audit disputes.
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
