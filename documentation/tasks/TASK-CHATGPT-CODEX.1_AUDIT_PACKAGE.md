# AUDIT_PACKAGE

Generated: 2026-07-14 15:11:44 UTC

## Goal

Final audit for the isolated official Codex App Server runtime boundary in TASK-CHATGPT-CODEX.1

## Scope Rules

- Audit the provided package and changed artifacts only.
- Do not rely on development chat history.
- Verify cost, caching, skill quality, safety scope, and validation evidence.
- On re-audit, review the blocker delta first before widening scope.
- If scoped paths were provided, treat them as the audit diff boundary.

## Bound Audit Inputs

- Spec: documentation/SPEC/CHATGPT_OAUTH_PROVIDER_FEATURE_SPEC.md (bound source Spec; only Task .1 is in audit scope)
- Task File: documentation/tasks/TASK-CHATGPT-CODEX-PROVIDER.md
- Backlog Item: N/A WITH REASON - No backlog marker provided.
- Pre-Implementation Check: documentation/tasks/TASK-CHATGPT-CODEX.1_precheck.md
- Manual Janus Evidence: PRESENT: operator manually opened Janus, created a new chat, sent 'Was kannst du?', and supplied the complete visible capability overview on 2026-07-14.
- Pipeline Completion Status: Task .1 implementation complete; automated validation PASS; manual Janus evidence PRESENT; Tasks .2-.4 intentionally parked and excluded.

## Backlog Item

```text
N/A WITH REASON - No backlog source or marker provided.
```

## Task Acceptance Scope

