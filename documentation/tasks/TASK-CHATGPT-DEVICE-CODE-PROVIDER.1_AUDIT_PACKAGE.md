# AUDIT_PACKAGE

Generated: 2026-07-14 23:39:16 UTC

## Goal

Independently audit Task .1 official device-code credential isolation, secure persistence, redaction, and two-account non-interference while production remains default-deny.

## Scope Rules

- Audit the provided package and changed artifacts only.
- Do not rely on development chat history.
- Verify credential isolation, secure persistence, redaction, provider boundaries, production default-deny, and validation evidence.
- On re-audit, review the blocker delta first before widening scope.
- If scoped paths were provided, treat them as the audit diff boundary.

## Bound Audit Inputs

- Spec: APPROVED: documentation/SPEC/CHATGPT_OFFICIAL_DEVICE_CODE_PROVIDER_REDESIGN_FEATURE_SPEC.md
- Task File: documentation\tasks\TASK-CHATGPT-DEVICE-CODE-PROVIDER.md
- Backlog Item: N/A - Spec task, no Backlog item
- Pre-Implementation Check: documentation\tasks\TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_precheck.md
- Manual Janus Evidence: PASS: documentation/test-results/TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_isolation_evidence.md
- Pipeline Completion Status: Task .1 implementation and validation complete; Tasks .2-.5 remain parked; production default-deny

## Backlog Item

```text
N/A WITH REASON - Task `.1` is compiled from the approved Feature Spec and has no separate Backlog item.
```

## Task Acceptance Scope

