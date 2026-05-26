# JANUS TESTSPEC - DIAMANTSTANDARD v1.0

## TESTSPEC REVIEW EXECUTION ROUTING

target_skill: TEST_SKILL_SECURITY
execution_mode: SWE_1_6
complexity_score: 62
confidence: HIGH
dashboard_hint: CAUTION
security_hint: HIGH
reason: Browser security headers and cookie flags reduce exploitability of XSS, clickjacking, MIME confusion, and permission abuse.

## TEST IDENTITY

- TestSpec Name: 04 Security Headers, Cookies and Browser Surface
- Capability Name: Janus Browser Security Baseline
- Source Input: Janus pre-launch security checklist
- Primary Test Goal: Validate that Janus serves secure HTTP headers, cookie attributes, CSP, framing controls, and restricted browser permissions.
- User Problem: Missing browser protections turn small rendering bugs into account compromise or data exfiltration.
- User Value: Janus sessions and UI are harder to exploit through common browser attack paths.
- Suggested Save Path: documentation/TEST_SPEC/Security Tests/04_security_headers_cookies_and_browser_surface.md
- Machine Result Schema: tests/e2e/generator/test-result.schema.json
- Required Result Markdown: documentation/test-results/<test_run_id>_results.md
- Required Result JSON: documentation/test-results/<test_run_id>_results.json

## TEST OBJECTIVE

Validate that Janus pages and API responses include appropriate security headers and cookie protections for the deployment mode being tested.

## SCOPE

This test covers CSP, frame restrictions, MIME sniffing prevention, referrer policy, permissions policy, HSTS in HTTPS deployments, secure cookie flags, CORS baseline, and browser storage exposure.

## OUT OF SCOPE

Full CSP bypass research, CDN edge configuration certification, and mobile WebView hardening are out of scope.

## USER EXPERIENCE CONTRACT

- Success Behavior: Janus UI works while browser protections are active.
- Failure Behavior: Blocked script/resource errors are fixed through explicit trusted sources, not by disabling policy globally.
- Proactive Clarification Behavior: N/A.
- Cancel / Undo Behavior: N/A.
- User-Facing Explanation: Security headers should be invisible during normal use.

## FUNCTIONAL TEST MATRIX

| TestCase-ID | Scenario | Test Method | Expected Result | Acceptance Criterion | Criticality |
|-------------|----------|-------------|-----------------|----------------------|-------------|
| TC-001 | CSP present | Inspect page headers | CSP exists and is restrictive enough for current architecture | No blanket `unsafe-inline`/`unsafe-eval` unless documented and temporary | HIGH |
| TC-002 | Clickjacking protection | Inspect `frame-ancestors` or `X-Frame-Options` | Framing restricted | App cannot be embedded by arbitrary origins | HIGH |
| TC-003 | MIME sniffing | Inspect `X-Content-Type-Options` | `nosniff` present | Header present on relevant HTML/script/style/API responses | HIGH |
| TC-004 | Referrer policy | Inspect headers | Privacy-preserving referrer policy | No full sensitive URLs leaked cross-origin | MEDIUM |
| TC-005 | Permissions policy | Inspect headers | Unneeded browser APIs disabled | Camera/mic/location/payment disabled unless feature requires them | MEDIUM |
| TC-006 | HSTS | HTTPS deployment only | HSTS enabled | `Strict-Transport-Security` present in HTTPS production/staging | HIGH |
| TC-007 | Session cookies | Inspect `Set-Cookie` | Secure cookie attributes | HttpOnly, Secure in HTTPS, SameSite Lax/Strict or justified None | CRITICAL |
| TC-008 | CORS baseline | Preflight and origin tests | CORS restricted | No wildcard credentials and no arbitrary trusted origin reflection | CRITICAL |

## SECURITY / PRIVACY / PROMPT-INJECTION GATE

- User Data Involved: NO
- Destructive Operations Possible: NO
- External Content Involved: NO
- Prompt Injection Surface: LOW
- Persistence Involved: NO
- Test Sandbox Required: YES
- Sensitive Logs Risk: LOW
- Allowed To Proceed: YES

## SECURITY TEST CASES

