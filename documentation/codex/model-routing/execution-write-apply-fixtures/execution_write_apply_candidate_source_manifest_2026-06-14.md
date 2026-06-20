Accepted local source package for initial `execution_write_apply_candidate` validation:

- `documentation/codex/model-routing/execution-review-runs/EXECUTION-PATCH-CANDIDATE-DELEGATED-001`

Reason:

- it already preserves `PRE-CHECK PASSED`
- it already preserves exact `allowed_files`
- it already preserves `max_touched_files`
- it already returns `EXECUTION_PATCH_CANDIDATE_READY_FOR_CODEX_REVIEW`
- it remains proposal-first, so this validation does not imply live write authority
