# TEST-RUN-2026-05-21-009 Final Audit

## Verdict

PASS. `TEST-RUN-2026-05-21-009` validates Janus Deployment Headers CORS CSP Cookie Scan with `10/10` passing checks, `0` failed, `0` blocked and `0` manual gates.

This audit validates Janus' packaged-local Electron beta deployment surface at `http://127.0.0.1:8001`. The HTTPS/HSTS requirement is explicitly scoped as mandatory for any future non-loopback hosted beta/staging URL; the current accepted exception is loopback-only local transport with browser headers, CORS, debug gates and file-serving controls validated against the real local target.

## Evidence

- TestSpec: `documentation/TEST_SPEC/02_security_safety/15_deployment_headers_cors_csp_cookie_scan.md`
- TestPlan: `documentation/test-runs/TEST-RUN-2026-05-21-009_plan.json`
- Deployment surface policy: `documentation/test-runs/TEST-RUN-2026-05-21-009_deployment_surface_policy.md`
- Runner: `tests/e2e/generated/TEST-RUN-2026-05-21-009.deployment-surface.spec.js`
- Playwright config: `tests/e2e/generated/TEST-RUN-2026-05-21-009.deployment-surface.playwright.config.js`
- Result JSON: `documentation/test-results/TEST-RUN-2026-05-21-009_results.json`
- Result Markdown: `documentation/test-results/TEST-RUN-2026-05-21-009_results.md`
- Evidence directory: `documentation/test-results/TEST-RUN-2026-05-21-009`

## Verification

- `npx playwright test --config tests/e2e/generated/TEST-RUN-2026-05-21-009.deployment-surface.playwright.config.js --reporter=list` -> PASS, `10 passed`.
- `python -m py_compile backend/main.py` -> PASS.
- `python -m pytest backend/tests/test_observability_redaction.py -q` -> PASS, `5 passed`.
- `npm run build` with `PYTHONIOENCODING=UTF-8` -> PASS; beta build emitted no public source maps.
- TestResult JSON schema validation against `tests/e2e/generator/test-result.schema.json` -> PASS.
- Focused credential-pattern scan over 009 evidence and run documentation -> PASS.

## Findings

Resolved during audit:

- Beta CORS allowed too many development origins plus `null` and exposed all headers. Packaged beta now allows only the local packaged origins unless development mode is explicitly enabled; methods, request headers and exposed headers are constrained.
- Source maps were emitted by default. Public beta source maps now require explicit `JANUS_EMIT_SOURCEMAPS=1` or `JANUS_UPLOAD_SOURCEMAPS=1`.
- User image/download routes set wildcard CORS. They now echo only approved origins, set `Vary: Origin`, keep `nosniff`, use private cache semantics and set inline disposition.

No open Critical or High deployment-surface blocker remains for the packaged-local beta gate.

## Watchpoints

- A hosted beta/staging URL would require a separate HTTPS/HSTS/reverse-proxy/CDN validation run. This local Electron gate must not be treated as hosted SaaS deployment certification.
- CSP still allows `'unsafe-inline'` for existing legacy frontend scripts/styles. That is accepted for the current app shape but should be retired in a future frontend hardening pass.
