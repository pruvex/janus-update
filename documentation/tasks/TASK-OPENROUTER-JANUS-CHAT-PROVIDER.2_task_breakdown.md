# TASK BREAKDOWN - TASK-OPENROUTER-JANUS-CHAT-PROVIDER.2

## Source Identity

- **Spec:** `documentation/SPEC/OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md`
- **Task File:** `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.md`
- **Backlog Item:** N/A WITH REASON - compiled Feature Spec task
- **Prior Gates:** `janus-spec-review` APPROVED; Task `.1` Final Audit PASS and merged to `master`; parent feature remains `PARTIAL IMPLEMENTATION (1/6)`

## Selected Target

- **Target Task:** `TASK-OPENROUTER-JANUS-CHAT-PROVIDER.2`
- **Target Subtask:** N/A
- **Mode:** SINGLE_TASK_PRECHECK
- **Goal:** Add an isolated OpenRouter credential lifecycle to the existing Janus API-key Settings surface, with content-free authenticated validation and truthful fail-closed `VALID` / `INVALID` / `UNVERIFIED` state, without enabling OpenRouter chat or models.

## Scope

- Add `openrouter` to the existing API-key Settings surface and the backend key-presence contract.
- Store the raw OpenRouter key only in the existing Windows keyring service `Janus-Projekt` under the provider-specific `openrouter` account; no config, database, log, response, test artifact, or browser storage may contain the raw key.
- Validate a newly saved or replaced key without chat content through the currently official authenticated key-info endpoint `GET https://openrouter.ai/api/v1/key`, using the submitted key only as the Bearer credential and sending no request body.
- Treat only a successful authenticated response with the expected non-secret response envelope as the authority that can grant `VALID` to a new or different key; map explicit authentication rejection (`401`) to `INVALID`. For a new, replaced, or otherwise not-yet-confirmed key, timeout, DNS/TLS/network failure, `5xx`, rate limiting, unexpected status, malformed response, or incomplete validation produces `UNVERIFIED` without retry.
- Persist non-secret validation state under a Janus-owned provider-specific authority and bind it to the exact stored key so replacement can never inherit a prior key's `VALID` state. The concrete persistence seam must be proven by precheck and must not create user-editable authority.
- When the same exact stored key is already bound to a confirmed `VALID` state, a temporary technical revalidation failure retains `VALID`; it must not downgrade that unchanged key to `UNVERIFIED` or `INVALID`, delete the key, retry automatically, or fall back to another credential/provider. An explicit authenticated `401` rejection still changes that exact key to `INVALID`.
- Add an OpenRouter-only delete path that removes the stored OpenRouter key and its validation metadata without reading, deleting, or mutating any other provider credential.
- Return and render only masked presence plus non-sensitive state; update the OpenRouter Settings state in place after save, replace, validation, and delete while preserving the separate ChatGPT connection card.
- Keep the production certification registry empty and keep OpenRouter absent from the usable chat provider/model selection until later tasks.

## Files

- `backend/api/routers/system.py`
- `backend/data/schemas.py`
- `frontend/index.html`
- `frontend/js/settings.js`
- `frontend/css/settings.css`
- `backend/tests/test_openrouter_key_settings_api.py` (new)
- `tests/e2e/openrouter-settings.spec.js` (new)

## Explicit Exclusions

- No real OpenRouter credential, live validation call, chat content, model request, chat transport, tool loop, provider/model picker eligibility, selection persistence, DeepDive telemetry, conformance battery, real candidate, release, publish, or production activation.
- No OpenRouter key in `config.json`, AppData JSON, environment variables, database rows, frontend storage, response bodies, logs, exception text, screenshots, Playwright traces, test results, or documentation evidence.
- No automatic validation retry, chat retry, credential fallback, provider fallback, or reuse of an OpenAI/Gemini/Anthropic/ChatGPT credential.
- No changes to Tasks `.3` through `.6`.
- No change to existing provider/model selection behavior; Task `.4` owns chat selection and disabled-selection persistence.

