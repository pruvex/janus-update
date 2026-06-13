# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
Implement a bounded operator-invoked fixed OpenRouter choice for the seven live-evidenced mini documentation skills without enabling production routing.

## Active Phase
Documentation-skill mini fixed-OR live enablement. The fixed-model mini evidence layer remains complete for `DOC-SKILL-001`, `DOC-SKILL-002`, `DOC-SKILL-003`, `DOC-SKILL-006`, `DOC-SKILL-008`, `DOC-SKILL-009`, and `DOC-SKILL-010` with preserved counts `OR_CONFIRMED=7`, `NEEDS_STRONGER_TEST=0`, and `OR_REJECTED=0`. A bounded operator-invoked runner, config, and fixture-validated local path now exist for those seven skills only, while Auto Router remains disabled and experiment-only.

## Last Decision
Fixed-model Auto-sparsam remains canonical. The new fixed-OR enablement is an operator-invoked bounded choice layer only. Auto Router remains disabled in this implementation and still experiment-only. No production routing, canonical routing-table update, global OR approval, `DOC-SKILL-011` run, `DOC-SKILL-012` start, or separate `5.4` candidate continuation is approved.

## Last Codex Work
Created a live-enablement note, a seven-skill fixed-model config JSON, a bounded operator-invoked runner, and fixture/local validation artifacts for the fixed-OR path. The runner supports `local` and `or` operator choices, enforces scope and governance gates before wrapper invocation, keeps Auto Router disabled, aborts when estimate or confidence metadata is missing, and produces compact operator summaries plus optional telemetry and healthcheck ingestion in fixture mode.

## Changed Files
- `documentation/codex/model-routing/doc_skill_mini_fixed_or_live_enablement_2026-06-13.md`
- `documentation/codex/model-routing/doc_skill_mini_fixed_or_live_validation_2026-06-13.md`
- `documentation/codex/model-routing/config/doc_skill_mini_fixed_or_live_enabled_2026-06-13.json`
- `documentation/codex/model-routing/config/doc_skill_mini_fixed_or_live_enabled_missing_confidence_fixture_2026-06-13.json`
- `documentation/codex/model-routing/fixtures/fixed_or_live_success_fixture_2026-06-13.json`
- `documentation/codex/model-routing/fixtures/fixed_or_live_missing_confidence_fixture_2026-06-13.jsonl`
- `documentation/codex/model-routing/scripts/doc_skill_mini_fixed_or_live_runner.py`
- `documentation/codex/model-routing/fixed_or_live_validation_out_of_scope_2026-06-13.json`
- `documentation/codex/model-routing/fixed_or_live_validation_missing_confidence_2026-06-13.json`
- `documentation/codex/model-routing/fixed-or-live-runs/FIXED-OR-LOCAL-VALIDATION-001/*`
- `documentation/codex/model-routing/fixed-or-live-runs/FIXED-OR-FIXTURE-VALIDATION-001/*`
- `documentation/codex/model-routing/fixed-or-live-runs/FIXED-OR-MISSING-CONFIDENCE-001/*`
- `documentation/codex/model-routing/or_healthcheck_telemetry_fixed_or_session_2026-06-13_FIXED-OR-FIXTURE-VALIDATION-001.jsonl`
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/SKILL_USAGE_LOG.md`

## Remote Sync Evidence
- Branch context: `develop` / `backup/develop` workflow.
- Intended commit for this block: `feat(codex): enable fixed OR choice for mini doc skills`
- Push target for this block: `backup/develop` only.
- No push to `origin`, tag, merge, release, reset, routing-table update, or production routing activation is part of this block.

## Tests / Validation Performed
- Fixed-OR config JSON parses: PASS.
- Fixed-OR config contains exactly seven enabled skills with the expected fixed model mapping: PASS.
- `auto_router_enabled=false` in the live-enablement config: PASS.
- Local operator choice path produces decision artifacts without wrapper response artifacts or OR call behavior: PASS.
- Fixture OR operator choice builds a fixed-model request and writes file-first artifacts plus accepted telemetry: PASS.
- `health_snapshot.py --or-telemetry-jsonl documentation/codex/model-routing/or_healthcheck_telemetry_fixed_or_session_2026-06-13_FIXED-OR-FIXTURE-VALIDATION-001.jsonl`: PASS.
- Out-of-scope `DOC-SKILL-011` is routed to `CODEX_ONLY_OUT_OF_SCOPE_SKILL` before wrapper invocation: PASS.
- Missing confidence metadata aborts before wrapper invocation: PASS.
- Operator-choice path and compact summary output exist in the runner: PASS.
- Local fixture validation keeps live OR calls at zero: PASS.
- no production activation language: PASS.

## Open Risks
- The repository worktree still contains many unrelated modified and untracked files; staging must remain path-specific.
- The new runner is fixture/local validated only in this block and does not itself prove a new live OR production path.
- Operator use still depends on estimate and confidence metadata staying available in the accepted baseline telemetry inputs.
- Auto Router remains separately negative or mixed evidence and must not be confused with this fixed-model bounded enablement.

## Next Recommended Step for ChatGPT
Review the bounded fixed-OR operator enablement as a local non-production execution layer for the seven live-evidenced mini documentation skills and keep fixed-model Auto-sparsam canonical.

## Next Recommended Step for Codex
Stage only the fixed-OR enablement files, pass staged-only governance checks, commit to `develop`, and push only to `backup/develop` if explicitly requested in this same bounded block.

## Last Updated
2026-06-13 23:19 local time
