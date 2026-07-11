---
name: janus-executioner
description: Execute exactly one Janus target task from bound artifacts after a valid preimplementation check. Use when the user asks to implement, fix, edit code, run task execution, continue a selected Backlog/Spec task, or apply changes after janus-preimplementation-check has passed.
---

# Janus Executioner

## Overview

Implement exactly one target task. Use bound artifacts only: task, Spec, Backlog item, precheck, and validation plan. Do not plan new features, expand scope, bypass evidence, or change provider/architecture boundaries unless the task explicitly requires it.
This is primarily a Codex execution skill. ChatGPT normally uses its result only when Codex returns `BLOCKED`, `FAILED`, `NEEDS_INFO`, or a reroute/escalation outcome.

## Source References

Read only when exact legacy wording is needed:

- `C:\KI\Janus-Projekt\.windsurf\workflows\SKILL 4 – EXECUTIONER.md`
- `C:\KI\Janus-Projekt\documentation\pipeline\PIPELINE_CONTRACT.md`
- `C:\KI\Janus-Projekt\AGENTS.md`

## Required Input

Require:

```text
Target Task:
Assigned Model:
Task:
Spec: <path | N/A WITH REASON>
Backlog Item: <BACKLOG-XXX | N/A>
Pre-Check: PRE-CHECK PASSED
```

If a precheck is claimed, validate the handoff literals from `janus-preimplementation-check`. Block if invalid.
Do not start implementation without a matching `PRE-CHECK PASSED` handoff bound to exactly one target task or implementation slice.

## Model Gate

Default execution model is `5.6 Terra`, medium/high.

Recommend `5.6 Sol` only for high-risk security/privacy/provider/memory architecture fixes or when the precheck requires strongest reasoning. Recommend `5.6 Luna` only for deterministic low-risk docs/config edits when they are a separated block and still likely cheaper than staying on warm `5.6 Terra`; otherwise use `5.6 Terra` low for short mechanical edits inside an ongoing `5.6 Terra` workflow.

## Same-Chat Output Rule

Execution stays artifact-first when we remain in the same chat.

- keep the conversational reply compact and outcome-focused
- do not dump large handoff blocks, giant task restatements, or full execution artifacts into chat unless the user explicitly asks for them or a real new-chat handoff is required
- when prior skills returned a compact summary, read the bound artifact file instead of expecting the chat reply to contain the full handoff text

## Cursor-First Execution Gate Rule

For bounded, prechecked execution slices, the current shared gate must actively surface Cursor when it is a viable path.

- if a Cursor option is visible in the current rollout state, probe that gate before silently defaulting to local Codex
- if Cursor is eligible and ROI-positive, present it explicitly as an execution option so we can gather evidence and avoid unnecessary local-only work
- if Cursor is hidden, unsupported for the lane, or ROI-negative, say that briefly and continue with the best remaining path
- do not skip the Cursor option merely because Codex can also perform the task locally

## Bounded Delegation Gate

Operator-facing entry for the current cost-aware four-choice rollout:

- `1 = Codex`
- `2 = OpenRouter`
- `3 = Cursor Composer`
- `4 = Cursor API`

Use the shared delegate entry first for eligible bounded execution slices:

```powershell
python documentation/codex/model-routing/scripts/janus_delegate.py --lane execution_patch_candidate --workflow-id <WORKFLOW-ID> --operator-choice prompt --input-package-json <input-package.json> --allowlist-file <allowlist.txt> --estimated-codex-saved-tokens <n> --estimated-delegation-overhead-tokens <n>
```

Notes:

- default behavior stays plan-only and review-first
- explicit live Cursor execution is allowed only with additional operator approval via `--execute-live-cursor`
- OpenRouter remains option `2`; older OR-specific runners remain sealed downstream helpers rather than the first visible entry
- Cursor Composer uses the Auto+Composer pool; Cursor API uses the same shared `janus_cursor_worker_runner.py` with per-lane `cursor_api_model` from the API pool
- `live_test_execution`, compiler steps, and final validation stay Codex-owned and are not widened by this gate
- the normal visible everyday shared gate is only for already approved bounded execution lanes; `execution_write_apply_candidate` remains fail-closed and hidden from the normal visible gate while its visibility status is still `HIDDEN_PARTIAL_CANDIDATE`

Current everyday recommendation for the execution lanes:

- `TASK-EX-001` / `execution_patch_candidate`: use `3 = Cursor Composer` or `4 = Cursor API` as the primary bounded worker paths for real proposal work when ROI is positive and the slice is allowlisted
- `TASK-EX-001` / option `2 = OpenRouter`: keep as an explicit secondary/experimental proposal path, mainly for comparative validation or when the operator deliberately wants OR
- `TASK-EX-002` / `execution_write_apply_candidate`: For `TASK-EX-002` / `execution_write_apply_candidate`, option `2` is now the sealed deterministic local apply worker; this lane stays fail-closed in the normal visible gate

After the first Cursor live wave, treat the shared `janus_delegate.py` four-choice surface as the primary everyday operator-facing gate for bounded execution slices. The older productive Dev-workhorse runner and direct OR helpers remain legacy/downstream validation helpers for explicit OpenRouter-specific checks, not the first visible entry for normal execution work.

Before offering OR, run the net-value check. OR is useful only when expected Codex savings clearly exceed the Codex overhead for creating the OR handoff, running the lane, reviewing the result, and documenting the outcome. Tiny tasks should stay local even if OR itself is cheap.

Net-value rule:

- if estimated Codex tokens saved <= estimated Codex OR orchestration/review overhead, choose Codex directly
- if estimates are close or uncertain, choose Codex directly unless the task is a deliberate OR lane validation
- if ROI is positive and the task is prechecked, bounded, and low/medium risk, route through the shared four-choice gate above; if an older direct productive helper is used instead, treat it as a legacy OpenRouter validation path and keep its local wording explicit as `1 = Codex` / `2 = OpenRouter`
- prefer write-capable bounded OR only when apply authority is constrained by allowlist, max touched files, no Git/release authority, and Codex-owned validation

Runner ROI fields:

```powershell
--estimated-codex-saved-tokens <n> --estimated-codex-or-overhead-tokens <n> --minimum-net-codex-saved-tokens <n>
```

Use `--require-positive-or-roi` when estimates must be present before showing the OR choice. If the gate is negative or incomplete, the runner returns `LOCAL_CODEX_PATH_SELECTED`.

Legacy OpenRouter validation/helper artifacts:

- `C:\KI\Janus-Projekt\documentation\codex\model-routing\scripts\codex_dev_workhorse_runner.py`
- `C:\KI\Janus-Projekt\documentation\codex\model-routing\scripts\codex_bounded_delegation_dispatcher.py`
- `C:\KI\Janus-Projekt\documentation\codex\model-routing\scripts\codex_execution_patch_candidate_runner.py`
- `C:\KI\Janus-Projekt\documentation\codex\model-routing\codex_execution_patch_candidate_plan_2026-06-14.md`

Use prompt mode only when you are explicitly validating the older OpenRouter-specific helper path rather than the normal shared delegate entry:

```powershell
python documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py --task-class execution_patch_candidate --task-label "<short execution slice>" --normal-target-model "<declared model/reasoning>" --operator-choice prompt --workflow-id <WORKFLOW-ID> --path-id productive_dev_workhorse_path --estimated-or-cost <estimated-cost> --cost-estimate-confidence-percent <confidence>
```

Expected local gate for that legacy helper path:

- `1 = Codex`
- `2 = OpenRouter`

Meaning here:

- `1` keeps the execution slice fully local in Codex.
- `2` enters the older productive Dev-workhorse OpenRouter branch, which then invokes the bounded delegated `execution_patch_candidate` proposal path behind that legacy gate.

Current legacy OR fallback candidate for this bounded lane when option `2 = OpenRouter` is explicitly chosen:

- `moonshotai/kimi-k2.5`

Use the smaller Qwen Coder lane only for deliberately narrow smoke/benchmark slices or when the sealed contract explicitly selects it. After BACKLOG-116, productive execution-patch work should default to the stronger OR lane because malformed/repetitive patch output from the smaller Qwen model caused Codex fallback.

When the selected OR model starts with `qwen/`, the dispatcher routes `execution_patch_candidate` through the Responses API `openrouter:apply_patch` runner:

- `C:\KI\Janus-Projekt\documentation\codex\model-routing\scripts\openrouter_qwen_execution_patch_candidate_runner.py`

This produces tool-call patch artifacts instead of prose-only JSON patches. After Codex accepts a bounded Qwen apply_patch proposal, normalize it for write-apply with:

```powershell
python documentation/codex/model-routing/scripts/normalize_openrouter_apply_patch_for_write_apply.py --source-run-dir <qwen-execution-run-dir> --workflow-id <WORKFLOW-ID>-WRITE-SOURCE
```