## Acceptance Criteria

1. OpenRouter key create/replace/read-presence/delete operations access only the `Janus-Projekt` provider-specific OpenRouter keyring entries and never read or mutate another provider's key.
2. Saving or replacing a key invalidates any stale prior validation binding before the new key can become eligible; the new key becomes `VALID` only after a successful expected response from the current official content-free authenticated key-info endpoint.
3. Explicit `401` authentication rejection produces `INVALID`. Technical or incomplete validation of a new, replaced, or not-yet-confirmed key produces `UNVERIFIED`; both states are non-eligible and fail closed.
4. A temporary technical validation failure for the same exact previously `VALID` key retains `VALID`, retains the stored key, performs no automatic retry, and does not switch credentials or providers. This preservation never applies to a new or different key, and an explicit `401` still produces `INVALID`.
5. Validation metadata is Janus-owned, non-secret, bound to the exact stored key, restart-safe, and cannot be granted or upgraded through user-editable config, request payload fields, browser storage, cached remote data, or a stale prior-key status.
6. Deleting OpenRouter removes only its raw key and validation metadata and returns the Settings surface to a non-sensitive missing/unverified state without affecting existing providers or ChatGPT connection state.
7. `/api/keys` and all new responses expose only allowlisted values such as masked presence and `VALID` / `INVALID` / `UNVERIFIED`; raw key material, key-derived identifiers, upstream labels, quotas, account identifiers, and diagnostic payloads are not returned.
8. Logs, exceptions, frontend console output, test fixtures/evidence, Playwright output, and screenshots contain no submitted key or credential-shaped derivative.
9. OpenRouter remains visible for credential management only; Task `.2` adds no usable chat provider/model and the empty Task `.1` certification registry remains unchanged.
10. Existing API-key Settings behavior and the separate ChatGPT connection card remain functionally unchanged.

## Tests

- `backend/tests/test_openrouter_key_settings_api.py`: mocked keyring and mocked HTTP-client cases for first save, replace, delete, successful expected response, explicit `401`, timeout/DNS/TLS/network errors, `429`, `5xx`, unexpected status, malformed response, and no automatic retry.
- `backend/tests/test_openrouter_key_settings_api.py`: prove replacement cannot inherit stale `VALID`, validation state is bound to the exact stored key, restart/reload reads the same non-secret state, technical failure leaves a new/different key `UNVERIFIED`, temporary technical revalidation failure preserves `VALID` only for the same exact previously confirmed key, explicit `401` changes that same key to `INVALID`, and deletion removes only OpenRouter state.
- `backend/tests/test_openrouter_key_settings_api.py`: sentinel-secret leak scan across response JSON, captured logs, raised errors, and persisted non-secret metadata; assert no other provider keyring account is read or mutated.
- Regression against existing API-key endpoints and `backend/tests/test_codex_connection_settings_api.py` so the ChatGPT card and API-key non-interference remain intact.
- `tests/e2e/openrouter-settings.spec.js`: headed mocked Settings flow for masked missing/present state, save/replace progress, visible `VALID`, `INVALID`, and `UNVERIFIED`, new/different-key technical failure as `UNVERIFIED`, unchanged previously `VALID` key remaining `VALID` after a temporary technical revalidation failure, explicit `401` becoming `INVALID`, OpenRouter-only delete, no raw key in DOM/console, and no forced navigation into chat/model selection.
- Python compilation for changed Python/test files, JavaScript syntax for `frontend/js/settings.js` and the E2E spec, and scoped `git diff --check`.
- No live OpenRouter call or real key is authorized in automated or manual validation for this task.

## Risks And Precheck Gates