```text
# TASK-CHATGPT-CODEX - ChatGPT Provider ueber offiziellen Codex-Zugang

## Source Binding

- Source Spec: `documentation/SPEC/CHATGPT_OAUTH_PROVIDER_FEATURE_SPEC.md`
- Backlog Item: `N/A`
- Compilation status: `HANDOFF`
- Generated: `2026-07-14`
- Constraint: Diese Tasks ersetzen keine bestehenden API-Key-Provider und duerfen keine der historischen `TASK-CHATGPT-OAUTH*`-Artefakte ausfuehren.

## Generated Tasks

### TASK-CHATGPT-CODEX.1 - Official Codex access boundary

- Task ID: `TASK-CHATGPT-CODEX.1`
- Ziel: Den offiziellen, Janus-isolierten Codex-Kontozugang als alleinige Authentifizierungs- und Session-Grenze fuer den sichtbaren Provider `ChatGPT` bereitstellen.
- Scope: Managed Login, Konto-/Workspace-Status, erneute Anmeldung, Janus-only Logout und sichere Fehlerzustaende ueber die offizielle Codex-Zugangsflaeche. Janus speichert keine ChatGPT-Secrets und uebernimmt keinen Token-Refresh.
- Files:
  - `backend/llm_providers/` (neues offizielles Codex-Zugangsmodul; genauer Name wird im Task Breakdown gebunden)
  - `backend/llm_providers/runtime_llm.py`
  - `backend/tests/` (neue fokussierte Zugangs- und Nichtoffenlegungs-Tests)
- Steps:
  1. Einen Adapter zur offiziell unterstuetzten Codex-Kontooberflaeche mit explizitem Janus-Sitzungsbereich binden.
  2. Dessen Login-, Abbruch-, Logout-, Konto-, Workspace- und Sitzungszustand in einen geheimnisfreien Janus-Vertrag ueberfuehren.
  3. Unsichere Ablage, direkte OAuth-Implementierung, Tokenexport, Klartext-Logging und eine Auswirkung auf fremde Codex-/ChatGPT-Sitzungen ablehnen.
  4. Den bestehenden `openai-codex`-Platzhalter nur ueber die neue offizielle Grenze aufloesen; keine API-Key- oder Provider-Ausweichlogik hinzufuegen.
- Acceptance Criteria:
  - Die offizielle Codex-Grenze bleibt Eigentuemerin von Secrets und Refresh; Janus exponiert ausschliesslich nicht geheime Zustandsdaten.
  - Login-Abbruch oder Fehler veraendert keinen vorhandenen Janus-Providerzustand.
  - Logout bzw. Account-Wechsel betrifft nur die Janus-Verbindung; andere lokale Codex-/ChatGPT-Sitzungen und Janus-Chatverlaeufe bleiben unveraendert.
  - Fehlende sichere Ablage oder ungueltige Sitzung blockiert `ChatGPT` sicher und ohne Fallback.
- Tests:
  - Fokussierte Adapter-/Lifecycle-Tests fuer Erfolg, Abbruch, Fehler, ungueltige Sitzung, Re-Login, Logout und Account-Wechsel.
  - Nichtoffenlegungs-Tests fuer Status, Fehler und Logs.
- Model: `5.6 Sol`, high
- Reason: Security-, Privacy- und Account-Isolationsgrenze mit hoher Architektur- und Persistenzrelevanz.
- Slice Theme: `official_codex_access_boundary`

### TASK-CHATGPT-CODEX.2 - Connection lifecycle in settings

- Task ID: `TASK-CHATGPT-CODEX.2`
- Ziel: Im bestehenden API-Key-Bereich eine bewusst getrennte ChatGPT-Verbindung mit Login, Status, Logout, Account-Wechsel und Retry sichtbar machen.
- Scope: Einstellungs-UI und geheimnisfreie Backend-Statusschnittstelle. Der Provider wird nach Login nur verfuegbar, aber nie automatisch aktiv.
- Files:
  - `frontend/index.html`
  - `frontend/js/settings.js`
  - `backend/api/routers/system.py` oder ein im Task Breakdown klar abgegrenzter neuer Connection-Status-Router
  - `backend/tests/` (neue fokussierte API-/UI-Vertragstests)
- Steps:
  1. Den Button `Mit ChatGPT anmelden` als separate Option neben der API-Key-Verwaltung ergaenzen.
  2. Den sichtbaren Verbindungsstatus mit Konto-Kennung, Workspace und `ueber Codex` sowie Login-, Logout-, Account-Wechsel- und Retry-Aktionen anbinden.
  3. Abbruch, Fehler, voruebergehend nicht verfuegbaren lokalen Zugang und sichere-Ablage-Fehler als sichtbare, retryfaehige Zustaende abbilden.
  4. Sicherstellen, dass weder eine Anmeldung die bestehende Providerwahl aendert noch ein Fehler auf API-Key-Provider ausweicht.
- Acceptance Criteria:
  - Nach erfolgreichem Login zeigt die Einstellung Konto, Workspace und `ueber Codex`; ohne Login zeigt sie keine nutzbare ChatGPT-Verbindung.
  - Logout und Account-Wechsel entfernen nur die Janus-Verbindung und lassen Chatverlauf sowie andere Provider erhalten.
  - Voruebergehende Nichtverfuegbarkeit laesst die Verbindung sichtbar, aber deaktiviert und mit `Erneut versuchen`.
  - Die API-Key-Verwaltung bleibt funktional unveraendert und ist kein Fallback.
- Tests:
  - Fokussierte Backend-Statusvertragstests ohne Secret-Werte.
  - UI-Tests fuer Login-Start, Abbruch, Fehler, Status, Logout, Account-Wechsel und Retry.
- Model: `5.6 Terra`, high
- Reason: Bestehende Einstellungen und neuer Lifecycle-Vertrag muessen ohne Rueckwirkung auf API-Key-Provider integriert werden.
- Slice Theme: `connection_lifecycle_and_settings`

### TASK-CHATGPT-CODEX.3 - Entitled model catalog and provider transport

- Task ID: `TASK-CHATGPT-CODEX.3`
- Ziel: `ChatGPT` nur dann im bestehenden Provider-/Modell-Dropdown anbieten, wenn eine aktive Verbindung besteht, und ausschliesslich die tatsaechlich nutzbaren Codex-Modelle des Kontos verwenden.
- Scope: Dynamischer, kontoabhaengiger Modellkatalog, bewusste Providerwahl und Transportauflosung ohne allgemeine ChatGPT-Webfunktionen, Modellsubstitution oder Fallback.
- Files:
  - `backend/services/model_catalog.py`
  - `backend/llm_providers/runtime_llm.py`
  - `frontend/js/app.js`
  - `backend/tests/test_runtime_llm.py`
  - `backend/tests/` (neue fokussierte Modellkatalog-/Entitlement-Tests)
- Steps:
  1. Den picker-sichtbaren Modellkatalog des aktiven offiziellen Codex-Zugangs in den Janus-Modellkatalog uebernehmen.
  2. `ChatGPT` erst nach erfolgreicher Verbindung als auswählbaren Provider und nur mit diesen Modellen anzeigen.
  3. Den Transport so binden, dass ein entzogenes oder nicht mehr nutzbares Modell eine bewusste neue Auswahl verlangt.
  4. Nicht berechtigte Modelle, manuell erfundene Modell-IDs, automatische Modellersatzwahl und Provider-/API-Key-Fallback ablehnen.
- Acceptance Criteria:
  - Dropdown und Modellpicker zeigen nur aktive, vom Konto tatsaechlich nutzbare Codex-Modelle.
  - Login aktiviert den Provider nicht automatisch; der Nutzer waehlt `ChatGPT` bewusst.
  - Modellverlust und ungueltige Sitzung blockieren den Sendefall mit einer bewussten Handlung, nicht mit automatischer Ersetzung.
  - Der Provider erhaelt keine Datei-, Shell- oder Codeaktionsrechte ueber bestehende Janus-Providerrechte hinaus.
- Tests:
  - Deterministische Modellkatalog-/Entitlement- und Transportaufloesungstests.
  - Negativtests fuer nicht berechtigte Modelle, fehlende Sitzung und jeden automatischen Fallback.
- Model: `5.6 Terra`, high
- Reason: Providerauflosung, Modellverfuegbarkeit und Transport muessen in den bestehenden Selektionsfluss passen.
- Slice Theme: `account_entitled_model_catalog_and_transport`

### TASK-CHATGPT-CODEX.4 - Chat continuity, privacy, limits, and recovery

- Task ID: `TASK-CHATGPT-CODEX.4`
- Ziel: Anbieterwechsel im bestehenden Chat, einmaligen Datenschutzhinweis und sicher blockierende Limit-/Wiederherstellungszustaende fuer `ChatGPT` vervollstaendigen.
- Scope: Bestehende Chatoberflaeche und Sendestatus; keine neue Chat-Historie, keine automatische Providerwahl und keine Erweiterung der Codex-Berechtigungen.
- Files:
  - `frontend/js/app.js`
  - `frontend/js/chat.js`
  - `frontend/index.html`
  - `backend/api/routers/` (bestehender oder im Task Breakdown gebundener Send-/Statusanschluss)
  - `backend/tests/` und Frontend-Testoberflaeche (neue fokussierte Tests)
- Steps:
  1. Providerwechsel zu und von `ChatGPT` im bestehenden Janus-Chat erhalten und ohne Verlaufsverlust abbilden.
  2. Vor dem ersten Senden ueber ChatGPT den einmaligen Datenschutzhinweis zum aktiven ChatGPT-/Codex-Workspace einholen.
  3. Ungueltige Sitzung, nicht verfuegbaren lokalen Zugang, Modellverlust und Kontolimit klar blockierend darstellen; Resetzeit zeigen, falls die offizielle Grenze sie liefert.
  4. Nach Logout bei aktivem `ChatGPT` bewusste erneute Anmeldung oder bewusste andere Providerwahl verlangen.
- Acceptance Criteria:
  - Ein Providerwechsel mitten im Chat behaelt den Janus-Chatverlauf.
  - Der Datenschutzhinweis erscheint genau einmal vor dem ersten ChatGPT-Senden im festgelegten Verbindungsbereich.
  - Kontolimits blockieren den Sendefall; ein verfuegbarer Resetzeitpunkt ist sichtbar; es gibt keinen Fallback.
  - Logout entfernt keinen Chatverlauf und bietet keine automatische Folgeproviderwahl.
- Tests:
  - Chat- und UI-Tests fuer Verlaufserhalt, Privacy-Gate, Logout bei aktiver Auswahl, Modellverlust, invalidierte Sitzung, Retry und Limit/Resetzeit.
  - Negativtests, die automatische Provider-/Modell-/API-Key-Ausweichlogik ausschliessen.
- Model: `5.6 Terra`, high
- Reason: Nutzerfluss, Datenschutz und blockierende Fehlerzustaende beruehren die bestehende Chatkontinuitaet.
- Slice Theme: `chat_continuity_privacy_and_limit_states`

## Execution Order

1. `TASK-CHATGPT-CODEX.1`
2. `TASK-CHATGPT-CODEX.2`
3. `TASK-CHATGPT-CODEX.3`
4. `TASK-CHATGPT-CODEX.4`

Nur der jeweils durch `janus-task-breakdown` und `janus-preimplementation-check` freigegebene Task darf implementiert werden.

## NEXT SKILL HANDOFF

```text
@janus-task-breakdown
Spec: documentation/SPEC/CHATGPT_OAUTH_PROVIDER_FEATURE_SPEC.md
Task Artifact: documentation/tasks/TASK-CHATGPT-CODEX-PROVIDER.md
Backlog Item: N/A
Target Task: TASK-CHATGPT-CODEX.1
Mode: TASK_REFINEMENT
Execution Model: 5.6 Sol
Reasoning: high
Rules: Bind exact repository seams and tests only for TASK-CHATGPT-CODEX.1. Preserve the official Codex-managed secret/refresh boundary; do not use stale TASK-CHATGPT-OAUTH artifacts; do not implement.
Expected Output: One validator-clean task-breakdown artifact, a single released task, explicit dependency/rollback/test boundaries, and the next preimplementation gate.
```
```

