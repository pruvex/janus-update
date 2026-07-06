# Delegation Evidence Gap Plan

- Generated at: `2026-07-06T14:03:46+00:00`
- Entry count: `11`
- Live call policy: No Cursor or OpenRouter live calls are authorized by this plan. Live runs require explicit operator approval.
- Manifest write policy: This plan is review-only and must not auto-change routing defaults.

| Priority | Lane | Task | Backend | Status | Action |
| ---: | --- | --- | --- | --- | --- |
| 100 | debug_repro_investigation | TASK-DBG-002 | cursor | NO_EVIDENCE | build_or_reuse_cursor_shadow_fixture_then_request_explicit_live_cursor_smoke |
| 100 | test_fixture_worker | TASK-TP-003 | cursor | NO_EVIDENCE | build_or_reuse_cursor_shadow_fixture_then_request_explicit_live_cursor_smoke |
| 90 | execution_write_apply_candidate | TASK-EX-002 | cursor | NO_EVIDENCE | build_or_reuse_cursor_shadow_fixture_then_request_explicit_live_cursor_smoke |
| 80 | feature_design_review | TASK-FD-001 | openrouter | NO_EVIDENCE | build_bounded_input_package_then_request_explicit_live_openrouter_smoke |
| 80 | health_check_review | TASK-HC-001 | openrouter | NO_EVIDENCE | build_bounded_input_package_then_request_explicit_live_openrouter_smoke |
| 80 | skill_router_review | TASK-SR-001 | openrouter | NO_EVIDENCE | build_bounded_input_package_then_request_explicit_live_openrouter_smoke |
| 70 | documentation_draft_review | TASK-DU-001 | openrouter | NO_EVIDENCE | build_bounded_input_package_then_request_explicit_live_openrouter_smoke |
| 70 | generator_review | TASK-TP-002 | openrouter | NO_EVIDENCE | build_bounded_input_package_then_request_explicit_live_openrouter_smoke |
| 65 | execution_patch_candidate | TASK-EX-001 | cursor | HIGH_VARIANCE_REVIEW_SCOPE | split_or_deprioritize_no_default_tuning |
| 0 | diamond_retest_audit | TASK-TP-006 | codex | NO_EVIDENCE | keep_codex_owned_never_delegate |
| 0 | live_test_execution | TASK-TP-004 | codex | NO_EVIDENCE | keep_codex_owned_never_delegate |

## debug_repro_investigation

- Task: `TASK-DBG-002`
- Skill: `janus-debug`
- Pipeline mode: `DEBUG_REPRO`
- Recommended backend: `cursor`
- Calibration status: `NO_EVIDENCE`
- Sample count: `0`
- Priority: `100`
- Next action: `build_or_reuse_cursor_shadow_fixture_then_request_explicit_live_cursor_smoke`
- Live requires explicit approval: `True`
- Do not tune manifest yet: `True`
- Rationale: cursor is configured as the preferred backend, but no bounded local evidence was found.

## test_fixture_worker

- Task: `TASK-TP-003`
- Skill: `janus-test-pipeline`
- Pipeline mode: `TEST_RUN_PRECHECK`
- Recommended backend: `cursor`
- Calibration status: `NO_EVIDENCE`
- Sample count: `0`
- Priority: `100`
- Next action: `build_or_reuse_cursor_shadow_fixture_then_request_explicit_live_cursor_smoke`
- Live requires explicit approval: `True`
- Do not tune manifest yet: `True`
- Rationale: cursor is configured as the preferred backend, but no bounded local evidence was found.

## execution_write_apply_candidate

- Task: `TASK-EX-002`
- Skill: `janus-executioner`
- Pipeline mode: `EXECUTION_WRITE_APPLY`
- Recommended backend: `cursor`
- Calibration status: `NO_EVIDENCE`
- Sample count: `0`
- Priority: `90`
- Next action: `build_or_reuse_cursor_shadow_fixture_then_request_explicit_live_cursor_smoke`
- Live requires explicit approval: `True`
- Do not tune manifest yet: `True`
- Rationale: cursor is configured as the preferred backend, but no bounded local evidence was found.

## feature_design_review

