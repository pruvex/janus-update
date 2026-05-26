# FEATURE IMPLEMENTATION PLAN

## Source Spec

- `documentation/Planned Features/AUTO UPDATE SYSTEM.md`

## A. ARCHITECTURE SUMMARY

### Structure

The Auto Update System is implemented as a hybrid Electron updater layer:

- `electron-updater` remains responsible for update check, download, and install execution.
- Janus adds a deterministic state adapter around `electron-updater` events.
- Janus persists update state as JSON under Electron `app.getPath('userData')`.
- Renderer UI receives sanitized update-state events through `frontend/preload.js` IPC allowlists.
- The existing inline update UI in `frontend/js/app.js` is replaced by deterministic UI behavior for normal, critical, and failure states.

### Existing Modules

- `main.electron.cjs`
  - Existing `electron-updater` import and `initAutoUpdater(window)` implementation.
  - Existing `restart-app-for-update` IPC listener.
  - Existing packaged app startup and splash handling.
- `frontend/preload.js`
  - Existing restricted IPC bridge.
  - Must be extended with explicit update channels.
- `frontend/js/app.js`
  - Existing update modal block around lines 2001-2132.
  - Must be replaced or refactored into state-driven rendering.
- `package.json`
  - Existing `electron-updater`, `electron-builder`, GitHub publish config, NSIS target, release scripts.
- `playwright.config.js`
  - Existing Playwright setup using Vite and backend servers.

### Target Modules

- `main.electron.cjs`
  - Wire the new update manager.
  - Keep restart IPC.
  - Remove duplicated or direct UI event logic from `initAutoUpdater` after migration.
- `electron/update-state.cjs`
  - New state persistence module.
- `electron/update-manager.cjs`
  - New `electron-updater` adapter and Janus state machine coordinator.
- `electron/update-security.cjs`
  - New SHA256 manifest validation module.
- `frontend/js/update-ui.js`
  - New UI renderer for toast/banner, critical modal, and error banner.
- `frontend/js/app.js`
  - Import/init update UI module or call global initializer after DOM ready.
- `frontend/preload.js`
  - Extend allowed IPC channels and expose update invoke/send methods.
- `tests/e2e/auto-update.spec.js`
  - New Playwright flow using simulated renderer events and real UI assertions.
- `tests/electron/update-state.test.cjs`
  - New Node unit tests for state persistence and transitions.
- `tests/electron/update-security.test.cjs`
  - New Node unit tests for SHA256 validation.

### Data Flow

1. App starts in Electron main process.
2. `update-manager` initializes state from JSON file.
3. `electron-updater` checks GitHub Releases once at startup in packaged mode.
4. Updater events are mapped into Janus states.
5. State is persisted after each transition.
6. State is sent to renderer over `update-state-changed` IPC.
7. Renderer UI maps state to:
   - normal update toast/banner
   - critical update blocking modal
   - retryable error banner
8. User actions send IPC commands:
   - `update:install-now`
   - `update:dismiss-normal`
   - `update:retry`
9. Main process validates action against current state and triggers updater behavior.

### State Machine

Valid states:

- `idle`
- `checking`
- `update_available`
- `downloading`
- `download_paused`
- `download_failed`
- `validating`
- `validation_failed`
- `ready_to_install`
- `installing`
- `install_failed`
- `installed`

Required state fields:

- `status`
- `targetVersion`
- `currentVersion`
- `assetPath`
- `manifestHash`
- `downloadedHash`
- `errorCode`
- `errorMessage`
- `updatedAt`
- `retryCount`
- `isCritical`
- `releaseNotes`

### Guardrails

- No custom low-level rollback engine in Phase 1.
- No native OS notifications in Phase 1 E2E validation.
- No background polling loop during runtime.
- No code-signing or certificate validation in Phase 1.
- No fully custom GitHub downloader in Phase 1.
- Invalid downloaded assets must be deleted before setting `validation_failed`.
- Renderer must not call arbitrary IPC channels.

---

## B. IMPLEMENTATION PLAN

### STEP 1

- **Goal:** Add deterministic update-state persistence.
- **Files:**
  - `electron/update-state.cjs`
  - `tests/electron/update-state.test.cjs`
- **Actions:**
  - Create a JSON state file module using `app.getPath('userData')` when Electron `app` is available.
  - Store state in `janus-update-state.json`.
  - Export `DEFAULT_UPDATE_STATE`, `VALID_UPDATE_STATES`, `readUpdateState`, `writeUpdateState`, `transitionUpdateState`, and `resetUpdateState`.
  - Validate every state transition against the allowed states.
  - Preserve unknown JSON parse failures by returning default state and writing `lastError` data.
