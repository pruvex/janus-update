# OpenRouter Three-Family Addon Certification Evidence

Candidate set: `OPENROUTER-THREE-FAMILY-ADDON-2026-07-18.1`  
Authoritative live TestRun: `TEST-RUN-2026-07-18-002`  
Canonical live state: **PASS** (`88/88`)

## Approved Exact Bindings

| Family | model_id | model_version | Live eligibility |
| --- | --- | --- | --- |
| Kimi | `moonshotai/kimi-k3` | `moonshotai/kimi-k3-20260715` | eligible |
| Grok | `x-ai/grok-4.3` | `x-ai/grok-4.3-20260430` | eligible |
| GPT | `openai/gpt-5.6-luna` | `openai/gpt-5.6-luna-20260709` | eligible |

## Bound Evidence Paths

- Plan: `documentation/test-runs/TEST-RUN-2026-07-18-002_plan.json`
- Generated runner: `documentation/test-runs/TEST-RUN-2026-07-18-002_generated.py`
- Offline gate: `documentation/test-results/TEST-RUN-2026-07-18-002_offline_gate.json`
- Live preflight: `documentation/test-results/TEST-RUN-2026-07-18-002_live_preflight.json`
- Results JSON: `documentation/test-results/TEST-RUN-2026-07-18-002_results.json`
- Results Markdown: `documentation/test-results/TEST-RUN-2026-07-18-002_results.md`
- Non-runtime registry candidate: `documentation/test-results/TEST-RUN-2026-07-18-002_registry_update_candidate.json`
- Evidence directory: `documentation/test-results/TEST-RUN-2026-07-18-002/`

## Budget And Safety

- Model transmissions: `30` (ceiling `30`)
- Estimated worst-case list cost at preflight: `USD 0.67072`
- Price drift limit: `USD 1.00`
- Runtime activation in candidate payload: `false`
- Candidate statuses: all `TEST_PASS_AUDIT_PENDING`
- Prior immutable FAIL (Luna PINJ-003 oracle): `TEST-RUN-2026-07-18-001` — not authoritative for activation

## Runtime Baseline Unchanged

At evidence capture time the packaged runtime registry and selectable OpenRouter catalog still expose only the previously activated four-family set:

- `anthropic/claude-sonnet-5`
- `z-ai/glm-5.2`
- `deepseek/deepseek-v4-pro`
- `qwen/qwen3.7-plus`

Addon models must not become selectable until Final Audit PASS and `janus-documentation-update` activation.
