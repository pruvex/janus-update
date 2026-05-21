# TEST-RUN-2026-05-21-006 Profile Isolation Map

## Verdict

PASS. Janus Spec 12 is validated for the real packaged-local Electron beta model: separate beta profiles with separate AppData, SQLite, upload and generated-artifact roots.

## Deployment Interpretation

Janus is not a hosted SaaS staging app. For this gate, "User A" and "User B" map to two separate local beta profiles. A future hosted Janus deployment must rerun this spec with real staging accounts and server-side tenant IDs.

## Fixture Model

| Profile | Runtime Root | Database | Files | Generated Artifacts |
|---|---|---|---|---|
| Profile A | `documentation/test-results/TEST-RUN-2026-05-21-006/fixtures/profile_a/AppData/Roaming/Janus Projekt` | isolated `janus.db` | isolated `uploads/` | isolated `generated_artifacts/` |
| Profile B | `documentation/test-results/TEST-RUN-2026-05-21-006/fixtures/profile_b/AppData/Roaming/Janus Projekt` | isolated `janus.db` | isolated `uploads/` | isolated `generated_artifacts/` |

## Coverage

- Chat/message object-ID swapping: Profile A cannot resolve Profile B chat or message IDs.
- Memory canary search: Profile A cannot find Profile B memory canaries.
- File/upload swapping: Profile B upload path is outside Profile A root and its content is absent from A files.
- Project/task state: Profile A cannot resolve Profile B project/task canaries.
- Generated artifacts: Profile A cannot resolve Profile B artifact IDs or file content.
- Export privacy: Profile A export scan contains no Profile B canaries.
- Tool-mediated access: deterministic cross-user gate blocks User B/Profile B/resourceId/JWT-cookie reuse requests before tools/LLM.
- Session boundary: JWT expiry and frontend invalid-token cleanup are present.
- Debug/admin boundary: debug endpoints are disabled in packaged beta mode; live `/api/debug/memory` returns `403`.

## Product Fixes Made

- Added `require_debug_endpoints_enabled` in `backend/dependencies.py`.
- Gated debug routes in `backend/main.py` and `backend/api/routers/system.py`.
- Expanded cross-user detection in `backend/services/orchestrator/execution_dispatcher.py` for User B/Profile B/resourceId/JWT-cookie reuse prompts.

## Watchpoints

- This is a packaged-local beta profile isolation gate, not a hosted SaaS tenant certification.
- If Janus later ships hosted accounts, Spec 12 must be rerun with real staging identities, real server-side tenant IDs and deployment-bound auth/session evidence.
