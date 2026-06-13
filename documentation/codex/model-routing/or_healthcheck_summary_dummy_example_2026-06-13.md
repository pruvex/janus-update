# OR Healthcheck Summary Dummy Example - 2026-06-13

Status: DUMMY SUMMARY / EXAMPLE ONLY / NO OR CALLS / NO MODEL CALLS / NO LIVE EVALS

This example references only fields defined in:

- `documentation/codex/model-routing/or_healthcheck_telemetry_jsonl_schema_2026-06-13.md`

## Example Summary

- `skill_id`: `DOC-SKILL-008`
- `or_model`: `qwen/qwen3.5-flash-02-23`
- `routing_mode`: `Auto-sparsam`
- `recommendation_signal`: `OR_PREFERRED`
- `validation_result`: `PASS`
- `fallback_used`: `NO`
- `rework_required`: `NO`
- `estimated_or_cost`: `0.00042`
- `actual_or_cost`: `0.00040`
- `cost_estimate_confidence_percent`: `72`
- `cost_estimate_sample_count`: `9`
- `cost_estimate_mean_abs_error_percent`: `11.4`
- `cost_estimate_p50_error_percent`: `9.1`
- `cost_estimate_p90_error_percent`: `24.8`
- `prompt_template_hash`: `sha256:dummy-doc-skill-008-template-v1`
- `task_variant`: `summary_short`
- `latency_ms`: `1840`
- `cost_delta_vs_codex_estimate`: `-0.00018`

## Example Interpretation

- Local validation succeeded, so the row contributes to per-skill and per-model reliability.
- No fallback and no rework reduce manual-review pressure.
- Actual OR cost landed slightly below the estimate.
- Confidence is moderate because the historical sample size is below the high-confidence tier.
- Recommendation remains `OR_PREFERRED` for this dummy example because validation passed, fallback was not needed, and cost stayed favorable versus the Codex estimate proxy.
