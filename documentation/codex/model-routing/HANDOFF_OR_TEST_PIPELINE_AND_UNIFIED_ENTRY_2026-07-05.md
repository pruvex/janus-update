# Codex Handoff: Test-Pipeline OR-Lane + Unified Entry Point + Model Registry

**Date:** 2026-07-05  
**Status:** READY FOR IMPLEMENTATION PLANNING  
**Scope:** Codex development-environment improvement only. No Janus product backlog item. No production routing activation. No canonical routing-table update. No Git/release/final-audit authority for OpenRouter.

**Requested by:** User review of OpenRouter delegation architecture for Codex token savings.

**Goal:** Reduce Codex token burn by delegating bounded work to proven OpenRouter models, while Codex remains orchestrator, reviewer, validator, and final acceptance owner.

---

## 0. Executive Summary

Two implementation tracks are bundled in this handoff:

| Track | What | Why |
| --- | --- | --- |
| **A** | Promote **Strong OR Test Worker** from pilot to everyday operator lane | Biggest remaining token-burn gap: bounded test fixture/helper authoring |
| **B** | Introduce **central Model Registry** + **Unified Entry Point** (`janus_or_delegate.py`) | Reduce orchestration overhead, eliminate model/doc drift, enforce ROI gates consistently |

Both tracks preserve existing governance:

- `1 = Codex` / `2 = OR` operator choice (with smarter defaults)
- proposal-first or assist-only lanes
- no delegated Git, release, audit PASS, or broad repo writes
- Codex reviews all OR artifacts before acceptance

---

## 1. Current State (Source of Truth)

### 1.1 What already works

| Lane | Skill | Class | OR model (current) | Status |
| --- | --- | --- | --- | --- |
| Execution patch | `janus-executioner` | `execution_patch_candidate` | `moonshotai/kimi-k2.5` | `OR_PROPOSAL_FIRST`, live evidence |
| Execution write-apply | `janus-executioner` | `execution_write_apply_candidate` | accepted-source + deterministic apply | `OR_PROPOSAL_FIRST`, audited foundation |
| Debug hypotheses | `janus-debug` | `debug_hypothesis_review` | `qwen/qwen3-coder-30b-a3b-instruct` | `OR_ASSIST_ONLY`, live evidence |
| Test triage | `janus-test-pipeline` | `test_result_triage_review` | `qwen/qwen3-coder-30b-a3b-instruct` | `OR_ASSIST_ONLY`, live evidence |
| Generator review | `janus-test-pipeline` | `generator_review` | `openai/gpt-oss-20b` via structured local executor | `STRUCTURED_LOCAL_INTERIM` |
| Spec/draft lanes | multiple skills | various draft classes | mostly `qwen/qwen3-coder-30b-a3b-instruct` | `OR_PROPOSAL_FIRST` |

### 1.2 Main gap

**Strong OR Test Worker** exists in skill guidance and scripts but is not yet a clean everyday lane:

- Skill: `janus-test-pipeline` → section `Strong OR Test Worker Gate`
- Runner: `test_pipeline_sidecar_write_pilot_runner.py`
- Worker backend: `isolated_aider_workspace_runner.py`
- Budget profile already exists: `strong_test_worker` in `or_task_budget_profiles_2026-06-19.json`
- Shadow eval bundle: `development/openrouter-skill-tests/janus-worker-gateway-shadow-eval/`

This lane should become the primary OR workhorse for **bounded test fixture/helper authoring**, not live Playwright execution or final PASS decisions.

### 1.3 Main pain points

1. **Fragmentation:** Skills reference many runners directly.
2. **Model drift:** eligibility config, SKILL.md files, and operator inventories disagree on default models.
3. **ROI gate underused:** not all lanes enforce token ROI before showing `2 = OR`.
4. **Operator friction:** manual `1/2` choice on every call.

---

## 2. Track A — Test-Pipeline OR-Lane (Strong OR Test Worker)

### 2.1 Lane definition

**New canonical task class:** `test_fixture_worker`

| Property | Value |
| --- | --- |
| Lane class | `OR_PROPOSAL_FIRST` |
| Skill owner | `janus-test-pipeline` |
| Backend | `isolated_aider_workspace_runner.py` via `test_pipeline_sidecar_write_pilot_runner.py` |
| Primary OR model | `moonshotai/kimi-k2.5` |
| Fallback OR model | `qwen/qwen3-coder-30b-a3b-instruct` |
| Budget profile | `strong_test_worker` |
| Worker profile | `aider-openrouter-kimi` (fallback: `aider-openrouter-qwen`) |

### 2.2 What OR may do

- Write/adjust one bounded test artifact in isolated temp workspace
- Run only explicit `pre_commands` / `post_commands` from worker package
- Return: `RESULT.json`, `RESULT.md`, `DIFF.patch`, `FILES_CHANGED.txt`, `CHECKS.log`, `COST.json`

### 2.3 What OR must NOT do

- Open-ended Playwright/live test execution
- Mutate result JSON or generated plan/runner by hand
- Declare final PASS, release readiness, or Backlog routing
- Git actions, secrets, or edits outside allowlist

### 2.4 Eligibility gate (show `2 = OR` only when ALL true)

1. One bound `TEST_RUN_ID` or one bounded test target
2. Worker package validates via `janus_worker_contract`
3. Explicit non-empty allowlist
4. `redaction_ready: true`
5. ROI gate `POSITIVE` (see 3.4)
6. Session budget under `strong_test_worker` cap