```text
TASK-CHATGPT-DEVICE-CODE-PROVIDER
- Source Spec: `documentation/SPEC/CHATGPT_OFFICIAL_DEVICE_CODE_PROVIDER_REDESIGN_FEATURE_SPEC.md`
- Backlog Item: N/A
- Feature: ChatGPT über offiziellen Codex-Device-Code als separate Janus-Provideroption
- Generated At: 2026-07-14 23:30:26 +02:00

## Generated Tasks

### TASK-CHATGPT-DEVICE-CODE-PROVIDER.1 Sichere Device-Code-Credential-Isolation implementieren
- Ziel: Den offiziellen Device-Code-Lifecycle mit einer ausschließlich Janus gehörenden, verschlüsselten und persistenten Credential-Ablage verbinden und die frühere gegenseitige Sitzungsbeeinflussung fail-closed ausschließen.
- Scope: Nur Lifecycle, sichere Persistenz, Credential-Namensraum, Redaktion, Janus-only Logout, Neustartpersistenz und der erste kontrollierte Zwei-Konten-Nichtbeeinflussungsnachweis; keine Settings-UX, Modellauswahl oder Chat-Nutzung.
- Files: `backend/llm_providers/codex_app_server.py`, `backend/tests/test_codex_app_server.py`, `tests/electron/codex-runtime-boundary.test.cjs`, `documentation/test-results/TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_isolation_evidence.md`
- Steps:
  1. Den vorhandenen Codex-App-Server-Lifecycle auf den offiziell dokumentierten Device-Code-Anmeldeweg begrenzen und den bisherigen Browser-Callback-Pfad aus diesem Featurepfad entfernen.
  2. Die Spec-konforme Janus-eigene verschlüsselte Persistenz nur dann anbinden, wenn der Precheck einen getrennten Credential-Namensraum ohne Codex-Desktop-, CLI- oder IDE-Sharing nachweist.
  3. Fehlende oder nicht eindeutig getrennte sichere Persistenz vor jedem Login- oder Refresh-Vorgang als nicht verfügbare Funktion behandeln.
  4. Login, Erneuerung, Neustartpersistenz und Logout so begrenzen, dass nur die Janus-Sitzung gelesen, verändert oder entfernt werden kann.
  5. Öffentliche Zustände, Fehler und Logs auf nicht-sensitive Werte begrenzen; Tokens, Device Codes und Credentials dürfen nicht in Fehlern, Logs oder Evidenzartefakten erscheinen.
  6. Nach grünen automatisierten Gates einen kontrollierten Zwei-Konten-Test für Janus-Login, Janus-Neustart und Janus-Logout durchführen; bei jeder Abweichung bleibt Produktion gesperrt.
- Acceptance Criteria:
  - Der Lifecycle startet ausschließlich den offiziellen Device-Code-Flow und importiert keine bestehenden Codex-Credentials.
  - Ohne nachweislich verschlüsselte und getrennte Persistenz startet kein Login, Refresh oder Account-Read mit Credentials.
  - Eine erfolgreich aufgebaute Janus-Sitzung übersteht einen Janus-Neustart, ohne den parallel angemeldeten Codex-Client zu verändern.
  - Janus-Logout entfernt nur die Janus-Sitzung; Konto, Kontingent, Einstellungen und Sitzungszustand des separaten Codex-Clients bleiben unverändert.
  - Automatisierte und manuelle Evidenz enthalten keine Tokens, Device Codes, Credentials oder privaten Account-Identifikatoren.
  - Die Produktionsfreigabe bleibt nach diesem Task weiterhin deaktiviert; der Task liefert nur den isolierten Foundation-Nachweis für nachfolgende Slices.
- Tests:
  - Fokus-Tests für Device-Code-Start, Abbruch, Persistenz, Refresh, Logout, Default-Deny und Redaktion in `backend/tests/test_codex_app_server.py`.
  - Electron-Grenztests für Runtime, Umgebungsvariablen, Credential-Namensraum und Secret-Vermeidung in `tests/electron/codex-runtime-boundary.test.cjs`.
  - Kontrollierter manueller Zwei-Konten-Test mit unterschiedlichen Janus- und Codex-Konten für Login, Neustart und Logout.
  - Scoped `git diff --check` und Syntaxprüfung der geänderten Runtime-Dateien.
- Model: 5.6 Sol
- Reason: Security- und Persistenzgrenze mit bereits nachgewiesener Cross-Client-Sitzungsbeeinflussung; bei nicht verfügbarem Sol dokumentierter Fallback auf 5.6 Terra/high.

### TASK-CHATGPT-DEVICE-CODE-PROVIDER.2 Settings-Lifecycle und atomaren Kontowechsel bereitstellen
- Ziel: Die bestehende ChatGPT-Verbindungsfläche in den Einstellungen auf den Device-Code-Ablauf, Janus-only Logout und atomaren Ein-Konto-Wechsel umstellen.
- Scope: Settings-UI und nicht-sensitive Backend-Verträge für getrennt, Anmeldung läuft, verbunden, Fehler, Abbruch, Wiederholung, Abmelden und Konto wechseln; keine Provider-/Modellfreigabe und kein Chat-Transport.
- Files: `backend/api/routers/system.py`, `frontend/index.html`, `frontend/js/settings.js`, `frontend/css/settings.css`, `backend/tests/test_codex_connection_settings_api.py`, `tests/e2e/codex-connection-settings.spec.js`
- Steps:
  1. Den Settings-Vertrag um die nicht-sensitiven Device-Code-Zustände und Benutzeraktionen erweitern.
  2. Den laufenden Anmeldevorgang mit offizieller Verifikationsadresse und Benutzer-Code ausschließlich in der vorgesehenen Login-Oberfläche darstellen, ohne diese Werte in Fehler oder Logs zu übernehmen.
  3. Abbruch und Wiederholung nicht-destruktiv gestalten.
  4. Janus-only Logout sichtbar von anderen Codex-, ChatGPT- und API-Key-Sitzungen abgrenzen.
  5. „Konto wechseln“ so umsetzen, dass die bestehende Janus-Verbindung erst nach erfolgreicher neuer Anmeldung ersetzt wird.
  6. Bei nicht verfügbarer sicherer Persistenz die Anmeldung deaktiviert mit verständlichem Grund anzeigen.
- Acceptance Criteria:
  - Alle spezifizierten Verbindungszustände sind in den bestehenden Einstellungen sichtbar und bedienbar.
  - Abbruch oder Fehler einer ersten Anmeldung hinterlassen keinen teilweise verbundenen Zustand.
  - Abbruch oder Fehler eines Kontowechsels erhalten die bestehende Janus-Verbindung vollständig.
  - Ein erfolgreicher Kontowechsel ersetzt das alte Janus-Konto erst nach bestätigtem Abschluss.
  - Janus-Logout und Fehlertexte versprechen und bewirken ausschließlich eine Änderung der Janus-Verbindung.
  - Nicht verfügbare sichere Persistenz bietet weder Klartext- noch Session-only-Fallback an.
- Tests:
  - Backend-Vertragstests für alle Lifecycle-Aktionen und nicht-sensitive Fehlerantworten.
  - Headed E2E für getrennt, Login läuft, Abbruch, verbunden, Wiederholung, Logout, Kontowechsel-Erfolg und Kontowechsel-Fehler.
  - Regression für unveränderte API-Key-Einstellungen.
  - Scoped `git diff --check` und JavaScript-Syntaxprüfung.
- Model: 5.6 Terra
- Reason: Mehrflächige Settings- und API-Umsetzung auf einer bereits bewiesenen Security-Foundation.

### TASK-CHATGPT-DEVICE-CODE-PROVIDER.3 Verifizierte ChatGPT-Modelle und fail-closed Providerwahl integrieren
- Ziel: ChatGPT nur bei gültiger Janus-Verbindung und mindestens einem aktuell verifiziert nutzbaren Modell im bestehenden Provider-/Modell-Dropdown anzeigen.
- Scope: Modellermittlung, nicht-stale Verfügbarkeitszustände, Dropdown-Sichtbarkeit, Wiederholung und Verlust der Modellnutzbarkeit; kein Chat-Transport und keine Datenschutzübermittlung.
- Files: `backend/llm_providers/codex_app_server.py`, `backend/api/routers/system.py`, `backend/services/model_catalog.py`, `frontend/index.html`, `frontend/js/chat.js`, `frontend/js/settings.js`, `backend/tests/test_codex_connection_settings_api.py`, `backend/tests/test_model_hierarchy_single_source.py`, `tests/e2e/codex-connection-settings.spec.js`
- Steps:
  1. Die aktuell nutzbaren Modelle ausschließlich aus der aktiven Janus-ChatGPT-Sitzung verifizieren und als nicht-sensitive Verfügbarkeit bereitstellen.
  2. ChatGPT nur bei verbundener Sitzung und mindestens einem verifiziert nutzbaren Modell als auswählbaren Provider anzeigen.
  3. Ausschließlich die aktuell bestätigten Modelle unter ChatGPT anzeigen; statische oder zuletzt bekannte Listen dürfen keine Auswahlberechtigung erzeugen.
  4. Bei fehlgeschlagener oder leerer Verifikation ChatGPT nicht auswählbar machen, die Anmeldung erhalten und eine nicht-destruktive Wiederholung anbieten.
  5. Ein inzwischen nicht mehr nutzbares ausgewähltes Modell vor der nächsten Übermittlung sperren und eine neue gültige Auswahl verlangen.
- Acceptance Criteria:
  - Das Dropdown enthält unter ChatGPT ausschließlich aktuell verifiziert nutzbare Modelle.
  - Ohne gültige Verbindung oder ohne verifiziertes Modell ist ChatGPT nicht auswählbar.
  - Ein Modellprüfungsfehler meldet „Modelle derzeit nicht verfügbar“, erhält die Anmeldung und bietet Wiederholung an.
  - Veraltete, statische oder zuvor bekannte Modelle bleiben bei fehlender aktueller Verifikation verborgen.
  - Andere Provider und deren Modellauswahl verhalten sich unverändert.
- Tests:
  - Backend-Tests für verbundene, leere, fehlgeschlagene und erneuerte Modellverifikation.
  - Frontend-/E2E-Tests für konditionale Provideranzeige und ausschließlich verifizierte Modelloptionen.
  - Regression für bestehende Model-Catalog- und Provider-Hierarchie-Verträge.
  - Scoped `git diff --check` und Syntaxprüfungen.
- Model: 5.6 Terra
- Reason: Provider- und Modellintegration mit klarer fail-closed Produktlogik auf vorhandenen Katalog- und Dropdown-Flächen.

### TASK-CHATGPT-DEVICE-CODE-PROVIDER.4 Chat-Transport, Kontextfortsetzung und Datenschutz-Gate anbinden
- Ziel: ChatGPT als echten Janus-Chatprovider nutzbar machen und den Wechsel mitten im Chat mit erforderlichem Kontext sowie einmaliger Datenschutzbestätigung absichern.
- Scope: Provider-Transport, bestehender Chatkontext, sichtbarer aktiver Provider, bestätigungsgebundene erste Übermittlung und unveränderte API-Key-Provider; keine Produktionsaktivierung ohne finalen Evidenz-Task.
- Files: `backend/llm_providers/runtime_llm.py`, `backend/services/chat_orchestrator.py`, `frontend/js/chat.js`, `frontend/js/beta-privacy-notice.js`, `backend/tests/test_context_privacy_externalization_boundary.py`, `backend/tests/test_provider_parity.py`, `backend/tests/test_provider_auth_fallback.py`, `tests/e2e/codex-connection-settings.spec.js`
- Steps:
  1. Den ChatGPT-Provider in den bestehenden Runtime- und Orchestrator-Pfad einbinden, ohne API-Key-Provider als Fallback oder Ersatz zu verwenden.
  2. Beim Providerwechsel den für die Fortsetzung benötigten bestehenden Janus-Gesprächskontext an ChatGPT übergeben.
  3. Den aktiven Provider während und nach dem Wechsel sichtbar halten.
  4. Vor der ersten ChatGPT-Inhaltsübertragung die bestätigte Datenschutzinformations-Version prüfen und ohne gültige Bestätigung fail-closed blockieren.
  5. Eine Bestätigung bei unveränderter Datenschutzinformation wiederverwenden und nach wesentlicher Versionsänderung erneut verlangen.
  6. Authentifizierungs-, Modell- und Transportfehler ausschließlich auf ChatGPT begrenzen; andere Provider bleiben nutzbar.
- Acceptance Criteria:
  - Ein Nutzer kann mitten im bestehenden Chat zu ChatGPT wechseln und mit dem benötigten bisherigen Kontext weiterarbeiten.
  - Vor der ersten ChatGPT-Inhaltsübertragung erfolgt ohne gültige Datenschutzbestätigung kein externer Versand.
  - Bei unveränderter bestätigter Datenschutzinformation unterbrechen spätere Providerwechsel den Chat nicht erneut.
  - Nach einer wesentlichen Datenschutzinformationsänderung wird vor der nächsten ChatGPT-Übertragung erneut bestätigt.
  - Der aktive Provider bleibt eindeutig sichtbar.
  - ChatGPT-Fehler lösen keinen API-Key-Fallback aus und verändern keine andere Providerverbindung.
- Tests:
  - Orchestrator- und Provider-Paritätstests für ChatGPT-Auswahl, Kontextfortsetzung und Fehlerisolation.
  - Privacy-Externalization-Tests für Erstbestätigung, Wiederverwendung, Versionsänderung und blockierten Versand.
  - E2E-Wechsel zwischen vorhandenem Provider und ChatGPT innerhalb desselben Chats.
  - Regression für bestehende API-Key-Provider und deren Authentifizierungsverhalten.
  - Scoped `git diff --check` und Syntaxprüfungen.
- Model: 5.6 Terra
- Reason: Komplexe, aber deterministisch spezifizierte Provider-/Orchestrator-Integration mit Privacy-Gate.

### TASK-CHATGPT-DEVICE-CODE-PROVIDER.5 Evidenzgebundenes Produktions-Aktivierungsgate implementieren
- Ziel: Die vollständige ChatGPT-Funktion erst nach reproduzierbarer automatisierter Evidenz und bestandenem realem Zwei-Konten-Test aus dem Default-Deny-Zustand freigeben.
- Scope: Vollständige Regression, reale Nichtbeeinflussungssequenz, evidenzgebundene Produktionsfreigabe und Rückfall auf deaktiviert bei jeder Abweichung; keine Berei
```

