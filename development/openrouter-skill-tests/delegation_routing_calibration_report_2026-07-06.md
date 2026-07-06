# Delegation Routing Calibration Report

- Generated at: `2026-07-06T12:58:30+00:00`
- Lane count: `23`
- Purpose: compare configured OpenRouter routing defaults against bounded local evidence only

| Lane | Task | Samples | Configured | Observed max | Suggested | Status |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| backlog_handoff_review | TASK-BH-001 | 2 | 0.00018 | 0.00017933 | 0.0001883 | ALIGNED |
| backlog_intake_review | TASK-BI-001 | 2 | 0.00018 | 0.00016096 | 0.00016901 | ALIGNED |
| backlog_prioritization_review | TASK-BP-001 | 2 | 0.00035 | 0.0003101 | 0.00032561 | ALIGNED |
| debug_hypothesis_review | TASK-DBG-001 | 4 | 0.00048 | 0.00045678 | 0.00047962 | ALIGNED |
| debug_repro_investigation | TASK-DBG-002 | 0 | - | - | - | NO_EVIDENCE |
| diamond_retest_audit | TASK-TP-006 | 0 | - | - | - | NO_EVIDENCE |
| documentation_draft_review | TASK-DU-001 | 0 | 0 | - | - | NO_EVIDENCE |
| execution_patch_candidate | TASK-EX-001 | 60 | - | 0.0810794 | 0.00467031 | HIGH_VARIANCE_REVIEW_SCOPE |
| execution_write_apply_candidate | TASK-EX-002 | 0 | - | - | - | NO_EVIDENCE |
| feature_design_review | TASK-FD-001 | 0 | 0.00024 | - | - | NO_EVIDENCE |
| generator_review | TASK-TP-002 | 0 | - | - | - | NO_EVIDENCE |
| health_check_review | TASK-HC-001 | 0 | 0.00016 | - | - | NO_EVIDENCE |
| live_test_execution | TASK-TP-004 | 0 | - | - | - | NO_EVIDENCE |
| precheck_review | TASK-PC-001 | 2 | 0.00012 | 0.00009597 | 0.00010077 | ALIGNED |
| quickchange_patch_review | TASK-QC-001 | 1 | 0.00013 | 0.00011984 | 0.00012583 | ALIGNED |
| skill_router_review | TASK-SR-001 | 0 | 0.00018 | - | - | NO_EVIDENCE |
| spec_generator_review | TASK-SG-001 | 3 | 0.00027 | 0.00071 | 0.0007455 | UNDER_ESTIMATED |
| spec_normalizer_review | TASK-SN-001 | 4 | 0.00022 | 0.00018921 | 0.00019867 | ALIGNED |
| spec_review | TASK-SR-002 | 2 | 0.00075 | 0.00071341 | 0.00074908 | ALIGNED |
| spec_to_task_review | TASK-ST-001 | 1 | 0.00037 | 0.00068685 | 0.00072119 | UNDER_ESTIMATED |
| task_breakdown_review | TASK-TB-001 | 2 | 0.00018 | 0.00017493 | 0.00018368 | ALIGNED |
| test_fixture_worker | TASK-TP-003 | 0 | - | - | - | NO_EVIDENCE |
| test_result_triage_review | TASK-TP-005 | 2 | 0.00031 | 0.00028765 | 0.00030203 | ALIGNED |

## backlog_handoff_review

- Task: `TASK-BH-001`
- Skill: `janus-backlog-handoff`
- Recommended backend: `openrouter`
- Configured estimate: `0.00018`
- Configured confidence: `76`
- Sample count: `2`
- Observed min/mean/max: `0.00017933` / `0.00017933` / `0.00017933`
- Suggested estimate: `0.0001883`
- Suggested confidence: `90`
- Status: `ALIGNED`
- Evidence:
  - `WF-BACKLOG-HANDOFF-EVERYDAY-OR-2026-06-28` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\backlog-handoff-review-runs\WF-BACKLOG-HANDOFF-EVERYDAY-OR-2026-06-28\validation_summary.json` -> `0.00017933`
  - `WF-BACKLOG-HANDOFF-FIXTURE-CHECK-2026-06-25` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\backlog-handoff-review-runs\WF-BACKLOG-HANDOFF-FIXTURE-CHECK-2026-06-25\validation_summary.json` -> `0.00017933`

