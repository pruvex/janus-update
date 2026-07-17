# AUDIT_PACKAGE

Generated: 2026-07-17 15:35:19 UTC

## Goal

Final audit of Task .4 OpenRouter chat eligibility, deliberate selector integration, retained-disabled selection, send blocking, recovery, window overrides, and privacy copy.

## Scope Rules

- Audit the provided package and changed artifacts only.
- Do not rely on development chat history.
- Verify cost, caching, skill quality, safety scope, and validation evidence.
- On re-audit, review the blocker delta first before widening scope.
- If scoped paths were provided, treat them as the audit diff boundary.

## Bound Audit Inputs

- Spec: PRESENT - documentation/SPEC/OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md; audit only Task .4, parent Spec remains partial.
- Task File: documentation\tasks\TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4_task_breakdown.md
- Backlog Item: N/A WITH REASON - compiled Feature Spec task
- Pre-Implementation Check: documentation\tasks\TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4_precheck.md
- Manual Janus Evidence: PRESENT - operator confirmed both checks PASS: privacy notice names OpenRouter plus selected upstream model provider; Chat selector keeps OpenRouter unusable while Settings reports not saved and UNVERIFIED.
- Pipeline Completion Status: Task .4 implementation complete yes; parent Tasks .5-.6 remain outside this single-task audit.

## Backlog Item

```text
N/A WITH REASON - No backlog source or marker provided.
```

## Task Acceptance Scope

