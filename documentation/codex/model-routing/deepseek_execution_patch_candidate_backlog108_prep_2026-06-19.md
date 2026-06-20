# DeepSeek BACKLOG-108 Execution Patch Candidate Prep - 2026-06-19

Status: PREPARED / NO LIVE OR CALL / NO PRODUCTION ROUTING

## Goal

Prepare exactly one bounded DeepSeek `execution_patch_candidate` live run for `BACKLOG-108` as the next best candidate for the missing second accepted larger-class evidence point.

This prep step does not authorize or execute a live OR call.

## Bound Artifacts

- `documentation/tasks/backlog_BACKLOG-108_preimplementation_check.md`
- `documentation/tasks/backlog_BACKLOG-108_bestaetigtes_kontaktwissen_aus_chat_landung_im_bestehenden_adressbuchkontakt.md`
- `documentation/codex/model-routing/execution-review-fixtures/backlog_108_execution_patch_candidate_input_package_2026-06-19.json`

## Why BACKLOG-108 Is Next

- `BACKLOG-108` is already prechecked.
- It exercises a different larger-class seam than `BACKLOG-110`.
- It stays inside a bounded existing-contact persistence/update path.
- It gives us a better next evidence investment than a third immediate `BACKLOG-110` retry on the same prompt shape.

## Proposed Live Run Shape

- workflow id: `DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-005`
- model: `deepseek/deepseek-v4-flash`
- task class: `execution_patch_candidate`
- budget profile: `execution_patch_candidate`
- class cap: `0.05` USD
- proposed `--max-tokens`: `2600`
- proposed `--estimated-prompt-tokens`: `1500`
- proposed `--estimated-completion-tokens`: `2600`
- proposed `--estimated-or-cost`: `0.000603`
- proposed confidence: `20%`

## Input Package Summary

- allowed files: 8 exact backend/test paths
- max touched files: 8
- regression focus:
  - `backend/tests/test_contact_manager.py`
  - `backend/tests/test_memory_tools.py`
  - `backend/tests/test_memory_write_update_conflict_handling.py`
- manual validation remains Codex-owned

## Acceptance Gates

Accept the future live result only if all are true:

- OR call count = `1`
- response body parses
- `generation_id` exists
- usage exists
- actual cost is below `0.05`
- `finish_reason != length`
- `patch_text` is valid unified diff text
- `changed_files` matches the diff
- `suggested_validation_steps` is non-empty
- `health_snapshot.py` ingests the telemetry JSONL successfully

If any gate fails, classify the run as debug-only evidence and fall back to Codex-only.

## Proposed Command

```powershell
python documentation\codex\model-routing\scripts\openrouter_direct_execution_patch_candidate_runner.py `
  --task-label "BACKLOG-108 execution patch candidate live" `
  --normal-target-model "5.4/medium" `
  --model "deepseek/deepseek-v4-flash" `
  --input-package-json documentation\codex\model-routing\execution-review-fixtures\backlog_108_execution_patch_candidate_input_package_2026-06-19.json `
  --estimated-prompt-tokens 1500 `
  --estimated-completion-tokens 2600 `
  --estimated-or-cost 0.000603 `
  --cost-estimate-confidence-percent 20 `
  --cost-estimate-sample-count 1 `
  --cost-estimate-mean-abs-error-percent 66.76 `
  --cost-estimate-p50-error-percent 66.76 `
  --cost-estimate-p90-error-percent 66.76 `
  --cost-estimate-basis "deepseek/deepseek-v4-flash+execution_patch_candidate+backlog108+second_slice_probe" `
  --prompt-template-hash "sha256:direct_or_execution_patch_candidate_v1_hardened" `
  --task-variant "execution_patch_candidate" `
  --price-snapshot-source "https://openrouter.ai/deepseek/deepseek-v4-flash" `
  --price-snapshot-timestamp "2026-06-19T16:10:00+02:00" `
  --workflow-id DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-005 `
  --max-tokens 2600 `
  --execute-live
```

## Boundary Reminder

- no production routing
- no canonical routing-table update
- no local apply in the OR run itself
- Codex remains review, validation, and apply-or-reject owner
