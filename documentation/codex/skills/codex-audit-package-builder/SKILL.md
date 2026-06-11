---
name: codex-audit-package-builder
description: Use before a final independent review to create or refresh a compact AUDIT_PACKAGE.md from implementation artifacts, changed files, validation output, known risks, and re-audit blocker deltas. Optimized for fresh 5.5/high final audit handoff without carrying development chat history.
metadata:
  short-description: Build compact final audit packages
---

# Codex Audit Package Builder

Create a compact final-review package so the final audit runs with minimal noise.
This is a Codex-led package-building skill. It prepares bounded evidence for `janus-final-audit`; it does not perform the final audit decision.

## Scope

- Use after implementation and validation.
- Summarize facts, not the development conversation.
- Prefer artifact paths and concise summaries over copied logs.
- Include full logs only when they are current failures.
- For blocked audits, update the existing package with a small delta instead of rebuilding from scratch.
- Use only bound evidence: changed files, validation evidence, known risks, relevant audit notes, unresolved blockers, and explicitly named artifacts.
- Do not reconstruct broad chat history, invent product decisions, add requirements, or infer unverified scope.
- Do not decide `PASS`, `PASS WITH FIXES`, or `BLOCKED`; that belongs to `janus-final-audit`.
- Do not run tests, builds, Git actions, release actions, or publish steps.
- Do not treat bare `ok` as a handoff, Git, release, or audit approval.

## Required Evidence

An audit package must include or explicitly mark as `MISSING` / `N/A WITH REASON`:

- changed files
- validation commands and results
- known risks
- relevant audit notes or prior blocker notes
- unresolved blockers
- bound Spec, Task, Backlog item, TestSpec/TestRun, or `N/A WITH REASON`
- preimplementation result when applicable
- manual Janus evidence when applicable

## Workflow

1. Run `documentation/codex/skills/codex-audit-package-builder/scripts/build_audit_package.py` and pass `--cwd <target-workspace>`.
2. Add or verify goal, scope, changed files, diff summary, validation, risks, and open issues.
3. If the worktree is dirty, pass `--only <path>` for the relevant task files so unrelated diffs stay out of the package.
4. If re-auditing after a blocker, pass a blocker label and a short delta summary.
5. Pass the minimum final-audit input fields explicitly: `Spec` or `N/A WITH REASON`, task file, backlog item, precheck result, manual Janus evidence, and pipeline completion status.
6. When the workspace is not a Git checkout, pass important artifact paths with `--include` so the package still has provenance.
7. Return a copy-paste final-audit handoff as one fenced `text` block so it renders as a gray box in Codex.

If required evidence is missing or contradictory, do not build a confident audit package. Return a compact blocker summary and route to caller review, `janus-debug`, `janus-test-pipeline`, or the skill that can produce the missing evidence.

## Script Contract

- Default output path: `<cwd>/AUDIT_PACKAGE.md` unless `--out` overrides it.
- Core CLI options:
  - `--cwd`, `--out`, `--goal`
  - `--validation-file`, `--notes-file`
  - `--risks`, `--open-issues`
  - `--reaudit-blocker`, `--reaudit-delta`, `--prior-audit`
  - `--spec-status`, `--task-file`, `--precheck-file`
  - `--backlog-file`, `--backlog-marker`
  - `--manual-janus-evidence`, `--pipeline-completion`
  - `--only`, `--include`
- The script renders bound excerpts for backlog, task, and precheck inputs and emits `MISSING FILE` or `N/A WITH REASON` markers when those inputs are absent.
- Re-audit deltas render as a compact section combining the primary blocker, prior audit/package reference, and the current delta summary.

## Package Sections

- Goal
- Scope Rules
- Bound Audit Inputs
- Backlog Item
- Task Acceptance Scope
- Pre-Implementation Check
- Changed Files
- Artifact Inventory
- Diff Summary
- Validation
- Notes
- Risks
- Open Issues
- Re-Audit Delta
- Final Audit Handoff

## Output

The generated package ends with this handoff block:

```text
NEW_CHAT_HANDOFF
NEXT: final-skill-audit
MODEL: 5.5/high
PASS: <AUDIT_PACKAGE.md>
ASK: Lade nur dieses Paket im neuen Chat und starte dann den Final Audit.
DROP: dev chat history
```

When presenting the next repo-skill step to the user, route that handoff to `janus-final-audit` without widening scope or turning the builder itself into a final-audit decision step.

For bounded same-thread re-audits after a local blocker fix, `5.4/high` is acceptable when the package stays compact and the risk did not escalate.

For same-context handoff, naming `NEXT: janus-final-audit` with the package path is enough. For any actor or fresh-chat boundary, emit exactly one compact fenced `text` block.