```text
# TASK BREAKDOWN - TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4

## Source Identity

- **Spec:** `documentation/SPEC/OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md`
- **Task File:** `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.md`
- **Backlog Item:** N/A WITH REASON - compiled Feature Spec task
- **Prior Gates:** Tasks `.1`, `.2`, and `.3` Final Audit PASS; parent feature remains `PARTIAL IMPLEMENTATION (3/6)`; production certification registry remains intentionally empty

## Selected Target

- **Target Task:** `TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4`
- **Target Subtask:** N/A
- **Mode:** SINGLE_TASK_PRECHECK
- **Goal:** Integrate OpenRouter and only its visible, exactly versioned certified models into the existing chat provider/model selectors, while preserving an invalidated saved OpenRouter selection visibly but disabled until the same selection becomes eligible again or the user deliberately chooses another valid selection.

## Source Of Truth

- The filtered catalog returned by `backend.utils.config_loader.load_model_catalog()` remains the sole model-certification authority. The UI must not read candidate data or the raw registry and must not infer certification.
- `backend.services.openrouter_credential_authority` remains the sole OpenRouter key-state authority. The UI receives only its non-secret public state and never raw credentials, fingerprints, or binding handles.
- `last_used_provider` plus `last_used_model` remain the existing persisted sidebar selection source. Existing chat/window provider and model overrides remain the window-local source and are not replaced by a second OpenRouter store.
- Task `.4` does not populate the empty certification registry. Production therefore remains disabled after implementation unless tests inject a certified catalog fixture.

## Scope

- Expose one non-secret OpenRouter chat-eligibility payload through the existing System API surface. It combines the public credential state with the already filtered OpenRouter catalog and reports whether OpenRouter is selectable plus a stable reason code. It must expose only visible certified exact model IDs and must never expose the key, key metadata internals, fingerprints, binding handles, candidate models, hidden registry records, or `latest` aliases.
- Add OpenRouter to the existing sidebar and window-header provider/model selectors only when the current UI state is eligible. The Settings key-management option remains visible independently.
- Treat the filtered catalog as the exact OpenRouter model allowlist. OpenRouter does not use the generic user-editable model-selection list, does not auto-select all catalog models as a user preference, and does not allow candidate, alias, hidden, locally injected, or uncertified IDs.
- Require deliberate user changes for a new OpenRouter provider/model selection. Do not automatically switch to OpenRouter, choose its first model, route between its models, or persist a model merely because eligibility appeared.
- Preserve a previously persisted OpenRouter provider/model pair when it becomes ineligible because the key is not `VALID` or the exact model disappears from the filtered catalog. Render that exact provider/model visibly as a disabled retained selection in the sidebar and corresponding window override, disable sending for that effective selection, and do not overwrite persisted state.
- Restore the same retained selection automatically only when both original conditions return: the key is `VALID` and the exact persisted model is again present in the filtered catalog. A deliberate choice of another currently eligible OpenRouter model may replace it through the existing persistence path.
- Special-case the existing generic missing-model fallback only for retained OpenRouter selections. Existing OpenAI, Gemini, Ollama, ChatGPT, sidebar, chat history, and window-override behavior must remain unchanged.
- Ensure the effective provider/model used by `frontend/js/chat.js` and `frontend/js/chat-manager.js` cannot submit while the retained OpenRouter selection is disabled. The disabled state must be based on the same eligibility payload and exact model identity used to render the selectors.
- Extend the existing beta privacy notice with explicit wording that selected content may pass through OpenRouter to the deliberately selected upstream model provider. Keep the existing acknowledgement/version behavior intact unless its current versioning contract requires a notice-version bump for changed copy.

## Files

- `frontend/index.html`
- `frontend/js/app.js`
- `frontend/js/beta-privacy-notice.js`
- `frontend/js/settings.js`
- `frontend/js/chat.js`
- `frontend/js/chat-manager.js`
- `frontend/js/window-state.js`
- `frontend/css/settings.css`
- `backend/main.py`
- `backend/api/routers/system.py`
- `backend/data/schemas.py`
- `backend/tests/test_openrouter_selection_api.py` (new focused API/eligibility and persistence evidence)
- `documentation/beta/BETA_PRIVACY_NOTICE.md`
- `tests/functional/chat-core.spec.js`
- `tests/e2e/openrouter-settings.spec.js`

The new focused backend test file refines the compiled task list only to provide direct automated evidence for the new non-secret eligibility and retained-selection API behavior. No new production subsystem or persistence store is introduced.

## Explicit Exclusions

- No OpenRouter key save/replace/delete or validation-network changes.
- No OpenRouter service, gateway, transport, tool-loop, credential invalidation, retry, fallback, or provider-runtime changes from Task `.3`.
- No certification candidate, registry population, runtime certification, full OpenRouter catalog, `latest` alias, or production activation.
- No DeepDive telemetry, token/cost persistence, database migration, conformance battery, live OpenRouter request, real credential, release, or publish action.
- No automatic OpenRouter provider/model choice, MoA routing, helper-provider selection, fallback to another OpenRouter model, or fallback to another provider.
- No second persistence mechanism for sidebar or window selections and no automatic deletion of an ineligible OpenRouter selection.
- No behavior change for existing providers beyond regressions needed to prove they are unchanged.

## Acceptance Criteria

1. The Settings OpenRouter key-management surface remains visible for `VALID`, `INVALID`, `UNVERIFIED`, and missing-key states.
2. OpenRouter is offered as a usable chat provider only when its public key state is `VALID` and the filtered catalog contains at least one visible certified exact model.
3. The OpenRouter model selector contains only exact IDs returned by the filtered catalog. Candidate-only records, hidden entries, user-injected records, ambiguous IDs, and `latest` aliases never appear.
4. Janus never selects OpenRouter or an OpenRouter model automatically. A new OpenRouter provider/model choice is persisted only after a deliberate user selection.
5. If a persisted OpenRouter key becomes non-`VALID` or its exact selected model disappears, the same provider/model remains visibly retained and persisted but disabled; sending is blocked and no fallback or replacement is written.
6. The retained provider/model survives UI rerender, reload, and Janus restart through the existing persistence paths. Corresponding explicit window overrides retain the same disabled exact value without changing sidebar defaults or unrelated windows.
7. When the same exact model becomes visible again and the key is `VALID`, the retained selection becomes usable without replacing it. A deliberate different eligible model choice also works and persists.
8. OpenAI, Gemini, Ollama, ChatGPT, sidebar/header synchronization, chat history, and existing window-override behavior remain unchanged.
9. The privacy notice explicitly states that selected content may be transmitted through OpenRouter to the selected model provider.
10. With the packaged empty certification registry, OpenRouter remains unavailable for production chat and zero OpenRouter model is selectable.

## Tests

- `backend/tests/test_openrouter_selection_api.py`: key-state/catalog matrix for missing, `UNVERIFIED`, `INVALID`, and `VALID`; empty versus injected filtered catalog; exact visible model IDs only; stable disabled reason; secret/fingerprint/binding absence; persisted invalid selection is returned unchanged; no server-side fallback or automatic replacement.
- `tests/functional/chat-core.spec.js`: focused selector-state units for deliberate selection, no auto-selection, exact model filtering, retained disabled selection, send blocking, recovery of the same model, deliberate valid reselection, and unchanged existing-provider fallback behavior.
- `tests/e2e/openrouter-settings.spec.js`: mocked headed scenarios for valid selection, missing key, empty certified catalog, key invalidation, model disappearance, reload/restart persistence, same-selection re-enable, deliberate alternative selection, window override retention, Settings visibility, versioned modal/notice privacy copy, and no secret exposure.
- Existing relevant Settings and chat regressions for navigation, Sidebar provider/model selection, last-used selection, header/window overrides, and ChatGPT isolation.
- Python compilation for changed Python files, JavaScript syntax checks for changed JavaScript files, scoped secret-shape assertions, and scoped `git diff --check`.
- Exact headed gate: `npx playwright test tests/e2e/openrouter-settings.spec.js --headed --workers=1 --reporter=list`.

## Risks And Precheck Gates

- Verify the UI consumes only the filtered catalog and the credential authority's public state; block any raw key, fingerprint, binding, registry-internal, candidate, or AppData-injected certification authority.
- Verify the retained disabled option is representational only and cannot be submitted. The send gate must use the effective sidebar/window provider and exact model, not only CSS or a disabled DOM option.
- Verify every generic auto-fallback branch in `frontend/js/app.js`, header synchronization, and reload handling is either unchanged for existing providers or explicitly bypassed only for retained OpenRouter selections.
- Verify no server or frontend save path deletes or replaces `last_used_provider`/`last_used_model` merely because OpenRouter is ineligible.
- Verify window-local overrides do not silently collapse to the sidebar or first model when their exact OpenRouter selection is temporarily ineligible.
- Verify the packaged empty registry keeps OpenRouter absent/unusable while mocked certified fixtures can exercise the positive UI path.
- Verify privacy copy names both OpenRouter and the selected upstream model provider without changing unrelated policy claims.
- Preserve all unrelated dirty and untracked operator files.

## Execution Model

- **Model:** `5.6 Terra`
- **Intelligence:** high
- **Reason:** This is a multi-surface UI, persistence, and fail-closed eligibility integration with clear existing architecture and no new credential or provider-runtime boundary.

## Decision

TASK DESIGN COMPLETE

```text
@janus-preimplementation-check
Spec: documentation/SPEC/OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md
Task: documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4_task_breakdown.md
Backlog Item: N/A
Target Task: TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.6 Terra
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```
```

