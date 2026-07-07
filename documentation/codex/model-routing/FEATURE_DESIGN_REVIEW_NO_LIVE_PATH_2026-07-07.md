# Feature Design Review No-Live Path - 2026-07-07

## Goal

Make `TASK-FD-001` / `feature_design_review` a clear operator-facing no-live reference for bounded OpenRouter-assisted feature-design consolidation.

This is not a live OR proof. It is the current clean everyday entry for planning and dry-run use until an explicitly approved live OR run is worth doing.

## Canonical Task

- Task ID: `TASK-FD-001`
- Skill: `janus-feature-design`
- Lane: `feature_design_review`
- Recommended backend: `3 = OpenRouter`
- Current recommended model: `qwen/qwen3-coder-30b-a3b-instruct`

## Intended Everyday Use

Use this lane when:

- one bounded feature-design package is already prepared
- the user wants draft consolidation help, not final product authority
- Codex should stay final owner of the `LATEST DECISION SUMMARY`
- a dry-run plan is enough for now, or live OR is still waiting on explicit approval

Do not use it when:

- product questions are still too open for a bounded package
- implementation, task creation, or release authority is needed
- a live OR call has not been explicitly approved but the operator is expecting executed results

## Shared Gate

Prompt-mode entry:

```powershell
python documentation/codex/model-routing/scripts/janus_delegate.py --lane feature_design_review --task-id TASK-FD-001 --workflow-id <WORKFLOW-ID> --operator-choice prompt --input-package-json development/openrouter-skill-tests/janus-feature-design/feature_design_input_package.json --estimated-codex-saved-tokens 12000 --estimated-delegation-overhead-tokens 4000
```

Expected gate:

- `1 = Codex`
- `2 = Cursor`
- `3 = OpenRouter`

Recommendation:

- `3 = OpenRouter`

## Current No-Live Package

Input package:

- `development/openrouter-skill-tests/janus-feature-design/feature_design_input_package.json`

Expected dry-run behavior:

- shared gate returns `recommended_backend = openrouter`
- option `3` plans `codex_feature_design_runner.py`
- no live OR call happens unless explicitly approved later

## Boundaries

- delegated output is draft material only
- no final product decision authority
- no implementation or task creation
- no Git, release, routing-table, or `CURRENT_STATE` writes by delegated path
- Codex remains final reviewer and acceptance owner

## Current Decision

Treat `feature_design_review` as the next clean no-live OpenRouter candidate: operator-ready for prompt and dry-run use, but still awaiting explicit approval before any live OR execution.