## backlog_intake_review

- Task: `TASK-BI-001`
- Skill: `janus-backlog-intake`
- Recommended backend: `openrouter`
- Configured estimate: `0.00018`
- Configured confidence: `74`
- Sample count: `2`
- Observed min/mean/max: `0.00016096` / `0.00016096` / `0.00016096`
- Suggested estimate: `0.00016901`
- Suggested confidence: `90`
- Status: `ALIGNED`
- Evidence:
  - `WF-BACKLOG-EVERYDAY-OR-2026-06-27` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\backlog-intake-review-runs\WF-BACKLOG-EVERYDAY-OR-2026-06-27\operator_choice_delegated.json` -> `0.00016096`
  - `WF-BACKLOG-FIXTURE-CHECK-2026-06-25` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\backlog-intake-review-runs\WF-BACKLOG-FIXTURE-CHECK-2026-06-25\operator_choice_delegated.json` -> `0.00016096`

## backlog_prioritization_review

- Task: `TASK-BP-001`
- Skill: `janus-backlog-prioritization`
- Recommended backend: `openrouter`
- Configured estimate: `0.00035`
- Configured confidence: `78`
- Sample count: `2`
- Observed min/mean/max: `0.0003101` / `0.0003101` / `0.0003101`
- Suggested estimate: `0.00032561`
- Suggested confidence: `90`
- Status: `ALIGNED`
- Evidence:
  - `WF-BACKLOG-PRIO-EVERYDAY-OR-2026-06-27` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\backlog-prioritization-review-runs\WF-BACKLOG-PRIO-EVERYDAY-OR-2026-06-27\operator_choice_delegated.json` -> `0.0003101`
  - `WF-BACKLOG-PRIO-FIXTURE-CHECK-2026-06-25` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\backlog-prioritization-review-runs\WF-BACKLOG-PRIO-FIXTURE-CHECK-2026-06-25\operator_choice_delegated.json` -> `0.0003101`

## debug_hypothesis_review

- Task: `TASK-DBG-001`
- Skill: `janus-debug`
- Recommended backend: `openrouter`
- Configured estimate: `0.00048`
- Configured confidence: `85`
- Sample count: `4`
- Observed min/mean/max: `0.00045678` / `0.00045678` / `0.00045678`
- Suggested estimate: `0.00047962`
- Suggested confidence: `90`
- Status: `ALIGNED`
- Evidence:
  - `WF-DEBUG-EVERYDAY-DELEGATED-003` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\debug-review-runs\WF-DEBUG-EVERYDAY-DELEGATED-003\operator_choice_delegated.json` -> `0.00045678`
  - `WF-DEBUG-EVERYDAY-DELEGATED-2026-06-27` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\debug-review-runs\WF-DEBUG-EVERYDAY-DELEGATED-2026-06-27\operator_choice_delegated.json` -> `0.00045678`
  - `WF-DEBUG-EVERYDAY-DELEGATED-2026-06-29-001` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\debug-review-runs\WF-DEBUG-EVERYDAY-DELEGATED-2026-06-29-001\operator_choice_delegated.json` -> `0.00045678`
  - `WF-DEBUG-EVERYDAY-OR-2026-06-28` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\debug-review-runs\WF-DEBUG-EVERYDAY-OR-2026-06-28\operator_choice_delegated.json` -> `0.00045678`

## debug_repro_investigation

- Task: `TASK-DBG-002`
- Skill: `janus-debug`
- Recommended backend: `cursor`
- Configured estimate: `-`
- Configured confidence: `-`
- Sample count: `0`
- Observed min/mean/max: `-` / `-` / `-`
- Suggested estimate: `-`
- Suggested confidence: `-`
- Status: `NO_EVIDENCE`
- Evidence: none collected from the bounded local lane patterns