## Pre-Implementation Check

```text
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
```

## Changed Files

```text
M backend/api/routers/system.py
 M backend/data/schemas.py
 M documentation/beta/BETA_PRIVACY_NOTICE.md
 M frontend/css/settings.css
 M frontend/index.html
 M frontend/js/app.js
 M frontend/js/beta-privacy-notice.js
 M frontend/js/chat.js
 M frontend/js/settings.js
 M tests/e2e/openrouter-settings.spec.js
 M tests/functional/chat-core.spec.js
?? backend/tests/test_openrouter_selection_api.py
?? documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4_debug_result_chat_core_readiness.md
?? documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4_debug_result_openrouter_suite_readiness.md
?? documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4_execution_result.md
?? documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4_precheck.md
?? documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4_task_breakdown.md
```

## Artifact Inventory

```text
FILE C:\KI\Janus-Projekt\documentation\SPEC\OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md (20971 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-OPENROUTER-JANUS-CHAT-PROVIDER.md (21859 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4_task_breakdown.md (11634 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4_precheck.md (9694 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4_execution_result.md (6592 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4_debug_result_chat_core_readiness.md (2418 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4_debug_result_openrouter_suite_readiness.md (2361 bytes)
```

## Diff Summary

```text
backend/api/routers/system.py             |  42 +++-
 backend/data/schemas.py                   |  15 ++
 documentation/beta/BETA_PRIVACY_NOTICE.md |   3 +-
 frontend/css/settings.css                 |  18 ++
 frontend/index.html                       |  12 +-
 frontend/js/app.js                        | 311 ++++++++++++++++++++++++++++--
 frontend/js/beta-privacy-notice.js        |   2 +-
 frontend/js/chat.js                       |  28 +++
 frontend/js/settings.js                   |   2 +
 tests/e2e/openrouter-settings.spec.js     | 302 +++++++++++++++++++++++++++++
 tests/functional/chat-core.spec.js        |  64 +++++-
 11 files changed, 778 insertions(+), 21 deletions(-)
```

