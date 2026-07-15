# AUDIT_PACKAGE

Generated: 2026-07-15 16:21:17 UTC

## Goal

Independently audit BACKLOG-131: restore a single state-consistent Settings navigation path without changing ChatGPT device-code credentials, provider/model selection, chat transport, API-key behavior, or production policy.

## Scope Rules

- Audit the provided package and changed artifacts only.
- Do not rely on development chat history.
- Verify cost, caching, skill quality, safety scope, and validation evidence.
- On re-audit, review the blocker delta first before widening scope.
- If scoped paths were provided, treat them as the audit diff boundary.

## Bound Audit Inputs

- Spec: N/A WITH REASON - standalone BACKLOG-131 navigation correction; no Feature Spec source is bound for its closeout.
- Task File: documentation/tasks/backlog_BACKLOG-131_settings_handler_navigation.md
- Backlog Item: BACKLOG-131
- Pre-Implementation Check: documentation/tasks/TASK-BACKLOG-131-SETTINGS-NAVIGATION_precheck.md
- Manual Janus Evidence: PASS: Account-free Task .2 Settings observation opened Einstellungen then API Keys and displayed the Settings/API-key surface. No login, device code, account, credential, provider, or production action occurred.
- Pipeline Completion Status: BACKLOG-131 precheck PASS; navigation correction implemented; initial headed E2E reached API-key surface then blocked on distinct mock sequencing; debug classified that blocker out of scope; Task .2.2 runner-only correction PASS; full headed E2E 8/8 PASS; focused API suite 11/11 PASS; Task .2 Final Audit PASS covers shared evidence but leaves BACKLOG-131 closeout separate.

## Backlog Item

```text
### BACKLOG-131 - Verzögerter Settings-Handler überschreibt die zustandsbehaftete Navigation

- **Typ:** BUG
- **Status:** IN PROGRESS
- **Quelle:** Audit / Mocked E2E 2026-07-15
- **Erstellt:** 2026-07-15
- **Aktualisiert:** 2026-07-15
- **Kurzbeschreibung:** Ein verzögerter Legacy-Block in `frontend/js/app.js` klont `#settings-btn` nach dem Start und ersetzt dessen zustandsbehafteten Handler. Die Ersatzfunktion öffnet Settings ohne `appState.currentView` zu synchronisieren oder `show-settings` auszulösen und startet anschließend `initializeApp()` erneut.
- **Erwartetes Verhalten:** Der sichtbare Settings-Button verwendet dauerhaft einen konsistenten Navigationspfad, setzt den View-State korrekt und zeigt den vorgesehenen Settings-Abschnitt ohne unerwartete Reinitialisierung an.
- **Tatsaechliches Verhalten:** Nach der verzögerten Handler-Ersetzung kann der reale Settings-Button zur Chat-Ansicht zurückführen; der erwartete API-Key-Abschnitt fehlt im headed E2E. Das blockiert die vollständige Task-`.2`-Validierung.
- **Reproduktion / Kontext:** Janus starten, mindestens 500 ms warten, den Sidebar-Button `Einstellungen` betätigen. Im aktuellen mocked headed Lauf `tests/e2e/codex-connection-settings.spec.js` ist `#api-key-section` anschließend nicht auffindbar. Die ursprüngliche und die verzögerte Handler-Definition stehen beide in `frontend/js/app.js`.
- **Betroffener Bereich:** Frontend / Settings-Navigation / E2E
- **Nachweise:** `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.2_debug_result.md`; `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.2_execution_result.md`; `test-results/tests-e2e-codex-connection-aed8d-thout-mutating-API-key-form-janus-chromium/error-context.md`; `frontend/js/app.js`
- **Akzeptanzkriterien:**
  - [ ] Der reale Settings-Button behält genau einen zustandskonsistenten Navigationspfad.
  - [ ] Öffnen der Settings synchronisiert View-State und Zielabschnitt ohne Reinitialisierungs-Race.
  - [ ] Der vollständige headed Task-`.2`-E2E-Lauf erreicht den API-Key-Abschnitt und besteht ohne DOM-/Timing-Workaround.
  - [ ] Die Korrektur verändert weder die Task-`.1`-Credential-Isolation noch Device-Code-, Provider-, Modell-, Chat- oder Produktionsverhalten.
