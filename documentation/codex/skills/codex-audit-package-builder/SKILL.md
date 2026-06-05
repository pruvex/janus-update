---
name: codex-audit-package-builder
description: Use before a final independent review to create or refresh a compact AUDIT_PACKAGE.md from implementation artifacts, changed files, validation output, known risks, and re-audit blocker deltas. Optimized for fresh 5.5/high final audit handoff without carrying development chat history.
metadata:
  short-description: Build compact final audit packages
---

# Codex Audit Package Builder

Create a compact final-review package so the final audit runs with minimal noise.

## Scope

- Use after implementation and validation.
- Summarize facts, not the development conversation.
- Prefer artifact paths and concise summaries over copied logs.
- Include full logs only when they are current failures.
- For blocked audits, update the existing package with a small delta instead of rebuilding from scratch.

## Workflow

1. Run `scripts/build_audit_package.py` from the target workspace.
2. Add or verify goal, scope, changed files, diff summary, validation, risks, and open issues.
3. If the worktree is dirty, pass `--only <path>` for the relevant task files so unrelated diffs stay out of the package.
4. If re-auditing after a blocker, pass a blocker label and a short delta summary.
5. Pass the minimum final-audit input fields explicitly: `Spec` or `N/A WITH REASON`, task file, backlog item, precheck result, manual Janus evidence, and pipeline completion status.
6. When the workspace is not a Git checkout, pass important artifact paths with `--include` so the package still has provenance.
7. Return a copy-paste final-audit handoff as one fenced `text` block so it renders as a gray box in Codex.

## Package Sections

- Goal
- Scope Rules
- Changed Files
- Artifact Inventory
- Diff Summary
- Validation
- Notes
- Risks
- Open Issues
- Re-Audit Delta
- Bound Audit Inputs
- Backlog Item
- Task Acceptance Scope
- Pre-Implementation Check
- Final Audit Handoff

## Output

Return the package path and this copy-paste handoff in one fenced `text` block:

```text
NEW_CHAT_HANDOFF
NEXT: final-skill-audit
MODEL: 5.5/high
PASS: <AUDIT_PACKAGE.md>
ASK: Lade nur dieses Paket im neuen Chat und starte dann den Final Audit.
DROP: dev chat history
```

For bounded same-thread re-audits after a local blocker fix, `5.4/high` is acceptable when the package stays compact and the risk did not escalate.
