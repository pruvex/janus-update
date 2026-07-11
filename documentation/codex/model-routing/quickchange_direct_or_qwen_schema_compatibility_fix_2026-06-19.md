# Quickchange Direct OR Qwen Schema Compatibility Fix - 2026-06-19

SKILL 5 DEBUG RESULT: NEEDS RETEST

Iteration: 2
Progress-Validierung: Failure Code `DIRECT_OR_SCHEMA_ENVELOPE_MISMATCH`; Evidence geaendert ggü. N-1: JA; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN

Root Cause:
- The earlier live `qwen/qwen3-coder-flash` quickchange comparison did not fail on transport, cost, or semantic task understanding.
- The failure was a narrow response-envelope mismatch.
- Qwen returned a compatible patch payload shape:
  - `file`
  - `diff`
  - nested `summary`
- The local quickchange runner previously accepted only the stricter canonical Janus shape:
  - `status`
  - `summary`
  - `changed_files`
  - `unified_diff`
  - `validation_notes`
  - `risk_notes`

Fix Summary:
- Added a narrow compatibility coercion path in `openrouter_direct_quickchange_patch_runner.py`.
- If the model returns the already-bounded `file` + `diff` quickchange shape, the runner now converts it into the canonical Janus quickchange schema before validation.
- The fix is intentionally narrow:
  - no broad relaxed validation
  - no widened file authority
  - no auto-apply behavior
  - no change to larger `execution_patch_candidate` handling

Auto-Verification:
- Status: PASS
- Evidence:
  - `python -m py_compile documentation/codex/model-routing/scripts/openrouter_direct_quickchange_patch_runner.py`
  - fixture revalidation workflow `DIRECT-OR-QWEN-QUICKCHANGE-SCHEMA-FIXTURE-001`
  - `operator_summary.json` with `validation_result=PASS`
  - `health_snapshot.py` ingestion `PASS`

Artifact Identity Check: PASS
Final Feature Suite: N/A WITH REASON
- This is bounded runner/debug infrastructure, not a product feature change.
- No new live OR call was made in this debug step.

Changed Files:
- `documentation/codex/model-routing/scripts/openrouter_direct_quickchange_patch_runner.py`
- `documentation/codex/model-routing/quickchange_direct_or_qwen_schema_compatibility_fix_2026-06-19.md`

NEXT_STEP
Target Skill: janus-debug
Canonical State: HANDOFF
Required Artifacts:
- `documentation/codex/model-routing/quickchange_direct_or_qwen_coder_flash_result_2026-06-19.md`
- `documentation/codex/model-routing/quickchange_direct_or_qwen_schema_compatibility_fix_2026-06-19.md`
- `documentation/codex/model-routing/scripts/openrouter_direct_quickchange_patch_runner.py`
- `documentation/codex/model-routing/direct-or-runs/DIRECT-OR-QWEN-QUICKCHANGE-SCHEMA-FIXTURE-001/operator_summary.json`
Evidence Paths:
- `documentation/codex/model-routing/direct-or-runs/DIRECT-OR-QWEN-QUICKCHANGE-SCHEMA-FIXTURE-001/operator_summary.json`
- `documentation/codex/model-routing/direct-or-runs/DIRECT-OR-QWEN-QUICKCHANGE-SCHEMA-FIXTURE-001/validation_summary.json`
- `documentation/codex/model-routing/direct-or-runs/DIRECT-OR-QWEN-QUICKCHANGE-SCHEMA-FIXTURE-001/healthcheck_summary.json`
Failure Code:
- `DIRECT_OR_SCHEMA_ENVELOPE_MISMATCH`
Changed Files:
- `documentation/codex/model-routing/scripts/openrouter_direct_quickchange_patch_runner.py`
- `documentation/codex/model-routing/quickchange_direct_or_qwen_schema_compatibility_fix_2026-06-19.md`
Decision:
- The Qwen quickchange lane is no longer blocked by a known local schema-adapter gap.
- A future bounded live retry on the same quickchange lane is now justified if we want real accepted Qwen evidence.
Reason:
- The saved live response now validates cleanly under the repaired bounded runner, which means the earlier fail was local contract rigidity rather than a semantic task miss.
Recommended Model:
- `5.4`
Recommended Intelligence:
- `medium`
Next User Action:
- Approve one bounded live `quickchange_patch_review` retry on `qwen/qwen3-coder-flash` if real accepted Qwen evidence is desired.