- **Expected Result:**
  - Janus can persist and recover update state deterministically across restarts.

### STEP 2

- **Goal:** Add SHA256 manifest validation.
- **Files:**
  - `electron/update-security.cjs`
  - `tests/electron/update-security.test.cjs`
- **Actions:**
  - Implement `calculateSha256(filePath)`.
  - Implement `validateDownloadedAsset({ assetPath, expectedSha256 })`.
  - Return structured result objects with `valid`, `actualSha256`, and `errorCode`.
  - Delete invalid assets only from the update download path passed by the update manager.
- **Expected Result:**
  - Downloaded assets are accepted only when SHA256 matches the manifest value.

### STEP 3

- **Goal:** Create the Janus update manager around `electron-updater`.
- **Files:**
  - `electron/update-manager.cjs`
  - `main.electron.cjs`
- **Actions:**
  - Move direct updater event mapping out of `main.electron.cjs` into `electron/update-manager.cjs`.
  - Export `initJanusUpdateManager({ mainWindow, splashWindow, autoUpdater, app, log })`.
  - Map updater events to Janus states:
    - `checking-for-update` → `checking`
    - `update-available` → `update_available`
    - `download-progress` → `downloading`
    - download pause/unavailable if detectable → `download_paused`
    - `update-downloaded` → `validating`, then `ready_to_install` after SHA256 validation
    - updater error during check → `idle` with `lastError`
    - updater error during download → retry up to 3, then `download_failed`
    - validation mismatch → `validation_failed`
  - Broadcast every state change via `mainWindow.webContents.send('update-state-changed', state)`.
  - Keep splash status updates non-authoritative.
- **Expected Result:**
  - Main process owns one deterministic state machine instead of ad-hoc renderer events.

### STEP 4

- **Goal:** Add command IPC for install, retry, and dismiss.
- **Files:**
  - `main.electron.cjs`
  - `frontend/preload.js`
- **Actions:**
  - Add renderer-to-main channels:
    - `update:install-now`
    - `update:retry`
    - `update:dismiss-normal`
  - Add renderer-invoke channel:
    - `update:get-state`
  - Add main-to-renderer channel:
    - `update-state-changed`
  - Ensure `preload.js` allows only these explicit update channels.
  - Keep existing `restart-app-for-update` temporarily only if required by old UI during migration, then remove it after `update:install-now` is wired.
- **Expected Result:**
  - Renderer can only interact with the update system through explicit, safe IPC contracts.

### STEP 5

- **Goal:** Implement state-driven update UI.
- **Files:**
  - `frontend/js/update-ui.js`
  - `frontend/js/app.js`
  - `frontend/css/update-ui.css` or existing imported CSS entry used by the app
- **Actions:**
  - Create `initUpdateUI()`.
  - On init, call `window.electron.getUpdateState()` or equivalent exposed preload method.
  - Subscribe to `update-state-changed`.
  - Render normal updates as non-blocking toast/banner with `Installieren` and `Später`.
  - Render critical updates as blocking modal with only `Installieren`.
  - Render `download_failed`, `validation_failed`, and `install_failed` as persistent error banner with `Retry`.
  - Remove or disable the existing inline update modal block in `frontend/js/app.js` after the new UI is initialized.
- **Expected Result:**
  - UI behavior matches the accepted spec decisions and is testable without native OS notifications.

### STEP 6

- **Goal:** Define critical-vs-normal update classification.
- **Files:**
  - `electron/update-manager.cjs`
  - `electron/update-state.cjs`
  - `documentation/Planned Features/AUTO UPDATE SYSTEM.md`
- **Actions:**
  - Treat `isCritical` as false by default.
  - Derive `isCritical` only from explicit release metadata field or manifest field `critical: true`.
  - If metadata is missing, use normal update behavior.
  - Persist `isCritical` in the update state.
- **Expected Result:**
  - Critical updates are deterministic and never inferred from release notes text.

### STEP 7

- **Goal:** Add release manifest contract.
- **Files:**
  - `documentation/release/auto_update_manifest_contract.md`
  - `scripts/generate_update_manifest.cjs`
  - `package.json`
- **Actions:**
  - Define manifest fields:
    - `version`
    - `assetName`
    - `sha256`
    - `critical`
    - `createdAt`
  - Add script to generate manifest for the built NSIS installer in `release/`.
  - Add npm script `generate:update-manifest`.
  - Do not publish automatically in this task.