Then feed the normalized output directory into `execution_write_apply_candidate` as `--accepted-source-run-dir`. This is the preferred productive path when the OR patch is accepted: OR writes the concrete patch artifact, the harness applies it deterministically inside the allowlist, and Codex reviews the resulting diff and runs validation instead of rewriting the change from scratch.

Boundaries stay strict:

- no delegated final apply
- no delegated test execution
- no delegated task completion claim
- no Git, release, or audit authority by delegated path
- Codex App remains patch reviewer, apply/reject owner, and final execution owner

If the user explicitly chooses a delegated path:

- if the user chooses `1`, `local`, or `codex`, invoke the dispatcher with `--operator-choice local`
- if the user chooses `2`, `or`, `openrouter`, or `opr`, prefer the shared `janus_delegate.py` option `2` first; use the older productive runner directly only when the task is explicitly testing or validating the legacy OpenRouter helper path
- if the user chooses `3`, `cursor-composer`, `composer`, or `cursor`, prefer the shared `janus_delegate.py` option `3` with the Auto+Composer pool
- if the user chooses `4`, `cursor-api`, `cursor_api`, or `api`, prefer the shared `janus_delegate.py` option `4` with the lane-specific API model
- for local fixture validation inside that legacy OR helper path, the downstream dispatcher still uses `--operator-choice delegated --execution-input-package <input-json> --execution-fixture-result <result-json>`
- for the real proposal-only legacy OR branch, the downstream dispatcher still uses `--operator-choice delegated --execution-input-package <input-json> --execution-live-sidecar`; this path stays read-only and captures a bounded patch proposal only

Important:

- this visible OR gate is still proposal-first, not broad write delegation
- it is valid only for exactly one prechecked implementation slice
- the delegated output may suggest a bounded patch, but Codex still decides whether to apply or reject it
- manual Janus validation remains Codex-owned even if the delegated proposal looks strong

For a later derivative bounded write candidate that is backed by an already accepted proposal-first execution package, keep the shared four-choice surface only as a future operator-entry target when the lane is visibility-ready. For `TASK-EX-002` / `execution_write_apply_candidate`, option `2` is now the sealed deterministic local apply worker, not Cursor Composer, Cursor API, or OpenRouter. The current everyday operator posture is still fail-closed: no normal visible delegated choice should be shown while the shared contract keeps this lane at `HIDDEN_PARTIAL_CANDIDATE`. The direct `codex_dev_workhorse_runner.py` path below remains a legacy/helper-focused OpenRouter validation artifact rather than the recommended or normally visible path for this lane:

```powershell
python documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py --task-class execution_write_apply_candidate --task-label "<short execution slice>" --normal-target-model "<declared model/reasoning>" --operator-choice prompt --workflow-id <WORKFLOW-ID> --path-id productive_dev_workhorse_path --estimated-or-cost <estimated-cost> --cost-estimate-confidence-percent <confidence> --accepted-source-run-dir <accepted-execution-patch-run-dir>
```

Meaning there for that legacy helper path:

- `1` keeps the execution slice fully local in Codex.
- `2` in the old legacy helper path enters the historical Dev-workhorse OpenRouter branch, but this legacy validation wording must not be surfaced as the normal everyday gate while `TASK-EX-002` remains visibility-hidden.
- accepted Qwen `openrouter:apply_patch` runs must first be normalized with `normalize_openrouter_apply_patch_for_write_apply.py`; accepted JSON `patch_text` runs use `normalize_execution_patch_candidate_for_write_apply.py`.

Extra write-candidate boundaries:

- delegated write candidacy must be backed by an accepted `execution_patch_candidate` package
- the live apply step is deterministic local patch application inside the exact accepted allowlist, not a second open-ended model writing pass
- do not route `TASK-EX-002` through Cursor `agent -p`; repeated live timeout evidence made that path a bad worker fit rather than a prompt-tuning problem
- do not invest in OpenRouter as the apply worker for `TASK-EX-002`; OR remains useful for proposal-first execution lanes, not this mechanical apply step
- this does not itself grant broad live write approval
- Codex still owns any future live-write approval, diff review, validation review, and final task completion
- manual Janus validation remains Codex-owned

Goal state for OR productivity:

