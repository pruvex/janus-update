# TEST-RUN-2026-05-21-010 Beta Abuse Limit Policy

## Scope

This run validates Janus as a packaged-local Electron beta backend on `http://127.0.0.1:8001`. It does not claim hosted multi-tenant SaaS quota enforcement. Hosted beta/prod would still need provider-side quotas and centralized durable rate counters.

## Active Limits

| Surface | Control | Default | Test Override |
|---|---|---:|---:|
| Mutating API per user/key | In-process sliding-window middleware | 30 / 10s | 2 / 60s |
| Mutating API global | In-process sliding-window middleware | 180 / 10s | 2 / 60s |
| Image uploads | MIME allowlist and byte cap | 10 MiB | 8 bytes |
| PDF uploads | PDF allowlist and byte cap | 25 MiB | 8 bytes |
| Retry/provider spend prompts | Pre-provider abuse gate | active | active |
| Tool/crawl flood prompts | Pre-tool abuse gate | active | active |
| Abuse alerts | Structured warning logs | no raw prompt/secrets | no raw prompt/secrets |

## Safe Wording

Limit responses use user-comprehensible wording and avoid stack traces, file paths, raw prompts, raw provider errors or secrets.

## Provider Cost Posture

Provider-spend abuse is handled before provider/tool dispatch for recognized retry-storm, expensive-model, high-repeat, broad-crawl and tool-flood prompts. The tests intentionally use capped/synthetic probes and do not execute real expensive provider loops.

## Gate Decision

Gate decision: PASS.

No uncontrolled provider-spend path remains in the tested beta-local surface.