- Reconfirm from current official OpenRouter documentation that `GET /api/v1/key` remains the authenticated content-free current-key endpoint and bind the exact success/auth-rejection contract before implementation. Stop if the official contract changed or cannot be tested without exposing sensitive response fields.
- Prove a Janus-owned restart-safe validation-state persistence seam that is bound to the exact stored OpenRouter key, cannot be user-spoofed, and cannot leave a stale `VALID` status after partial save/replace failure. Stop if this requires a product or architecture decision not fixed by the approved Spec.
- Verify atomic/fail-closed ordering for key save/replace plus validation metadata: no failure may leave a new key carrying an old key's `VALID` state.
- Verify the exact-key branch explicitly: temporary technical failure preserves `VALID` only when the current stored key still matches the fingerprint bound to its confirmed `VALID` metadata; a missing or mismatched binding must be `UNVERIFIED`, while explicit `401` must be `INVALID`.
- Verify that adding OpenRouter delete semantics does not widen generic deletion authority to other providers and that existing provider behavior remains unchanged.
- Verify that the HTTP client uses a bounded timeout, zero automatic retries, no redirect to an unapproved host, and redacted exception/log handling.
- Verify the public response allowlist and frontend rendering before any test uses a sentinel secret; screenshots, traces, logs, and error bodies must remain secret-free.
- Verify Task `.2` can remain within the seven listed files. If a new shared credential service, database migration, chat eligibility integration, or cross-provider architecture change is required, block and route back instead of widening execution.
- Existing unrelated dirty-worktree paths remain out of scope and must be preserved.

## Delegated Review Evidence

- Operator selected OpenRouter for the bounded assist-only review.
- Model: `qwen/qwen3-coder-30b-a3b-instruct`
- Actual cost: `$0.00021586`
- Result: `TASK_BREAKDOWN_FAILED_VALIDATION`; rejected because the draft used legacy `5.4` model values and named the input package instead of the approved Spec/task artifact as source of truth.
- Codex fallback applied; no delegated status, model recommendation, or handoff authority was accepted.
- Evidence: `documentation/codex/model-routing/task-breakdown-runs/WF-OPENROUTER-TASK2-BREAKDOWN-2026-07-16/validation_summary.json`

## Precheck Blocker Resolution

- The blocked precheck at `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.2_precheck.md` identified that the prior wording collapsed new/different-key validation and same-key revalidation into one `UNVERIFIED` rule.
- This revision resolves only that contradiction: new/different/unconfirmed key plus incomplete technical validation is `UNVERIFIED`; the same exact previously confirmed `VALID` key preserves `VALID` through temporary technical failure; explicit authenticated `401` is always `INVALID`; replacement never inherits prior `VALID`.
- No new public state, product behavior, file, architecture, provider eligibility, or implementation authority was added.

## Execution Model

- **Model:** `5.6 Terra`
- **Intelligence:** high
- **Reason:** Credential isolation, remote authentication classification, restart-safe state binding, redaction, and existing Settings/ChatGPT non-interference are security-sensitive but remain bounded to one established surface if precheck proves the persistence and atomicity seams.

## Completion Metadata

- **Status:** DONE - task-scoped Final Audit PASS; parent Feature Spec remains active.
- **Completed At:** 2026-07-17
- **Final Audit:** `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.2_final_audit.md` (`PASS`)
- **Execution Result:** `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.2_execution_result.md`
- **Audit Package:** `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.2_AUDIT_PACKAGE.md`
- **Validation:** OpenRouter API lifecycle `19 passed`; isolated ChatGPT non-interference `1 passed`; Python/JavaScript syntax PASS; scoped mocked Headed Playwright `3 passed`; manual Settings missing-state evidence PASS; Final-Audit-Validator PASS.
- **Production State:** DISABLED - Task `.2` manages only the isolated credential lifecycle; no OpenRouter chat provider, model, selection, transport, live credential validation, or production activation is enabled.
- **Parent Progress:** `2/6` tasks complete; Tasks `.3` through `.6` remain open.

## Decision

TASK DESIGN COMPLETE

```text
@janus-preimplementation-check
Spec: documentation/SPEC/OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md
Task: documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.2_task_breakdown.md
Backlog Item: N/A
Target Task: TASK-OPENROUTER-JANUS-CHAT-PROVIDER.2
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.6 Terra
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```
