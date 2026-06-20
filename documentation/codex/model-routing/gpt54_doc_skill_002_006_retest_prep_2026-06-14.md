# GPT-5.4 DOC-SKILL-002 and DOC-SKILL-006 Retest Prep - 2026-06-14

Status: PREPARED / NO LIVE CALLS RUN / NON-PRODUCTION

## Prepared Scope

Prepared narrow retest workflow:

- workflow_id: `GPT54-DOC-SKILL-002-006-RETEST-001`
- skills: `DOC-SKILL-002`, `DOC-SKILL-006`
- models: `deepseek/deepseek-v4-flash`, `qwen/qwen3.5-flash-02-23`
- total planned calls: `4`

## Bound Prompt Overrides

- `DOC-SKILL-002`: [prompt_retest_v2_2026-06-14.md](/C:/KI/Janus-Projekt/documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-LIVE-EVAL-001/prompt_retest_v2_2026-06-14.md)
- `DOC-SKILL-006`: [prompt_retest_v2_2026-06-14.md](/C:/KI/Janus-Projekt/documentation/codex/model-routing/live-eval/DOC-SKILL-006-GPT54-LIVE-EVAL-001/prompt_retest_v2_2026-06-14.md)

## Bound Manifest

- [gpt54_doc_skill_002_006_retest_manifest_2026-06-14.json](/C:/KI/Janus-Projekt/documentation/codex/model-routing/gpt54_doc_skill_002_006_retest_manifest_2026-06-14.json)

Configured overrides:

- `DOC-SKILL-002`: `max_tokens=1400`
- `DOC-SKILL-006`: `max_tokens=2200`

## Prepared Command

```powershell
python documentation/codex/model-routing/scripts/gpt54_doc_skill_multi_model_batch_runner.py `
  --workflow-id GPT54-DOC-SKILL-002-006-RETEST-001 `
  --telemetry-jsonl documentation/codex/model-routing/or_healthcheck_telemetry_gpt54_doc_skill_002_006_retest_2026-06-14.jsonl `
  --run-root documentation/codex/model-routing/fixed-or-live-runs/GPT54-DOC-SKILL-002-006-RETEST-001 `
  --skills DOC-SKILL-002 DOC-SKILL-006 `
  --models deepseek/deepseek-v4-flash qwen/qwen3.5-flash-02-23 `
  --skill-overrides-json documentation/codex/model-routing/gpt54_doc_skill_002_006_retest_manifest_2026-06-14.json `
  --per-call-cap 0.01 `
  --total-cap 0.04
```

## Expected Interpretation

- `DOC-SKILL-002`: prompt-precision probe with only a modest completion-budget increase
- `DOC-SKILL-006`: structure-retention probe with a clearly larger completion budget

## Boundaries

- no live calls have been run by this prep artifact
- no production routing
- no canonical routing-table update
- no Auto Router
- no global OR approval