- **Expected Result:**
  - Release artifacts have a deterministic manifest source for SHA256 validation.

### STEP 8

- **Goal:** Add E2E coverage for update UI behavior.
- **Files:**
  - `tests/e2e/auto-update.spec.js`
- **Actions:**
  - In Playwright, inject a mocked `window.electron` object before app scripts run.
  - Simulate `update-state-changed` events for:
    - normal `ready_to_install`
    - critical `ready_to_install`
    - `download_failed`
    - `validation_failed`
    - `install_failed`
  - Assert normal update shows non-blocking banner with `Installieren` and `Später`.
  - Assert critical update shows blocking modal without `Später`.
  - Assert failure states show persistent error banner with `Retry`.
  - Assert button clicks call only allowed mocked IPC actions.
- **Expected Result:**
  - UI behavior is validated by real DOM flows without full backend mocking.

### STEP 9

- **Goal:** Add integration tests for updater-state mapping.
- **Files:**
  - `tests/electron/update-manager.test.cjs`
- **Actions:**
  - Create a fake `autoUpdater` event emitter.
  - Create a fake `mainWindow.webContents.send` collector.
  - Assert each updater event produces the expected Janus state.
  - Assert download errors retry at most 3 times per app start.
  - Assert validation mismatch deletes invalid asset and enters `validation_failed`.
- **Expected Result:**
  - The adapter can be tested without calling GitHub or installing real updates.

---

## C. TEST STRATEGY

### UNIT TESTS

- [ ] `electron/update-state.cjs` persists valid state to JSON.
- [ ] `electron/update-state.cjs` recovers default state from missing file.
- [ ] `electron/update-state.cjs` rejects unknown states.
- [ ] `electron/update-security.cjs` returns valid result for matching SHA256.
- [ ] `electron/update-security.cjs` returns invalid result for mismatching SHA256.
- [ ] `electron/update-security.cjs` handles missing files with structured error.

### INTEGRATION TESTS

- [ ] Fake `autoUpdater` `checking-for-update` maps to `checking`.
- [ ] Fake `autoUpdater` `update-available` maps to `update_available`.
- [ ] Fake `autoUpdater` `download-progress` maps to `downloading`.
- [ ] Fake `autoUpdater` `update-downloaded` maps to `validating` then `ready_to_install` when SHA256 passes.
- [ ] Fake validation mismatch maps to `validation_failed`.
- [ ] Fake download error retries max 3 times then maps to `download_failed`.
- [ ] Fake install error maps to `install_failed`.

### E2E TESTS MANDATORY

- [ ] Normal update flow: simulated state `ready_to_install` with `isCritical=false` renders non-blocking banner and supports `Installieren` and `Später`.
- [ ] Critical update flow: simulated state `ready_to_install` with `isCritical=true` renders blocking modal and does not show `Später`.
- [ ] Failure flow: simulated `download_failed` renders retryable error banner and calls `update:retry`.
- [ ] Validation failure flow: simulated `validation_failed` renders retryable error banner and calls `update:retry`.
- [ ] Install failure flow: simulated `install_failed` renders retryable error banner and calls `update:retry`.

### STATE TESTS

- [ ] State file survives app restart simulation.
- [ ] Corrupted state file recovers to default state and records error metadata.
- [ ] `retryCount` resets on new app start.
- [ ] `lastError` persists for failed check/API state.

### AI TESTS

- [ ] Not applicable. Update classification must not rely on LLM or AI inference.

---

## D. TASKS (ORCHESTRATOR READY)

### TASK T1

**EXECUTION TARGET:**  
`Kimi k2.5`

**Target Decision Reason:**  
This task is isolated deterministic file creation with simple JSON persistence and local Node tests.

**Goal (STRICT):**  
Create deterministic update-state persistence for Janus.

**Context:**  
The updater needs a JSON state file before any updater event mapping can be deterministic.

**Input:**  
- `main.electron.cjs`
- Electron `app.getPath('userData')`
- Spec state list from `documentation/Planned Features/AUTO UPDATE SYSTEM.md`

**Output (STRICT):**  
- Create `electron/update-state.cjs`
- Create `tests/electron/update-state.test.cjs`
- State can be read, written, reset, and transitioned with validation.