## Pre-Implementation Check

```text
PRE-CHECK RESULT
PRE-CHECK PASSED

```text
legacy handoff start
NEXT: janus-executioner
Target Task: TASK-CHATGPT-DEVICE-CODE-PROVIDER.1
Target Subtask: N/A
Task: documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.md
Task Breakdown: documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_task_breakdown.md
Spec: documentation/SPEC/CHATGPT_OFFICIAL_DEVICE_CODE_PROVIDER_REDESIGN_FEATURE_SPEC.md
Backlog Item: N/A
Assigned Model: 5.6 Sol
Assigned Intelligence: high
Fallback: 5.6 Terra / high only with SOL_UNAVAILABLE_FOR_CHATGPT_CODEX_ACCOUNT recorded
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The actually bundled `@openai/codex` runtime is pinned to `0.144.4`; its generated App Server schema exposes `chatgptDeviceCode`, `userCode`, and `verificationUrl`.
- Official pinned source `rust-v0.144.4` routes `account/login/start` with `chatgptDeviceCode` through `request_device_code` and `complete_device_code_login`; completion persists through the configured Codex auth storage. Janus must use only this App Server contract and must not own OAuth tokens or call private auth endpoints.
- The same pinned source derives both direct-keyring and Windows encrypted-secrets keyring identities from the canonical `CODEX_HOME`. On Windows, the keyring backend defaults to `Secrets`, which stores the auth payload in a local encrypted secrets file and stores its key under an OS-keyring account derived from the canonical home. The Janus-only absolute `JANUS_CODEX_HOME` therefore supplies a separately named persistent credential boundary without importing another Codex client's credential slot.
- This source-level feasibility proof does not override the prior failed browser-flow evidence. Task `.1` must retain default-deny after implementation and must not set `PRODUCTION_ISOLATION_EVIDENCE_REVISION` or any equivalent production activation marker.
- No live account action is authorized by this precheck. After all automated gates are green, janus-executioner must stop and request separate explicit user authority before device-code login, restart, refresh, logout, revocation, or two-account evidence actions.
- The existing isolated Janus Account-B credential and its cleanup are outside this task and must not be inspected, imported, copied, mutated, or removed.
Affected Files:
- backend/llm_providers/codex_app_server.py
- backend/tests/test_codex_app_server.py
- tests/electron/codex-runtime-boundary.test.cjs
- documentation/test-results/TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_isolation_evidence.md (create only from an actually authorized and executed controlled evidence run)
Evidence Focus:
- Replace the managed browser login request type with official `chatgptDeviceCode`; expose only the non-sensitive lifecycle data required by later Settings work.
- Preserve the absolute Janus-only `CODEX_HOME`, forced `cli_auth_credentials_store="keyring"`, stripped API-key environment, strict configuration, and redacted public state.
- Prove with fakes that secure-store unavailability blocks login, credential-bearing account reads, and refresh before process or network effects; no plaintext, `auto`, file, ephemeral, API-key, shared-session, or credential-import fallback is allowed.
- Prove that cancel, restart persistence, refresh, and logout address only the Janus-owned App Server lifecycle and never read or mutate Codex Desktop, Codex CLI, IDE, browser-cookie, or API-key-provider credentials.
- Device codes, verification values, tokens, credentials, auth URLs containing secrets, private account identifiers, and keyring contents must not appear in logs, generic errors, snapshots, or evidence artifacts.
Scope-Regel:
- Implement only the bound target task. No Settings UX, provider/model dropdown, model discovery, chat transport, privacy acknowledgement, atomic UI account switch, API-key-provider change, production activation, release, or multi-account support.
- Do not add private OAuth clients, direct token exchange, undocumented auth/backend endpoints, Hermes credential logic, existing-Codex credential import, or a second product module to work around the bound lifecycle.
- If the official App Server contract cannot satisfy the task inside the listed product/test boundary, stop with BLOCKED and return to janus-task-breakdown instead of widening scope.
Automated Evidence Gate:
- python -m pytest backend/tests/test_codex_app_server.py -q
- node --test tests/electron/codex-runtime-boundary.test.cjs
- python -m py_compile backend/llm_providers/codex_app_server.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
- npx playwright test tests/e2e/codex-connection-settings.spec.js --headed --workers=1 --reporter=list
- git diff --check -- backend/llm_providers/codex_app_server.py backend/tests/test_codex_app_server.py tests/electron/codex-runtime-boundary.test.cjs documentation/test-results/TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_isolation_evidence.md
Artifact Identity Check:
- PASS: Spec, compiled task, Task `.1` breakdown, target identifier, file boundary, evidence path, and parked Tasks `.2` through `.5` match.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan or TestResult artifacts. The named isolation evidence file may be created only from the actually executed controlled evidence required by the approved Spec; route any TestSpec/TestPlan change through janus-test-pipeline.
Keep Context:
- documentation/SPEC/CHATGPT_OFFICIAL_DEVICE_CODE_PROVIDER_REDESIGN_FEATURE_SPEC.md
- documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.md
- documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_task_breakdown.md
- pinned Codex `rust-v0.144.4` App Server device-code and auth-storage source
- affected file cluster and automated evidence commands
Drop Context:
- prior browser-callback implementation assumptions
- Hermes direct OAuth details
- unrelated provider, Settings, model, chat, release, backlog, and historical debug context
Completion Rule:
- End Task `.1` implementation with PASS, BLOCKED, NEEDS_INFO, or HANDOFF plus concrete evidence paths. Production activation remains disabled. Live account actions require a new explicit user gate after green automated validation.
Expected Output:
- Bounded implementation result, executed automated checks, changed files, redaction confirmation, and either the separate controlled-evidence authorization gate or a concrete blocker.
legacy handoff end
```

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.6 Sol
Recommended Intelligence: high
User Action: Approve implementation of Task `.1` only. Do not log in, log out, retry, switch accounts, refresh, revoke, inspect, or clean up credentials until Codex reaches the separately announced controlled-evidence gate.
```

