{
  "workflow_id": "SIDECAR-TEST-ARTIFACT-LIVE-2026-06-27-904",
  "skill_id": "janus-test-pipeline",
  "action_type": "run_generator",
  "executor_status": "PASS",
  "schema_validation": "PASS",
  "mapping_resolution": "PASS",
  "allowlist_status": "PASS",
  "output_artifact_status": "PASS",
  "codex_review_required": true,
  "detail": "Generator executed through deterministic local mapping.",
  "action_summary": {
    "generator_id": "compile_testspec_to_testplan_v1",
    "command": [
      "C:\\nvm4w\\nodejs\\node.exe",
      "tests/e2e/generator/compile-testspec-to-testplan.mjs",
      "--spec",
      "documentation/TEST_SPEC/07_regression_suite/18_testspec_testplan_generator_regression.md",
      "--test-run-id",
      "TEST-RUN-2026-06-27-904",
      "--output-dir",
      "documentation/test-runs"
    ],
    "output_artifacts": [
      "documentation/test-runs/TEST-RUN-2026-06-27-904_plan.json",
      "documentation/test-runs/TEST-RUN-2026-06-27-904_generated.spec.js",
      "documentation/test-runs/TEST-RUN-2026-06-27-904_skill2_handover.txt"
    ],
    "stdout_path": "documentation/codex/model-routing/sidecar-runs/SIDECAR-TEST-ARTIFACT-LIVE-2026-06-27-904/structured-action-runs/SIDECAR-TEST-ARTIFACT-LIVE-2026-06-27-904/20260627-212420/stdout.log",
    "stderr_path": "documentation/codex/model-routing/sidecar-runs/SIDECAR-TEST-ARTIFACT-LIVE-2026-06-27-904/structured-action-runs/SIDECAR-TEST-ARTIFACT-LIVE-2026-06-27-904/20260627-212420/stderr.log",
    "exit_code_path": "documentation/codex/model-routing/sidecar-runs/SIDECAR-TEST-ARTIFACT-LIVE-2026-06-27-904/structured-action-runs/SIDECAR-TEST-ARTIFACT-LIVE-2026-06-27-904/20260627-212420/exit_code.txt"
  },
  "run_directory": "documentation/codex/model-routing/sidecar-runs/SIDECAR-TEST-ARTIFACT-LIVE-2026-06-27-904/structured-action-runs/SIDECAR-TEST-ARTIFACT-LIVE-2026-06-27-904/20260627-212420"
}