# TEST-RUN-2026-05-21-007 Redacted Secret Inventory

## Evidence Policy

Raw secret values are never written to this file or test evidence. The runner records key names, source classes, value lengths and short SHA-256 fingerprints only.

## Secret Classes

| Class | Source System | Storage Source | Beta-Facing | Rotation Status |
|---|---|---|---|---|
| `OPENAI_API_KEY` | OpenAI | ignored `backend/.env` / OS keyring runtime path | Yes | Certified local-current; provider console rotation requires owner action |
| `GEMINI_API_KEY` | Google/Gemini | ignored `backend/.env` / OS keyring runtime path | Yes | Certified local-current; provider console rotation requires owner action |
| `YOUTUBE_API_KEY` | Google/YouTube | ignored `backend/.env` | Conditional | Certified local-current; provider console rotation requires owner action |
| `SUPABASE_URL` | Supabase | ignored `backend/.env` / env | Yes for telemetry/logging | Certified local-current; project-side rotation requires owner action |
| `SUPABASE_KEY` | Supabase | ignored `backend/.env` / env | Yes for telemetry/logging | Certified local-current; project-side rotation requires owner action |
| `SENTRY_AUTH_TOKEN` | Sentry | ignored `frontend/.env` | Release-only | Source-map upload is now opt-in via `JANUS_UPLOAD_SOURCEMAPS=1` |
| `JWT_SECRET_KEY` / `jwt_secret_key` | Local Janus auth | env or AppData config | Local beta session | Generated/stored locally; not bundled |
| `api_key` | Local Janus internal API | AppData config | Local backend internal auth | Generated/stored locally; not bundled |

## Certification

- `.env` and `.env.*` files are ignored.
- `janus_backend.spec` does not bundle `.env`.
- Sentry source-map upload is not automatic; it requires `JANUS_UPLOAD_SOURCEMAPS=1` and a token.
- Provider-side least-privilege and cost-cap settings must be owner-certified in provider consoles before broad beta.
