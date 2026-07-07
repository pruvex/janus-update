# Codex Master Handoff: Tri-Modal Delegation + Task List + Example Packages

**Date:** 2026-07-05  
**Status:** READY FOR IMPLEMENTATION  
**Scope:** Codex development-environment orchestration only. No Janus product routing. No production Auto Router. No delegated Git/release/final-audit authority.

---

## 0. What this handoff bundle contains

| Artifact | Path | Purpose |
| --- | --- | --- |
| Tri-modal architecture | `HANDOFF_TRI_MODAL_DELEGATION_ROUTING_2026-07-05.md` | `1=Codex / 2=Cursor / 3=OR` design + `janus_delegate.py` |
| OR foundation | `HANDOFF_OR_TEST_PIPELINE_AND_UNIFIED_ENTRY_2026-07-05.md` | OR lanes, ROI, test_fixture_worker baseline |
| Routing manifest | `config/delegation_routing_manifest.json` | lane → backend → model |
| Task list JSON | `config/delegation_task_list_2026-07-05.json` | concrete tasks for executioner/debug/test-pipeline |
| Task list MD | `config/delegation_task_list_2026-07-05.md` | human-readable flows |
| Example packages | `fixtures/examples/*.json` | copy-safe input packages per lane |
| This file | `HANDOFF_MASTER_TRI_MODAL_WITH_EXAMPLES_2026-07-05.md` | single entry point for Codex |

---

## 1. Operator model

Every eligible bounded task shows:

```text
1 = Codex
2 = Cursor
3 = OpenRouter
```

Codex:

1. matches work to `task_id` / `lane_id` from the task list
2. loads routing from the manifest
3. shows recommendation (`recommended_backend`)
4. waits for operator choice
5. delegates with the model from the task's `models` block
6. reviews normalized artifacts before accept/reject

**Never auto-delegate without visible operator choice.**

---

## 2. Implementation target

### New scripts to build

| Script | Purpose |
| --- | --- |
| `scripts/or_model_registry.py` | optional thin loader; prefer manifest |
| `scripts/janus_delegate.py` | unified `1/2/3` entry |
| `scripts/janus_cursor_worker_runner.py` | Cursor CLI wrapper |
| `scripts/delegation_task_list.py` | validate task list against manifest |

### Existing scripts to reuse

| Backend | Existing runner |
| --- | --- |
| OpenRouter | `codex_bounded_delegation_dispatcher.py`, lane `*_runner.py`, `codex_dev_workhorse_runner.py`, `test_pipeline_sidecar_write_pilot_runner.py` |
| Cursor | new wrapper around `agent -p` |
| Codex | local path only; no external invoke |

---

## 3. Task list quick map

| Task ID | Skill | Recommend | Example package |
| --- | --- | --- | --- |
| TASK-DBG-001 | janus-debug | OR | `fixtures/examples/debug_hypothesis_review_input_package_example.json` |
| TASK-DBG-002 | janus-debug | Cursor | `fixtures/examples/debug_repro_investigation_input_package_example.json` |
| TASK-TP-001 | janus-test-pipeline | Codex | compiler only; no package |
| TASK-TP-002 | janus-test-pipeline | OR | `fixtures/examples/generator_review_input_package_example.json` |
| TASK-TP-003 | janus-test-pipeline | Cursor | `fixtures/examples/test_fixture_worker_input_package_example.json` |
| TASK-TP-004 | janus-test-pipeline | Codex | live test; user `OK START LIVE TEST` |
| TASK-TP-005 | janus-test-pipeline | OR | `fixtures/examples/test_result_triage_input_package_example.json` |
| TASK-TP-006 | janus-test-pipeline | Codex | retest audit |
| TASK-EX-001 | janus-executioner | Cursor | `fixtures/examples/execution_patch_candidate_input_package_example.json` |
| TASK-EX-002 | janus-executioner | Cursor | `fixtures/examples/execution_write_apply_input_package_example.json` |
| TASK-EX-003 | janus-executioner | Codex | validation/completion |