## diamond_retest_audit

- Task: `TASK-TP-006`
- Skill: `janus-test-pipeline`
- Recommended backend: `codex`
- Configured estimate: `-`
- Configured confidence: `-`
- Sample count: `0`
- Observed min/mean/max: `-` / `-` / `-`
- Suggested estimate: `-`
- Suggested confidence: `-`
- Status: `NO_EVIDENCE`
- Evidence: none collected from the bounded local lane patterns

## documentation_draft_review

- Task: `TASK-DU-001`
- Skill: `janus-documentation-update`
- Recommended backend: `openrouter`
- Configured estimate: `0`
- Configured confidence: `60`
- Sample count: `0`
- Observed min/mean/max: `-` / `-` / `-`
- Suggested estimate: `-`
- Suggested confidence: `60`
- Status: `NO_EVIDENCE`
- Evidence: none collected from the bounded local lane patterns

## execution_patch_candidate

- Task: `TASK-EX-001`
- Skill: `janus-executioner`
- Recommended backend: `cursor`
- Configured estimate: `-`
- Configured confidence: `-`
- Sample count: `60`
- Observed min/mean/max: `0.00016867` / `0.00424574` / `0.0810794`
- Suggested estimate: `0.00467031`
- Suggested confidence: `60`
- Status: `HIGH_VARIANCE_REVIEW_SCOPE`
- Evidence:
  - `WF-EXEC-EVERYDAY-OR-2026-06-27` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\bounded-dispatch-runs\WF-EXEC-EVERYDAY-OR-2026-06-27\dispatcher_result.json` -> `0.00063384`
  - `WF-EXEC-EVERYDAY-OR-2026-06-28` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\bounded-dispatch-runs\WF-EXEC-EVERYDAY-OR-2026-06-28\dispatcher_result.json` -> `0.00063384`
  - `BACKLOG-116-EXECUTION-OR-001` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\BACKLOG-116-EXECUTION-OR-001\validation_summary.json` -> `0.00097661`
  - `DEV-WORKHORSE-EXECUTION-GATE-001` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\DEV-WORKHORSE-EXECUTION-GATE-001\validation_summary.json` -> `0.00016867`
  - `DEV-WORKHORSE-EXECUTION-GATE-002` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\DEV-WORKHORSE-EXECUTION-GATE-002\validation_summary.json` -> `0.00075572`
  - `DEV-WORKHORSE-EXECUTION-GATE-003` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\DEV-WORKHORSE-EXECUTION-GATE-003\validation_summary.json` -> `0.00047768`
  - `DIRECT-OR-DEEPSEEK-EXECUTION-CURRENT-SHAPE-007` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\DIRECT-OR-DEEPSEEK-EXECUTION-CURRENT-SHAPE-007\validation_summary.json` -> `0.00108089`
  - `DIRECT-OR-DEEPSEEK-EXECUTION-HARDEN-FIXTURE-001` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\DIRECT-OR-DEEPSEEK-EXECUTION-HARDEN-FIXTURE-001\validation_summary.json` -> `0.0002114`
  - `DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-001` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-001\validation_summary.json` -> `0.00047174`
  - `DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-002` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-002\validation_summary.json` -> `0.00073542`
  - `DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-003` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-003\validation_summary.json` -> `0.00048402`
  - `DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-004` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-004\validation_summary.json` -> `0.0007378`
  - `DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-005` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-005\validation_summary.json` -> `0.00059865`
  - `DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-006` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-006\validation_summary.json` -> `0.00039312`
  - `DIRECT-OR-DEEPSEEK-EXECUTION-NORMALIZE-FIXTURE-001` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\DIRECT-OR-DEEPSEEK-EXECUTION-NORMALIZE-FIXTURE-001\validation_summary.json` -> `0.0002114`
  - `DIRECT-OR-DEEPSEEK-EXECUTION-POST-WRITE-008` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\DIRECT-OR-DEEPSEEK-EXECUTION-POST-WRITE-008\validation_summary.json` -> `0.00063384`
  - `DIRECT-OR-DEEPSEEK-EXECUTION-REDESIGN-FIXTURE-001` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\DIRECT-OR-DEEPSEEK-EXECUTION-REDESIGN-FIXTURE-001\validation_summary.json` -> `0.0002114`
  - `DIRECT-OR-DEEPSEEK-EXECUTION-REDESIGN-FIXTURE-002` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\DIRECT-OR-DEEPSEEK-EXECUTION-REDESIGN-FIXTURE-002\validation_summary.json` -> `0.0002114`
  - `DIRECT-OR-EXECUTION-DISPATCH-FIXTURE-001` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\DIRECT-OR-EXECUTION-DISPATCH-FIXTURE-001\validation_summary.json` -> `0.0002114`
  - `DIRECT-OR-EXECUTION-DISPATCH-LIVE-002` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\DIRECT-OR-EXECUTION-DISPATCH-LIVE-002\validation_summary.json` -> `0`
  - `DIRECT-OR-EXECUTION-FIXTURE-001` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\DIRECT-OR-EXECUTION-FIXTURE-001\validation_summary.json` -> `0.0002114`
  - `DIRECT-OR-EXECUTION-FIXTURE-TIMEOUT-HARDEN-001` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\DIRECT-OR-EXECUTION-FIXTURE-TIMEOUT-HARDEN-001\validation_summary.json` -> `0.0002114`
  - `DIRECT-OR-QWEN-EXECUTION-FIXTURE-003` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\DIRECT-OR-QWEN-EXECUTION-FIXTURE-003\validation_summary.json` -> `0.00041862`
  - `DIRECT-OR-QWEN-EXECUTION-LIVE-001` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\DIRECT-OR-QWEN-EXECUTION-LIVE-001\validation_summary.json` -> `0.00542782`
  - `DIRECT-OR-WAVE1-DEEPSEEK-V4FLASH-001` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\DIRECT-OR-WAVE1-DEEPSEEK-V4FLASH-001\validation_summary.json` -> `0.00018936`
  - `DIRECT-OR-WAVE1-GLM52-001` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\DIRECT-OR-WAVE1-GLM52-001\validation_summary.json` -> `0.0810794`
  - `DIRECT-OR-WAVE1-GPT53-CODEX-LIVE-RETRY-001` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\DIRECT-OR-WAVE1-GPT53-CODEX-LIVE-RETRY-001\validation_summary.json` -> `0.02699375`
  - `DIRECT-OR-WAVE1-GPT53-CODEX-SCHEMA-FIX-FIXTURE-001` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\DIRECT-OR-WAVE1-GPT53-CODEX-SCHEMA-FIX-FIXTURE-001\validation_summary.json` -> `0.0002114`
  - `DIRECT-OR-WAVE1-GPT53-CODEX-SCHEMA-FIX-FIXTURE-002` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\DIRECT-OR-WAVE1-GPT53-CODEX-SCHEMA-FIX-FIXTURE-002\validation_summary.json` -> `0.0002114`
  - `EXEC-PATCH-CURRENT-SHAPE-001` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\EXEC-PATCH-CURRENT-SHAPE-001\validation_summary.json` -> `0.00041508`
  - `EXEC-PATCH-CURRENT-SHAPE-CONTRACT-001` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\EXEC-PATCH-CURRENT-SHAPE-CONTRACT-001\validation_summary.json` -> `0.0002114`
  - `EXEC-PATCH-CURRENT-SHAPE-LIVE-002` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\EXEC-PATCH-CURRENT-SHAPE-LIVE-002\validation_summary.json` -> `0.0010171`
  - `EXEC-PATCH-CURRENT-SHAPE-SIGNATURE-CONTRACT-001` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\EXEC-PATCH-CURRENT-SHAPE-SIGNATURE-CONTRACT-001\validation_summary.json` -> `0.0002114`
  - `EXEC-PATCH-EXACT-CONTEXT-CLEANED-FIXTURE-001` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\EXEC-PATCH-EXACT-CONTEXT-CLEANED-FIXTURE-001\validation_summary.json` -> `0.0002114`
  - `EXEC-PATCH-EXACT-CONTEXT-CONTRACT-001` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\EXEC-PATCH-EXACT-CONTEXT-CONTRACT-001\validation_summary.json` -> `0.0002114`
  - `EXEC-PATCH-EXACT-CONTEXT-LIVE-004` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\EXEC-PATCH-EXACT-CONTEXT-LIVE-004\validation_summary.json` -> `0.00031797`
  - `EXEC-PATCH-EXACT-CONTEXT-LIVE-005` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\EXEC-PATCH-EXACT-CONTEXT-LIVE-005\validation_summary.json` -> `0.00097742`
  - `EXEC-PATCH-SIGNATURE-AWARE-LIVE-003` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\EXEC-PATCH-SIGNATURE-AWARE-LIVE-003\validation_summary.json` -> `0.00037287`
  - `LEAN-EXEC-deepseek-deepseek-v4-flash` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\LEAN-EXEC-deepseek-deepseek-v4-flash\validation_summary.json` -> `0.00052528`
  - `LEAN-EXEC-moonshotai-kimi-k2.5` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\LEAN-EXEC-moonshotai-kimi-k2.5\validation_summary.json` -> `0.00947481`
  - `LEAN-EXEC-qwen-qwen3-coder-30b-a3b-instruct` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\LEAN-EXEC-qwen-qwen3-coder-30b-a3b-instruct\validation_summary.json` -> `0.00045318`
  - `LEAN-EXEC-qwen-qwen3.5-flash-02-23` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\LEAN-EXEC-qwen-qwen3.5-flash-02-23\validation_summary.json` -> `0.00134804`
  - `LEAN-EXEC-z-ai-glm-4.7-flash` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\LEAN-EXEC-z-ai-glm-4.7-flash\validation_summary.json` -> `0.00067913`
  - `LIVE-HARNESS-EXECUTION-OR-001` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\LIVE-HARNESS-EXECUTION-OR-001\validation_summary.json` -> `0.0072798`
  - `LIVE-HARNESS-EXECUTION-OR-002` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\LIVE-HARNESS-EXECUTION-OR-002\validation_summary.json` -> `0.006237`
  - `LIVE-HARNESS-EXECUTION-OR-003` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\LIVE-HARNESS-EXECUTION-OR-003\validation_summary.json` -> `0.00607275`
  - `LIVE-HARNESS-EXECUTION-OR-004` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\LIVE-HARNESS-EXECUTION-OR-004\validation_summary.json` -> `0.005778`
  - `TASK-SPEC28.1-EXECUTION-OR-001` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\TASK-SPEC28.1-EXECUTION-OR-001\validation_summary.json` -> `0.05054355`
  - `TASK-SPEC28.1-EXECUTION-OR-002` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\TASK-SPEC28.1-EXECUTION-OR-002\validation_summary.json` -> `0.0080658`
  - `TASK-SPEC28.1-EXECUTION-OR-003` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\TASK-SPEC28.1-EXECUTION-OR-003\validation_summary.json` -> `0.0225945`
  - `WF-B113-EVERYDAY-OR-EP-001` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\WF-B113-EVERYDAY-OR-EP-001\validation_summary.json` -> `0.00063384`
  - `WF-BACKLOG-108-EXEC-OR-GATE-2026-06-28-001` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\WF-BACKLOG-108-EXEC-OR-GATE-2026-06-28-001\validation_summary.json` -> `0.00035266`
  - `WF-BACKLOG-115-EXEC-GATE-2026-06-30-001` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\WF-BACKLOG-115-EXEC-GATE-2026-06-30-001\validation_summary.json` -> `0.00033592`
  - `WF-EXEC-EVERYDAY-OR-2026-06-27` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\WF-EXEC-EVERYDAY-OR-2026-06-27\validation_summary.json` -> `0.00063384`
  - `WF-EXEC-EVERYDAY-OR-2026-06-28` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\WF-EXEC-EVERYDAY-OR-2026-06-28\validation_summary.json` -> `0.00063384`
  - `WF-EXEC-EVERYDAY-OR-2026-06-28-002` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\WF-EXEC-EVERYDAY-OR-2026-06-28-002\validation_summary.json` -> `0.00037007`
  - `WF-OPENROUTER-LIVE-SMOKE-002` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\WF-OPENROUTER-LIVE-SMOKE-002\validation_summary.json` -> `0.00044332`
  - `WF-OPENROUTER-LIVE-SMOKE-003` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\WF-OPENROUTER-LIVE-SMOKE-003\validation_summary.json` -> `0.00086083`
  - `WF-OPENROUTER-LIVE-SMOKE-004` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\WF-OPENROUTER-LIVE-SMOKE-004\validation_summary.json` -> `0.00184338`
  - `WF-SPEC25-CURR-OR-EP-001` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\WF-SPEC25-CURR-OR-EP-001\validation_summary.json` -> `0.0002114`
  - `WF-SPEC25-CURR-OR-EP-002` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-direct-or-runs\WF-SPEC25-CURR-OR-EP-002\validation_summary.json` -> `0.00063384`

## execution_write_apply_candidate

- Task: `TASK-EX-002`
- Skill: `janus-executioner`
- Recommended backend: `cursor`
- Configured estimate: `-`
- Configured confidence: `-`
- Sample count: `0`
- Observed min/mean/max: `-` / `-` / `-`
- Suggested estimate: `-`
- Suggested confidence: `-`
- Status: `NO_EVIDENCE`
- Evidence: none collected from the bounded local lane patterns

## feature_design_review

- Task: `TASK-FD-001`
- Skill: `janus-feature-design`
- Recommended backend: `openrouter`
- Configured estimate: `0.00024`
- Configured confidence: `68`
- Sample count: `0`
- Observed min/mean/max: `-` / `-` / `-`
- Suggested estimate: `-`
- Suggested confidence: `68`
- Status: `NO_EVIDENCE`
- Evidence: none collected from the bounded local lane patterns

## generator_review

- Task: `TASK-TP-002`
- Skill: `janus-test-pipeline`
- Recommended backend: `openrouter`
- Configured estimate: `-`
- Configured confidence: `-`
- Sample count: `0`
- Observed min/mean/max: `-` / `-` / `-`
- Suggested estimate: `-`
- Suggested confidence: `-`
- Status: `NO_EVIDENCE`
- Evidence: none collected from the bounded local lane patterns

## health_check_review

- Task: `TASK-HC-001`
- Skill: `janus-health-check`
- Recommended backend: `openrouter`
- Configured estimate: `0.00016`
- Configured confidence: `69`
- Sample count: `0`
- Observed min/mean/max: `-` / `-` / `-`
- Suggested estimate: `-`
- Suggested confidence: `69`
- Status: `NO_EVIDENCE`
- Evidence: none collected from the bounded local lane patterns

## live_test_execution

- Task: `TASK-TP-004`
- Skill: `janus-test-pipeline`
- Recommended backend: `codex`
- Configured estimate: `-`
- Configured confidence: `-`
- Sample count: `0`
- Observed min/mean/max: `-` / `-` / `-`
- Suggested estimate: `-`
- Suggested confidence: `-`
- Status: `NO_EVIDENCE`
- Evidence: none collected from the bounded local lane patterns

## precheck_review

- Task: `TASK-PC-001`
- Skill: `janus-preimplementation-check`
- Recommended backend: `openrouter`
- Configured estimate: `0.00012`
- Configured confidence: `82`
- Sample count: `2`
- Observed min/mean/max: `0.00009588` / `0.00009593` / `0.00009597`
- Suggested estimate: `0.00010077`
- Suggested confidence: `85`
- Status: `ALIGNED`
- Evidence:
  - `WF-PRECHECK-FIXTURE-CHECK-2026-06-25` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\precheck-review-runs\WF-PRECHECK-FIXTURE-CHECK-2026-06-25\response_summary.json` -> `0.00009588`
  - `WF-PRECHECK-REVIEW-LIVE-PROD-2026-07-05-001` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\precheck-review-runs\WF-PRECHECK-REVIEW-LIVE-PROD-2026-07-05-001\response_summary.json` -> `0.00009597`

## quickchange_patch_review

- Task: `TASK-QC-001`
- Skill: `janus-quickchange`
- Recommended backend: `openrouter`
- Configured estimate: `0.00013`
- Configured confidence: `65`
- Sample count: `1`
- Observed min/mean/max: `0.00011984` / `0.00011984` / `0.00011984`
- Suggested estimate: `0.00012583`
- Suggested confidence: `65`
- Status: `ALIGNED`
- Evidence:
  - `BOUNDED-QUICKCHANGE-OR-LIVE-001` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\direct-or-runs\BOUNDED-QUICKCHANGE-OR-LIVE-001\operator_summary.json` -> `0.00011984`