- **Fehlende Informationen:** Keine
- **Notizen:** Separater Produktfehler außerhalb der gebundenen Task-`.2`-Dateiliste. Task `.2` bleibt bis zur validierten Korrektur blockiert; kein Live-Konto-Test ist für diesen Defekt erforderlich.
- **Wichtigkeit:** HIGH
- **Umsetzungsrisiko:** MEDIUM
- **Aufwand:** S
- **Umsetzungsreife:** READY
- **Empfehlung:** DO NOW
- **Entry Point:** PRE_IMPLEMENTATION_VERIFICATION
- **Routing reason:** Ein klarer, einzelner Frontend-Navigationsfehler mit mittelbarem Einfluss auf die allgemeine Settings-Ansicht; die genaue kleinste Korrektur und Testoberfläche müssen vor Implementierung separat geprüft werden.
- **Routing confidence:** HIGH
- **Routing decided by:** BACKLOG SKILL 3
- **Routing decided at:** 2026-07-15
- **Handoff:** documentation/tasks/backlog_BACKLOG-131_settings_handler_navigation.md
- **Recommended next skill:** SKILL 3
- **Handoff created:** 2026-07-15
```

## Task Acceptance Scope

```text
# BACKLOG HANDOFF - BACKLOG-131

## HANDOFF_SCOPE

- Backlog Item: `BACKLOG-131`
- Target Task: `TASK-BACKLOG-131-SETTINGS-NAVIGATION`
- Entry Point: `PRE_IMPLEMENTATION_VERIFICATION`
- Required Next Skill: `janus-preimplementation-check`
- Required Artifact: this handoff
- Evidence Paths:
  - `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.2_debug_result.md`
  - `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.2_execution_result.md`
  - `test-results/tests-e2e-codex-connection-aed8d-thout-mutating-API-key-form-janus-chromium/error-context.md`
  - `frontend/js/app.js`
- Dropped Context: unrelated backlog items, old DONE history, Task `.1` implementation history, device-code account actions, provider/model selection, API-key management, transport, and release work.

## Bound Problem

`frontend/js/app.js` first binds `#settings-btn` to the stateful Settings transition, then a delayed legacy block clones the same button and replaces that listener with `forceOpenSettings()`. The replacement does not synchronize `appState.currentView` or dispatch `show-settings`, and it invokes `initializeApp()` again. After the delay, the visible Settings button can therefore leave the application in the Chat surface and the API-key section is unavailable to the bound headed E2E suite.

## Goal

Restore one durable, state-consistent Settings navigation path for the visible sidebar button without changing the Task `.1` credential boundary or the Task `.2` Device-Code lifecycle contract.

## Bound Scope For Precheck

- Inspect `frontend/js/app.js` navigation initialization and determine the narrowest safe removal, consolidation, or synchronization of the duplicate Settings-button binding.
- Candidate product file: `frontend/js/app.js`.
- Candidate validation file: `tests/e2e/codex-connection-settings.spec.js`; precheck may name one additional focused navigation test only if required to prove the general button behavior.
- Re-run the full bound Task `.2` mocked headed E2E suite after the navigation correction, plus the focused Settings/API contract checks already bound to Task `.2`.

## Explicitly Out Of Scope

- Device-Code/OAuth flows, token or credential persistence, keyring storage, public API response shapes, renderer Device-Code presentation, account switching, API-key providers, provider/model selection, chat transport, privacy acknowledgement, production activation, release, and live account actions.
- Broad navigation redesign, unrelated emergency navigation helpers, or changes to the Task `.1` final-audit record.

## Acceptance Gate

- After application initialization, the visible `#settings-btn` has one state-consistent navigation path that reaches Settings and the API-key section.
- The correction does not trigger a second application initialization solely to open Settings.
- `tests/e2e/codex-connection-settings.spec.js` passes headed with its mocked lifecycle responses and no DOM/timing workaround.
- Task `.1` credential isolation, redaction, two-account non-interference evidence, API-key behavior, provider/model non-selection, and production default-deny remain unchanged.

## Next Skill Copy Prompt

```text
@[/SKILL 3 - PRE-IMPLEMENTATION VERIFICATION]
Target Task: TASK-BACKLOG-131-SETTINGS-NAVIGATION
Task: documentation/tasks/backlog_BACKLOG-131_settings_handler_navigation.md
Backlog Item: BACKLOG-131
```

Keep Context:
- `BACKLOG-131`
- this handoff
- `TASK-CHATGPT-DEVICE-CODE-PROVIDER.2_debug_result.md`

Drop Context:
- unrelated READY items
- old DONE history
- broad backlog narrative
```

## Pre-Implementation Check

```text
# PRE-IMPLEMENTATION CHECK - TASK-BACKLOG-131-SETTINGS-NAVIGATION

PRE-CHECK RESULT
PRE-CHECK PASSED

