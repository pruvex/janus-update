---
name: janus-final-audit
description: Perform the Janus final quality and release gate after implementation and validation, deciding PASS, PASS WITH FIXES, or BLOCKED against bound artifacts only. Use after execution/precheck/test evidence exists and before documentation update, release, closing Backlog items, or moving Specs to Spec Done.
---

# Janus Final Audit

## Overview

Audit completed Janus work against the bound Spec, Task, Backlog item, TestSpec, changed files, diff, precheck, and evidence. Do not implement, redesign, add requirements, or use chat history as source of truth.

## Source References

Read only when exact legacy wording is needed:

- `C:\KI\Janus-Projekt\.windsurf\workflows\SKILL 6 – DIAMANTSTANDARD FINAL AUDIT.md`
- `C:\KI\Janus-Projekt\documentation\pipeline\PIPELINE_CONTRACT.md`
- `C:\KI\Janus-Projekt\AGENTS.md`

## Model Gate

Before auditing, recommend model/intelligence:

- Low/local deterministic scope: `5.3 codex` or current capable coding model, medium.
- Medium risk or multiple files: `5.3 codex`, high.
- High/critical risk, security, privacy, provider routing, memory, release-critical, unclear evidence, contradictory artifacts, or missing tests: `5.5`, high/very high.

If current setup is weaker than required, stop with a model-switch handoff. Do not perform the audit.

## Required Input

Require a compact audit package:

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

If the package is incomplete, return `FINAL AUDIT RESULT: BLOCKED`.

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
8. Decide exactly one result: `PASS`, `PASS WITH FIXES`, or `BLOCKED`.

## Decision Rules

- `PASS`: requirements met, tests green, no relevant blockers, manual evidence present or N/A with reason.
- `PASS WITH FIXES`: only small safe documentation or non-architectural fixes remain and are already applied or explicitly non-blocking.
- `BLOCKED`: missing/failed evidence, incomplete tasks, unclear package, scope drift, security/privacy/provider risk, unresolved debug, failed manual test, or non-deterministic assessment.

## Spec Done Rule

Only on `PASS` or `PASS WITH FIXES`, if a Spec file is bound:

- Add or update `## SPEC IMPLEMENTATION METADATA`.
- Set `Implementation Status: DONE`.
- Set `Final Audit: PASS | PASS WITH FIXES`.
- Set completion date.
- Include validation evidence.
- Move to `documentation/SPEC/Spec Done/<original-filename>.md` unless already there.
- Do not overwrite an existing target file; block on collision.

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

For `BLOCKED`, hand off to `janus-debug`, `janus-executioner`, or `janus-preimplementation-check` with exact reason and required artifacts.

## Validator

When an audit report is saved, run:

```powershell
python C:\Users\pruve\.codex\skills\janus-final-audit\scripts\validate_final_audit.py <path-to-final-audit.md>
```

