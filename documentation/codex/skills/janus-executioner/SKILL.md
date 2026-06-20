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

Default execution model is `5.4`, medium/high.

Recommend `5.5` only for high-risk security/privacy/provider/memory architecture fixes or when the precheck requires strongest reasoning. Recommend `5.4 mini` only for deterministic low-risk docs/config edits when they are a separated block and still likely cheaper than staying on warm `5.4`; otherwise use `5.4` low for short mechanical edits inside an ongoing `5.4` workflow.

## Bounded Delegation Gate

For one prechecked execution slice that fits either the proposal-first `execution_patch_candidate` class or the later derivative `execution_write_apply_candidate` class, prefer the shared dispatcher as the operator-facing gate instead of choosing low-level helpers manually.

Binding artifacts:

- `C:\KI\Janus-Projekt\documentation\codex\model-routing\scripts\codex_bounded_delegation_dispatcher.py`
- `C:\KI\Janus-Projekt\documentation\codex\model-routing\scripts\codex_execution_patch_candidate_runner.py`
- `C:\KI\Janus-Projekt\documentation\codex\model-routing\codex_execution_patch_candidate_plan_2026-06-14.md`

Use prompt mode first:

```powershell
python documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py --task-class execution_patch_candidate --task-label "<short execution slice>" --normal-target-model "<declared model/reasoning>" --operator-choice prompt --workflow-id <WORKFLOW-ID>
```

Expected operator gate:

- `1 = Codex`
- `2 = Delegated`

Meaning here:

- `1` keeps the execution slice fully local in Codex.
- `2` uses the bounded delegated `execution_patch_candidate` proposal path.

Boundaries stay strict:

- no delegated final apply
- no delegated test execution
- no delegated task completion claim
- no Git, release, or audit authority by delegated path
- Codex App remains patch reviewer, apply/reject owner, and final execution owner

If the user chooses the delegated path:

- if the user chooses `1`, `local`, or `codex`, invoke the dispatcher with `--operator-choice local`
- if the user chooses `2`, `delegated`, or `sidecar` for local fixture validation, invoke the dispatcher with `--operator-choice delegated --execution-input-package <input-json> --execution-fixture-result <result-json>`
- if the user chooses `2`, `delegated`, or `sidecar` for the real proposal-only path, invoke the dispatcher with `--operator-choice delegated --execution-input-package <input-json> --execution-live-sidecar`; this path stays read-only and captures a bounded patch proposal only

Important:

- this class is proposal-first, not broad write delegation
- it is valid only for exactly one prechecked implementation slice
- the delegated output may suggest a bounded patch, but Codex still decides whether to apply or reject it
- manual Janus validation remains Codex-owned even if the delegated proposal looks strong

For a later derivative bounded write candidate that is backed by an already accepted proposal-first execution package, use the separate `execution_write_apply_candidate` class:

```powershell
python documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py --task-class execution_write_apply_candidate --task-label "<short execution slice>" --normal-target-model "<declared model/reasoning>" --operator-choice prompt --workflow-id <WORKFLOW-ID> --accepted-source-run-dir <accepted-execution-patch-run-dir>
```

Meaning there:

- `1` keeps the execution slice fully local in Codex.
- `2` uses the bounded delegated `execution_write_apply_candidate` path.

Extra write-candidate boundaries:

- delegated write candidacy must be backed by an accepted `execution_patch_candidate` package
- this does not itself grant live write approval
- Codex still owns any future live-write approval, diff review, validation review, and final task completion
- manual Janus validation remains Codex-owned

Use `execution_write_apply_candidate` only when:

- exactly one prechecked task slice is bound
- the accepted proposal-first source package already proves allowlist and touched-file discipline
- the next goal is to evaluate future bounded write readiness, not to bypass Codex governance

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

Valid precheck must contain:

```text
BEGIN COPY FOR SKILL 4
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
Scope-Regel:
Automated Evidence Gate:
npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
Oracle-/TestPlan-Regel:
END COPY FOR SKILL 4
```

If missing:

```text
BLOCKED: INVALID_SKILL3_HANDOVER
Reason: Skill-3 handoff lacks complete V3.2 copyblock.
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
