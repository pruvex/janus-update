# BACKLOG-132 - OpenRouter Settings E2E App-Ready Race

## Identity

- Backlog Item: `BACKLOG-132`
- Target Task: `BACKLOG-132`
- Entry Point: `PRE_IMPLEMENTATION_VERIFICATION`
- Required Next Skill: `janus-preimplementation-check`
- Risk: LOW
- Estimated Effort: XS

## Goal

Make the existing headed OpenRouter Settings runner detect the already-rendered Janus app deterministically instead of depending only on a one-shot console readiness event.

## Bound Scope

- Primary file: `tests/e2e/openrouter-settings.spec.js`
- Read-only context if required: `frontend/js/app.js`
- Do not change product runtime behavior, OpenRouter provider code, Settings assertions, API mocks, secret checks, ChatGPT-card isolation, Playwright global configuration, or unrelated runners.

## Expected Behavior

- Readiness uses a repeatedly observable app/UI state or a fail-safe combination of that state and the existing console signal.
- Missing the one-shot console event does not fail setup when Janus is demonstrably ready.
- A genuinely unready or broken app still fails with bounded timeout evidence.

## Acceptance Criteria

- The exact command passes twice consecutively:
  - `npx playwright test tests/e2e/openrouter-settings.spec.js --headed --workers=1 --reporter=list`
- Each run reports `3 passed`.
- Existing OpenRouter state, same-key technical failure, delete isolation, secret-leak, and ChatGPT-card assertions remain unchanged in strength.
- `node --check tests/e2e/openrouter-settings.spec.js` passes.
- Scoped `git diff --check` passes.

## Evidence

- `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3_debug_result_stream_fail_closed.md`
- `test-results/tests-e2e-openrouter-setti-d443a-ce-without-exposing-the-key-janus-chromium/error-context.md`
- `test-results/tests-e2e-openrouter-setti-d443a-ce-without-exposing-the-key-janus-chromium/trace.zip`
- Prior green evidence: `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3_execution_result.md`

## HANDOFF_SCOPE

- Backlog Item: `BACKLOG-132`
- Entry Point: `PRE_IMPLEMENTATION_VERIFICATION`
- Required Artifact: this task file
- Required Next Skill: `janus-preimplementation-check`
- Evidence Paths: the four paths above
- Dropped Context: unrelated backlog items, provider-stream implementation history beyond the runner-blocker summary, old DONE history
