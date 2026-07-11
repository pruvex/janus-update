# Example Delegation Input Packages

Copy-safe example packages for tri-modal routing (`1=Codex / 2=Cursor / 3=OpenRouter`).

| File | Task ID | Lane | Recommended |
| --- | --- | --- | --- |
| `debug_hypothesis_review_input_package_example.json` | TASK-DBG-001 | debug_hypothesis_review | OR |
| `debug_repro_investigation_input_package_example.json` | TASK-DBG-002 | debug_repro_investigation | Cursor |
| `generator_review_input_package_example.json` | TASK-TP-002 | generator_review | OR |
| `test_fixture_worker_input_package_example.json` | TASK-TP-003 | test_fixture_worker | Cursor |
| `test_fixture_worker_package_example.json` | TASK-TP-003 | test_fixture_worker (OR worker) | OR |
| `test_result_triage_input_package_example.json` | TASK-TP-005 | test_result_triage_review | OR |
| `execution_patch_candidate_input_package_example.json` | TASK-EX-001 | execution_patch_candidate | Cursor |
| `execution_write_apply_input_package_example.json` | TASK-EX-002 | execution_write_apply_candidate | Cursor |

Allowlists:

- `allowlists/debug_repro_allowlist.txt`
- `allowlists/test_fixture_allowlist.txt`
- `allowlists/execution_patch_allowlist.txt`

These are examples only. Replace paths, TEST_RUN_IDs, and evidence with real bounded values before live use.