```text
legacy handoff start
NEXT: janus-executioner
Target Task: TASK-BACKLOG-131-SETTINGS-NAVIGATION
Target Subtask: N/A
Task: documentation/tasks/backlog_BACKLOG-131_settings_handler_navigation.md
Spec: N/A WITH REASON - independent bounded Backlog BUG; no Feature Spec is required for this small navigation correction.
Backlog Item: BACKLOG-131
Assigned Model: 5.6 Terra
Assigned Intelligence: high
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound failure is deterministic: a 500-ms legacy listener replacement clones `#settings-btn`, removes the stateful listener, invokes `forceOpenSettings()`, and reinitializes the app without synchronized Settings state/event handling.
- The target is a small general-Settings navigation correction, separate from the blocked Task `.2` Device-Code presentation work. Task `.2` remains blocked until this task is validated and its headed suite can run green.
- Task `.1` secure credential isolation, redaction, two-account evidence, and production default-deny are binding regressions only; no lifecycle, credential, provider, or production behavior belongs to this task.
Affected Files:
- frontend/js/app.js
- tests/e2e/codex-connection-settings.spec.js
Evidence Focus:
- Preserve one state-consistent `#settings-btn` path after application initialization.
- Preserve the intended API-key Settings entry without a redundant initialization race.
- `node --check frontend/js/app.js`
- `node --check tests/e2e/codex-connection-settings.spec.js`
- `python -m pytest backend/tests/test_codex_connection_settings_api.py -q`
- `npx playwright test tests/e2e/codex-connection-settings.spec.js --headed --workers=1 --reporter=list`
- `git diff --check -- frontend/js/app.js tests/e2e/codex-connection-settings.spec.js`
Scope-Regel:
- Implement only TASK-BACKLOG-131-SETTINGS-NAVIGATION within the two affected files. No Device-Code/OAuth, credential/keyring, API-router, API-key, provider/model, chat transport, privacy, production, release, live-account, or Git action.
- Do not reintroduce a DOM/timing workaround in the E2E helper; correct the bounded application navigation defect and prove the existing mocked suite through the real Settings control.
Automated Evidence Gate:
- node --check frontend/js/app.js
- node --check tests/e2e/codex-connection-settings.spec.js
- python -m pytest backend/tests/test_codex_connection_settings_api.py -q
- npx playwright test <runner> --headed --workers=1 --reporter=list
- npx playwright test tests/e2e/codex-connection-settings.spec.js --headed --workers=1 --reporter=list
- git diff --check -- frontend/js/app.js tests/e2e/codex-connection-settings.spec.js
Artifact Identity Check:
- PASS: Target Task, Backlog Item, IN PROGRESS Backlog handoff path, and explicit no-Spec rationale verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. No TestSpec change is in scope; retain the existing mocked E2E as the bound regression runner.
Keep Context:
- BACKLOG-131 and its selected handoff
- frontend/js/app.js duplicate Settings-handler evidence
- tests/e2e/codex-connection-settings.spec.js and its headed failure context
Drop Context:
- unrelated Backlog history
- Task `.1` implementation details and live account history
- Task `.2` product changes beyond the bound regression runner
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.
legacy handoff end
```

## NEXT STEP

Recommended Skill: janus-executioner
Recommended Model: 5.6 Terra
Recommended Intelligence: high
User Action: Reply `ok` to execute only TASK-BACKLOG-131-SETTINGS-NAVIGATION; no live account or Git action is authorized.
```

## Changed Files

```text
No uncommitted changes detected.
```

## Artifact Inventory

```text
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-BACKLOG-131-SETTINGS-NAVIGATION_execution_result.md (3727 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-BACKLOG-131-SETTINGS-NAVIGATION_debug_result.md (3816 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-BACKLOG-131-SETTINGS-NAVIGATION_precheck.md (3883 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-CHATGPT-DEVICE-CODE-PROVIDER.2.2_execution_result.md (3250 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-CHATGPT-DEVICE-CODE-PROVIDER.2_final_audit.md (5344 bytes)
FILE C:\KI\Janus-Projekt\frontend\js\app.js (88596 bytes)
FILE C:\KI\Janus-Projekt\tests\e2e\codex-connection-settings.spec.js (13180 bytes)
```

## Diff Summary

```text
No diff stat available.
```

## Validation

```text
# TASK EXECUTION RESULT - TASK-BACKLOG-131-SETTINGS-NAVIGATION

Canonical State: BLOCKED
Target Task: TASK-BACKLOG-131-SETTINGS-NAVIGATION

## Implemented Scope

- Removed the delayed legacy rebind that cloned `#settings-btn` and replaced the stateful Settings navigation with `forceOpenSettings()`.
- Bound the intended Settings transition immediately after DOM readiness and guarded it against duplicate attachment across later application initialization.
- Kept the distinct modal fallback unchanged. No Device-Code, credential, API, provider/model, chat, production, account, or Git behavior changed.

## Changed Files

