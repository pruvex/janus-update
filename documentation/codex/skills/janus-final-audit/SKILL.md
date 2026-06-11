---
name: janus-final-audit
description: Perform the Janus final quality and release gate after implementation and validation, deciding PASS, PASS WITH FIXES, or BLOCKED against bound artifacts only. Use after execution/precheck/test evidence exists and before documentation update, release, closing Backlog items, or moving Specs to Spec Done.
---

# Janus Final Audit

## Overview

Audit completed Janus work against the bound Spec, Task, Backlog item, TestSpec, changed files, diff, precheck, and evidence. Do not implement, redesign, add requirements, or use chat history as source of truth.
This is a shared governance skill. ChatGPT is preferred for independent final review when risk, release proximity, security/privacy/provider impact, or unclear evidence matters. Codex may audit bounded evidence in the same warm context only when the audit package is compact, current, and low risk.

## Source References

Read only when exact legacy wording is needed:

- `C:\KI\Janus-Projekt\.windsurf\workflows\SKILL 6 – DIAMANTSTANDARD FINAL AUDIT.md`
- `C:\KI\Janus-Projekt\documentation\pipeline\PIPELINE_CONTRACT.md`
- `C:\KI\Janus-Projekt\AGENTS.md`

## Model Gate

Before auditing, recommend model/intelligence:

- Low/local deterministic scope: `5.4` or current capable coding model, medium.
- Medium risk or multiple files: `5.4`, high.
- High/critical risk, security, privacy, provider routing, memory, release-critical, unclear evidence, contradictory artifacts, or missing tests: `5.5`, high.

If current setup is weaker than required, stop with a model-switch handoff. Do not perform the audit.

## Required Input

Require one compact audit package file, preferably `AUDIT_PACKAGE.md`.

Minimum required package contents:

- Spec or `N/A WITH REASON`
- Task file or TestSpec/TestRun package
- Backlog item if applicable
- Pre-implementation check result if applicable
- changed files
- diff summary or relevant diff
- validation commands and results
- evidence paths
- manual Janus evidence: `PRESENT`, `MISSING`, or `N/A WITH REASON`
- pipeline completion status: remaining tasks none, implementation complete yes, or validation-only run

The audit package is the primary source for the audit. Open additional artifacts only when the package points to a specific ambiguity, risk, or contradiction.
Do not reconstruct requirements from broad chat history. If the bound package cannot support the decision, return `FINAL AUDIT RESULT: BLOCKED`.

If the package is incomplete, return `FINAL AUDIT RESULT: BLOCKED`.

## Audit Package Rule

Before a fresh final audit in a new chat, prefer `codex-audit-package-builder` to create or refresh the package. For single-task or bounded Backlog audits inside a still-warm `5.4` thread, a fresh chat is optional if the audit package is already compact and current.

Do not re-read broad development history when the package already contains:

- scope
- changed files
- validation evidence
- explicit risks
- open issues
- prior audit blocker if one exists

## Debug Package Blocker

Immediately block and route to `janus-debug` if input contains open failure/debug indicators:

```text
FEATURE DEBUG
TASK EXECUTION BLOCKED
Auto-Verification FAILED
Verification Status: FAILED
ASSERTION_MISMATCH
Provider-specific failure
Context-Leakage
Fix Applied
Investigate
```

Do not turn a debug package into a final audit PASS.

## Audit Procedure

1. Verify package completeness.
2. Verify all tasks are complete or validation-only mode is explicit.
3. Compare implementation/results against Spec, Backlog, or TestSpec acceptance criteria.
4. Check scope drift and architecture/provider/security boundaries.
5. Check test evidence, including whether tests are relevant and not fake core assertions.
6. Check regression risk outside declared scope.
7. Check precheck compliance where applicable.
8. For BLOCKED, PASS WITH FIXES, or high-risk findings, targeted-search `WHAT_I_LEARNED.md` for matching prior tripwires before deciding final routing.
9. If this is a re-audit after a previously blocked audit, review only the blocker-related delta first, then widen scope only if the new evidence suggests spillover.
10. Decide exactly one result: `PASS`, `PASS WITH FIXES`, or `BLOCKED`.

## Decision Rules

