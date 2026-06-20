# TASK-SPEC21.4 Skill-Context Evidence

Canonical State: PASS
Scope: installed `janus-debug` and `janus-test-pipeline` skill-context visibility evidence only
Live OR Calls: `0`

## Installed Skill Sync

- Repo and installed `janus-debug` `SKILL.md` hashes match after sync.
- Repo and installed `janus-test-pipeline` `SKILL.md` hashes match after sync.
- The installed copies now contain the bounded consumer-entry wording for:
  - `build_consumer_input_package(...)`
  - `run_consumer_flow(...)`
  - visible `1 = Codex` / `2 = OR-Arbeitspferd`

## Debug Skill Evidence

- Workflow ID: `TASK-SPEC21-4-INSTALLED-DEBUG-001`
- Prompt artifact: `documentation/codex/model-routing/debug-review-runs/TASK-SPEC21-4-INSTALLED-DEBUG-001/consumer_operator_choice_prompt.json`
- Delegated artifact: `documentation/codex/model-routing/debug-review-runs/TASK-SPEC21-4-INSTALLED-DEBUG-001/consumer_operator_choice_delegated.json`
- Validation artifact: `documentation/codex/model-routing/debug-review-runs/TASK-SPEC21-4-INSTALLED-DEBUG-001/validation_summary.json`
- Visible gate evidence:
  - `1 = Codex`
  - `2 = OR-Arbeitspferd`
  - selected model shown
  - estimated cost `0.000400000`
  - confidence `81%`
- Codex-owned delegated outcome evidence:
  - `validation_result = PASS`
  - `final_outcome = DEBUG_HYPOTHESIS_REVIEW_READY_FOR_CODEX_VALIDATION`
  - `codex_owned_outcome_status = DELEGATED_REVIEW_PENDING_CODEX_DECISION`

## Test-Pipeline Skill Evidence

- Workflow ID: `TASK-SPEC21-4-INSTALLED-TRIAGE-001`
- Prompt artifact: `documentation/codex/model-routing/test-triage-runs/TASK-SPEC21-4-INSTALLED-TRIAGE-001/consumer_operator_choice_prompt.json`
- Delegated artifact: `documentation/codex/model-routing/test-triage-runs/TASK-SPEC21-4-INSTALLED-TRIAGE-001/consumer_operator_choice_delegated.json`
- Validation artifact: `documentation/codex/model-routing/test-triage-runs/TASK-SPEC21-4-INSTALLED-TRIAGE-001/validation_summary.json`
- Visible gate evidence:
  - `1 = Codex`
  - `2 = OR-Arbeitspferd`
  - selected model shown
  - estimated cost `0.000500000`
  - confidence `79%`
- Codex-owned delegated outcome evidence:
  - `validation_result = PASS`
  - `final_outcome = TEST_RESULT_TRIAGE_REVIEW_READY_FOR_CODEX_VALIDATION`
  - `codex_owned_outcome_status = DELEGATED_REVIEW_PENDING_CODEX_DECISION`

## Evidence Command

```powershell
python documentation/codex/model-routing/scripts/generate_task_spec21_4_skill_context_evidence.py
```

## Acceptance Notes

- Evidence is local-fixture-only and bounded to the two approved pilot classes.
- No production routing was activated.
- No live OR call was made.
- The evidence closes the final-audit blocker `SPEC21_4_REAL_SKILL_CONTEXT_EVIDENCE_MISSING` without widening Spec 21 scope.