- OR should not remain a pure chatbot or prose reviewer for eligible code work.
- For meaningful bounded execution slices, OR should produce or apply concrete code artifacts inside rails.
- Codex should avoid rewriting accepted OR work from scratch; Codex should review, validate, and only repair locally when the delegated result is rejected or fails evidence gates.
- Proposal-first is a safety fallback, not the target for every eligible execution task.
- For Qwen execution tasks, prefer the apply_patch tool-call path over prose JSON when ROI and risk gates pass.

Use `execution_write_apply_candidate` only when:

- exactly one prechecked task slice is bound
- the accepted proposal-first source package already proves allowlist and touched-file discipline
- the next goal is to evaluate future bounded write readiness, not to bypass Codex governance
- if estimate, confidence, or productive-path eligibility is missing, abort before any dispatcher or wrapper invocation

## Golden Path

1. Load bound artifacts and isolate the target task.
2. Validate precheck/handoff before any edits.
3. For non-trivial or risky tasks, targeted-search `WHAT_I_LEARNED.md` using relevant subsystem/error tags.
4. Output a command-first Mini-TestPlan or N/A plan before product edits.
5. Implement only in target scope.
6. Run specified tests or the smallest meaningful test set.
7. Run Playwright/generator validation unless N/A is explicitly valid.
8. Fix verification failures only inside task scope, max two focused attempts.
9. End in exactly one canonical state: `PASS`, `BLOCKED`, `NEEDS_INFO`, `FAILED`, or `HANDOFF`.

If the work stops being exactly one target task or one implementation slice, stop immediately and reroute instead of widening the execution.

## Command-First Rule

Before edits, state:

```text
MINI TEST PLAN
- Target Task:
- Scope:
- Files Expected:
- Unit/Integration Checks:
- Playwright/E2E Check:
- N/A Reason: <only if valid>
```

Playwright N/A is valid only for pure `.md`, `.yml`, or `.css` changes with no logic, chat, backend, provider, stream, tool, memory, or frontend runtime path.

## Precheck Handoff Gate

Valid precheck must contain the compact Codex-native result fields:

- `PRE-CHECK RESULT`
- `PRE-CHECK PASSED`
- `Pre-Check: PRE-CHECK PASSED`
- `Pre-Check Context:`
- `Scope-Regel:`
- `Automated Evidence Gate:`
- `npx playwright test <runner> --headed --workers=1 --reporter=list`
- `Artifact Identity Check:`
- `Oracle-/TestPlan-Regel:`
- `NEXT STEP`
- `Recommended Skill: janus-executioner`
- `Recommended Model:`
- `Recommended Intelligence:`
- `User Action:`

When the prior precheck stayed in the same chat and returned only a compact summary, validate these literals from the bound precheck artifact file rather than requiring the user-facing reply to repeat a large handoff block.

If missing:

```text
BLOCKED: INVALID_SKILL3_HANDOVER
Reason: Skill-3 handoff lacks the required Codex-native precheck fields.
Required Fix: Run janus-preimplementation-check again.
```

A bare `ok` or similar acknowledgement is never a valid handoff replacement.

## Provider Isolation

For provider-specific tasks:

- no cross-provider fallback
- no model switch as fake fix
- validate the original provider/test case
- if provider is not testable, output credential check without secrets
- if runtime evidence is missing, hand off to `janus-debug`

## TestSpec and TestRun Boundaries

For TestSpec/TestPlan/Oracle/Assertion tasks:

- edit source-of-truth TestSpec/Oracle only
- never patch old generated TestPlan manually
- never create fake TestResult evidence
- end with `IMPLEMENTATION COMPLETE - VALIDATION REQUIRED`
- hand off to `janus-test-pipeline`

For TestRun-finding product fixes:

- local implementation may complete
- do not mark Backlog DONE
- do not route to final audit until focused or full retest evidence exists
- hand off to `janus-test-pipeline`

## Failure Management

If validation fails:

- record exact failure command, code, evidence path, and excerpt
- make at most two focused fixes in scope
- if still failing or out of scope, hand off to `janus-debug`
- never proceed to final audit on unresolved failure

Treat any of these as scope-growth or reroute signals:

- a second target task becomes necessary
- the touched area expands beyond the expected file cluster
- product or architecture decisions appear mid-implementation
- the required validation surface stops being bounded and obvious

## Completion Rules

`TASK COMPLETE` or `ALL TASKS COMPLETE` requires an immediately preceding block:

```text
Auto-Verification:
- Status: PASS
```

If Auto-Verification is N/A, do not say `TASK COMPLETE`; use `N/A-SCOPE CLOSURE` with reason and next gate.

## Manual Janus Validation Gate