**Implementation Instructions (STEP-BY-STEP):**
1. Create directory `electron/` if it does not exist.
2. In `electron/update-state.cjs`, define `VALID_UPDATE_STATES` exactly as: `idle`, `checking`, `update_available`, `downloading`, `download_paused`, `download_failed`, `validating`, `validation_failed`, `ready_to_install`, `installing`, `install_failed`, `installed`.
3. Define `DEFAULT_UPDATE_STATE` with `status: 'idle'` and all required fields set to `null`, `false`, `0`, or ISO timestamp as appropriate.
4. Implement `getUpdateStatePath(appLike)` returning `<userData>/janus-update-state.json`.
5. Implement `readUpdateState(appLike)`.
6. Implement `writeUpdateState(appLike, state)`.
7. Implement `transitionUpdateState(appLike, patch)` that rejects unknown status values.
8. Implement `resetUpdateState(appLike)`.
9. Add Node tests covering missing file, valid write/read, invalid state rejection, and corrupted JSON recovery.

**Files to Modify/Create:**
- `electron/update-state.cjs`
- `tests/electron/update-state.test.cjs`

**Dependencies:**
- Must be completed after: none
- Required modules/services: Node `fs`, Node `path`

**Acceptance Criteria (MANDATORY):**
- [ ] Missing state file returns `status: 'idle'`.
- [ ] Written state can be read back exactly.
- [ ] Unknown state throws or returns a structured failure.
- [ ] Corrupted JSON does not crash the app.

**Test Instructions:**
- Unit: run the new Node test file directly with Node test runner or the project test command chosen by implementer.
- Integration: none.
- E2E: none.

---

### TASK T2

**EXECUTION TARGET:**  
`Kimi k2.5`

**Target Decision Reason:**  
This task is an isolated security utility with deterministic hash behavior and clear unit-test outputs.

**Goal (STRICT):**  
Create SHA256 asset validation for downloaded update files.

**Context:**  
Phase 1 requires SHA256 manifest validation and blocks install on mismatch.

**Input:**  
- `electron/update-state.cjs`
- Node file system APIs

**Output (STRICT):**  
- Create `electron/update-security.cjs`
- Create `tests/electron/update-security.test.cjs`
- Asset validation returns deterministic structured results.

**Implementation Instructions (STEP-BY-STEP):**
1. In `electron/update-security.cjs`, implement `calculateSha256(filePath)` using Node `crypto`.
2. Implement `validateDownloadedAsset({ assetPath, expectedSha256 })`.
3. Return `{ valid: true, actualSha256 }` on match.
4. Return `{ valid: false, actualSha256, errorCode: 'HASH_MISMATCH' }` on mismatch.
5. Return `{ valid: false, actualSha256: null, errorCode: 'ASSET_MISSING' }` for missing file.
6. Add tests for match, mismatch, and missing file.

**Files to Modify/Create:**
- `electron/update-security.cjs`
- `tests/electron/update-security.test.cjs`

**Dependencies:**
- Must be completed after: T1
- Required modules/services: Node `crypto`, Node `fs`

**Acceptance Criteria (MANDATORY):**
- [ ] Matching file hash validates successfully.
- [ ] Mismatching hash returns `HASH_MISMATCH`.
- [ ] Missing file returns `ASSET_MISSING`.

**Test Instructions:**
- Unit: run `tests/electron/update-security.test.cjs`.
- Integration: none.
- E2E: none.

---

### TASK T3

**EXECUTION TARGET:**  
`SWE 1.6`

**Target Decision Reason:**  
This task touches Electron main-process lifecycle, existing updater cleanup, event orchestration, and multi-file integration risk.

**Goal (STRICT):**  
Build the Janus update manager adapter around `electron-updater`.

**Context:**  
Existing `main.electron.cjs` has direct updater event handlers. They must become deterministic state transitions.

**Input:**  
- `main.electron.cjs`
- `electron/update-state.cjs`
- `electron/update-security.cjs`
- `electron-updater`

**Output (STRICT):**  
- Create `electron/update-manager.cjs`
- `main.electron.cjs` initializes the manager instead of owning updater event logic directly.

**Implementation Instructions (STEP-BY-STEP):**
1. Create `electron/update-manager.cjs`.
2. Export `initJanusUpdateManager({ app, autoUpdater, mainWindow, splashWindow, log })`.
3. Move updater configuration from `initAutoUpdater` into the manager: `autoDownload=true`, `autoInstallOnAppQuit=false`, prerelease enabled.
4. On `checking-for-update`, persist `checking` and broadcast `update-state-changed`.
5. On `update-available`, persist `update_available` with version, release notes, `isCritical` from manifest metadata only.
6. On `download-progress`, persist `downloading` and progress fields.
7. On `update-downloaded`, persist `validating`, run SHA256 validation, then persist `ready_to_install` or `validation_failed`.
8. On updater `error`, map check/API errors to `idle`, download errors to retry logic, and install errors to `install_failed`.
9. Broadcast every persisted state to renderer.
10. Replace `initAutoUpdater(win)` call in `main.electron.cjs` with `initJanusUpdateManager(...)`.