## Changed Files

```text
M backend/llm_providers/codex_app_server.py
 M backend/tests/test_codex_app_server.py
 M tests/electron/codex-runtime-boundary.test.cjs
?? documentation/SPEC/CHATGPT_OFFICIAL_DEVICE_CODE_PROVIDER_REDESIGN_FEATURE_SPEC.md
?? documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_debug_result_device_auth_disabled.md
?? documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_execution_result.md
?? documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_precheck.md
?? documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_task_breakdown.md
?? documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.md
?? documentation/test-results/TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_isolation_evidence.md
```

## Artifact Inventory

```text
FILE C:\KI\Janus-Projekt\documentation\SPEC\CHATGPT_OFFICIAL_DEVICE_CODE_PROVIDER_REDESIGN_FEATURE_SPEC.md (14448 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-CHATGPT-DEVICE-CODE-PROVIDER.md (14441 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_task_breakdown.md (5963 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_precheck.md (6753 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_execution_result.md (10346 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_debug_result_device_auth_disabled.md (4793 bytes)
FILE C:\KI\Janus-Projekt\documentation\test-results\TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_isolation_evidence.md (7378 bytes)
```

## Diff Summary

```text
backend/llm_providers/codex_app_server.py      | 165 +++++++++++++++++----
 backend/tests/test_codex_app_server.py         | 192 +++++++++++++++++++++++--
 tests/electron/codex-runtime-boundary.test.cjs |  23 +++
 3 files changed, 341 insertions(+), 39 deletions(-)
```