- Task: `TASK-FD-001`
- Skill: `janus-feature-design`
- Pipeline mode: `FEATURE_DESIGN_REVIEW`
- Recommended backend: `openrouter`
- Calibration status: `NO_EVIDENCE`
- Sample count: `0`
- Priority: `80`
- Next action: `build_bounded_input_package_then_request_explicit_live_openrouter_smoke`
- Live requires explicit approval: `True`
- Do not tune manifest yet: `True`
- Rationale: openrouter is configured as the preferred backend, but no bounded local evidence was found.

## health_check_review

- Task: `TASK-HC-001`
- Skill: `janus-health-check`
- Pipeline mode: `HEALTH_CHECK_REVIEW`
- Recommended backend: `openrouter`
- Calibration status: `NO_EVIDENCE`
- Sample count: `0`
- Priority: `80`
- Next action: `build_bounded_input_package_then_request_explicit_live_openrouter_smoke`
- Live requires explicit approval: `True`
- Do not tune manifest yet: `True`
- Rationale: openrouter is configured as the preferred backend, but no bounded local evidence was found.

## skill_router_review

- Task: `TASK-SR-001`
- Skill: `janus-skill-router`
- Pipeline mode: `SKILL_ROUTER_REVIEW`
- Recommended backend: `openrouter`
- Calibration status: `NO_EVIDENCE`
- Sample count: `0`
- Priority: `80`
- Next action: `build_bounded_input_package_then_request_explicit_live_openrouter_smoke`
- Live requires explicit approval: `True`
- Do not tune manifest yet: `True`
- Rationale: openrouter is configured as the preferred backend, but no bounded local evidence was found.

## documentation_draft_review

- Task: `TASK-DU-001`
- Skill: `janus-documentation-update`
- Pipeline mode: `DOCUMENTATION_DRAFT_REVIEW`
- Recommended backend: `openrouter`
- Calibration status: `NO_EVIDENCE`
- Sample count: `0`
- Priority: `70`
- Next action: `build_bounded_input_package_then_request_explicit_live_openrouter_smoke`
- Live requires explicit approval: `True`
- Do not tune manifest yet: `True`
- Rationale: openrouter is configured as the preferred backend, but no bounded local evidence was found.

## generator_review

- Task: `TASK-TP-002`
- Skill: `janus-test-pipeline`
- Pipeline mode: `TEST_RUN_PRECHECK`
- Recommended backend: `openrouter`
- Calibration status: `NO_EVIDENCE`
- Sample count: `0`
- Priority: `70`
- Next action: `build_bounded_input_package_then_request_explicit_live_openrouter_smoke`
- Live requires explicit approval: `True`
- Do not tune manifest yet: `True`
- Rationale: openrouter is configured as the preferred backend, but no bounded local evidence was found.

## execution_patch_candidate

- Task: `TASK-EX-001`
- Skill: `janus-executioner`
- Pipeline mode: `EXECUTION_PATCH`
- Recommended backend: `cursor`
- Calibration status: `HIGH_VARIANCE_REVIEW_SCOPE`
- Sample count: `60`
- Priority: `65`
- Next action: `split_or_deprioritize_no_default_tuning`
- Live requires explicit approval: `True`
- Do not tune manifest yet: `True`
- Rationale: Existing evidence is too mixed to tune automatically; separate transport/runtime evidence before changing defaults.

## diamond_retest_audit

- Task: `TASK-TP-006`
- Skill: `janus-test-pipeline`
- Pipeline mode: `DIAMOND_RETEST_AUDIT`
- Recommended backend: `codex`
- Calibration status: `NO_EVIDENCE`
- Sample count: `0`
- Priority: `0`
- Next action: `keep_codex_owned_never_delegate`
- Live requires explicit approval: `False`
- Do not tune manifest yet: `True`
- Rationale: Lane is Codex-owned by policy and should not become delegated evidence work.

## live_test_execution

- Task: `TASK-TP-004`
- Skill: `janus-test-pipeline`
- Pipeline mode: `LIVE_TEST_EXECUTION`
- Recommended backend: `codex`
- Calibration status: `NO_EVIDENCE`
- Sample count: `0`
- Priority: `0`
- Next action: `keep_codex_owned_never_delegate`
- Live requires explicit approval: `False`
- Do not tune manifest yet: `True`
- Rationale: Lane is Codex-owned by policy and should not become delegated evidence work.
