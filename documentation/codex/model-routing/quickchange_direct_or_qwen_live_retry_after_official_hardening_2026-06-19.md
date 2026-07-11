# Quickchange Direct OR Qwen Live Retry After Official Hardening - 2026-06-19

SKILL 5 DEBUG RESULT: ESCALATION REQUIRED

Iteration: 5
Progress-Validierung: Failure Code `DIRECT_OR_PROVIDER_PARAMETER_COMPATIBILITY_BLOCK`; Evidence geaendert ggü. N-1: JA; Stagnationszaehler: 0; Stopp-Regel ausgeloest: JA

Root Cause:
- The official-doc hardening changed the Qwen failure mode from post-response schema drift to pre-response provider routing incompatibility.
- The single bounded live retry `DIRECT-OR-QWEN-QUICKCHANGE-LIVE-003` did execute exactly one real OR call attempt.
- OpenRouter returned HTTP `404` with:
  - `No endpoints found that can handle the requested parameters.`
- This means the hardened request combination is not currently satisfiable on the Qwen provider path for this exact lane:
  - `provider.require_parameters=true`
  - `response-healing` plugin
  - `qwen/qwen3-coder-flash`
  - bounded quickchange structured-output contract
- So we now have two distinct live Qwen failure modes on the same lane:
  - without stricter provider enforcement: live responses arrive but drift across non-canonical JSON envelopes
  - with stricter provider enforcement: no compatible endpoint is available

Fix Summary:
- No additional local code widening was applied after the single bounded live retry.
- The hardened request path itself remained active and produced the new evidence.
- The correct next step is not another blind retry, but explicit escalation and decision-making.

Auto-Verification:
- Status: PASS
- Evidence:
  - `documentation/codex/model-routing/direct-or-runs/DIRECT-OR-QWEN-QUICKCHANGE-LIVE-003/response_summary.json`
  - `documentation/codex/model-routing/direct-or-runs/DIRECT-OR-QWEN-QUICKCHANGE-LIVE-003/response_body.json`
  - `documentation/codex/model-routing/direct-or-runs/DIRECT-OR-QWEN-QUICKCHANGE-LIVE-003/validation_summary.json`
  - `documentation/codex/model-routing/direct-or-runs/DIRECT-OR-QWEN-QUICKCHANGE-LIVE-003/healthcheck_summary.json`

Artifact Identity Check: PASS
Final Feature Suite: N/A WITH REASON
- This is bounded OpenRouter/Qwen provider-path debug evidence only.
- No product feature files were changed and no second OR retry was made.

Changed Files:
- `documentation/codex/model-routing/quickchange_direct_or_qwen_live_retry_after_official_hardening_2026-06-19.md`

NEXT_STEP
Target Skill: janus-debug
Canonical State: ESCALATED
Required Artifacts:
- `documentation/codex/model-routing/quickchange_direct_or_qwen_official_integration_findings_2026-06-19.md`
- `documentation/codex/model-routing/quickchange_direct_or_qwen_live_retry_after_official_hardening_2026-06-19.md`
- `documentation/codex/model-routing/direct-or-runs/DIRECT-OR-QWEN-QUICKCHANGE-LIVE-003/response_summary.json`
- `documentation/codex/model-routing/direct-or-runs/DIRECT-OR-QWEN-QUICKCHANGE-LIVE-003/response_body.json`
- `documentation/codex/model-routing/direct-or-runs/DIRECT-OR-QWEN-QUICKCHANGE-LIVE-003/validation_summary.json`
Evidence Paths:
- `documentation/codex/model-routing/direct-or-runs/DIRECT-OR-QWEN-QUICKCHANGE-LIVE-003/response_summary.json`
- `documentation/codex/model-routing/direct-or-runs/DIRECT-OR-QWEN-QUICKCHANGE-LIVE-003/response_body.json`
- `documentation/codex/model-routing/direct-or-runs/DIRECT-OR-QWEN-QUICKCHANGE-LIVE-003/validation_summary.json`
- `documentation/codex/model-routing/direct-or-runs/DIRECT-OR-QWEN-QUICKCHANGE-LIVE-003/healthcheck_summary.json`
Failure Code:
- `DIRECT_OR_PROVIDER_PARAMETER_COMPATIBILITY_BLOCK`
Changed Files:
- `documentation/codex/model-routing/quickchange_direct_or_qwen_live_retry_after_official_hardening_2026-06-19.md`
Decision:
- Do not mark Qwen accepted for the bounded quickchange lane.
- Escalate before any further Qwen live spend on this class.
Reason:
- We now have conflicting bounded realities on the same lane: relaxed request settings allow live responses but unstable schema, while strict official-doc settings block routing entirely.
Recommended Model:
- `5.5`
Recommended Intelligence:
- `high`
Next User Action:
- Decide whether Qwen should get one deeper architecture/provider-analysis pass, or be parked for this lane while we prioritize already stable families.