## Validation

```text
# TASK EXECUTION RESULT - TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4

Canonical State: HANDOFF
Target Task: TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4
Pre-Check: PRE-CHECK PASSED

## Scope Delivered

- Eine neue nicht geheime System-API kombiniert den öffentlichen OpenRouter-Keyzustand mit dem bereits fail-closed gefilterten Zertifizierungskatalog.
- OpenRouter wird im Chat nur angeboten, wenn der Key `VALID` ist und mindestens ein exakt zertifiziertes Modell sichtbar ist.
- Eine neue OpenRouter-Auswahl erfordert eine bewusste Provider- und Modellauswahl; das erste Modell wird nicht automatisch gewählt oder gespeichert.
- Eine gespeicherte, inzwischen ungültige OpenRouter-Provider-/Modellkombination bleibt in Sidebar und Fenster-Override sichtbar, ist aber deaktiviert und kann keinen Request senden.
- Dasselbe Modell wird bei wiederhergestellter Eignung erneut nutzbar. Ein anderes gültiges Modell kann bewusst gewählt und über den vorhandenen Last-used-/Fensterpfad gespeichert werden.
- OpenAI, Gemini, Ollama und ChatGPT behalten ihre bisherigen generischen Auswahl- und Fallbackpfade.
- Die Beta-Datenschutzerklärung und das versionierte In-App-Modal nennen ausdrücklich die mögliche Weiterleitung über OpenRouter an den ausgewählten Upstream-Modellanbieter.
- Der produktive Zertifizierungs-Registry bleibt absichtlich leer. Die Implementierung aktiviert daher noch kein produktives OpenRouter-Chatmodell.

Changed Files:
- `backend/api/routers/system.py`
- `backend/data/schemas.py`
- `backend/tests/test_openrouter_selection_api.py`
- `frontend/index.html`
- `frontend/css/settings.css`
- `frontend/js/app.js`
- `frontend/js/beta-privacy-notice.js`
- `frontend/js/chat.js`
- `frontend/js/settings.js`
- `documentation/beta/BETA_PRIVACY_NOTICE.md`
- `tests/e2e/openrouter-settings.spec.js`
- `tests/functional/chat-core.spec.js`
- `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4_task_breakdown.md`
- `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4_precheck.md`
- `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4_debug_result_chat_core_readiness.md`
- `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4_debug_result_openrouter_suite_readiness.md`
- `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4_execution_result.md`
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/SKILL_USAGE_LOG.md`

Executed Checks:
- Task-breakdown validator: PASS.
- Preimplementation validator: PASS.
- `python -m pytest -q backend/tests/test_openrouter_selection_api.py backend/tests/test_openrouter_key_settings_api.py backend/tests/test_openrouter_certification_registry.py`: PASS, `41 passed`.
- `npx playwright test tests/e2e/openrouter-settings.spec.js --headed --workers=1 --reporter=list`: PASS, `4 passed`.
- `npx playwright test tests/functional/chat-core.spec.js --workers=1 --reporter=list`: PASS, `1 passed`.
- `node --check` for all changed and directly protected JavaScript runners/modules: PASS.
- `python -m py_compile backend/api/routers/system.py backend/data/schemas.py backend/tests/test_openrouter_selection_api.py`: PASS.
- Scoped `git diff --check`: PASS.
- Scoped raw OpenRouter-secret and raw Bearer scan: PASS, zero matches.
- Debug-result validators: PASS for both bounded runner-readiness slices.
- No live OpenRouter request, real API key mutation, registry population, release, publish, merge, commit, push, or sync occurred.

Auto-Verification:
- Status: PASS
- Evidence: non-secret key/catalog matrix, exact-model allowlist, deliberate-selection behavior, retained-disabled state, no-stream guarantee, same-model recovery, deliberate alternative selection, window-override retention, privacy copy, existing credential regressions, deterministic OpenAI chat submit, syntax/compile/diff and leak gates all passed.

