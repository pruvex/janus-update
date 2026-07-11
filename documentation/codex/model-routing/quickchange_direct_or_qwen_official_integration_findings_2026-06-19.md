# Quickchange Direct OR Qwen Official Integration Findings - 2026-06-19

SKILL 5 DEBUG RESULT: NEEDS RETEST

Iteration: 4
Progress-Validierung: Failure Code `DIRECT_OR_SCHEMA_ENVELOPE_VARIANT_DRIFT`; Evidence geaendert ggü. N-1: JA; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN

Root Cause:
- The two captured live `qwen/qwen3-coder-flash` responses prove that transport, usage capture, `generation_id`, finish reason, cost capture, and healthcheck ingestion are not the problem.
- The remaining defect is contract instability on structured output enforcement:
  - live response 1 returned `file` + unified `diff` + nested `summary`
  - live response 2 returned string `summary` + structured `diff[]`
- Official OpenRouter guidance says structured outputs should be paired with `provider.require_parameters=true` so requests only route to providers that support the required parameters.
- Official OpenRouter guidance also recommends the `response-healing` plugin for non-streaming `json_schema` requests to repair malformed or mixed JSON.
- Official Qwen guidance says the Qwen3 family thinks by default and can be forced into non-thinking mode with `/no_think`.

Fix Summary:
- Hardened the quickchange direct-OR request builder, without making a new live OR call:
  - add `provider.require_parameters=true` for structured-output requests
  - add OpenRouter `response-healing` plugin for structured-output requests
  - add Qwen-specific `/no_think` instruction on the system message for `qwen/*` models
- Added targeted local tests that verify the hardened request shape.

Auto-Verification:
- Status: PASS
- Evidence:
  - `python -m py_compile documentation/codex/model-routing/scripts/openrouter_direct_quickchange_patch_runner.py`
  - `python -m unittest discover -s documentation/codex/model-routing/tests -p test_openrouter_direct_quickchange_patch_runner.py`

Artifact Identity Check: PASS
Final Feature Suite: N/A WITH REASON
- This is bounded provider/debug runner hardening only.
- No product code or live OR retry was executed in this step.

Changed Files:
- `documentation/codex/model-routing/scripts/openrouter_direct_quickchange_patch_runner.py`
- `documentation/codex/model-routing/tests/test_openrouter_direct_quickchange_patch_runner.py`
- `documentation/codex/model-routing/quickchange_direct_or_qwen_official_integration_findings_2026-06-19.md`

NEXT_STEP
Target Skill: janus-debug
Canonical State: HANDOFF
Required Artifacts:
- `documentation/codex/model-routing/quickchange_direct_or_qwen_coder_flash_result_2026-06-19.md`
- `documentation/codex/model-routing/quickchange_direct_or_qwen_live_retry_after_schema_fix_2026-06-19.md`
- `documentation/codex/model-routing/quickchange_direct_or_qwen_official_integration_findings_2026-06-19.md`
- `documentation/codex/model-routing/direct-or-runs/DIRECT-OR-QWEN-QUICKCHANGE-LIVE-001/response_body.json`
- `documentation/codex/model-routing/direct-or-runs/DIRECT-OR-QWEN-QUICKCHANGE-LIVE-002/response_body.json`
Evidence Paths:
- `documentation/codex/model-routing/direct-or-runs/DIRECT-OR-QWEN-QUICKCHANGE-LIVE-001/response_body.json`
- `documentation/codex/model-routing/direct-or-runs/DIRECT-OR-QWEN-QUICKCHANGE-LIVE-002/response_body.json`
- `documentation/codex/model-routing/scripts/openrouter_direct_quickchange_patch_runner.py`
Failure Code:
- `DIRECT_OR_SCHEMA_ENVELOPE_VARIANT_DRIFT`
Changed Files:
- `documentation/codex/model-routing/scripts/openrouter_direct_quickchange_patch_runner.py`
- `documentation/codex/model-routing/tests/test_openrouter_direct_quickchange_patch_runner.py`
- `documentation/codex/model-routing/quickchange_direct_or_qwen_official_integration_findings_2026-06-19.md`
Decision:
- Keep Qwen in the candidate pool, but only with the hardened structured-output request path.
- Do not classify Qwen as accepted yet.
Reason:
- The official docs support three concrete request-path hardening steps, but a fresh bounded live retry is still required to prove they stabilize the live envelope.
Recommended Model:
- `5.4`
Recommended Intelligence:
- `medium`
Next User Action:
- Approve exactly one bounded Qwen quickchange live retry through the hardened request path if we want to prove the official-doc hardening under real traffic.

Sources:
- OpenRouter Structured Outputs: https://openrouter.ai/docs/guides/features/structured-outputs
- OpenRouter Provider Routing: https://openrouter.ai/docs/guides/routing/provider-selection
- OpenRouter Response Healing: https://openrouter.ai/docs/guides/features/plugins/response-healing
- OpenRouter Qwen3 Coder Flash model page: https://openrouter.ai/qwen/qwen3-coder-flash
- Qwen thinking/non-thinking mode: https://qwen.readthedocs.io/en/latest/inference/transformers.html