After Auto-Verification PASS and before any `janus-final-audit` handoff, require an explicit user-facing manual Janus validation gate for product-relevant changes.

The gate must include:

- one concrete Janus test prompt, click path, or UI check the user can run
- the expected successful behavior in plain language
- the failure route: if the user reports the manual test failed, route to `janus-debug`
- the success route: only after the user confirms the manual test passed may the next handoff target `janus-final-audit`

Use this block in the execution result:

```text
Manual Janus Validation Gate:
- Status: PENDING_USER_TEST | PASS | N/A WITH REASON
- Test Example:
- Expected Result:
- If Failed: route to janus-debug
- If Passed: route to janus-final-audit
```

`N/A WITH REASON` is valid only for pure documentation/config/meta-skill changes with no Janus product runtime behavior. Backend, frontend, chat, provider, stream, tool, memory, persistence, Electron, and UI changes require a concrete manual test request unless a bound TestRun/TestPipeline result already provides equivalent live Janus evidence.

For final task completion, hand off to `janus-final-audit` only when Auto-Verification is PASS, the Manual Janus Validation Gate is PASS or valid `N/A WITH REASON`, and a compact audit package path exists or is explicitly requested to be built. If the Manual Janus Validation Gate is `PENDING_USER_TEST`, stop with `Canonical State: NEEDS_INFO` and ask the user to run the example. If the user reports failure, route to `janus-debug`.

## Audit Package Handoff Rule

Before handing off to `janus-final-audit`, prepare or refresh a compact audit package, preferably `AUDIT_PACKAGE.md`, containing:

- scope and target task
- changed files
- validation commands and results
- evidence paths
- known risks
- open issues
- if this is a re-audit, a short blocker delta summary

Prefer `codex-audit-package-builder` for this package. For blocker follow-up work, update the existing package instead of creating a new broad package from scratch.

If the next step should happen in a fresh chat, the final answer must include one fenced `text` `NEW_CHAT_HANDOFF` block that references the package path, target skill, and model/reasoning. Do not rely on prose-only routing.
If the next step stays in the same warm Codex context, naming `Target Skill: janus-final-audit` is enough after a successful bounded execution.

## CURRENT_STATE Requirement

Before finishing a substantial Janus work block, update `documentation/ai/CURRENT_STATE.md`.

A Janus work block is substantial when at least one of these is true:

- files changed
- validation executed
- a blocker documented
- a formal next-skill handoff produced

Pure routing replies, short status answers, and other mini-interactions do not require a CURRENT_STATE update.

Keep the update concise and include:

- what changed
- which files changed
- which checks ran
- what remains risky or open
- what ChatGPT should review next
- what Codex should do next

CURRENT_STATE does not replace Backlog, Spec, TestSpec, TestRun, TestResult, audit package, or dashboard artifacts.

Commit and push remain gated by `janus-git-governance` and explicit user approval.

If no push happens or push fails, the execution result or handoff must explicitly say that a remote such as GitHub may not contain the latest CURRENT_STATE yet.

## Output Skeleton

```text
TASK EXECUTION RESULT
Canonical State: PASS | BLOCKED | FAILED | HANDOFF | NEEDS_INFO
Target Task:
Changed Files:
Executed Checks:
Auto-Verification:
- Status: PASS | FAIL | N/A
- Evidence:
Manual Janus Validation Gate:
- Status: PENDING_USER_TEST | PASS | N/A WITH REASON
- Test Example:
- Expected Result:
- If Failed: route to janus-debug
- If Passed: route to janus-final-audit

NEXT_STEP
Target Skill: janus-final-audit | janus-debug | janus-test-pipeline | janus-preimplementation-check
Canonical State: HANDOFF | BLOCKED
Required Artifacts:
Audit Package:
Evidence Paths:
Failure Code:
Changed Files:
Decision:
Reason:
Recommended Model:
Recommended Intelligence:
New Chat: yes | no
Next User Action:
NEW_CHAT_HANDOFF: <fenced text block only when New Chat: yes>
```

For `BLOCKED`, `FAILED`, `NEEDS_INFO`, or reroute states that must go back to ChatGPT, emit exactly one compact fenced `text` block with the blocked target task, failure or scope-growth reason, minimum artifacts, and exact next skill when known.

## Validator

When an execution result is saved, run:

```powershell
python C:\Users\pruve\.codex\skills\janus-executioner\scripts\validate_execution_result.py <path-to-execution-result.md>
```
