# Direct OR Execution Patch Candidate Validator Normalization Fix - 2026-06-19

Status: LOCAL VALIDATOR SEAM FIXED / NO NEW LIVE OR CALL

## Root Cause

The remaining rejection on the hardened second DeepSeek larger-class live retry was caused by local path normalization, not by model behavior.

Specifically:

- `normalize_repo_path()` used `lstrip("./")`
- that removed the leading dot from `.gitignore`
- this created a mismatch between:
  - `changed_files`
  - files extracted from `patch_text`
  - allowlist normalization

## Fix

Updated:

- `documentation/codex/model-routing/scripts/openrouter_direct_execution_patch_candidate_runner.py`

Changes:

1. `normalize_repo_path()` now removes only true leading `./` segments and leading `/`, without stripping the filename-leading dot from `.gitignore`.
2. `extract_patch_files()` now runs the same normalization path before comparison.

## Validation

- `python -m py_compile documentation/codex/model-routing/scripts/openrouter_direct_execution_patch_candidate_runner.py`: PASS
- direct function probe:
  - `.gitignore -> .gitignore`
  - `./.gitignore -> .gitignore`
  - patch extraction from `+++ b/.gitignore` stays `.gitignore`
- local fixture validation:
  - workflow: `DIRECT-OR-DEEPSEEK-EXECUTION-NORMALIZE-FIXTURE-001`
  - result: `PASS`
  - healthcheck ingestion: `PASS`

## Re-check Of Existing Live Evidence

The already captured hardened DeepSeek live retry artifact

- `DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-002`

was re-validated locally with the fixed validator logic.

Result:

- `validate_result_payload(...)` returned `[]`

Interpretation:

- the previously recorded live DeepSeek retry no longer shows validation issues once the `.gitignore` normalization seam is fixed
- the earlier rejection was a local validator artifact, not new negative model evidence

## Implication

This means the hardened second DeepSeek larger-class live retry is now best interpreted as:

- technically acceptable bounded execution patch candidate evidence

subject to the usual Janus boundary:

- Codex still reviews
- Codex still decides whether to apply or reject locally
- no production routing is activated

## Next Safe Step

Do not spend another live call for this same seam.

Instead:

1. record the normalization fix as the cause of the prior false rejection
2. decide whether to treat `DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-002` as accepted larger-class evidence after this local validator repair