## Pre-Implementation Check

```text
PRE-CHECK RESULT
PRE-CHECK PASSED

```text
legacy handoff start
NEXT: janus-executioner
Target Task: TASK-CHATGPT-CODEX.1
Target Subtask: N/A
Task: documentation/tasks/TASK-CHATGPT-CODEX.1_task_breakdown.md
Spec: documentation/SPEC/CHATGPT_OAUTH_PROVIDER_FEATURE_SPEC.md
Backlog Item: N/A
Assigned Model: 5.6 Terra
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- Exactly one high-risk slice is released: the Janus-owned lifecycle boundary around the official Codex App Server managed ChatGPT-account surface.
- Official App Server documentation confirms that managed `chatgpt` login owns the browser OAuth flow, credential persistence, automatic refresh, account read, login cancel, and logout; Janus must consume only this surface and never handle tokens directly.
- Official configuration documentation exposes `cli_auth_credentials_store = "keyring"`; unlike `auto`, the current official storage implementation fails when the OS keyring is unavailable and does not fall back to an auth file.
- The current official storage implementation derives the keyring account key from the canonical `CODEX_HOME`. A Janus-specific immutable home therefore creates a credential entry distinct from other Codex clients; Janus logout targets only its owned App Server process and that isolated home.
- `@openai/codex@0.144.4-win32-x64` is an official Apache-2.0 npm distribution whose dry-run manifest contains `vendor/x86_64-pc-windows-msvc/bin/codex.exe`. It may be pinned and copied as an Electron resource without using `PATH`.
- OpenRouter counter-review reported three missing-proof blockers. Codex resolved all three against current official documentation, official source, npm package metadata, and the inspected Janus lifecycle/packaging seams; delegated output remains review material only.
- No product test, live login, build, or code edit was performed during precheck.
Affected Files:
- backend/llm_providers/codex_app_server.py
- backend/main.py
- main.electron.cjs
- scripts/run-backend-dev.cjs
- package.json
- package-lock.json
- backend/utils/redaction.py
- licenses/openai-codex/LICENSE.txt
- backend/tests/test_codex_app_server.py
- tests/electron/codex-runtime-boundary.test.cjs
Evidence Focus:
- Official contracts: https://developers.openai.com/codex/app-server/ and https://developers.openai.com/codex/config-reference/
- Official source: https://github.com/openai/codex/blob/main/codex-rs/core/src/auth/storage.rs and https://github.com/openai/codex/blob/main/LICENSE
- Distribution proof: `npm view @openai/codex@0.144.4 bin optionalDependencies --json`; `npm view @openai/codex@0.144.4-win32-x64 version license dist.tarball --json`; `npm pack @openai/codex@0.144.4-win32-x64 --dry-run --json`
- `python -m pytest backend/tests/test_codex_app_server.py -q`
- `node --test tests/electron/codex-runtime-boundary.test.cjs`
- `python -m pytest backend/tests/test_runtime_llm.py -q`
- `npm run build`
- `npx electron-builder --dir --publish never`
- Verify the unpacked Electron resource contains the pinned `codex.exe` and Apache-2.0 license copy at the exact paths asserted by `tests/electron/codex-runtime-boundary.test.cjs`.
Scope-Regel:
- Implement only `TASK-CHATGPT-CODEX.1`. No direct OAuth, token parsing, token refresh, credential-file storage, shared `CODEX_HOME`, system/PATH runtime discovery, API-key fallback, provider/model fallback, UI, API router, model discovery, provider transport, chat behavior, or scope expansion.
- Pin the official runtime to exact version `0.144.4` and use only the Windows x64 package resource `vendor/x86_64-pc-windows-msvc/bin/codex.exe`; do not silently select another architecture or installation.
- Force `CODEX_HOME` to a deterministic Janus-only application-data directory and force `cli_auth_credentials_store = "keyring"`; unavailable protected storage is a fail-closed provider-unavailable state.
- Extend `backend/utils/redaction.py` only for credential-container keys and OAuth URL/query shapes such as authorization codes, state, and callback parameters that the current helper does not fully cover.
- Add only the official Apache-2.0 license text under `licenses/openai-codex/LICENSE.txt` and package it with the runtime. No broader licensing refactor is authorized.
- `janus_backend.spec`, `backend/llm_providers/runtime_llm.py`, all frontend files, all routers, and every existing API-key provider remain unchanged.
Automated Evidence Gate:
- `python -m pytest backend/tests/test_codex_app_server.py -q`
- `node --test tests/electron/codex-runtime-boundary.test.cjs`
- `python -m pytest backend/tests/test_runtime_llm.py -q`
- `npm run build`
- `npx electron-builder --dir --publish never`
- npx playwright test <runner> --headed --workers=1 --reporter=list
- `npx playwright test tests/e2e/capability-overview.spec.js --headed --workers=1 --reporter=list`
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, parent task, and task-breakdown handoff path verified. Historical `TASK-CHATGPT-OAUTH*` artifacts are stale and forbidden as execution inputs.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route later TestSpec, packaged live-login, provider/model, or UI evidence to janus-test-pipeline.
Keep Context:
- documentation/SPEC/CHATGPT_OAUTH_PROVIDER_FEATURE_SPEC.md
- documentation/tasks/TASK-CHATGPT-CODEX-PROVIDER.md
- documentation/tasks/TASK-CHATGPT-CODEX.1_task_breakdown.md
- documentation/tasks/TASK-CHATGPT-CODEX.1_precheck.md
- current official Codex App Server, configuration, storage-source, license, and pinned npm distribution evidence
Drop Context:
- all historical TASK-CHATGPT-OAUTH task/precheck artifacts
- unrelated provider, UI, model-catalog, chat, audit, release, and backlog history
Completion Rule:
- End with PASS, BLOCKED, or HANDOFF and concrete evidence paths. Stop immediately if keyring-only isolation, pinned-resource resolution, protocol compatibility, redaction, or license packaging cannot be proven without widening scope.
Expected Output:
- Implementation result, executed checks, affected files, residual risks, and the next-skill handoff.
legacy handoff end
```

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.6 Terra
Recommended Intelligence: high
User Action: Approve implementation of exactly TASK-CHATGPT-CODEX.1 in this bounded context. If 5.6 Sol becomes executable for the current ChatGPT Codex account, it may be used; otherwise retain the documented `SOL_UNAVAILABLE_FOR_CHATGPT_CODEX_ACCOUNT` fallback to 5.6 Terra/high.
```