- `frontend/js/app.js`
- `documentation/tasks/TASK-BACKLOG-131-SETTINGS-NAVIGATION_execution_result.md`
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/SKILL_USAGE_LOG.md`

`tests/e2e/codex-connection-settings.spec.js` remains the bound regression runner but was not changed in this execution slice.

## Executed Checks

- Precheck validator: PASS.
- `node --check frontend/js/app.js`: PASS.
- `node --check tests/e2e/codex-connection-settings.spec.js`: PASS.
- `python -m pytest backend/tests/test_codex_connection_settings_api.py -q`: PASS, `11 passed`.
- Scoped `git diff --check` for `frontend/js/app.js` and the bound E2E runner: PASS.
- `npx playwright test tests/e2e/codex-connection-settings.spec.js --headed --workers=1 --reporter=list`: BLOCKED, `4 passed`, one replacement-account scenario timed out waiting for `Abmelden`, and three later scenarios did not run.

## Blocker And Boundaries

- Failure code: `E2E_REPLACEMENT_LIFECYCLE_PENDING_STUCK`.
- The navigation correction is effective: the first four headed scenarios now pass and the failure snapshot shows the Settings/API-key surface. In the replacement scenario, the card renders `second@example.com` while still showing `Anmeldung läuft` and `Anmeldung abbrechen`; the expected `Abmelden` action never appears.
- This is a different, narrower failure from the fixed delayed Settings-button replacement. The two focused execution fixes are exhausted; no further test or product edit is safe in this execution run.
- The lifecycle remains fully mocked. No live account, Device-Code use, credential, token, provider selection, or production action occurred.

Auto-Verification:
- Status: FAIL
- Evidence: syntax, focused API regression, and scoped diff checks pass; the required full headed E2E suite does not pass.

## NEXT_STEP

Target Skill: janus-debug
Canonical State: BLOCKED
Required Artifacts: this execution result; passed BACKLOG-131 precheck; `frontend/js/app.js`; `tests/e2e/codex-connection-settings.spec.js`; current headed E2E error context and trace.
Audit Package: none - final audit is not authorized while the E2E gate is blocked.
Evidence Paths: `documentation/tasks/TASK-BACKLOG-131-SETTINGS-NAVIGATION_precheck.md`; this execution result; `test-results/tests-e2e-codex-connection-8aef9-es-it-only-after-completion-janus-chromium/error-context.md`; `test-results/tests-e2e-codex-connection-8aef9-es-it-only-after-completion-janus-chromium/trace.zip`.
Failure Code: E2E_REPLACEMENT_LIFECYCLE_PENDING_STUCK
Changed Files: see scope list above.
Decision: diagnose the mocked replacement lifecycle state transition without changing credentials, provider behavior, or production policy.
Reason: the Settings navigation defect is corrected, but the replacement-account regression remains pending instead of reaching its expected connected action state.
Recommended Model: 5.6 Terra
Recommended Intelligence: high
New Chat: no
Next User Action: approve `janus-debug` for the single mocked replacement-lifecycle failure; do not run final audit, documentation closeout, live account actions, or Git actions.
```

## Notes

No additional notes provided.

## Risks

The real Settings button must retain one state-consistent path; the correction must not alter Task .1 credential isolation, API-key providers, device-code lifecycle, provider/model availability, chat transport, or production default-deny.

## Open Issues

No known remaining navigation failure. BACKLOG-131 closeout must remain separate from Task .2 and must not imply Feature Spec completion or production readiness.

## Re-Audit Delta

Primary blocker: E2E_REPLACEMENT_LIFECYCLE_PENDING_STUCK

The initial BACKLOG-131 execution corrected the delayed Settings-handler overwrite but stopped on a distinct mocked replacement-state blocker. That blocker was diagnosed as runner sequencing, not a navigation defect; Task .2.2 staged connected replacement state after login POST. The complete headed runner now passes 8/8, including the real Settings-to-API-Keys path. Task .2 Final Audit PASS confirms the shared regression evidence but deliberately did not close BACKLOG-131.

## Final Audit Handoff

```text
NEW_CHAT_HANDOFF
NEXT: final-skill-audit
MODEL: 5.6 Sol/high if runtime-supported; otherwise 5.6 Terra/high
PASS: C:\KI\Janus-Projekt\documentation\tasks\BACKLOG-131_AUDIT_PACKAGE.md
ASK: Lade nur dieses Paket im neuen Chat und starte dann den Final Audit.
DROP: dev chat history
```

Use `5.6 Sol/high` when the current Codex run can start it; if Codex reports `gpt-5.6-sol` is unsupported for the active ChatGPT account, use `5.6 Terra/high` and record `SOL_UNAVAILABLE_FOR_CHATGPT_CODEX_ACCOUNT`.

For bounded same-thread re-audits after a local blocker fix, `5.6 Terra/high` is acceptable when the package stays compact and the risk did not escalate.
