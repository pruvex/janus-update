# DOC-SKILL-010 Live Evaluation Summary

## Result

PASS on `qwen/qwen3.5-flash-02-23` after sequential evaluation.

## Attempted Models

- `openai/gpt-oss-20b` - HOLD
- `openai/gpt-oss-120b` - HOLD
- `qwen/qwen3.5-flash-02-23` - PASS

## Skipped

- `deepseek/deepseek-v4-flash` - not needed after first PASS

## Counts

- Attempted: 3
- Completed: 3
- Failed: 0
- Skipped: 1

## Governance Checks

- Overall HOLD remains HOLD: PASS
- PASS models remain PASS: PASS
- `production_approved=false` preserved: PASS
- No production routing approval: PASS
- No repo-write or Git action: PASS
- No raw private prompt invention or exposure: PASS

## Notes

The first two candidates preserved the required boundaries but did not fully satisfy the task rubric. `qwen/qwen3.5-flash-02-23` satisfied the rubric and became the selected external candidate.
