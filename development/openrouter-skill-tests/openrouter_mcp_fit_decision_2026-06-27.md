# OpenRouter MCP Fit Decision - 2026-06-27

Status: DECISION LOCKED / DEV INFRA ONLY / NO PRODUCTION ROUTING CHANGE

## Decision

OpenRouter MCP is useful for our Codex-to-OR program as a live information and telemetry helper, but not as the main execution architecture for bounded repo workhorse tasks.

## Use It For

- live model discovery
- live pricing checks
- live credit checks
- benchmark and ranking lookups
- docs lookup for OpenRouter-specific setup questions
- generation follow-up lookups by `generation_id`
- cheap prompt or model comparison probes when a billable `chat-send` is explicitly useful

## Do Not Use It For

- replacing the bounded structured local executor
- replacing our current skill-level operator gate architecture
- direct repo-write delegation
- final validation authority
- production routing activation
- canonical routing-table updates

## Why

The documented MCP surface is mostly read-only plus one billable `chat-send` tool.

That makes it a strong fit for:

- choosing models with live rather than stale data
- checking current prices before bounded tests
- tracking exact generation cost after a call

It is not a strong fit for:

- deterministic local file generation
- bounded repo edits
- trusted execution of approved local generators and validators

Our current structured action plus structured local executor architecture already solves the harder part:

- delegated intent stays bounded
- local execution stays deterministic
- Codex keeps review and acceptance authority

## Best Integration Point

Use OpenRouter MCP as a supporting layer around the existing OR workflow:

1. before a live bounded test:
   - query models, prices, and rankings
2. during model-candidate selection:
   - shortlist candidates with live catalog and benchmark data
3. after a live OR call:
   - enrich cost and provider evidence via `generation-get`

Keep actual app/runtime calls on the normal OpenRouter API path, exactly as the MCP docs recommend.

## Practical Recommendation

- continue the current bounded executor-based rollout for everyday skills
- optionally add OpenRouter MCP later as a live research and telemetry helper
- do not pause the current rollout to re-architect around MCP

## Next Good Slice

Small bounded Dev slice:

- add one explicit MCP integration note to the OR workflow docs
- define where `models-list`, `benchmarks`, `credits-get`, and `generation-get` fit in candidate testing and telemetry

