# PRE-IMPLEMENTATION CHECK - TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4

PRE-CHECK RESULT
PRE-CHECK PASSED

## Pre-Check Identity

- Target Task: `TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4`
- Target Subtask: N/A
- Task: `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4_task_breakdown.md`
- Spec: `documentation/SPEC/OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md`
- Backlog Item: N/A WITH REASON - compiled Feature Spec task
- Mode: `SINGLE_TASK_PRECHECK`
- Assigned Model: `5.6 Terra`
- Assigned Intelligence: high
- Risk: MEDIUM
- Artifact Identity Check: PASS - exactly one target task, its approved source Spec, and the matching task-breakdown artifact are bound.
- Implementation Started: NO
- Product Tests Executed: NO
- Live Provider/Credential Action: NO
- Git Action: NO

## Gate Review

- Scope and files: PASS - the existing System API, last-used selection, sidebar selector, window override, send path, Settings refresh, privacy notice, and focused regression seams are concrete and readable.
- Certification source: PASS - `load_model_catalog()` already filters OpenRouter through the packaged certification registry and strips AppData authority. Task `.4` consumes that filtered result only and does not populate the registry.
- Credential source: PASS - the existing credential authority exposes a non-secret public state. No raw key, fingerprint, metadata binding, or invalidation capability is needed by the UI.
- Persistence: PASS - `last_used_provider` and `last_used_model` already provide restart-safe sidebar persistence; chat/window provider and model overrides already have their own existing persistence path. The task forbids a second store.
- Retained disabled state: PASS - the generic render and header synchronization currently auto-fallback when a model disappears. The bound task explicitly limits the required exception to persisted OpenRouter selections and requires the exact disabled value to remain representable without becoming sendable.
- Deliberate selection: PASS - provider/model change listeners are concrete persistence seams. OpenRouter auto-selection, first-model fallback, MoA routing, and implicit persistence are explicitly forbidden.
- Send gate: PASS - `effectiveProviderModelForWindow()` is the concrete effective sidebar/window resolver and `sendMessage()` is a concrete pre-transmission gate. Task `.4` requires exact eligibility there, not a CSS-only disable.
- Settings lifecycle refresh: PASS - existing OpenRouter save/delete actions and public-state rendering are concrete points to refresh chat eligibility without changing key network behavior.
- Privacy: PASS - the modal, its acknowledgement version constant, and the linked beta privacy notice are concrete versioned copy surfaces. The required statement is fixed by the Spec and introduces no open policy decision.
- Existing providers: PASS - OpenAI, Gemini, Ollama, and ChatGPT generic fallback and selector behavior are explicitly protected by regression evidence.
- Production safety: PASS - the packaged certification registry remains empty, so implementation alone cannot make OpenRouter production-selectable.
- Open product decisions: NONE.
- Open architecture decisions: NONE. Exact helper names, endpoint path, stable reason-code names, and DOM class names remain bounded implementation choices inside the named files and binary contracts.

## Execution Risk Controls

- Use only mocked public key states and injected certified catalog fixtures. Never read, enter, save, or print a real credential and never make a live OpenRouter request.
- The frontend must not infer certification from candidate data, raw registry content, settings model-selection data, model-name prefixes, or local catalog injection.
- A retained disabled OpenRouter option must be visibly selected but impossible to submit; selector rendering and the send gate must share exact provider/model eligibility semantics.
- Generic fallback remains unchanged for existing providers. Only an ineligible persisted OpenRouter selection bypasses automatic deletion or replacement.
- Window-local OpenRouter overrides retain their exact disabled provider/model without overwriting sidebar defaults or unrelated window state.
- No TestPlan/TestResult files are manually created or edited. No final audit, documentation closeout, Git, release, or production action occurs in execution.
- Preserve unrelated dirty and untracked operator files.

## Validation