## Validation

```text
# TASK EXECUTION RESULT - TASK-CHATGPT-DEVICE-CODE-PROVIDER.1

Canonical State: PASS
Target Task: TASK-CHATGPT-DEVICE-CODE-PROVIDER.1

## Scope Delivered

- The Janus lifecycle now starts only the official Codex App Server `chatgptDeviceCode` login type. Browser-callback login is no longer used by this lifecycle.
- Login response handling accepts only the pinned official verification location `https://auth.openai.com/codex/device` and a bounded one-time user-code shape.
- Device-code login type and connected-account auth mode are separate: login uses `chatgptDeviceCode`; account state continues to accept only `chatgpt` or disconnected.
- Verification URL and user code remain transient. They are returned only by the direct lifecycle start result, never added to public state, and exact active values are removed from App Server diagnostics and completion errors before generic redaction.
- Cancel, logout, retry, and shutdown clear all transient login values. Refresh remains an owned App Server `account/read` request with no token supplied by Janus.
- The pinned runtime command still forces `cli_auth_credentials_store="keyring"`, the absolute Janus-only `CODEX_HOME`, strict ChatGPT login, and API-key environment removal. No plaintext, file, auto, ephemeral, API-key, existing-Codex credential import, private OAuth client, direct token exchange, or private auth endpoint was added.
- The prior failed evidence revision is no longer a possible activation target. The required revision points to the later device-code release-evidence Task `.5`, while `PRODUCTION_ISOLATION_EVIDENCE_REVISION` remains `None` and normal production stays unavailable.
- Existing uncommitted isolation changes already present in the three bound files were preserved; this execution amended those files in place and did not claim ownership of unrelated worktree changes.

