DEBUG_HYPOTHESIS_REVIEW
Status: PASS
Primary Failure Code: RUNNER_ARTIFACT_MISMATCH
Likely Subsystem: test_pipeline_sidecar_write_pilot_runner
Hypothesis 1: Artifact target name is built differently in the runner and the post-validator.
Hypothesis 1 Confidence: HIGH
Hypothesis 1 Evidence: The evidence snippets show PASS status but zero accepted artifacts, which fits a path or naming mismatch more than a runtime crash.
Hypothesis 2: The helper writes artifacts into a nested run directory that the validator does not inspect.
Hypothesis 2 Confidence: MEDIUM
Hypothesis 2 Evidence: The validator reports output-path mismatch, which is consistent with an unexpected subdirectory boundary.
Hypothesis 3: N/A
Hypothesis 3 Confidence: N/A
Hypothesis 3 Evidence: N/A
Suggested Local Verifiers: Compare the runner's computed output paths with the validator's expected output paths; log both in one local dry-run.
Instrumentation Suggestion: Add one temporary local debug line that prints the resolved output artifact paths before validation starts.
Escalation Trigger: Escalate if the computed path and expected path already match but the artifact is still absent after a local dry-run.
Redaction Check: PASS
Notes: Assist-only hypothesis review. No fix claim and no command execution.
