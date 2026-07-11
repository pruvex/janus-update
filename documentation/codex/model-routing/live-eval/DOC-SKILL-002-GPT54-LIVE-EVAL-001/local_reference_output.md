# Local Reference Output

## Overall Status

The scoring report remains candidate-only. Several models are cheaper than `GPT-5.4`, but catalog price does not establish replacement quality.

## Candidate Notes

- `openai/gpt-oss-20b`: `CANDIDATE_NOT_APPROVED`; structured/tool metadata makes it suitable for later sanitized fixture testing.
- `openai/gpt-oss-120b`: `CANDIDATE_NOT_APPROVED`; stronger OpenAI-family candidate, but no `5.4` documentation-skill replacement evidence exists yet.

## HOLD / UNKNOWN / Experiment-Only Notes

- `minimax/minimax-m3`: `HOLD` because earlier schema/provider concerns remain unresolved.
- `openrouter/auto`: `EXPERIMENT_ONLY`; prior mini evidence was mixed and does not support broad adoption.
- `unknown/provider-placeholder`: `UNKNOWN`; insufficient catalog and quality evidence.

## Boundaries

No production routing, canonical routing-table update, global OR approval, or `5.4` replacement decision is created by this summary.

## Next Safe Step

Prepare local `5.4` baselines and sanitized fixture tests before any live OR comparison is requested.
