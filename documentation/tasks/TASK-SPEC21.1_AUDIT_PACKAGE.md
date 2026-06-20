TASK-SPEC21.1 AUDIT PACKAGE

Scope
- Target Task: `TASK-SPEC21.1`
- Feature: Assistierter OR-Arbeitspferd-Modus fuer Janus-Skills
- Slice Goal: Narrow the shared bounded OR eligibility path to the first approved pilot classes and enforce a locally testable request allowlist/redaction gate before any delegated OR request can be emitted.

Bound Artifacts
- Spec: `documentation/SPEC/21_assisted_or_workhorse_mode_for_janus_skills.md`
- Task: `documentation/tasks/TASK-SPEC21_assisted_or_workhorse_mode_for_janus_skills.md`
- Task Breakdown: `documentation/tasks/TASK-SPEC21.1_task_breakdown.md`
- Preimplementation Check: `documentation/tasks/TASK-SPEC21.1_preimplementation_check.md`
- Execution Result: `documentation/tasks/TASK-SPEC21.1_execution_result.md`

Changed Files
- `documentation/codex/model-routing/config/bounded_or_worker_eligibility_2026-06-17.json`
- `documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py`
- `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`
- `documentation/codex/model-routing/scripts/codex_structured_action_request_builder.py`
- `documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py`

Implementation Summary
- Added a dedicated `assistive_or_workhorse_pilot` scope to the shared eligibility config.
- Added pilot-specific eligibility evaluation for `janus-debug/debug_hypothesis_review` and `janus-test-pipeline/test_result_triage_review`.
- Added request-package allowlist validation so forbidden or unredacted fields are rejected before delegated dispatch.
- Replaced the shared dispatcher entry seam with a pilot-only eligibility gate so prompt, local, and delegated paths all reject legacy task classes before any helper is selected.
- Added focused tests for allowed debug and triage pilot payloads, explicit legacy-task rejection at the dispatcher entry gate, forbidden field rejection, and dispatcher-side pre-dispatch fallback.

Validation
- `python -m unittest discover -s documentation/codex/model-routing/tests -p test_bounded_or_worker_eligibility.py`
- `python -m py_compile documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/model-routing/scripts/codex_structured_action_request_builder.py`
- `git diff --check -- documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/model-routing/scripts/codex_structured_action_request_builder.py documentation/codex/model-routing/config/bounded_or_worker_eligibility_2026-06-17.json documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py`
- `python -c "import sys; sys.path.insert(0, r'documentation/codex/model-routing/scripts'); from codex_bounded_delegation_dispatcher import evaluate_assistive_or_workhorse_dispatcher_eligibility; print(evaluate_assistive_or_workhorse_dispatcher_eligibility(task_class='quickchange_patch_review')); print(evaluate_assistive_or_workhorse_dispatcher_eligibility(task_class='test_result_triage_review'))"`

Manual Validation Gate
- Status: `N/A WITH REASON`
- Reason: This slice changes only internal delegation governance, allowlist validation, and test coverage. It does not yet add or alter a Janus end-user runtime path.

Known Risks
- The broader legacy bounded OR infrastructure still exists in the repo; later slices must continue using the new pilot-specific gate instead of assuming the old wider class set is acceptable.
- Cost/confidence UI, OR telemetry capture, actual-cost reporting, and healthcheck optimization summaries are still deferred to later slices.
- No real delegated live run is enabled by this slice alone.

Blocker Delta
- Resolved: the first rollout boundary is now enforced at the shared dispatcher entry gate instead of only inside the two pilot invoke paths.
- Resolved: positive accepted triage coverage now exists alongside explicit legacy-class rejection coverage at the dispatcher seam.
- Remaining: later slices still need to expose the operator gate, telemetry capture, and healthcheck ingestion on top of this narrowed pre-request seam.
