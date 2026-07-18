# OpenRouter Certification Evidence — TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6

Generated: 2026-07-18 (final-audit closeout)
Battery: `OPENROUTER-JANUS-CONFORMANCE` / `1.0.0`
Candidate set: `OPENROUTER-FOUR-FAMILY-2026-07-17.1`
Authoritative live TestRun: `TEST-RUN-2026-07-17-008`

## Canonical test outcome

- Status: **PASS**
- Case results: **117 PASS / 0 FAIL / 0 BLOCKED**
- Live transmissions: **40** (budget ceiling 40; 10 per candidate × 4)
- Retry count across cases: **0**
- Provider/model fallback: **none**
- Secret-shaped content in results JSON: **none detected** in scoped scan
- Runtime activation in TestRun: **FORBIDDEN** / candidate remains non-runtime

## Eligible candidates (all four)

| Family | model_id | model_version | eligible |
|--------|----------|---------------|----------|
| Claude | `anthropic/claude-sonnet-5` | `anthropic/claude-sonnet-5-20260630` | true |
| GLM | `z-ai/glm-5.2` | `z-ai/glm-5.2-20260616` | true |
| DeepSeek | `deepseek/deepseek-v4-pro` | `deepseek/deepseek-v4-pro-20260423` | true |
| Qwen | `qwen/qwen3.7-plus` | `qwen/qwen3.7-plus-20260602` | true |

## Evidence paths

- Plan: `documentation/test-runs/TEST-RUN-2026-07-17-008_plan.json`
- Results: `documentation/test-results/TEST-RUN-2026-07-17-008_results.json`
- Summary: `documentation/test-results/TEST-RUN-2026-07-17-008_results.md`
- Per-scenario dir: `documentation/test-results/TEST-RUN-2026-07-17-008/`
- Non-runtime registry candidate: `documentation/test-results/TEST-RUN-2026-07-17-008_registry_update_candidate.json`
- Task-scoped candidate mirror: `documentation/test-results/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6_registry_update_candidate.json`

## Runtime authority (unchanged by Task .6)

- `backend/config/openrouter_certified_models.json` remains empty (`models: []`) until `janus-documentation-update` after Final Audit PASS writes only audit-approved rows.
- Normal `model_catalog.json` OpenRouter count remains `0` until the same activation step adds exact matching catalog rows.
- Candidate status until activation: `TEST_PASS_AUDIT_PENDING`, `runtime: false`.

## Historical superseded run

- `TEST-RUN-2026-07-17-007` remains immutable **FAIL** evidence and must not be used for certification.