## Changed Files

```text
M backend/main.py
 M backend/services/chat_orchestrator.py
 M backend/tests/integration/test_help_integration_real.py
 M backend/utils/redaction.py
 M main.electron.cjs
 M package-lock.json
 M package.json
 M scripts/run-backend-dev.cjs
 M tests/e2e/capability-overview.spec.js
?? backend/llm_providers/codex_app_server.py
?? backend/tests/test_codex_app_server.py
?? documentation/tasks/TASK-CHATGPT-CODEX.1_debug_result.md
?? documentation/tasks/TASK-CHATGPT-CODEX.1_execution_result.md
?? licenses/openai-codex/LICENSE.txt
?? tests/electron/codex-runtime-boundary.test.cjs
```

## Artifact Inventory

```text
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-CHATGPT-CODEX.1_execution_result.md (5495 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-CHATGPT-CODEX.1_debug_result.md (3874 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-CHATGPT-CODEX.1_precheck.md (6552 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-CHATGPT-CODEX.1_task_breakdown.md (10152 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-CHATGPT-CODEX.1_validation_summary.md (1057 bytes)
```

## Diff Summary

```text
backend/main.py                                    |  23 ++++
 backend/services/chat_orchestrator.py              |   4 +
 .../integration/test_help_integration_real.py      |  59 ++++++++++
 backend/utils/redaction.py                         |  13 ++-
 main.electron.cjs                                  |  79 ++++++++++++-
 package-lock.json                                  | 126 +++++++++++++++++++++
 package.json                                       |  11 ++
 scripts/run-backend-dev.cjs                        |  36 +++++-
 tests/e2e/capability-overview.spec.js              |  26 ++++-
 9 files changed, 368 insertions(+), 9 deletions(-)
```