## skill_router_review

- Task: `TASK-SR-001`
- Skill: `janus-skill-router`
- Recommended backend: `openrouter`
- Configured estimate: `0.00018`
- Configured confidence: `70`
- Sample count: `0`
- Observed min/mean/max: `-` / `-` / `-`
- Suggested estimate: `-`
- Suggested confidence: `70`
- Status: `NO_EVIDENCE`
- Evidence: none collected from the bounded local lane patterns

## spec_generator_review

- Task: `TASK-SG-001`
- Skill: `janus-spec-generator`
- Recommended backend: `openrouter`
- Configured estimate: `0.00027`
- Configured confidence: `70`
- Sample count: `3`
- Observed min/mean/max: `0.00071` / `0.00071` / `0.00071`
- Suggested estimate: `0.0007455`
- Suggested confidence: `85`
- Status: `UNDER_ESTIMATED`
- Evidence:
  - `WF-SPEC-GEN-CURRENT-002` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\spec-generator-review-runs\WF-SPEC-GEN-CURRENT-002\validation_summary.json` -> `0.00071`
  - `WF-SPEC-GEN-LIVE-FIXTURE-2026-06-26` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\spec-generator-review-runs\WF-SPEC-GEN-LIVE-FIXTURE-2026-06-26\validation_summary.json` -> `0.00071`
  - `WF-SPEC-GEN-STRUCTURED-FIXTURE-2026-06-26` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\spec-generator-review-runs\WF-SPEC-GEN-STRUCTURED-FIXTURE-2026-06-26\validation_summary.json` -> `0.00071`

## spec_normalizer_review

- Task: `TASK-SN-001`
- Skill: `janus-spec-normalizer`
- Recommended backend: `openrouter`
- Configured estimate: `0.00022`
- Configured confidence: `78`
- Sample count: `4`
- Observed min/mean/max: `0.00018797` / `0.0001889` / `0.00018921`
- Suggested estimate: `0.00019867`
- Suggested confidence: `85`
- Status: `ALIGNED`
- Evidence:
  - `WF-SPEC-NORMALIZER-LIVE-2026-06-26` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\spec-normalizer-runs\WF-SPEC-NORMALIZER-LIVE-2026-06-26\response_summary.json` -> `0.00018921`
  - `WF-SPEC-NORMALIZER-LIVE-PROD-2026-07-05-001` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\spec-normalizer-runs\WF-SPEC-NORMALIZER-LIVE-PROD-2026-07-05-001\response_summary.json` -> `0.00018797`
  - `WF-SPEC-NORMALIZER-LIVE-REPEAT-2026-06-26` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\spec-normalizer-runs\WF-SPEC-NORMALIZER-LIVE-REPEAT-2026-06-26\response_summary.json` -> `0.00018921`
  - `WF-SPEC-NORMALIZER-REAL-LIFE-2026-06-28-001` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\spec-normalizer-runs\WF-SPEC-NORMALIZER-REAL-LIFE-2026-06-28-001\response_summary.json` -> `0.00018921`

## spec_review

- Task: `TASK-SR-002`
- Skill: `janus-spec-review`
- Recommended backend: `openrouter`
- Configured estimate: `0.00075`
- Configured confidence: `55`
- Sample count: `2`
- Observed min/mean/max: `0.00015036` / `0.00043188` / `0.00071341`
- Suggested estimate: `0.00074908`
- Suggested confidence: `60`
- Status: `ALIGNED`
- Evidence:
  - `WF-SPEC-REVIEW-FIXTURE-CHECK-2026-06-25` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\spec-review-runs\WF-SPEC-REVIEW-FIXTURE-CHECK-2026-06-25\validation_summary.json` -> `0.00015036`
  - `WF-SPEC-REVIEW-LIVE-PROD-2026-07-05-001` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\spec-review-runs\WF-SPEC-REVIEW-LIVE-PROD-2026-07-05-001\validation_summary.json` -> `0.00071341`

## spec_to_task_review

- Task: `TASK-ST-001`
- Skill: `janus-spec-to-task`
- Recommended backend: `openrouter`
- Configured estimate: `0.00037`
- Configured confidence: `74`
- Sample count: `1`
- Observed min/mean/max: `0.00068685` / `0.00068685` / `0.00068685`
- Suggested estimate: `0.00072119`
- Suggested confidence: `74`
- Status: `UNDER_ESTIMATED`
- Evidence:
  - `WF-SPEC-TO-TASK-FIXTURE-CHECK-2026-06-26` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\spec-to-task-runs\WF-SPEC-TO-TASK-FIXTURE-CHECK-2026-06-26\validation_summary.json` -> `0.00068685`

