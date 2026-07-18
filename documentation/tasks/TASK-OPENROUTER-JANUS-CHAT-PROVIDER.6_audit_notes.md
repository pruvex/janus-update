# Task .6 Final-Audit Notes (compact)

## Goal

Independent final audit of `TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6` after live conformance `TEST-RUN-2026-07-17-008` reached canonical `PASS` (`117/117`).

## Scope

- Dedicated OpenRouter conformance runner, fixtures, schemas, focused tests
- Offline/static/mocked matrix + live preflight + live four-candidate battery
- Non-runtime registry **candidate** only (`TEST_PASS_AUDIT_PENDING`)
- **Not** in scope: production activation, release/publish, sidebar/UI model-management parity, populating runtime `openrouter_certified_models.json` before this audit PASS

## Authoritative live evidence

- Plan: `documentation/test-runs/TEST-RUN-2026-07-17-008_plan.json`
- Results: `documentation/test-results/TEST-RUN-2026-07-17-008_results.json` / `.md`
- Candidate (non-runtime): `documentation/test-results/TEST-RUN-2026-07-17-008_registry_update_candidate.json`
- Evidence dir: `documentation/test-results/TEST-RUN-2026-07-17-008/`

## Runtime invariants that must still hold at audit time

- Committed runtime registry authority remains empty:
  `backend/config/openrouter_certified_models.json` → `models: []`
- `model_catalog.json` contains **no** OpenRouter chat entries until a later docs/activation step after audit PASS
- Candidate status is `TEST_PASS_AUDIT_PENDING`, `runtime: false`
- Any working-tree fill of the runtime registry with `audit_evidence: passed` before this audit is **unauthorized** and must not be treated as activation

## Known product follow-up (out of Task .6 audit)

After audit PASS + documentation-update activates certified registry **and** matching catalog rows, OpenRouter can appear in the sidebar when key is `VALID`. Optional Gemini-like Modellverwaltung over **only certified** IDs is a separate bounded UX slice, not part of Task `.6`.