---

## 4. Example invocation patterns

### 4.1 Unified entry (target state)

```powershell
python documentation/codex/model-routing/scripts/janus_delegate.py `
  --lane debug_hypothesis_review `
  --workflow-id WF-DBG-HYPOTHESIS-EXAMPLE-001 `
  --operator-choice prompt `
  --input-package-json documentation/codex/model-routing/fixtures/examples/debug_hypothesis_review_input_package_example.json `
  --estimated-codex-saved-tokens 12000 `
  --estimated-delegation-overhead-tokens 4000
```

Operator answers `1`, `2`, or `3`.

### 4.2 Transitional OR path (until `janus_delegate.py` exists)

```powershell
python documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py `
  --task-label "Bounded debug hypothesis review" `
  --normal-target-model "5.4 high" `
  --operator-choice prompt `
  --workflow-id WF-DBG-HYPOTHESIS-EXAMPLE-001 `
  --estimated-or-cost 0.0005 `
  --cost-estimate-confidence-percent 85 `
  --input-package-json documentation/codex/model-routing/fixtures/examples/debug_hypothesis_review_input_package_example.json
```

### 4.3 Transitional Cursor path (after `janus_cursor_worker_runner.py` exists)

```powershell
python documentation/codex/model-routing/scripts/janus_cursor_worker_runner.py `
  --lane debug_repro_investigation `
  --workflow-id WF-DBG-REPRO-EXAMPLE-001 `
  --model composer-2.5 `
  --input-package-json documentation/codex/model-routing/fixtures/examples/debug_repro_investigation_input_package_example.json `
  --allowlist-file documentation/codex/model-routing/fixtures/examples/allowlists/debug_repro_allowlist.txt
```

### 4.4 Test fixture worker

**Cursor (recommended):**

```powershell
python documentation/codex/model-routing/scripts/janus_delegate.py `
  --lane test_fixture_worker `
  --workflow-id WF-TEST-FIXTURE-EXAMPLE-001 `
  --operator-choice 2 `
  --input-package-json documentation/codex/model-routing/fixtures/examples/test_fixture_worker_input_package_example.json `
  --allowlist-file documentation/codex/model-routing/fixtures/examples/allowlists/test_fixture_allowlist.txt
```

**OpenRouter (fallback):**

```powershell
python documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py `
  --testspec-path documentation/TEST_SPEC/EXAMPLE-FEATURE-001.md `
  --test-run-id TEST-RUN-042 `
  --operator-choice 2 `
  --workflow-id WF-TEST-FIXTURE-EXAMPLE-001 `
  --sidecar-model moonshotai/kimi-k2.5 `
  --isolated-aider-package-json documentation/codex/model-routing/fixtures/examples/test_fixture_worker_package_example.json `
  --estimated-or-cost 0.05 `
  --cost-estimate-confidence-percent 80
