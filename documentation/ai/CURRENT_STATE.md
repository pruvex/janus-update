# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
Run the approved DOC-SKILL-001 live evaluation against the 12 A1 OpenRouter candidates only.

## Active Phase
Documentation-skill single-fixture live evaluation evidence checkpoint. OpenRouter inference/model calls were run only for DOC-SKILL-001 after explicit user approval. No production routing, no routing-table update, no benchmark JSON generation, no release action, and no product-code change.

## Last Decision
The documentation-skill routing table remains the canonical reference for documentation-skill model and scope boundaries.

The approved DOC-SKILL-001 live evaluation ran exactly the 12 A1 request payloads listed in the manifest.

DOC-SKILL-001 is now `COMPLETED_EVALUATED` as evidence only. No routing decision was made, no model was marked production-approved, no external model recommendation is canonical, and no DOC-SKILL-002 or later task was started.

## Last Codex Work
Created:

- `documentation/codex/model-routing/live-eval/DOC-SKILL-001-GPT54-MINI-LIVE-EVAL-001/results/evaluation_summary.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-001-GPT54-MINI-LIVE-EVAL-001/results/evaluation_results.json`
- raw response evidence under `documentation/codex/model-routing/live-eval/DOC-SKILL-001-GPT54-MINI-LIVE-EVAL-001/results/raw/`
- normalized response evidence under `documentation/codex/model-routing/live-eval/DOC-SKILL-001-GPT54-MINI-LIVE-EVAL-001/results/normalized/`

Run results:

- attempted: 12
- completed with normalized model content: 10
- failed/skipped attempts: 2
- PASS: 9
- HOLD: 3
- FAIL: 0

PASS:

- `deepseek/deepseek-v4-flash`
- `minimax/minimax-m3`
- `nvidia/nemotron-3-nano-30b-a3b`
- `openai/gpt-5-mini`
- `openai/gpt-5.1-codex-mini`
- `openai/gpt-5.4-nano`
- `openai/gpt-oss-120b`
- `openai/gpt-oss-20b`
- `qwen/qwen3.5-flash-02-23`

HOLD:

- `openai/gpt-5-nano`: empty normalized content
- `qwen/qwen3-235b-a22b-thinking-2507`: empty normalized content
- `stepfun/step-3.7-flash`: incomplete response missing completion of model_beta/model_gamma and final governance note

## Changed Files
- `documentation/codex/model-routing/live-eval/DOC-SKILL-001-GPT54-MINI-LIVE-EVAL-001/README.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-001-GPT54-MINI-LIVE-EVAL-001/results/evaluation_summary.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-001-GPT54-MINI-LIVE-EVAL-001/results/evaluation_results.json`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-001-GPT54-MINI-LIVE-EVAL-001/results/raw/*.json`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-001-GPT54-MINI-LIVE-EVAL-001/results/normalized/*.md`
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/SKILL_USAGE_LOG.md`

## Remote Sync Evidence
- Branch context: `develop` / `backup/develop` workflow.
- This block is intended to be committed as `docs(codex): run doc skill 001 live evaluation` and pushed to `backup/develop` only.
- No push to `origin`, tag, merge, reset, release, routing-table update, benchmark JSON generation, DOC-SKILL-002 continuation, or production routing activation is part of this block.

## Tests / Validation
- Start-of-work healthcheck reminder: DUE, user deferred it for later.
- Bound artifact reread for DOC-SKILL-001 live evaluation: PASS.
- Exactly 12 model calls attempted or explicitly recorded: PASS.
- Raw responses saved for completed calls and recorded attempts: PASS.
- Normalized responses saved for completed calls and recorded attempts: PASS.
- `evaluation_results.json` parses: PASS.
- `evaluation_summary.md` exists: PASS.
- DOC-SKILL-001 status updated to `COMPLETED_EVALUATED`: PASS.
- No DOC-SKILL-002+ files created or modified: PASS.
- No routing table update: PASS.
- `git diff --check` on touched files: PASS.
- Benchmark JSON generation: NOT RUN / forbidden by scope.

## Open Risks
- The repository worktree contains many unrelated pre-existing modified and untracked files. Commit staging must remain path-specific.
- The A1 candidate list is time-sensitive metadata; current OpenRouter pricing must be rechecked before any future execution.
- The DOC-SKILL-001 live results are evidence only; they are not approval to offer a model externally, batch multiple tasks, update the routing table, or activate production routing.

## Next Recommended Step for ChatGPT
Review the DOC-SKILL-001 evidence summary and decide whether a separate governance review should consider any non-production external option.

## Next Recommended Step for Codex
Run final validation, commit the DOC-SKILL-001 live evaluation evidence checkpoint, and push `backup/develop` only.

## Last Updated
2026-06-13 01:24 local time