| SecurityCase-ID | Risk | Test Method | Expected Safe Behavior | Acceptance Criterion |
|-----------------|------|-------------|------------------------|----------------------|
| SEC-001 | Clickjacking | Try loading Janus in attacker iframe | Blocked by header | Browser refuses arbitrary framing |
| SEC-002 | Cookie theft via JS | Inspect document.cookie after login | Session token not readable | Auth cookies are HttpOnly |
| SEC-003 | Cross-origin credential abuse | CORS request with attacker origin | Denied | No credentialed wildcard or origin reflection |
| SEC-004 | CSP regression | Inject inline script in test page/context | Blocked or sanitized | CSP and renderer prevent execution |
| SEC-005 | Overbroad permissions | Query permission policy | Sensitive APIs disabled | No camera/mic/location/payment unless feature-owned |

## TEST DATA AND SANDBOX

- Test Data Required: Test login session, attacker-origin test page or local origin, representative page/API URLs.
- Sandbox Required: YES.
- Real User Data Allowed: NO.
- Rollback / Recovery: N/A.
- Destructive Test Isolation: N/A.

## LOGGING AND TELEMETRY PRIVACY

- Required Evidence: Header snapshots, cookie attribute screenshots/text, CORS test output, iframe test result.
- Backend Log Evidence: Optional.
- Frontend Debug Evidence: Browser network/security panel evidence recommended.
- Cost / Token Evidence: N/A unless AI summarizes results.
- Sensitive Data Must Not Include: Raw session cookie values.

## MACHINE-READABLE TEST RESULT CONTRACT

- TestResultJson Required: YES
- JSON Schema: tests/e2e/generator/test-result.schema.json
- Markdown Result Path: documentation/test-results/<test_run_id>_results.md
- JSON Result Path: documentation/test-results/<test_run_id>_results.json
- Dashboard Consumption: YES
- Skill 4 / Skill 5 Handoff Evidence: JSON path plus markdown summary path

## COST AND TOKEN OPTIMIZATION CHECKS

- Cost Goal: Deterministic HTTP/browser checks; no LLM needed for PASS/FAIL except policy review.
- Token Goal: Store compact header tables.
- Caching Expectation: Reuse URL inventory and expected header profile.
- Smallest Model First: YES.
- Escalation Limit: Escalate only for CSP tradeoff review.

## SKILL / TOOL ROUTING CHECKS

- Expected Skill / Tool: HTTP client, browser automation, CORS tester.
- Expected Fallback: If production HTTPS is unavailable locally, mark HSTS as deployment-only pending check.
- Clarification Required If: Deployment target or allowed origins are undefined.
- Routing Failure Behavior: Mark failed if app requires disabling core browser protections for normal operation.

## ACCEPTANCE CRITERIA

- [ ] CSP, frame restrictions, nosniff, referrer policy, and permissions policy are present and appropriate.
- [ ] HTTPS deployment sends HSTS.
- [ ] Session cookies are HttpOnly, Secure where applicable, and SameSite protected.
- [ ] CORS does not allow credentialed wildcard or arbitrary origin reflection.
- [ ] Browser storage does not expose long-lived session secrets.

## BLOCKING CONDITIONS

- [ ] No runnable Janus HTTP target exists.
- [ ] Auth flow cannot create a test session.
- [ ] Header behavior differs by deployment and target environment is unknown.
- [ ] TestResultJson cannot be generated.

## RETEST RULES

- [ ] Retest after any framework, proxy, CDN, auth, or deployment config change.
- [ ] Retest both HTML pages and API routes.
- [ ] Retest result is documented under documentation/test-results/.
- [ ] TestResultJson validates against tests/e2e/generator/test-result.schema.json.

## INTERNAL TEST COMPLEXITY BREAKDOWN

Scope Size: 12 - Headers, cookies, CORS, browser storage.
Security Risk: 16 - Missing cookie/CORS protections can be critical.
Provider Matrix Complexity: 0 - No provider matrix required.
Live Test Complexity: 18 - Needs running app and browser/network evidence.
Ambiguity Level: 16 - CSP and allowed origins depend on architecture.
Total Complexity Score: 62
Routing Decision: SWE_1_6
Routing Confidence: HIGH
Dashboard Hint: CAUTION
Security Hint: HIGH
