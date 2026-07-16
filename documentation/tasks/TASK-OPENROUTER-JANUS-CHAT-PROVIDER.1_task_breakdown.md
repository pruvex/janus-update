# TASK BREAKDOWN - TASK-OPENROUTER-JANUS-CHAT-PROVIDER.1

## Source Identity

- **Spec:** `documentation/SPEC/OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md`
- **Task File:** `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.md`
- **Backlog Item:** N/A WITH REASON - compiled Feature Spec task
- **Prior Gates:** `janus-spec-review` APPROVED; complexity `80`; `Skill-1 Ready: YES`; split `NO`

## Selected Target

- **Target Task:** `TASK-OPENROUTER-JANUS-CHAT-PROVIDER.1`
- **Target Subtask:** N/A
- **Mode:** SINGLE_TASK_PRECHECK
- **Goal:** Establish exactly one checked-update-owned, fail-closed OpenRouter certification authority and expose only fully certified exact-version models through every normal Janus catalog path, without selecting or enabling any production candidate yet.

## Scope

- Add the release-owned versioned OpenRouter certification dataset under `backend/config/` and load it from packaged Janus resources as the sole runtime certification authority.
- Bind each eligible record to exact model ID, concrete model version, battery version, passed status, and complete mandatory test/audit evidence state.
- Treat missing, malformed, duplicate, incomplete, failed, ambiguous, alias-based, or binding-mismatched records as not certified.
- Filter OpenRouter entries before they can leave either model-catalog loader or `/api/models/catalog`.
- Keep the production certification dataset empty or non-certified in Task `.1`; use isolated test fixtures for valid and invalid record cases. Exact Claude/GLM/DeepSeek/Qwen candidate selection and real certification remain Task `.6`.
- Preserve all non-OpenRouter catalog entries and selection behavior unchanged.

## Files

- `backend/config/openrouter_certified_models.json` (new)
- `backend/config/model_catalog.json`
- `backend/utils/config_loader.py`
- `backend/services/model_catalog.py`
- `backend/api/routers/system.py`
- `backend/tests/test_openrouter_certification_registry.py` (new)
- `backend/tests/test_model_hierarchy_single_source.py`

## Explicit Exclusions

- No real launch-model IDs, model availability research, live OpenRouter call, runtime certification, full catalog import, hot pull, or candidate PASS marking; those belong to Task `.6`.
- No OpenRouter key storage or validation, Settings key UI, provider/model selection persistence, chat transport, tool loop, DeepDive telemetry, privacy copy, release, publish, or production activation.
- No user-editable AppData file, `config.json`, `model_selection`, environment variable, remote response, or cached last-known list may grant OpenRouter certification.
- No modification of OpenAI, Gemini, Ollama, ChatGPT, image, audio, or local model eligibility.
- No implementation of Tasks `.2` through `.6`.

## Acceptance Criteria

1. Exactly one release-owned certification dataset is the runtime authority for OpenRouter model visibility.
2. AppData catalog overrides and all other user-editable or runtime-derived state cannot create, upgrade, or restore OpenRouter certification.
3. A model is eligible only when one unambiguous record binds an exact model ID, concrete model version, current battery version, passed status, and complete mandatory test/audit evidence state.
4. Missing, malformed, duplicate, incomplete, failed, ambiguous, `latest`-based, or binding-mismatched records are fail-closed and invisible.
5. A change to model ID, concrete model version, or battery version invalidates the prior binding until a later checked update supplies a new fully passed record.
6. `backend.utils.config_loader.load_model_catalog()`, `backend.services.model_catalog.get_models_by_provider("openrouter")`, and `/api/models/catalog` expose the same filtered OpenRouter set.
7. Task `.1` exposes no production-certified OpenRouter model because exact candidates and real evidence are deferred to Task `.6`.
8. Existing non-OpenRouter model catalog entries and `/api/models/catalog` output remain unchanged.
9. Invalid registry content produces a non-sensitive fail-closed result and does not fall back to a user catalog, remote list, alias, or previously cached OpenRouter set.
10. The packaged backend includes the release-owned dataset through the existing `backend/config` resource bundle without adding a mutable second authority.

## Tests

- `backend/tests/test_openrouter_certification_registry.py`: isolated temporary-fixture cases for valid binding, empty registry, missing required binding, failed status/evidence, duplicate exact ID, malformed JSON, unknown schema/battery version, version mismatch, `latest` alias, and fail-closed no-fallback behavior.
- `backend/tests/test_openrouter_certification_registry.py`: parity assertions across the config loader, service loader, and `/api/models/catalog`, including AppData attempts that must not grant OpenRouter visibility.
- `backend/tests/test_model_hierarchy_single_source.py`: regression that existing provider catalog/hierarchy ownership remains unchanged and Task `.1` adds no OpenRouter MOA hierarchy.
- Static JSON parsing for `backend/config/model_catalog.json` and `backend/config/openrouter_certified_models.json`.
- Python syntax checks for changed Python files and scoped `git diff --check`.
- No live provider request, credential read/write, model certification, release action, or production call is authorized in validation.

## Risks And Precheck Gates

- Verify that the existing AppData-wins merge in `backend/utils/config_loader.py` cannot influence OpenRouter certification or reintroduce an invalidated OpenRouter entry.
- Verify that `backend/services/model_catalog.py` does not remain an independent unfiltered OpenRouter path; it must share the same certification decision or return no OpenRouter models.
- Verify that API catalog assembly in `backend/api/routers/system.py` cannot append or restore an uncertified OpenRouter entry through another lifecycle or model source.
- Verify the dataset is bundled by the existing `backend/config` PyInstaller resource rule and is read as release content, not copied into a user-authoritative mutable source.
- Verify loader caching, if used, cannot keep a previously certified OpenRouter record visible after a binding/version change.
- Block precheck if implementation would require selecting real model IDs, defining the conformance battery contents, changing existing provider eligibility, or using AppData/remote state as certification authority.
- Block precheck if a single shared filtered catalog decision cannot cover both loader paths without architecture invention beyond the approved Spec.

## Execution Model

- **Model:** `5.6 Terra`
- **Intelligence:** high
- **Reason:** Bounded catalog/config implementation with a security-relevant fail-closed authority boundary and two existing loader paths; no architecture or product decision remains if precheck confirms shared ownership.

## Decision

TASK DESIGN COMPLETE

```text
@janus-preimplementation-check
Spec: documentation/SPEC/OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md
Task: documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.1_task_breakdown.md
Backlog Item: N/A
Target Task: TASK-OPENROUTER-JANUS-CHAT-PROVIDER.1
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.6 Terra
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```