- `PASS`: requirements met, tests green, no relevant blockers, manual evidence present or N/A with reason.
- `PASS WITH FIXES`: only small safe documentation, metadata, or non-architectural fixes remain and are already applied or explicitly non-blocking; no product, test, security, provider, or release risk may remain open.
- `BLOCKED`: missing/failed evidence, incomplete tasks, unclear package, scope drift, security/privacy/provider risk, unresolved debug, failed manual test, or non-deterministic assessment.

A bare `ok` or similar acknowledgement is never a valid audit handoff replacement.

## Re-Audit Loop Rule

If the audit is `BLOCKED` and the issue is locally fixable, do not force a full restart. Hand back a narrow re-audit package update path:

- identify the exact blocker category
- name the minimum files or evidence that must change
- require the existing audit package to be updated, not rebuilt from scratch
- route back to `janus-executioner`, `janus-debug`, or `janus-preimplementation-check` with a blocker-focused copy prompt

Prefer a same-chat re-audit after the fix when all are true:

- the scope is still the same task/backlog item
- no new architecture or provider decision was introduced
- the updated audit package contains a short delta summary

Recommend a fresh audit chat only when:

- the blocker changed the scope materially
- multiple new files or subsystems were touched
- the first blocker exposed a broader security/privacy/provider risk
- the audit package is no longer compact

## Spec Done Rule

Only on `PASS` or `PASS WITH FIXES`, if a Spec file is bound:

- Add or update `## SPEC IMPLEMENTATION METADATA`.
- Set `Implementation Status: DONE`.
- Set `Final Audit: PASS | PASS WITH FIXES`.
- Set completion date.
- Include validation evidence.
- Move to `documentation/SPEC/Spec Done/<original-filename>.md` unless already there.
- Do not overwrite an existing target file; block on collision.

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

If no push happens or push fails, the audit result or handoff must explicitly say that a remote such as GitHub may not contain the latest CURRENT_STATE yet.

## Output Contract

Use:

```text
FINAL AUDIT RESULT: PASS | PASS WITH FIXES | BLOCKED
Audit Model To Use: <model/tier>
Canonical State: PASS | BLOCKED | NEEDS_INFO | HANDOFF

Audit Scope:
- Spec:
- Task:
- Backlog Item:
- TestSpec/TestRun:
- Changed Files:

Testmatrix:
- <command/evidence>: PASS | FAIL | N/A WITH REASON

Findings:
- NONE
```

For `BLOCKED`, also include:

```text
Blocked By:
- <single primary blocker>

Re-Audit Trigger:
- <what must be true before re-audit>

Audit Package Delta Required:
- <exact section or evidence updates required in AUDIT_PACKAGE.md>
```

For `PASS` or `PASS WITH FIXES`, end with:

```text
NEXT_SKILL_HANDOFF
Target Skill: janus-documentation-update
Canonical State: HANDOFF
Required Artifacts: Spec or N/A WITH REASON, Task/TestRun, Backlog Item, Final Audit Result, Changed Files, Test Results, Evidence Paths, Manual Janus Evidence
Evidence Paths: <paths>
Failure Code: N/A
Changed Files: <files>
Decision: HANDOFF
Reason: FINAL AUDIT RESULT PASS | PASS WITH FIXES; documentation sync required.
Copy Prompt: Use janus-documentation-update with this audit result and evidence package.
```

For `BLOCKED`, hand off to `janus-debug`, `janus-executioner`, or `janus-preimplementation-check` with exact reason, exact required artifacts, and the minimum audit-package delta needed before re-audit.
If control moves to ChatGPT for `BLOCKED`, `UNCLEAR_EVIDENCE`, or `RISK_ESCALATION`, emit exactly one compact fenced `text` block with the blocker, bound evidence paths, minimum next action, and exact next skill when known.
If `PASS` or `PASS WITH FIXES` stays in the same warm Codex context, naming `Target Skill: janus-documentation-update` is enough; across actor or chat boundaries, emit exactly one compact fenced `text` handoff block.

## Validator

When an audit report is saved, run:

```powershell
python C:\Users\pruve\.codex\skills\janus-final-audit\scripts\validate_final_audit.py <path-to-final-audit.md>
```