```

---

## 5. Implementation phases

| Phase | Deliverable | Use examples |
| --- | --- | --- |
| **1** | manifest loader + task-list validator | validate all `fixtures/examples/*.json` lane ids exist |
| **2** | `janus_delegate.py` dry-run | print gate for each example package |
| **3** | `janus_cursor_worker_runner.py` mocked tests | debug_repro + test_fixture + execution_patch examples |
| **4** | wire OR through `janus_delegate.py --operator-choice 3` | existing runners, no behavior change |
| **5** | update skills to `1/2/3` | executioner, debug, test-pipeline |
| **6** | no-live validation suite | pytest over all example packages |
| **7** | one live pilot per backend | only with explicit user approval |

**Stop after phase 6 unless user approves live calls.**

---

## 6. Validation commands for example packages

```powershell
# Task list sanity
python documentation/codex/model-routing/scripts/delegation_task_list.py validate `
  --manifest documentation/codex/model-routing/config/delegation_routing_manifest.json `
  --tasks documentation/codex/model-routing/config/delegation_task_list_2026-07-05.json

# Dry-run unified entry (after implementation)
python documentation/codex/model-routing/scripts/janus_delegate.py `
  --lane debug_hypothesis_review `
  --workflow-id WF-DBG-HYPOTHESIS-EXAMPLE-001 `
  --operator-choice prompt `
  --input-package-json documentation/codex/model-routing/fixtures/examples/debug_hypothesis_review_input_package_example.json `
  --dry-run
```

---

## 7. Acceptance criteria

- [ ] All example packages validate against manifest lanes
- [ ] `janus_delegate.py` shows `1/2/3` with recommendation for each example
- [ ] Cursor path blocked when `CURSOR_API_KEY` missing
- [ ] OR path blocked when `OPENROUTER_API_KEY` missing
- [ ] ROI negative hides external options
- [ ] `live_test_execution` and `diamond_retest_audit` remain Codex-only
- [ ] Example packages contain no secrets
- [ ] Skills document unified entry, not scattered runners

---

## 8. Governance boundaries (unchanged)

- no production routing
- no delegated Git/release/final-audit PASS
- no secrets in packages or logs
- Codex final reviewer on all backends
- live external calls only with explicit user approval

---

## 9. Copy-paste prompt for Codex

```text
Read and implement this bundle in order:

1. documentation/codex/model-routing/HANDOFF_MASTER_TRI_MODAL_WITH_EXAMPLES_2026-07-05.md
2. documentation/codex/model-routing/HANDOFF_TRI_MODAL_DELEGATION_ROUTING_2026-07-05.md
3. documentation/codex/model-routing/HANDOFF_OR_TEST_PIPELINE_AND_UNIFIED_ENTRY_2026-07-05.md

Routing artifacts:
- documentation/codex/model-routing/config/delegation_routing_manifest.json
- documentation/codex/model-routing/config/delegation_task_list_2026-07-05.json
- documentation/codex/model-routing/fixtures/examples/

Constraints:
- Keep OpenRouter as option 3
- Add Cursor as option 2
- Codex remains option 1 and final acceptance owner
- No production routing activation
- No Git commit unless I explicitly ask
- No live Cursor or OpenRouter calls without my explicit approval

Execute phases 1-6 only:
- manifest loader + task-list validator
- janus_delegate.py dry-run
- janus_cursor_worker_runner.py with mocked tests
- wire OR through janus_delegate.py option 3
- update janus-executioner, janus-debug, janus-test-pipeline skills to 1/2/3 gate
- pytest validation for all fixtures/examples packages

After phase 6, stop and report:
- changed files
- pytest output
- sample dry-run gate output for TASK-DBG-001, TASK-TP-003, TASK-EX-001
```

---

## 10. File tree added by this bundle

```text
documentation/codex/model-routing/
  HANDOFF_MASTER_TRI_MODAL_WITH_EXAMPLES_2026-07-05.md
  HANDOFF_TRI_MODAL_DELEGATION_ROUTING_2026-07-05.md
  HANDOFF_OR_TEST_PIPELINE_AND_UNIFIED_ENTRY_2026-07-05.md
  config/
    delegation_routing_manifest.json
    delegation_task_list_2026-07-05.json
    delegation_task_list_2026-07-05.md
  fixtures/examples/
    README.md
    debug_hypothesis_review_input_package_example.json
    debug_repro_investigation_input_package_example.json
    generator_review_input_package_example.json
    test_fixture_worker_input_package_example.json
    test_fixture_worker_package_example.json
    test_result_triage_input_package_example.json
    execution_patch_candidate_input_package_example.json
    execution_write_apply_input_package_example.json
    allowlists/
      debug_repro_allowlist.txt
      test_fixture_allowlist.txt
      execution_patch_allowlist.txt
```

---

*End of master handoff.*