## task_breakdown_review

- Task: `TASK-TB-001`
- Skill: `janus-task-breakdown`
- Recommended backend: `openrouter`
- Configured estimate: `0.00018`
- Configured confidence: `75`
- Sample count: `2`
- Observed min/mean/max: `0.00017092` / `0.00017292` / `0.00017493`
- Suggested estimate: `0.00018368`
- Suggested confidence: `90`
- Status: `ALIGNED`
- Evidence:
  - `WF-TASK-BREAKDOWN-FIXTURE-CHECK-2026-06-26` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\task-breakdown-runs\WF-TASK-BREAKDOWN-FIXTURE-CHECK-2026-06-26\validation_summary.json` -> `0.00017092`
  - `WF-TASK-BREAKDOWN-REAL-LIFE-2026-06-28-001` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\task-breakdown-runs\WF-TASK-BREAKDOWN-REAL-LIFE-2026-06-28-001\validation_summary.json` -> `0.00017493`

## test_fixture_worker

- Task: `TASK-TP-003`
- Skill: `janus-test-pipeline`
- Recommended backend: `cursor`
- Configured estimate: `-`
- Configured confidence: `-`
- Sample count: `0`
- Observed min/mean/max: `-` / `-` / `-`
- Suggested estimate: `-`
- Suggested confidence: `-`
- Status: `NO_EVIDENCE`
- Evidence: none collected from the bounded local lane patterns

## test_result_triage_review

- Task: `TASK-TP-005`
- Skill: `janus-test-pipeline`
- Recommended backend: `openrouter`
- Configured estimate: `0.00031`
- Configured confidence: `90`
- Sample count: `2`
- Observed min/mean/max: `0.00028765` / `0.00028765` / `0.00028765`
- Suggested estimate: `0.00030203`
- Suggested confidence: `90`
- Status: `ALIGNED`
- Evidence:
  - `WF-TRIAGE-EVERYDAY-DELEGATED-003` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\test-triage-runs\WF-TRIAGE-EVERYDAY-DELEGATED-003\operator_choice_delegated.json` -> `0.00028765`
  - `WF-TRIAGE-EVERYDAY-DELEGATED-2026-06-29-001` via `C:\KI\Janus-Projekt\documentation\codex\model-routing\test-triage-runs\WF-TRIAGE-EVERYDAY-DELEGATED-2026-06-29-001\operator_choice_delegated.json` -> `0.00028765`
