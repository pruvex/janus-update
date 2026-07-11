## Productive Dev-Workhorse Everyday Entry Validation

Date: `2026-06-24`
Task: `BACKLOG-113`
Skill: `janus-executioner`
Canonical state: `PASS`

### Goal

Validate the visible operator-facing everyday entry that the installed `janus-executioner` skill now presents:

- `1 = Codex`
- `2 = OR`

This validation is bounded to the productive Dev-workhorse entry only. It does not enable production routing, does not change canonical routing tables, and does not perform a new live OpenRouter call.

### Scope

- repo skill source `documentation/codex/skills/janus-executioner/SKILL.md`
- installed skill copy `C:\Users\pruve\.codex\skills\janus-executioner\SKILL.md`
- repo skill source `documentation/codex/skills/janus-debug/SKILL.md`
- installed skill copy `C:\Users\pruve\.codex\skills\janus-debug\SKILL.md`
- productive runner `documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py`

### Skill / wording alignment

`rg` evidence confirms:

- repo and installed `janus-executioner` copies both point to `codex_dev_workhorse_runner.py`
- repo and installed `janus-executioner` copies both show `1 = Codex` and `2 = OR`
- repo and installed `janus-debug` copies both keep the visible bounded wording `1 = Codex` and `2 = OR-Arbeitspferd`
- the Dev runbook also points to the productive runner as the canonical visible gate

### Fresh operator-facing validation

#### 1. Prompt gate proof

Command:

```powershell
python documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py --task-class execution_patch_candidate --task-label "BACKLOG-113 everyday entry prompt proof" --normal-target-model "5.4 medium" --operator-choice prompt --workflow-id WF-B113-EVERYDAY-PROMPT-EP-001 --path-id productive_dev_workhorse_path --estimated-or-cost 0.00072 --cost-estimate-confidence-percent 87
```

Result: `PASS`

Observed operator lines:

- `1 = Codex`
- `2 = OR`
- fixed recommended OR model `deepseek/deepseek-v4-flash`
- pre-call cost basis shown
- estimate and confidence shown: `0.000720000`, `87%`

#### 2. execution_patch_candidate OR-branch proof without live OR call

Command:

```powershell
python documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py --task-class execution_patch_candidate --task-label "BACKLOG-113 everyday entry OR proof" --normal-target-model "5.4 medium" --operator-choice or --workflow-id WF-B113-EVERYDAY-OR-EP-001 --path-id productive_dev_workhorse_path --estimated-or-cost 0.00072 --cost-estimate-confidence-percent 87 --execution-input-package documentation/codex/model-routing/execution-review-fixtures/backlog_108_execution_patch_candidate_input_package_current_shape_2026-06-24.json --use-local-or-fixture --or-local-fixture-response-path documentation/codex/model-routing/execution-review-fixtures/direct_or_execution_patch_candidate_current_shape_fixture_response_2026-06-24.json
```

Result: `PASS`

Key outcomes:

- selected path: `direct_or_execution_patch_candidate_then_codex_review`
- validation result: `PASS`
- final outcome: `DIRECT_OR_EXECUTION_PATCH_READY_FOR_CODEX_REVIEW`
- healthcheck status: `PASS`
- generation id present: `gen-direct-or-execution-current-shape-fixture-001`
- actual OR cost displayed to the operator: `0.000633840`

Artifacts:

- `documentation/codex/model-routing/execution-direct-or-runs/WF-B113-EVERYDAY-OR-EP-001/*`
- `documentation/codex/model-routing/productive-dev-workhorse-runs/WF-B113-EVERYDAY-OR-EP-001/*`
- `documentation/codex/model-routing/or_healthcheck_telemetry_direct_or_execution_patch_2026-06-24_WF-B113-EVERYDAY-OR-EP-001.jsonl`
- `documentation/codex/model-routing/or_healthcheck_telemetry_productive_dev_workhorse_2026-06-24_WF-B113-EVERYDAY-OR-EP-001.jsonl`

#### 3. execution_write_apply_candidate delegated proof without live OR call

Command:

```powershell
python documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py --task-class execution_write_apply_candidate --task-label "BACKLOG-113 everyday entry delegated proof" --normal-target-model "5.4 medium" --operator-choice or --workflow-id WF-B113-EVERYDAY-OR-EW-001 --path-id productive_dev_workhorse_path --estimated-or-cost 0.00095 --cost-estimate-confidence-percent 87 --accepted-source-run-dir documentation/codex/model-routing/execution-write-apply-source-bridges/EXEC-WRITE-APPLY-SOURCE-BRIDGE-003
```

Result: `PASS`

Key outcomes:

- selected path: `delegated_execution_write_apply_candidate`
- validation result: `PASS`
- final outcome: `EXECUTION_WRITE_APPLY_CANDIDATE_READY_FOR_CODEX_ACCEPT_REJECT`
- accepted source run dir: `EXEC-WRITE-APPLY-SOURCE-BRIDGE-003`
- healthcheck status: `PASS`
- operator-facing cost line remains explicit: `Tatsaechliche Kosten: N/A (usage missing, fallback documented)`

Artifacts:

- `documentation/codex/model-routing/execution-write-apply-runs/WF-B113-EVERYDAY-OR-EW-001/*`
- `documentation/codex/model-routing/productive-dev-workhorse-runs/WF-B113-EVERYDAY-OR-EW-001/*`
- `documentation/codex/model-routing/or_healthcheck_telemetry_productive_dev_workhorse_2026-06-24_WF-B113-EVERYDAY-OR-EW-001.jsonl`

### Boundaries confirmed

- no new live OR call
- no production routing
- no canonical routing-table update
- no broad write delegation
- Codex remains final reviewer, apply/reject owner, and final task owner

### Conclusion

The visible everyday `janus-executioner` entry is now freshly re-proven from the current worktree:

- the operator sees `1 = Codex` and `2 = OR`
- the OR branch shows a fixed recommended model plus cost/confidence before execution
- the bounded proposal-first OR lane reports actual cost after completion
- the later delegated write-apply lane remains bounded and explicitly Codex-owned

This is sufficient evidence that the operator-facing productive Dev-workhorse entry is practically runnable again without reopening live OR execution in this slice.