- Task/Spec identity and single-target scope: PASS
- Affected files exist or are explicitly marked new: PASS
- Filtered catalog authority and packaged-empty production state: PASS
- Non-secret credential public-state boundary: PASS
- Existing sidebar and restart persistence seams: PASS
- Existing window override persistence seams: PASS
- Effective provider/model and pre-send gate seams: PASS
- Retained disabled exact-selection contract: PASS
- Deliberate-selection/no-fallback contract: PASS
- Privacy-copy surface: PASS
- Required backend, functional, headed, syntax, leak, and diff evidence: PASS
- Product tests or live-provider checks during precheck: NOT RUN by rule

## Execution Handoff

```text
legacy handoff start
NEXT: janus-executioner
Target Task: TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4
Target Subtask: N/A
Task: documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4_task_breakdown.md
Spec: documentation/SPEC/OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md
Backlog Item: N/A
Assigned Model: 5.6 Terra
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- Integrate OpenRouter into existing sidebar/window provider-model selectors through one non-secret eligibility state derived only from the credential authority public state and the already filtered certified catalog.
- Preserve an ineligible persisted OpenRouter provider/model visibly but disabled across rerender, reload, restart, and explicit window overrides; block sending and never auto-delete, auto-replace, or fallback.
Affected Files:
- frontend/index.html
- frontend/js/app.js
- frontend/js/beta-privacy-notice.js
- frontend/js/settings.js
- frontend/js/chat.js
- frontend/js/chat-manager.js
- frontend/js/window-state.js
- frontend/css/settings.css
- backend/main.py
- backend/api/routers/system.py
- backend/data/schemas.py
- backend/tests/test_openrouter_selection_api.py
- documentation/beta/BETA_PRIVACY_NOTICE.md
- tests/functional/chat-core.spec.js
- tests/e2e/openrouter-settings.spec.js
Evidence Focus:
- Public API key-state/catalog matrix, exact filtered model IDs, stable eligibility reason, retained persistence, and absence of secret/fingerprint/binding data.
- Sidebar and window selectors: deliberate valid choice, retained disabled exact selection, no automatic fallback, reload/restart persistence, same-selection recovery, and deliberate valid reselection.
- Effective provider/model send blocking, packaged-empty registry non-activation, Settings visibility, privacy wording, and unchanged existing-provider behavior.
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
- Do not change key validation/network behavior, provider runtime, telemetry, registry contents, conformance, release, or production activation.
Automated Evidence Gate:
- python -m pytest -q backend/tests/test_openrouter_selection_api.py backend/tests/test_openrouter_key_settings_api.py backend/tests/test_openrouter_certification_registry.py
- node --check frontend/js/app.js
- node --check frontend/js/beta-privacy-notice.js
- node --check frontend/js/settings.js
- node --check frontend/js/chat.js
- node --check frontend/js/chat-manager.js
- node --check frontend/js/window-state.js
- npx playwright test tests/functional/chat-core.spec.js --workers=1 --reporter=list
- Required runner form: npx playwright test <runner> --headed --workers=1 --reporter=list
- npx playwright test tests/e2e/openrouter-settings.spec.js --headed --workers=1 --reporter=list
- git diff --check -- frontend/index.html frontend/js/app.js frontend/js/beta-privacy-notice.js frontend/js/settings.js frontend/js/chat.js frontend/js/chat-manager.js frontend/js/window-state.js frontend/css/settings.css backend/main.py backend/api/routers/system.py backend/data/schemas.py backend/tests/test_openrouter_selection_api.py documentation/beta/BETA_PRIVACY_NOTICE.md tests/functional/chat-core.spec.js tests/e2e/openrouter-settings.spec.js
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md
- documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4_task_breakdown.md
- documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4_precheck.md
- named affected files and evidence commands only
Drop Context:
- Tasks .1 through .3 implementation history
- Tasks .5 and .6, unrelated backlog, audit, release, and Git history
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths. Stop before final audit, documentation closeout, Git, release, or production activation.
Expected Output:
- Implementation result, executed checks, affected files, residual risks, and exact next-skill handoff.
legacy handoff end
```

## NEXT STEP

Recommended Skill: janus-executioner

Recommended Model: `5.6 Terra`

Recommended Intelligence: high

User Action: Execute exactly `TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4` from this canonical PASS artifact; do not broaden scope or perform live-provider, credential, Git, release, or production actions.
