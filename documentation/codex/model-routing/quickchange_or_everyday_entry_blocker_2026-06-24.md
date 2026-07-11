## Quickchange OR Everyday Entry Blocker

Date: `2026-06-24`
Canonical state: `PASS`
Scope: bounded operator-facing OR entry for `janus-quickchange`

### Summary

The earlier contract contradiction at the shared quickchange dispatcher gate is now resolved.

Historical blocker:

- the repo and installed `janus-quickchange` skills still describe a visible bounded OR gate
- the shared dispatcher had rejected `quickchange_patch_review` at the entry boundary with `OR_NOT_ELIGIBLE`
- the rejection reason had been `SKILL_NOT_ALLOWED`
- the evidence status had been `LEGACY_DIRECT_ENTRY_DISABLED`

Resolution result:

- `quickchange_patch_review` is again `OR_ALLOWED` in the shared bounded eligibility contract
- the focused gate regression test now expects the visible prompt path again
- the shared dispatcher prompt gate is restored as the bounded everyday OR entry for this lane

### Evidence

Command:

```powershell
python documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py --task-class quickchange_patch_review --task-label "Quickchange OR gate proof" --normal-target-model "5.4 medium" --operator-choice prompt --workflow-id WF-QC-OR-GATE-001 --editable-path documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md --max-touched-files 1 --selected-or-model deepseek/deepseek-v4-flash --estimated-or-cost 0.00025 --cost-estimate-confidence-percent 68
```

Observed result at blocker discovery time:

- `selected_path`: `codex_only_pre_dispatch`
- `eligibility_result`: `OR_NOT_ELIGIBLE`
- `eligibility_reason_code`: `SKILL_NOT_ALLOWED`
- `evidence_status`: `LEGACY_DIRECT_ENTRY_DISABLED`
- `final_outcome`: `LOCAL_CODEX_PATH_SELECTED`

Operator message:

> Legacy quickchange patch review is no longer OR-eligible at the shared dispatcher entry.

### Resolution evidence

Updated contract:

- `documentation/codex/model-routing/config/bounded_or_worker_eligibility_2026-06-17.json`
  - `quickchange_patch_review` -> `eligibility_result: OR_ALLOWED`
  - `reason_code: ELIGIBILITY_CONFIRMED`
  - `evidence_status: BOUNDED_LIVE_EVIDENCE_CONFIRMED`

Focused regression test:

- `python -m unittest documentation.codex.model-routing.tests.test_bounded_or_worker_gate_prompt`

Restored dispatcher prompt proof:

```powershell
python documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py --task-class quickchange_patch_review --task-label "Quickchange OR gate restore proof" --normal-target-model "5.4 medium" --operator-choice prompt --workflow-id WF-QC-OR-GATE-RESTORE-001 --editable-path documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md --max-touched-files 1 --selected-or-model deepseek/deepseek-v4-flash --estimated-or-cost 0.00025 --cost-estimate-confidence-percent 68
```

### Why this matters

The quickchange skill text and the lived dispatcher behavior are no longer aligned.

This is not a wording-only issue:

- changing the visible label alone would be misleading
- the real issue is that the quickchange shared-entry path is disabled at the dispatcher boundary
- any next fix must decide whether quickchange should:
  - remain disabled at the shared dispatcher entry, with the skill text updated accordingly, or
  - regain an explicit bounded operator-facing OR entry through a new approved implementation slice

### Scope decision

The blocker has been closed by a bounded Lean-Dev contract repair rather than by a product or routing expansion.

### Validation run in this investigation

- `python -m unittest documentation.codex.model-routing.tests.test_bounded_or_worker_gate_prompt`: surfaced the quickchange expectation mismatch while the temporary wording experiment was in progress
- temporary local wording/test edits were reverted in the same work block
- the blocking dispatcher prompt run above reproduced the real behavior from the current worktree

### Conclusion

`janus-quickchange` no longer needs to stay blocked for this shared prompt-gate contradiction. The lane can again be tracked as an operator-facing bounded OR lane, while all existing review-first and no-production-routing boundaries stay unchanged.
