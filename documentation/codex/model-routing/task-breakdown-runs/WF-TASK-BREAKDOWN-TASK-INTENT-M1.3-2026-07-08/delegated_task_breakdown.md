{
  "spec_path": "documentation/Cursor specs/INTENT_ENGINE_HERMES_INSPIRED_UPGRADE_PLAN.md",
  "task_file_path": "documentation/tasks/TASK-INTENT-M1_auxiliary_action_subject_classifier.md",
  "backlog_item": "N/A",
  "target_task": "TASK-INTENT-M1.3",
  "target_subtask": "N/A",
  "decision": "TASK DESIGN COMPLETE",
  "source_of_truth": "documentation/tasks/TASK-INTENT-M1_auxiliary_action_subject_classifier.md",
  "files": [
    "backend/scripts/run_intent_benchmark.py",
    "backend/tests/test_intent_benchmark.py",
    "backend/tests/test_intent_aux_classifier.py",
    "backend/tests/test_calendar_routing_fix.py",
    "documentation/test-runs/INTENT_BENCHMARK_BASELINE.md",
    "documentation/test-runs/"
  ],
  "acceptance_criteria": [
    "Contact/Pet/Recall show at least +12 pp against the M0 baseline or the blocker is documented clearly",
    "backend/tests/test_calendar_routing_fix.py stays green",
    "P95 latency of the auxiliary classifier stays below 400 ms or a credible blocker is documented",
    "flag off remains identical to legacy behavior"
  ],
  "tests": [
    "rerun the intent benchmark with the auxiliary classifier enabled and compare Contact/Pet/Recall explicitly to the M0 baseline",
    "keep focused regression coverage for auxiliary classifier and calendar routing intact",
    "capture a targeted latency or telemetry check for the auxiliary classifier execution path",
    "preserve a scoped git diff check across the touched benchmark, test, and task-chain artifacts"
  ],
  "execution_model": "5.4",
  "readiness": "precheck-ready",
  "next_skill": "janus-preimplementation-check",
  "model_recommendation": "5.4",
  "notes": "The task is scoped to evidence-only closure of M1.3 against M0 baseline without adding new intent features, as per selection rationale."
}