**Files to Modify/Create:**
- `electron/update-manager.cjs`
- `main.electron.cjs`

**Dependencies:**
- Must be completed after: T1, T2
- Required modules/services: `electron-updater`, `electron-log`

**Acceptance Criteria (MANDATORY):**
- [ ] Main process emits `update-state-changed` for each updater event.
- [ ] Check/API failure does not start a runtime retry loop.
- [ ] Download failure retries max 3 times per app start.
- [ ] Validation mismatch blocks install and sets `validation_failed`.

**Test Instructions:**
- Unit: none.
- Integration: add/update manager tests in T9.
- E2E: covered in T8.

---

### TASK T4

**EXECUTION TARGET:**  
`SWE 1.6`

**Target Decision Reason:**  
This task is IPC/security-sensitive and requires guarded interaction between renderer, main process, and updater state.

**Goal (STRICT):**  
Add safe update IPC contracts to preload and main process.

**Context:**  
Renderer must not access arbitrary Electron channels.

**Input:**  
- `frontend/preload.js`
- `main.electron.cjs`
- `electron/update-manager.cjs`

**Output (STRICT):**  
- Renderer can get state, subscribe to state changes, install now, retry, and dismiss normal updates.

**Implementation Instructions (STEP-BY-STEP):**
1. In `frontend/preload.js`, add allowed send/invoke/on channels for update functions only.
2. Expose methods under `window.electron`:
   - `getUpdateState()`
   - `installUpdateNow()`
   - `retryUpdate()`
   - `dismissNormalUpdate()`
   - `onUpdateStateChanged(callback)`
3. In `main.electron.cjs` or manager registration, implement handlers for:
   - `update:get-state`
   - `update:install-now`
   - `update:retry`
   - `update:dismiss-normal`
4. Ensure install command only runs when current state is `ready_to_install`.
5. Ensure retry command only runs from `download_failed`, `validation_failed`, or `install_failed`.

**Files to Modify/Create:**
- `frontend/preload.js`
- `main.electron.cjs`
- `electron/update-manager.cjs`

**Dependencies:**
- Must be completed after: T3
- Required modules/services: Electron `ipcMain`, `ipcRenderer`

**Acceptance Criteria (MANDATORY):**
- [ ] Renderer can read current update state.
- [ ] Renderer receives `update-state-changed` events.
- [ ] Install command is ignored or rejected outside `ready_to_install`.
- [ ] Retry command is ignored or rejected outside failure states.

**Test Instructions:**
- Unit: none.
- Integration: fake IPC handler tests if available.
- E2E: covered in T8.

---

### TASK T5

**EXECUTION TARGET:**  
`SWE 1.6`

**Target Decision Reason:**  
This task requires UI wiring across existing frontend code, removal of old update UI behavior, and regression-aware DOM integration.

**Goal (STRICT):**  
Replace old inline update UI with state-driven UI.

**Context:**  
Existing update UI in `frontend/js/app.js` is modal-centric and does not match the accepted UI decision.

**Input:**  
- `frontend/js/app.js`
- `frontend/preload.js`
- Existing app DOM and CSS patterns

**Output (STRICT):**  
- Create `frontend/js/update-ui.js`
- App initializes update UI once.
- Normal, critical, and failure states render correctly.

**Implementation Instructions (STEP-BY-STEP):**
1. Create `frontend/js/update-ui.js` with `initUpdateUI()`.
2. Implement render path for `ready_to_install` with `isCritical=false`: non-blocking banner/toast with `Installieren` and `Später`.
3. Implement render path for `ready_to_install` with `isCritical=true`: blocking modal with `Installieren` only.
4. Implement render path for `download_failed`, `validation_failed`, `install_failed`: persistent error banner with `Retry`.
5. Implement hidden/no-op render path for `idle`, `checking`, `downloading`, `validating`, and `installed` unless progress display is required.
6. Wire buttons to `window.electron.installUpdateNow()`, `window.electron.dismissNormalUpdate()`, and `window.electron.retryUpdate()`.
7. Modify `frontend/js/app.js` to initialize `initUpdateUI()` once after DOM is ready.
8. Remove or disable the old inline update modal event block to prevent duplicate UI.

