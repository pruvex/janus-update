TASK-SPEC21.3 AUDIT PACKAGE

Scope
- Target Task: `TASK-SPEC21.3`
- Feature: Assistierter OR-Arbeitspferd-Modus fuer Janus-Skills
- Slice Goal: Add file-first OR capture, bounded telemetry, actual-cost visibility, and healthcheck ingestion for accepted and rejected bounded pilot review runs without widening the pilot scope.

Bound Artifacts
- Spec: `documentation/SPEC/21_assisted_or_workhorse_mode_for_janus_skills.md`
- Task: `documentation/tasks/TASK-SPEC21_assisted_or_workhorse_mode_for_janus_skills.md`
- Task Breakdown: `documentation/tasks/TASK-SPEC21.3_task_breakdown.md`
- Preimplementation Check: `documentation/tasks/TASK-SPEC21.3_preimplementation_check.md`
- Execution Result: `documentation/tasks/TASK-SPEC21.3_execution_result.md`

Changed Files
- `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`
- `documentation/codex/model-routing/tests/test_assistive_or_review_capture_dispatcher.py`

Implementation Summary
- Extended the shared bounded dispatcher so the two approved assistive pilot review classes can run through the existing file-first wrapper in bounded fixture or live mode, while still keeping Codex as local validation and acceptance owner.
- Reused the existing debug- and triage-review payload validators and markdown renderers so wrapper-captured OR output must still satisfy the same bounded assist-only review contracts as the earlier local fixture paths.
- Added bounded telemetry-row generation plus `health_snapshot.py` ingestion directly after capture, including actual-cost, generation-id, usage, fallback, and validation-result fields.
- Finalized the bounded telemetry contract so every wrapper run now persists exactly one truthful durable JSONL row, including wrapper-failure and healthcheck-failure fallback paths.
- Preserved deterministic rejection semantics when usage, generation-id, parseability, or review validation data is missing, so incomplete capture cannot appear as accepted success.

Validation
- `python -m unittest documentation.codex.model-routing.tests.test_assistive_or_review_capture_dispatcher`
- `python -m unittest documentation.codex.model-routing.tests.test_bounded_or_worker_eligibility`
- `python -m py_compile documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/model-routing/scripts/bounded_or_worker_outcome.py documentation/codex/skills/janus-health-check/scripts/health_snapshot.py documentation/codex/model-routing/tests/test_assistive_or_review_capture_dispatcher.py`
- `python documentation/codex/skills/janus-health-check/scripts/health_snapshot.py --repo . --mode DAILY`
- `git diff --check -- documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/model-routing/tests/test_assistive_or_review_capture_dispatcher.py documentation/tasks/TASK-SPEC21.3_preimplementation_check.md documentation/codex/SKILL_USAGE_LOG.md documentation/ai/CURRENT_STATE.md`

Manual Validation Gate
- Status: `N/A WITH REASON`
- Reason: This slice extends internal bounded review capture, telemetry, and healthcheck wiring only. It does not yet introduce a new Janus product-surface interaction beyond the already sealed operator gate, and everyday consumer integration remains intentionally deferred to `TASK-SPEC21.4`.

Blocker Delta
- The wrapper non-zero path now writes one rejected telemetry row plus a validation summary instead of returning with no durable telemetry evidence.
- The healthcheck path now rewrites the same JSONL file to the final failure state when ingestion fails, so persisted `validation_result`, `final_outcome`, `fallback_used`, and `recommendation_signal` match the operator result.
- The focused dispatcher test suite now includes wrapper-failure and healthcheck-failure regression coverage in addition to the existing accepted and missing-usage paths.

Known Risks
- The pilot scope must remain fixed to `debug_hypothesis_review` and `test_result_triage_review`; this slice must not be treated as permission to widen rollout to other task classes.
- Everyday consumer integration for `janus-debug` and `janus-test-pipeline` still does not exist; that wiring remains intentionally deferred to `TASK-SPEC21.4`.
- Live OR execution is not broadly enabled by this slice alone; the new path is primarily validated through bounded local fixture capture and healthcheck ingestion.