Manual Janus Validation Gate:
- Status: PASS
- Test Example: Janus normal neu starten, ohne einen API-Key einzugeben oder zu ändern. Im neuen Datenschutzdialog prüfen, dass OpenRouter und der ausgewählte Modellanbieter ausdrücklich genannt werden. Danach `Einstellungen > API Keys` öffnen und den vorhandenen OpenRouter-Status ansehen. Zur Chat-Ansicht zurückkehren und den Provider-Selector prüfen.
- Expected Result: Der Datenschutzdialog erklärt die mögliche Weiterleitung über OpenRouter. Bei fehlendem, `UNVERIFIED` oder `INVALID` Key und dem absichtlich leeren produktiven Zertifizierungs-Registry ist OpenRouter im Chat nicht als nutzbarer Provider auswählbar; eine eventuell bereits gespeicherte OpenRouter-Auswahl bleibt nur deaktiviert sichtbar. OpenAI/Gemini/Ollama bleiben unverändert nutzbar. Es wird kein OpenRouter-Request gesendet.
- If Failed: route to janus-debug
- If Passed: route to janus-final-audit
- Evidence: Operator confirmed both observations with `beide pass`: the versioned privacy notice names OpenRouter plus the selected model provider, and OpenRouter is not usable in the chat selector while Settings reports `OpenRouter: nicht gespeichert · UNVERIFIED`. The unrelated ChatGPT card reported unavailable and was not changed.

Known Risks:
- Positive OpenRouter-Auswahlzustände wurden ausschließlich mit gemockten öffentlichen Zuständen und zertifizierten Modellfixtures geprüft, weil der produktive Registry absichtlich leer bleibt.
- Die Headed-Läufe protokollieren weiterhin unabhängige degradierte Vector-/Vision-Startup-Warnungen; sie beeinflussten die gebundenen Assertions nicht.
- Tasks `.5` und `.6`, echte Kandidatenzertifizierung, Telemetrie-/DeepDive-Abschluss, Release und Produktionsaktivierung sind nicht Bestandteil dieses Tasks.

NEXT_STEP
Target Skill: janus-final-audit
Canonical State: HANDOFF
Required Artifacts: dieses Execution-Ergebnis, Task-.4-Precheck, beide grünen Debug-Nachweise und Manual Janus Validation PASS
Evidence Paths: `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4_execution_result.md`; `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4_precheck.md`; `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4_debug_result_chat_core_readiness.md`; `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4_debug_result_openrouter_suite_readiness.md`
Failure Code: N/A - no product failure remains in automated evidence
Changed Files: see the exact scope list above
Decision: Task `.4` zur finalen unabhängigen Qualitätsprüfung übergeben
Reason: automatische Evidenz und die sichere reale Janus-Beobachtung sind vollständig PASS
Recommended Model: 5.6 Terra
Recommended Intelligence: high
New Chat: no
Next User Action: keine weitere manuelle Prüfung vor dem Final Audit
```

## Notes

No additional notes provided.

## Risks

Positive OpenRouter selection uses controlled fixtures because the production certification registry remains intentionally empty; parent Tasks .5-.6 and production activation are outside this audit.

## Open Issues

None inside Task .4 after automated and manual PASS evidence.

## Re-Audit Delta

No re-audit delta provided.

## Final Audit Handoff

```text
NEW_CHAT_HANDOFF
NEXT: final-skill-audit
MODEL: 5.6 Sol/high if runtime-supported; otherwise 5.6 Terra/high
PASS: C:\KI\Janus-Projekt\documentation\tasks\TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4_AUDIT_PACKAGE.md
ASK: Lade nur dieses Paket im neuen Chat und starte dann den Final Audit.
DROP: dev chat history
```

Use `5.6 Sol/high` when the current Codex run can start it; if Codex reports `gpt-5.6-sol` is unsupported for the active ChatGPT account, use `5.6 Terra/high` and record `SOL_UNAVAILABLE_FOR_CHATGPT_CODEX_ACCOUNT`.

For bounded same-thread re-audits after a local blocker fix, `5.6 Terra/high` is acceptable when the package stays compact and the risk did not escalate.