### 2.5 Implementation tasks

**A1** — Register `test_fixture_worker` in `bounded_or_worker_eligibility_2026-06-17.json`

**A2** — Wire route in `codex_bounded_delegation_dispatcher.py` → `test_pipeline_sidecar_write_pilot_runner.py`

**A3** — Add template: `fixtures/test_fixture_worker_package_template.json`

**A4** — Add no-live fixture + `tests/test_test_fixture_worker_lane.py`

**A5** — Update `janus-test-pipeline/SKILL.md` with decision table:

| Work type | Path |
| --- | --- |
| TestSpec → TestPlan | local compiler |
| Generator review only | `generator_review` |
| Bounded fixture/helper write | `test_fixture_worker` |
| Live Playwright | `LIVE_TEST_EXECUTION` + user approval |
| Failure interpretation | `test_result_triage_review` |
| Retest audit | Codex `DIAMOND_RETEST_AUDIT` |

**A6** — Live pilot after no-live PASS: `WF-TEST-FIXTURE-OR-PILOT-001`

---

## 3. Track B — Model Registry + Unified Entry Point

### 3.1 New registry

**File:** `documentation/codex/model-routing/config/or_model_registry.json`

Single source for per-lane:

- `primary_model`, `fallback_model`
- `lane_class`, `budget_profile`, `entry_runner`
- `operator_gate_visibility`, `evidence_status`
- `minimum_net_codex_saved_tokens`

Initial lanes: `execution_patch_candidate`, `execution_write_apply_candidate`, `debug_hypothesis_review`, `test_result_triage_review`, `test_fixture_worker`, `generator_review`, `quickchange_patch_review`.

### 3.2 Registry loader

**File:** `scripts/or_model_registry.py` + `tests/test_or_model_registry.py`

### 3.3 Unified entry

**File:** `scripts/janus_or_delegate.py`

```powershell
python documentation/codex/model-routing/scripts/janus_or_delegate.py `
  --lane <lane_id> `
  --workflow-id <WORKFLOW-ID> `
  --operator-choice <prompt|local|delegated> `
  [--input-package-json <path>] `
  [--estimated-or-cost <usd>] `
  [--cost-estimate-confidence-percent <0-100>] `
  [--estimated-codex-saved-tokens <n>] `
  [--estimated-codex-or-overhead-tokens <n>] `
  [--minimum-net-codex-saved-tokens <n>] `
  [--dry-run]
```

Behavior:

1. Load lane from registry
2. Check eligibility + budget + ROI
3. Gate modes:
   - visibility not approved → Codex-only
   - ROI negative → Codex-only
   - ROI positive → recommend `2=OR`
   - budget exceeded → Codex-only with reason
4. Route to existing `entry_runner` (thin wrapper, no duplicate logic)
5. Show session budget in gate output

### 3.4 ROI minimums

| Lane | min net saved tokens |
| --- | ---: |
| `quickchange_patch_review` | 3000 |
| `generator_review` | 3000 |
| `debug_hypothesis_review` | 5000 |
| `test_result_triage_review` | 8000 |
| `test_fixture_worker` | 8000 |
| `execution_patch_candidate` | 10000 |
| `execution_write_apply_candidate` | 12000 |

### 3.5 Refactor tasks

**B1** — registry + loader + tests  
**B2** — `janus_or_delegate.py` + tests  
**B3** — eligibility config references registry lanes  
**B4** — dispatcher becomes thin shim to unified entry  
**B5** — skills use unified entry in SKILL.md  
**B6** — new `CURRENT_OR_STATE.md`; dated summaries become evidence only

---

## 4. Implementation Order

| Phase | Tasks | Stop condition |
| --- | --- | --- |
| 1 | B1 | tests green |
| 2 | B2 | dry-run routes debug/triage/execution |
| 3 | A1–A4 | `test_fixture_worker` no-live PASS |
| 4 | A5, B5 | skills wired |
| 5 | A6 | one live pilot with evidence |
| 6 | B3, B4, B6 | no model drift |

No live OpenRouter without `OPENROUTER_API_KEY` + explicit user approval.

---

## 5. Acceptance Criteria

**Track A:** lane registered, dispatcher wired, no-live tests PASS, live pilot accepted by Codex review, cost ≤ cap.

**Track B:** registry is single model source, unified entry documented in skills, ROI enforced, session budget visible, `CURRENT_OR_STATE.md` current.

**Governance:** no production routing, no delegated Git/release/audit, no secrets in repo, Codex final owner.

---

## 6. Copy-Paste Prompt For Codex

```text
Read and implement:
documentation/codex/model-routing/HANDOFF_OR_TEST_PIPELINE_AND_UNIFIED_ENTRY_2026-07-05.md

Constraints:
- Codex development-environment scope only
- no production routing activation
- no Git commit unless I explicitly ask
- no live OpenRouter without my explicit approval
- preserve Codex-owned review/acceptance for all OR lanes

Execute in order:
Phase 1 (registry + loader + tests)
Phase 2 (janus_or_delegate.py + tests)
Phase 3 (test_fixture_worker lane registration + no-live tests)
Stop after Phase 3 and report status before any live pilot.
```

---

## 7. Open Questions

1. Positive ROI: auto-default `2=OR` or only recommend? (Handoff: recommend-first.)
2. Live pilot model: `kimi-k2.5` or `qwen3-coder-30b` first?
3. One PR or two (registry/entry vs test lane)?

---

*End of handoff.*