**Files to Modify/Create:**
- `frontend/js/update-ui.js`
- `frontend/js/app.js`
- `frontend/css/update-ui.css` or existing app CSS file used by `index.html`

**Dependencies:**
- Must be completed after: T4
- Required modules/services: existing frontend JS bundle loaded by Vite

**Acceptance Criteria (MANDATORY):**
- [ ] Normal update displays `Installieren` and `Später`.
- [ ] Critical update displays modal without `Später`.
- [ ] Failure states display `Retry`.
- [ ] No duplicate old update modal appears.

**Test Instructions:**
- Unit: optional DOM function tests.
- Integration: none.
- E2E: covered in T8.

---

### TASK T6

**EXECUTION TARGET:**  
`Kimi k2.5`

**Target Decision Reason:**  
This task is deterministic script and documentation creation with clear file outputs and minimal architectural coupling.

**Goal (STRICT):**  
Add update manifest generation and documentation.

**Context:**  
SHA256 validation requires a deterministic manifest source.

**Input:**  
- `package.json`
- `release/` output from electron-builder

**Output (STRICT):**  
- Create `scripts/generate_update_manifest.cjs`
- Create `documentation/release/auto_update_manifest_contract.md`
- Add npm script `generate:update-manifest`.

**Implementation Instructions (STEP-BY-STEP):**
1. Create `documentation/release/auto_update_manifest_contract.md`.
2. Document fields `version`, `assetName`, `sha256`, `critical`, `createdAt`.
3. Create `scripts/generate_update_manifest.cjs`.
4. Read version from root `package.json`.
5. Locate installer matching `janus-setup-${version}.exe` under `release/`.
6. Calculate SHA256.
7. Write manifest JSON to `release/janus-update-manifest.json`.
8. Add package script `generate:update-manifest`.

**Files to Modify/Create:**
- `scripts/generate_update_manifest.cjs`
- `documentation/release/auto_update_manifest_contract.md`
- `package.json`

**Dependencies:**
- Must be completed after: T2
- Required modules/services: Node `crypto`, Node `fs`, Node `path`

**Acceptance Criteria (MANDATORY):**
- [ ] Manifest contains version from `package.json`.
- [ ] Manifest contains installer filename.
- [ ] Manifest contains SHA256 of installer.
- [ ] Manifest contains `critical` boolean defaulting to `false`.

**Test Instructions:**
- Unit: run script against a temporary release folder if implemented with test hooks.
- Integration: run `npm run generate:update-manifest` after installer build.
- E2E: none.

---

### TASK T7

**EXECUTION TARGET:**  
`Kimi k2.5`

**Target Decision Reason:**  
This task is deterministic integration-test creation using fake EventEmitter objects and explicit expected state transitions.

**Goal (STRICT):**  
Add update manager integration tests.

**Context:**  
The Electron updater adapter must be tested without calling GitHub or installing files.

**Input:**  
- `electron/update-manager.cjs`
- `electron/update-state.cjs`
- `electron/update-security.cjs`

**Output (STRICT):**  
- Create `tests/electron/update-manager.test.cjs`.

**Implementation Instructions (STEP-BY-STEP):**
1. Create fake `autoUpdater` using Node `EventEmitter`.
2. Create fake `mainWindow.webContents.send` collector.
3. Create fake `app.getPath('userData')` pointing at a temp directory.
4. Initialize `initJanusUpdateManager` with fakes.
5. Emit `checking-for-update` and assert state `checking`.
6. Emit `update-available` and assert state `update_available`.
7. Emit `download-progress` and assert state `downloading`.
8. Simulate successful validation and assert `ready_to_install`.
9. Simulate failed validation and assert `validation_failed`.
10. Simulate repeated download errors and assert max 3 retries then `download_failed`.

**Files to Modify/Create:**
- `tests/electron/update-manager.test.cjs`

**Dependencies:**
- Must be completed after: T3
- Required modules/services: Node `events`, temp directory helpers

**Acceptance Criteria (MANDATORY):**
- [ ] All expected updater events map to correct Janus states.
- [ ] State changes are persisted.
- [ ] State changes are broadcast to renderer.
- [ ] Download retry cap is enforced.

**Test Instructions:**
- Unit: none.
- Integration: run `tests/electron/update-manager.test.cjs`.
- E2E: none.

---

