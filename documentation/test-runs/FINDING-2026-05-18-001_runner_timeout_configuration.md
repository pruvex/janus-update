# Finding: Runner Timeout Configuration Too Short

**Finding ID:** FINDING-2026-05-18-001
**TestRun:** TEST-RUN-2026-05-18-025
**Severity:** HIGH
**Category:** GENERATOR_TIMEOUT_CONFIGURATION
**Status:** OPEN

## Summary

All 26 tests in TEST-RUN-2026-05-18-025 (OWASP Injection, XSS, CSRF, SSRF, Path Traversal) are BLOCKED due to systematic timeout failure in the generated Playwright runner. The `page.waitForFunction` timeout of 15000ms (15 seconds) is insufficient for the model selection UI stabilization phase.

## Root Cause

The generator (`tests/e2e/generator/generate-live-runner.mjs`) produces runners with hardcoded timeout constants:
```javascript
const STREAM_REQUEST_TIMEOUT_MS = 15000;
```

The `model_selection_v2_5` strategy waits for the send button to become enabled after changing provider/model. The 15-second timeout is exceeded before the UI state stabilizes, causing all tests to fail before execution.

## Impact

- **Affected Tests:** All tests using `model_selection_v2_5` strategy
- **Blocked Capabilities:** Security testing (OWASP injection, XSS, CSRF, SSRF, path traversal)
- **Scope:** Systemic - affects current and future test runs with this strategy

## Evidence

- TestRun: TEST-RUN-2026-05-18-025
- Result: 26/26 BLOCKED with identical error
- Error: `TimeoutError: page.waitForFunction: Timeout 15000ms exceeded.`
- Evidence Directory: `documentation/test-results/TEST-RUN-2026-05-18-025/`

## Recommended Fix

### Option 1: Increase Hardcoded Timeout (Quick Fix)
Update generator template to increase `STREAM_REQUEST_TIMEOUT_MS` from 15000ms to 30000ms or 60000ms.

### Option 2: Configurable Timeout (Proper Fix)
Add timeout configuration to TestPlan schema and generate runners with TestPlan-specified timeout values.

### Option 3: Retry Logic (Robust Fix)
Add exponential backoff retry logic for UI stabilization waits instead of single timeout.

## Next Steps

1. Implement fix in `tests/e2e/generator/generate-live-runner.mjs`
2. Regenerate runner for TEST-RUN-2026-05-18-025
3. Execute LIVE_RETEST
4. Validate fix resolves timeout issue

## Related Artifacts

- TestSpec: `documentation/TEST_SPEC/02_security_safety/05_owasp_injection_xss_csrf_ssrf_path_traversal.md`
- TestPlan: `documentation/test-runs/TEST-RUN-2026-05-18-025_plan.json`
- Strategy Registry: `tests/e2e/generator/strategy-registry.json`
- Generator: `tests/e2e/generator/generate-live-runner.mjs`