Changed Files:

- `backend/llm_providers/codex_app_server.py`
- `backend/tests/test_codex_app_server.py`
- `tests/electron/codex-runtime-boundary.test.cjs`
- `documentation/test-results/TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_isolation_evidence.md`
- `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_debug_result_device_auth_disabled.md`
- `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_execution_result.md`
- `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_AUDIT_PACKAGE.md`
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/SKILL_USAGE_LOG.md`

Executed Checks:

- `python C:\Users\pruve\.codex\skills\janus-preimplementation-check\scripts\validate_precheck.py documentation\tasks\TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_precheck.md` PASS.
- Targeted `WHAT_I_LEARNED.md` search completed; no device-code-specific reusable root-cause pattern was found.
- `python -m pytest backend/tests/test_codex_app_server.py -q` PASS: `22 passed`.
- `node --test tests/electron/codex-runtime-boundary.test.cjs` PASS: `9 passed`.
- `python -m py_compile backend/llm_providers/codex_app_server.py` PASS.
- `npx playwright test tests/e2e/codex-connection-settings.spec.js --headed --workers=1 --reporter=list` PASS: `4 passed`.
- Scoped `git diff --check` for the three bound product/test files PASS.
- Headed startup emitted pre-existing Vector/Vision dependency warnings outside this task; the Playwright result remained PASS.
- Controlled pre-mutation baseline read with `refresh_token=False` PASS: the Janus-only store reports only `connection_state=connected`, `auth_mode=chatgpt`, and no pending login. No identifier or credential value was emitted, no refresh was requested, and the lifecycle was closed afterward.
- The baseline process also emitted pre-existing Vector/Skill-index startup warnings outside this task; they did not change the safe account-state result.
- Operator observation after the safe baseline read PASS: Account A remained unchanged with account, quota, settings, and connected state visible.
- Controlled Janus-only logout of the pre-existing session PASS: the lifecycle returned `connection_state=disconnected`, no auth mode, and no pending login. A redacted App Server diagnostic reported that the old Janus token was already invalidated; no token value or account identifier was emitted.
- Operator observation after Janus-only logout PASS: Account A remained unchanged with account, quota, settings, and connected state visible.
- Fresh official `chatgptDeviceCode` start PASS: the pinned App Server returned the allowlisted official verification destination and a transient user code. The code was transferred only in memory to the browser controller and was not emitted to chat, logs, state, or evidence.
- The official browser flow reached the Account-B security gate and reported that Codex device-code authorization is disabled for that account. Device-code submission and login completion did not occur.
- Debug cleanup PASS: the failed attempt was terminated, zero matching Janus App Server processes remained, and the transient code was removed from the browser-controller session without emission.
- Operator setting confirmation PASS: Codex device-code authorization was enabled for Account B through the provider-owned ChatGPT Security surface.
- Fresh retry start PASS: the pinned App Server returned the allowlisted official verification destination and a new transient code held only in memory. The official page now waits for operator-controlled Account-B sign-in; Janus reports connecting, login pending, and no retry reason.
- Browser-session distinction confirmed: Account B was authenticated in a normal browser, but the separate Codex in-app OpenAI tab still required sign-in. The pending attempt expired before that sign-in, so its code was removed and the worker stopped. No device-code attempt is currently active.
- Invisible-tab root cause confirmed and corrected: the local browser finalizer had received the wrong argument shape and therefore omitted/closed the intended handoff tab. The generic official OpenAI page was reopened, browser visibility enabled, and the tab retained with an explicit handoff entry. This was not a Janus or OpenAI auth failure.
- Fresh official login completion PASS: after operator-controlled Account-B authentication, a new memory-only code was distributed across the unique official one-time-code fields and submitted. The official success page appeared; Janus reached `connected` with auth mode `chatgpt`, no pending login, and no retry reason. The transient code was cleared without emission.
- Operator observation after fresh Account-B login PASS: Account A remained unchanged with the same account, quota, settings, and connected state visible.
- Restart persistence without refresh PASS: the original lifecycle exited, and a new lifecycle against the same isolated home returned connected ChatGPT auth with no pending login or retry reason using `account/read(refreshToken=false)`.
- The shutdown-time SQLite panic was reproduced by an import-only Janus backend process with no App Server or account action. It is therefore classified as a pre-existing Vector/Skill-index backend-import side effect outside the auth/persistence slice, not an App Server failure. Zero matching Janus App Server processes remained.
- Operator observation after the restart/read PASS: Account A was reported unchanged.
- Janus-owned refresh PASS: exactly one isolated `account/read(refreshToken=true)` returned connected ChatGPT auth with no pending login or retry reason. The known import-side-effect panic recurred only during Python process shutdown, and zero matching Janus App Server processes remained.
- Operator observation after the owned refresh PASS: Account A in Codex remained fully healthy.
- Final Janus-only Account-B logout PASS: exactly one isolated `account/logout` returned disconnected state with no auth mode, pending login, or retry reason. The known import-side-effect panic recurred only at Python shutdown, and zero matching Janus App Server processes remained.
- Final operator observation after Janus-only logout PASS: Account A in Codex remained fully healthy.
- No credential inspection, revocation experiment, Account-A mutation, commit, push, or sync was performed.

Auto-Verification:
- Status: PASS
- Evidence: focused Python lifecycle tests, Electron runtime-boundary tests, Python compile, headed Settings regression, and scoped diff check listed above.

Manual Janus Validation Gate:
- Status: PASS
- Test Example: After separate explicit authorization, keep the Codex desktop client connected as user-labelled Account A. Start a fresh Janus official device-code login with a different user-labelled Account B, restart Janus, perform an owned refresh, and finally log Account B out only through the Janus lifecycle. After every Janus step, the operator checks that Account A still shows the same account, quota, settings, and connected state.
- Expected Result: The Janus Account-B session persists across Janus restart, and Janus login, refresh, restart, and logout never alter Account A. No token, credential, user code, verification value, cookie, keyring content, or private account identifier is recorded in evidence.
- If Failed: route to janus-debug
- If Passed: route to janus-final-audit

NEXT_STEP
Target Skill: janus-final-audit
Canonical State: HANDOFF
Required Artifacts: approved device-code Spec; Task `.1`; Task `.1` breakdown; passed precheck; this execution result; completed controlled isolation evidence.
Audit Package: `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_AUDIT_PACKAGE.md`.
Evidence Paths: `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_execution_result.md`; `documentation/test-results/TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_isolation_evidence.md`.
Failure Code: NONE
Changed Files: see scope list above.
Decision: accept the complete live two-account evidence gate and compact audit package as PASS, then route Task `.1` to independent final audit.
Reason: fresh login, restart persistence, owned refresh, final Janus-only logout, every Account-A observation, and all automated gates passed without credential emission or cross-client impact.
Recommended Model: 5.6 Sol
Recommended Intelligence: high
New Chat: yes for independent final audit after package creation
Next User Action: open a fresh chat with only the audit package and run `janus-final-audit`; no further account action is required.
```

