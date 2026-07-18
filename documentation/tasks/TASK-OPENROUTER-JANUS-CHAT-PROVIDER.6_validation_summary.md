Validation summary for Task .6 audit package:

Offline / focused:
- pytest openrouter conformance + certification registry: historically PASS (83+; later suites grew through debug iterations; treat current suite as re-checkable)
- headed openrouter-settings.spec.js: PASS twice consecutively (4 passed) after readiness repair
- runtime registry empty invariant SHA256 at execution: 7712D5B2775F5BDED03EF1C2DAE4228F9FCC8B7441140FC4F1AB8F56210EC46F

Live:
- TEST-RUN-2026-07-17-007: FAIL (historical; superseded)
- TEST-RUN-2026-07-17-008: PASS 117/117, 0 FAIL, 0 BLOCKED
- registry candidate: TEST_PASS_AUDIT_PENDING, runtime false
- runtime activation: FORBIDDEN until independent final audit PASS and later docs activation

Manual Janus evidence:
- Operator saved dedicated certification key through Settings (VALID reported during live phase)
- N/A for production chat use: OpenRouter remains intentionally non-selectable with empty runtime registry
