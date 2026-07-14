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
- Status: `DONE (task-scoped final audit PASS)`
- Final Audit: `documentation/tasks/TASK-CHATGPT-CODEX.1_final_audit.md`
- Audit Package: `documentation/tasks/TASK-CHATGPT-CODEX.1_AUDIT_PACKAGE.md`
- Validation: runtime/LLM/help `34 passed`; Electron boundary `7 passed`; headed capability E2E `2 passed`; build PASS; manual Janus PASS.
- Boundary: This closes only `.1`. Tasks `.2` through `.4` remain parked; no ChatGPT settings UI, picker, transport, or account workflow is claimed as delivered.

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