## Notes

# TASK-CHATGPT-DEVICE-CODE-PROVIDER.1 - Controlled Isolation Evidence

## Evidence Boundary

- Runtime: bundled official Codex `0.144.4`
- Auth transport: Codex App Server only
- Login mode under test: `chatgptDeviceCode`
- Credential policy: `keyring` with the Janus-only `CODEX_HOME`
- Production activation revision: unset
- Account labels: `Account A` is the parallel Codex desktop account; `Account B` is reserved for the fresh Janus device-code login
- Redaction rule: no names, email addresses, account/workspace identifiers, tokens, cookies, device codes, verification values, auth URLs, keyring contents, or credential values

## Controlled Sequence

| Time | Step | Result | Account-A observation | Notes |
| --- | --- | --- | --- | --- |
| 2026-07-15 00:07 +02:00 | Explicit authority received | PASS | Baseline reported healthy before sequence | User authorized the official device-code two-account test. |
| 2026-07-15 00:07 +02:00 | Janus baseline read with refresh disabled | PASS | Pending | Janus-only store reported connected ChatGPT auth and no pending login; only non-sensitive booleans/state were emitted. |
| 2026-07-15 00:10 +02:00 | Operator observation after baseline read | PASS | Account A unchanged | Same account, quota, settings, and connected state reported visible. |
| 2026-07-15 00:17 +02:00 | Janus-only logout of the pre-existing session | PASS | Pending | Janus returned disconnected, no auth mode, and no pending login. A redacted diagnostic reported that the old Janus token was already invalidated; no credential value was emitted. |
| 2026-07-15 00:20 +02:00 | Operator observation after Janus-only logout | PASS | Account A unchanged | Same account, quota, settings, and connected state reported visible. |
| 2026-07-15 00:28 +02:00 | Fresh official device-code login started | PASS | Observation required after completion | The pinned App Server returned only the approved official verification destination and a transient code. The code was passed in memory to the browser controller, never emitted to chat/log/evidence. The official page requires the operator to sign into Account B before code submission. |
| 2026-07-15 00:34 +02:00 | Official Account-B device authorization gate | NEEDS_INFO | Account A not changed by this step | The official page reported that Codex device-code authorization is disabled for Account B. The attempt was terminated, no matching Janus App Server process remained, and the transient code was removed without emission. |
| 2026-07-15 00:45 +02:00 | Operator enabled Account-B device authorization | PASS | No Account-A action requested | Operator confirmed the provider-owned Codex device-code authorization setting was enabled in the browser for Account B. |
| 2026-07-15 00:48 +02:00 | Fresh official retry started | PASS | Observation required after completion | A new pinned App Server attempt returned the allowlisted official verification destination and a fresh transient code held only in memory. The official page opened and redirected to OpenAI sign-in; Janus remains connecting with login pending and no retry reason. |
| 2026-07-15 01:03 +02:00 | Browser-session mismatch and timeout cleanup | NEEDS_INFO | No Account-A action occurred | The operator was signed into Account B in a normal browser, while the separate Codex in-app OpenAI tab still required sign-in. The pending device attempt expired before that sign-in; Codex removed the transient code, stopped the worker, and reopened the generic official OpenAI login page for Account-B authentication before the next fresh attempt. |
| 2026-07-15 01:11 +02:00 | In-app browser handoff correction | PASS | No Account-A action occurred | Root cause of the invisible tab was local orchestration: `tabs.finalize` had been called with a tab object instead of the required `{ keep: [{ tab, status }] }` options shape, so the tab was omitted and closed. Codex reopened the generic official page, enabled browser visibility, and finalized it with explicit handoff retention. No device-code attempt is active. |
| 2026-07-15 01:15 +02:00 | Fresh official code submitted and login completed | PASS | Observation required now | The operator authenticated Account B in the retained official tab. Codex started a new pinned App Server attempt, validated only the code shape, distributed the memory-only code across the unique official one-time-code fields, and submitted it. The official success page appeared; redacted Janus state became connected with auth mode `chatgpt`, no pending login, and no retry reason. The transient code was cleared and not emitted. |
| 2026-07-15 01:17 +02:00 | Operator observation after fresh Account-B login | PASS | Account A unchanged | Same Account-A identity, quota, settings, and connected state reported visible. |
| 2026-07-15 01:23 +02:00 | Janus lifecycle restart persistence read without refresh | PASS | Observation required now | The original lifecycle exited completely. A new lifecycle against the same isolated Janus home used `account/read` with refresh disabled and returned connected ChatGPT auth, no pending login, and no retry reason. A shutdown-time SQLite panic was reproduced by an import-only Janus backend probe with no App Server or account action, proving it is a pre-existing Vector/Skill-index import side effect rather than an auth/persistence failure. Zero matching Janus App Server processes remained. |
| 2026-07-15 01:24 +02:00 | Operator observation after Janus restart/read | PASS | Account A unchanged | The operator reported Account A unchanged in response to the current post-restart gate. |
| 2026-07-15 01:25 +02:00 | Janus-owned Account-B token refresh | PASS | Observation required now | A new isolated lifecycle executed exactly one `account/read` with refresh enabled. Redacted state remained connected with auth mode `chatgpt`, no pending login, and no retry reason. The previously isolated backend-import panic recurred only at Python process shutdown; zero matching Janus App Server processes remained. |
| 2026-07-15 01:27 +02:00 | Operator observation after Janus-owned refresh | PASS | Account A unchanged | Operator confirmed Account A in Codex remained fully healthy after the Account-B refresh. |
| 2026-07-15 01:30 +02:00 | Final Janus-only Account-B logout | PASS | Final observation required now | Exactly one isolated `account/logout` returned disconnected state with no auth mode, pending login, or retry reason. The known backend-import panic recurred only at Python shutdown; zero matching Janus App Server processes remained. |
| 2026-07-15 01:35 +02:00 | Final operator observation after Janus-only logout | PASS | Account A unchanged | Operator confirmed Account A in Codex remained fully healthy after the final Janus-only Account-B logout. |

