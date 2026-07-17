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
