# Janus Worker Gateway Profiles

## MVP Scope

The current Janus Worker Gateway MVP uses Aider/OpenRouter only.

Codex remains the owner for:
- task selection
- scope definition
- allowlist definition
- accept or reject decisions
- fallback decisions
- all Git, release, publish, dependency, security, privacy, and architecture authority

The worker may only:
- operate in an isolated temp workspace
- edit explicitly allowlisted files
- return normalized result artifacts for Codex review

The worker may not:
- commit
- push
- tag
- merge
- release
- publish
- change dependencies
- handle secrets or auth decisions
- make architecture decisions

## Initial Profiles

### `aider-openrouter-qwen`

- Backend: `aider`
- Provider: `OpenRouter`
- Recommended model family: `qwen/qwen3-coder-30b-a3b-instruct`
- Use for: small and medium bounded Dev or Docs tasks with explicit allowlists
- Not for: release work, security/privacy work, broad refactors, or product-facing risky tasks

### `aider-openrouter-kimi`

- Backend: `aider`
- Provider: `OpenRouter`
- Recommended model family: `moonshotai/kimi-k2.5`
- Use for: bounded coding tasks where the stronger model may justify higher spend
- Not for: MVP default path until the bounded live-dev pilot has accepted evidence

## Selection Guidance

Choose the worker gateway when:
- the task is bounded
- the file allowlist is explicit
- Codex review overhead is lower than doing the whole task locally
- the task is mostly implementation or mechanical follow-through

Keep the task local to Codex when:
- the scope is unclear
- product decisions are still open
- the task touches security, privacy, release, or Git governance
- the validation surface is broad or expensive
- the expected savings are too small

## Result Package Expectations

Every gateway run should produce:
- `RESULT.json`
- `RESULT.md`
- `DIFF.patch`
- `FILES_CHANGED.txt`
- `CHECKS.log`
- `COST.json`

Codex should reject or fallback when:
- required artifacts are missing
- `success` is claimed without matching checks or changed files
- scope drift is detected
- repo-root side effects appear
- the result is plausible but not sufficiently evidenced

## Explicit Non-MVP Backends

The following are intentionally outside the current MVP:
- `OpenCode`
- `OpenHands`
- any broad auto-router or dynamic multi-backend delegation layer