## Current Gate

- Live evidence gate: PASS.
- Fresh Account-B login, restart persistence without refresh, owned refresh, Janus-only logout, and every independent Account-A non-interference observation passed.
- Next required action: build the compact audit package and route Task `.1` to independent final audit while production remains default-deny.
- No credential inspection, revocation experiment, Account-A mutation, commit, push, or sync occurred.
- The pre-existing Vector/Skill-index backend-import side effect remains outside this auth task; production stays disabled pending later Task `.5`.

## Risks

Production activation remains unset; later Tasks .2-.5 are parked; pre-existing Vector/Skill-index import-side-effect panic is outside the auth slice.

## Open Issues

Independent final audit remains; no product-code issue is open inside Task .1 evidence.

## Re-Audit Delta

No re-audit delta provided.

## Final Audit Handoff

```text
NEW_CHAT_HANDOFF
NEXT: janus-final-audit
MODEL: 5.6 Sol/high if runtime-supported; otherwise 5.6 Terra/high
PASS: C:\KI\Janus-Projekt\documentation\tasks\TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_AUDIT_PACKAGE.md
ASK: Lade nur dieses Paket im neuen Chat und starte dann `janus-final-audit`.
DROP: dev chat history
```

Use `5.6 Sol/high` when the current Codex run can start it; if Codex reports `gpt-5.6-sol` is unsupported for the active ChatGPT account, use `5.6 Terra/high` and record `SOL_UNAVAILABLE_FOR_CHATGPT_CODEX_ACCOUNT`.

For bounded same-thread re-audits after a local blocker fix, `5.6 Terra/high` is acceptable when the package stays compact and the risk did not escalate.
