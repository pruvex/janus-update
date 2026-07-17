# PRE-IMPLEMENTATION CHECK - BACKLOG-132

PRE-CHECK RESULT
PRE-CHECK PASSED

## Identity

- Target Task: `BACKLOG-132`
- Task: `documentation/tasks/backlog_BACKLOG-132_openrouter_settings_e2e_app_ready_race.md`
- Spec: N/A WITH REASON - bounded E2E runner-readiness bug with no product behavior change
- Backlog Item: `BACKLOG-132`
- Assigned Model: `5.6 Terra`
- Assigned Intelligence: medium
- Mode: `SINGLE_TASK_PRECHECK`
- Risk: LOW
- Artifact Identity Check: PASS - Backlog item, task path, target ID, handoff metadata, failure evidence, and single affected runner match.

## Gate Review

- Scope atomicity: PASS - one readiness seam in one E2E runner.
- Product/architecture decisions: NONE - no Janus runtime behavior changes.
- Acceptance measurability: PASS - syntax, scoped diff, preserved assertion review, and two consecutive exact headed runs.
- Test ownership: PASS - this is the source E2E runner itself, not a generated TestPlan/TestResult artifact.
- Scope exclusions: PASS - no provider, Settings runtime, global Playwright config, API mock, assertion-strength, or unrelated runner changes.
- Evidence basis: PASS - two identical readiness timeouts before the first OpenRouter assertion; both snapshots show the Janus UI rendered.

```text
legacy handoff start
NEXT: janus-executioner
Target Task: BACKLOG-132
Target Subtask: N/A
Task: documentation/tasks/backlog_BACKLOG-132_openrouter_settings_e2e_app_ready_race.md
Spec: N/A WITH REASON - bounded E2E runner-readiness bug with no product behavior change
Backlog Item: BACKLOG-132
Assigned Model: 5.6 Terra
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- Replace the one-shot-only readiness dependency with a deterministic observable Janus app/UI readiness condition while preserving the existing console signal where useful.
- Keep every OpenRouter Settings, secret-leak, and ChatGPT-card assertion unchanged in strength.
Affected Files:
- tests/e2e/openrouter-settings.spec.js
Evidence Focus:
- node --check tests/e2e/openrouter-settings.spec.js
- scoped git diff --check and assertion-preservation review
- two consecutive complete headed passes of the exact runner
- Required command shape: npx playwright test <runner> --headed --workers=1 --reporter=list
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
- Do not change product code, API mocks, global Playwright configuration, or unrelated E2E files.
Automated Evidence Gate:
- node --check tests/e2e/openrouter-settings.spec.js
- npx playwright test tests/e2e/openrouter-settings.spec.js --headed --workers=1 --reporter=list
- npx playwright test tests/e2e/openrouter-settings.spec.js --headed --workers=1 --reporter=list
- git diff --check -- tests/e2e/openrouter-settings.spec.js
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. The source E2E runner may change only at its bounded readiness seam.
Keep Context:
- BACKLOG-132, its task/precheck, the one runner, and the two failure snapshots/traces
Drop Context:
- unrelated backlog items, provider implementation details, old DONE history, and broad audit history
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Bounded runner fix, two consecutive exact headed passes, changed files, and next-skill handoff.
legacy handoff end
```

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.6 Terra
Recommended Intelligence: medium
User Action: none; Codex may execute the bounded runner fix in the current chat.