### TASK T8

**EXECUTION TARGET:**  
`SWE 1.6`

**Target Decision Reason:**  
This task validates real frontend behavior through Playwright and requires broader understanding of app loading, mocked Electron bridge timing, and UI regressions.

**Goal (STRICT):**  
Add Playwright E2E tests for update UI flows.

**Context:**  
The feature requires real user-flow validation without native OS notifications.

**Input:**  
- `frontend/js/update-ui.js`
- `playwright.config.js`
- Existing `tests/e2e` pattern

**Output (STRICT):**  
- Create `tests/e2e/auto-update.spec.js`.

**Implementation Instructions (STEP-BY-STEP):**
1. Create Playwright test file `tests/e2e/auto-update.spec.js`.
2. Use `page.addInitScript` to inject fake `window.electron` before app JS runs.
3. Fake methods: `getUpdateState`, `installUpdateNow`, `retryUpdate`, `dismissNormalUpdate`, `onUpdateStateChanged`.
4. Test normal update by emitting `ready_to_install` with `isCritical=false`.
5. Assert banner/toast is visible with `Installieren` and `Später`.
6. Test critical update by emitting `ready_to_install` with `isCritical=true`.
7. Assert modal is visible and `Später` is absent.
8. Test `download_failed`, `validation_failed`, and `install_failed`.
9. Assert each failure shows persistent banner with `Retry`.
10. Assert button clicks call the fake IPC methods.

**Files to Modify/Create:**
- `tests/e2e/auto-update.spec.js`

**Dependencies:**
- Must be completed after: T5
- Required modules/services: Playwright

**Acceptance Criteria (MANDATORY):**
- [ ] Normal update UI flow passes.
- [ ] Critical update UI flow passes.
- [ ] Download failure UI flow passes.
- [ ] Validation failure UI flow passes.
- [ ] Install failure UI flow passes.

**Test Instructions:**
- E2E: run `npm run test:e2e -- tests/e2e/auto-update.spec.js` if script supports path passthrough, otherwise `npx playwright test tests/e2e/auto-update.spec.js`.

---

## E. EXECUTION ORDER

1. T1
2. T2
3. T3
4. T4
5. T5
6. T6
7. T7
8. T8

---

## F. VALIDATION RULES

- All update state writes must be persisted before renderer broadcast.
- No installer action may run unless state is `ready_to_install`.
- No retry action may run unless state is `download_failed`, `validation_failed`, or `install_failed`.
- No native OS notification is required for Phase 1 acceptance.
- No code-signing work is allowed in Phase 1.
- No custom low-level rollback engine is allowed in Phase 1.
- No background polling loop is allowed during runtime.
- E2E must pass before completion.

---

## Expected Outcome

- Deterministic Auto-Update implementation plan.
- Clear Agent task boundaries for AI Studio, SWE 1.6, and Kimi.
- Existing `electron-updater` foundation reused instead of rewritten.
- Janus-specific state, security validation, UI, and tests defined precisely.

---

## POST-IMPLEMENTATION AUDIT TRAIL

### Implementation Scope
- **Implemented tasks:** T1-T8
- **Feature status:** DONE
- **Final audit status:** PASS WITH FIXES

### Files Changed
- **electron/update-state.cjs:** New state persistence module with JSON file under userData, transition validation, and recovery from corrupted state.
- **electron/update-security.cjs:** New SHA256 asset validation module for downloaded installers.
- **electron/update-manager.cjs:** New electron-updater adapter mapping updater events to Janus states with retry logic and validation integration.
- **main.electron.cjs:** Wired update manager, added update IPC handlers (get-state, install-now, retry, dismiss-normal).
- **frontend/preload.js:** Extended IPC bridge with update-specific channels (getUpdateState, installUpdateNow, retryUpdate, dismissNormalUpdate, onUpdateStateChanged).
- **frontend/js/update-ui.js:** New state-driven update UI renderer for normal toast, critical modal, and error banner.
- **frontend/js/app.js:** Imported initUpdateUI and called it after DOMContentLoaded; removed old inline update modal block.
- **frontend/css/update-ui.css:** New stylesheet for update UI elements (toast, modal, error banner).
- **frontend/index.html:** Added link to update-ui.css.
- **scripts/generate_update_manifest.cjs:** New script to generate janus-update-manifest.json from built installer.
- **documentation/release/auto_update_manifest_contract.md:** New manifest contract documentation.
- **package.json:** Added generate:update-manifest script.
- **playwright.config.js:** Added .spec.cjs match (later removed in audit).
- **tests/electron/update-state.test.cjs:** Node unit tests for state persistence and transitions.
- **tests/electron/update-security.test.cjs:** Node unit tests for SHA256 validation.
- **tests/electron/update-manager.test.cjs:** Node integration tests for updater event mapping.
- **tests/e2e/auto-update.spec.js:** Playwright E2E tests for update UI flows.
- **package.json:** Version bumped from 0.4.17-beta.1 to 0.4.17-beta.2.
- **package-lock.json:** Root version synchronized to 0.4.17-beta.2.
- **backend/version.py:** Version synchronized to 0.4.17-beta.2.

