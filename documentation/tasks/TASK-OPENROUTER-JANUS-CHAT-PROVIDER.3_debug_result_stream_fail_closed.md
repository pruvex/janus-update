# TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3 - Stream Fail-Closed Debug Result

SKILL 5 DEBUG RESULT: NEEDS RETEST

Iteration: 1

Progress-Validierung: Failure Code `OPENROUTER_STREAM_FAIL_CLOSED_EVIDENCE_MISSING` resolved; new independent Failure Code `RUNNER_VALIDATION_FAILED`; Evidence geaendert ggü. N-1: JA; Stagnationszaehler: 0; Stopp-Regel ausgeloest: JA - two identical headed-runner readiness failures reached the bounded retry limit.

## Root Cause

- The final audit correctly found that an empty OpenRouter upstream stream could emit `done` without any model-identified chunk or upstream completion marker.
- Direct service/gateway tests for stream authentication rejection, exact response identity, malformed/incomplete completion, technical interruption, single attempt, and state-neutral non-auth failures were absent.
- That provider blocker is repaired and the focused/aggregate Python evidence passes.
- The unchanged headed Settings runner now fails before executing its first assertion because it waits for a one-shot browser console readiness message. In both post-fix runs the captured page snapshot shows the Janus UI fully rendered, but `page.waitForEvent('console')` times out after 30 seconds. This is a runner-readiness race outside the Task `.3` stream delta.

## Fix Summary

- `OpenRouterServiceProvider.generate_response_stream()` now requires at least one exact-model upstream chunk and an upstream finish marker before emitting terminal `finish` and `done`.
- A missing model identity raises the existing non-secret model-identity error; a stream ending without completion raises the existing malformed-response error.
- `OpenRouterGateway.stream()` now maps malformed streams to a dedicated terminal non-secret error.
- Added direct service/gateway regressions for complete, empty, incomplete, model-mismatched, authenticated-rejected, and technically interrupted streams; all assert one attempt and correct invalidation/state-neutral behavior.
- Did not modify the evidence-only headed runner after its two out-of-scope readiness failures.

Auto-Verification:
- Status: PASS
- Evidence: focused provider suite `19 passed`; bound Python suites `46 passed`, `44 passed`, and `26 passed` (`116` total); Python compile, JavaScript syntax, scoped diff, new-file whitespace, and credential-shape checks PASS.

Artifact Identity Check: PASS - the product/test delta is limited to the dedicated OpenRouter service, gateway, and provider regressions named by the blocked audit.

Final Feature Suite: FAIL - the exact headed Settings command failed twice at the unchanged console-readiness wait before the first OpenRouter assertion; snapshots show Janus rendered, but the formal runner remains red.

Changed Files:
- `backend/llm_providers/openrouter/service.py`
- `backend/llm_providers/openrouter/gateway.py`
- `backend/tests/test_openrouter_provider.py`
- `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3_FINAL_AUDIT.md`
- `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3_debug_result_stream_fail_closed.md`

## NEXT_STEP

Target Skill: janus-backlog-intake
Canonical State: BLOCKED
Required Artifacts: this debug result, the two headed runner failure traces/screenshots, unchanged `tests/e2e/openrouter-settings.spec.js`, and the prior headed PASS evidence
Evidence Paths: `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3_debug_result_stream_fail_closed.md`; `test-results/tests-e2e-openrouter-setti-d443a-ce-without-exposing-the-key-janus-chromium/error-context.md`; `test-results/tests-e2e-openrouter-setti-d443a-ce-without-exposing-the-key-janus-chromium/trace.zip`; `tests/e2e/openrouter-settings.spec.js`
Failure Code: `RUNNER_VALIDATION_FAILED`
Changed Files: no runner file changed; provider debug delta listed above
Decision: create a separate bounded runner-readiness backlog item before changing the evidence-only E2E runner, then retest Task `.3`.
Reason: the OpenRouter stream blocker is resolved, but final-audit completion cannot use a red headed command and the runner fix is outside the bound Task `.3` scope.
Recommended Model: 5.6 Terra
Recommended Intelligence: medium
Next User Action: none for diagnosis; Codex may intake the separate runner-readiness issue, but any later implementation must follow its own bounded handoff.
