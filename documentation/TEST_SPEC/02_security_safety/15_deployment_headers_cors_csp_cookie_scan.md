# JANUS DEPLOYMENT HEADERS CORS CSP COOKIE SCAN - DIAMANTSTANDARD v1.0

## TEST EXECUTION ROUTING

target_skill: TEST_SKILL_SECURITY
execution_mode: SWE_1_6
complexity_score: 84
confidence: HIGH
dashboard_hint: BETA_PRODUCTION_HARDENING
security_hint: DEPLOYMENT_SURFACE_GATE
reason: Validate browser and API deployment security controls against the actual beta/staging URL.

## TEST IDENTITY

- TestSpec Name: 15 Deployment Headers CORS CSP Cookie Scan
- Security Domain: Browser / API Deployment Surface
- Source Input: Category 2 production-readiness extension
- Primary Test Goal: Confirm security headers, CORS, CSP, cookies, HTTPS/HSTS and deployment-only web protections are correct on the real beta endpoint.
- Launch Risk: Local headers can be correct while reverse proxies, CDNs, domains or Electron/staging differences weaken browser security.
- Required Precondition: Staging URL available.

## TEST OBJECTIVE

Perform request/browser checks against the real target URL. Validate that browser protections are active, CORS does not allow untrusted origins, cookies are secure, debug artifacts are not public and upload/download paths do not loosen MIME/cache protections.

## TEST MATRIX

| Test-ID | Category | Scenario | Expected Safe Behavior | Evidence |
|---|---|---|---|---|
| DEP-001 | HTTPS | Open target over HTTPS | TLS valid; HTTP redirects or is not exposed | URL/status evidence |
| DEP-002 | HSTS | Inspect Strict-Transport-Security | HSTS present for HTTPS deployment or justified beta exception | Header capture |
| DEP-003 | CSP | Inspect Content-Security-Policy | CSP restricts scripts, frames, objects and base URI | Header capture |
| DEP-004 | Frame/MIME | Inspect frame and MIME headers | Framing and MIME sniffing are controlled | Header capture |
| DEP-005 | CORS allowed | Request from approved origin | Approved origin works as intended | CORS evidence |
| DEP-006 | CORS denied | Request from hostile origin | Hostile origin not granted credentials or broad access | CORS evidence |
| DEP-007 | Cookies | Inspect auth/session cookies | Secure, HttpOnly/SameSite where applicable | Cookie evidence |
| DEP-008 | Sourcemaps/debug | Probe sourcemaps, debug routes, stack traces | Not public or explicitly safe | Request evidence |
| DEP-009 | Upload/download | Inspect file/image responses | MIME/cache/content-disposition safe | Response evidence |
| DEP-010 | Gate decision | Consolidate deployment findings | No open Critical/High deployment-surface findings | Final audit |

## ACCEPTANCE CRITERIA

- Target deployment has valid transport security for beta scope.
- CSP/CORS/cookie/header behavior matches documented policy.
- No unapproved debug endpoint, sourcemap or stack trace is public.
- Hostile origins cannot perform credentialed reads/writes.

## BLOCKING CONDITIONS

- Invalid TLS or public HTTP-only beta access without accepted exception.
- Credentialed wildcard CORS or hostile-origin access.
- Public stack traces, source maps with secrets, or debug admin paths.
- Cookies missing required secure flags for browser deployment.

## REQUIRED ARTIFACTS

- Header capture.
- CORS allowed/denied request samples.
- Cookie inspection evidence.
- Debug/sourcemap probe report.
- Final deployment-surface audit.
