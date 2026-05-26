# TEST-RUN-2026-05-21-009 Deployment Surface Policy

## Target

Janus beta is validated as a packaged-local Electron app served from `http://127.0.0.1:8001` on loopback. It is not a hosted SaaS deployment and does not expose a public HTTPS endpoint in this scope.

## Transport Exception

HTTPS and HSTS are mandatory for any future non-loopback hosted beta/staging URL. For the current packaged-local target, the accepted exception is loopback-only transport with browser headers, CORS, debug gates and file-serving controls validated locally.

## Allowed Origins

Packaged beta allows only:

- `http://127.0.0.1:8001`
- `http://localhost:8001`
- `electron://localhost`
- `janus://app`

Development origins are only added when `NODE_ENV=development` or `JANUS_DEV_MODE=true`.

## Debug and Artifact Policy

- Debug endpoints must remain disabled unless `JANUS_ENABLE_DEBUG_ENDPOINTS=1` is explicitly set in a development-safe environment.
- Public beta builds must not emit public source maps unless `JANUS_EMIT_SOURCEMAPS=1` or `JANUS_UPLOAD_SOURCEMAPS=1` is explicitly set for a controlled release workflow.
- User image/download responses must not grant wildcard credentialed CORS and must keep `nosniff` plus private cache semantics.