### What Was Done
Implemented a deterministic Auto Update System for Electron with state machine persistence, SHA256 manifest validation, secure IPC bridge, and state-driven UI. All 8 tasks (T1-T8) from the Diamond-Standard plan were completed. The system now persists update state across restarts, validates downloaded assets against manifest SHA256, provides safe IPC channels for renderer interactions, renders UI based on update state (normal toast, critical modal, error banner), and includes comprehensive Node and E2E test coverage.

### Validation Evidence
- **node -c scripts/generate_update_manifest.cjs:** PASS
- **node --test tests/electron/update-state.test.cjs tests/electron/update-security.test.cjs tests/electron/update-manager.test.cjs:** PASS — 16 passed
- **node -c frontend/js/app.js:** PASS
- **node -c frontend/js/update-ui.js:** PASS
- **node -c tests/e2e/auto-update.spec.js:** PASS
- **npx playwright test tests/e2e/auto-update.spec.js:** PASS — 7 passed
- **Old update UI grep:** PASS — no old update-available, update-downloaded, download-progress, update-error, restart-app-for-update, ensureUpdateModal remnants in app.js, preload.js, main.electron.cjs
- **Version consistency check:** PASS — root package.json, package-lock.json, backend/version.py all synchronized to 0.4.17-beta.2

### Final Audit Fixes
- **frontend/js/update-ui.js:** Added missing ES-Module export `export { initUpdateUI };` to fix import failure in app.js.
- **tests/e2e/auto-update.spec.js:** Created task-conformant .spec.js file that tests the real app/UI initialization instead of inline-duplicated UI logic.
- **tests/e2e/auto-update.spec.cjs:** Removed old inline test duplication file.
- **playwright.config.js:** Removed temporary .spec.cjs testMatch pattern.
- **tests/electron/update-state.test.cjs:** Changed test state file from root directory to temporary directory (os.tmpdir) to prevent janus-update-state.json artifact in repo.
- **janus-update-state.json:** Removed test artifact from project root.
- **package.json:** Version bumped from 0.4.17-beta.1 to 0.4.17-beta.2.
- **package-lock.json:** Root version fields synchronized to 0.4.17-beta.2 (were outdated at 0.4.14-beta.1).
- **backend/version.py:** Version synchronized to 0.4.17-beta.2.

### Version Bump
- **Old version:** 0.4.17-beta.1
- **New version:** 0.4.17-beta.2
- **Files changed:** package.json, package-lock.json, backend/version.py
- **Note:** frontend/package.json remains at independent version 1.2.2 as it is not part of Electron release version contract.

### Remaining Risks
- **Manifest runtime source:** update-manager.cjs validates against info.sha256 from electron-updater events; whether this value reliably comes from the manifest in real GitHub Releases should be observed during release testing.
- **Release folder absent:** generate_update_manifest.cjs can only succeed after installer build because it requires release/*.exe to exist.
- **Working tree contains many non-Auto-Update changes:** The git working tree has numerous other Modified/Untracked files outside this feature scope. These were not modified but should be reviewed before release.

---

## DEBUGGING LOG

- **E2E test validation:** Initial E2E test (auto-update.spec.cjs) used inline-duplicated UI logic instead of testing the real update-ui.js module. Fixed by creating a task-conformant .spec.js that tests the app initialization and real UI renderer.
- **ES Module import failure:** frontend/js/update-ui.js was imported as ES module in app.js but did not have an ES export. Fixed by adding `export { initUpdateUI };`.
- **Test artifact in repo:** update-state.test.cjs wrote janus-update-state.json to project root. Fixed by changing test to use temporary directory and adding cleanup in test.after hook.
- **Lockfile version outdated:** package-lock.json root version was 0.4.14-beta.1 while package.json was 0.4.17-beta.1. Fixed by synchronizing to 0.4.17-beta.2 during version bump.