## Validation

```text
# TASK-CHATGPT-CODEX.1 Validation Summary

- `python -m pytest backend/tests/test_codex_app_server.py backend/tests/test_runtime_llm.py backend/tests/integration/test_help_integration_real.py -q`: PASS (`34 passed`).
- `node --test tests/electron/codex-runtime-boundary.test.cjs`: PASS (`7 passed`).
- `npx playwright test tests/e2e/capability-overview.spec.js --headed --workers=1 --reporter=list`: PASS (`2 passed`).
- `npm run build`: PASS.
- `python C:\Users\pruve\.codex\skills\janus-debug\scripts\validate_debug_result.py documentation/tasks/TASK-CHATGPT-CODEX.1_debug_result.md`: PASS.
- Manual Janus evidence: PASS. The operator created a new chat, sent `Was kannst du?`, and confirmed the complete rendered capability overview.

Known unrelated environment/repository conditions: the focused broader Help selector suite has one pre-existing canonical-skill-ID failure (`session_search`); the local vector/embedding stack logs its existing `tokenizers`/`transformers` mismatch. Neither affects the bound runtime or headed capability evidence above.
```

## Notes

No additional notes provided.

## Risks

No live ChatGPT account login/UI/provider-model transport is in this task; managed account behavior remains for later tasks. Existing local embedding dependency degradation is unrelated.

## Open Issues

None for the bound .1 implementation; later Tasks .2-.4 are intentionally parked.

## Re-Audit Delta

No re-audit delta provided.

## Final Audit Handoff

```text
NEW_CHAT_HANDOFF
NEXT: final-skill-audit
MODEL: 5.6 Sol/high if runtime-supported; otherwise 5.6 Terra/high
PASS: C:\KI\Janus-Projekt\documentation\tasks\TASK-CHATGPT-CODEX.1_AUDIT_PACKAGE.md
ASK: Lade nur dieses Paket im neuen Chat und starte dann den Final Audit.
DROP: dev chat history
```

Use `5.6 Sol/high` when the current Codex run can start it; if Codex reports `gpt-5.6-sol` is unsupported for the active ChatGPT account, use `5.6 Terra/high` and record `SOL_UNAVAILABLE_FOR_CHATGPT_CODEX_ACCOUNT`.

For bounded same-thread re-audits after a local blocker fix, `5.6 Terra/high` is acceptable when the package stays compact and the risk did not escalate.
