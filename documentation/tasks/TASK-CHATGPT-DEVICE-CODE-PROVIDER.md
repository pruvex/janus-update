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
- Files: `backend/llm_providers/codex_app_server.py`, `backend/api/routers/system.py`, `backend/services/model_catalog.py`, `frontend/index.html`, `frontend/js/app.js`, `frontend/js/chat.js`, `frontend/js/settings.js`, `backend/tests/test_codex_connection_settings_api.py`, `backend/tests/test_model_hierarchy_single_source.py`, `tests/e2e/codex-connection-settings.spec.js`
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
- Scope: Vollständige Regression, reale Nichtbeeinflussungssequenz, evidenzgebundene Produktionsfreigabe und Rückfall auf deaktiviert bei jeder Abweichung; keine Bereinigung alter Test-Credentials und kein Release/Publish.
- Files: `backend/llm_providers/codex_app_server.py`, `backend/tests/test_codex_app_server.py`, `backend/tests/test_codex_connection_settings_api.py`, `backend/tests/test_provider_parity.py`, `tests/electron/codex-runtime-boundary.test.cjs`, `tests/e2e/codex-connection-settings.spec.js`, `documentation/test-results/TASK-CHATGPT-DEVICE-CODE-PROVIDER.5_release_evidence.md`
- Steps:
  1. Die automatisierten Lifecycle-, Settings-, Modell-, Privacy-, Provider- und Redaktionsgates als gemeinsame Release-Evidenz ausführen.
  2. Mit zwei unterschiedlichen Konten die Sequenz Login, Neustart, Modellerneuerung, Kontowechsel, Chat-Nutzung und Janus-Logout kontrolliert prüfen.
  3. Nach jedem Janus-Schritt bestätigen, dass Konto, Kontingent, Einstellungen und Sitzungszustand des separaten Codex-Clients unverändert bleiben.
  4. Die Produktionsfreigabe ausschließlich an die exakt dokumentierte bestandene Evidenz binden.
  5. Bei fehlender, veralteter oder fehlgeschlagener Evidenz den Default-Deny-Zustand erhalten und keine Freigabekennung setzen.
  6. API-Key-Anbieter und bestehende Providerwechsel im finalen Regressionstest unverändert nachweisen.
- Acceptance Criteria:
  - Alle gebundenen automatisierten Tests sind reproduzierbar grün.
  - Der vollständige reale Zwei-Konten-Test ist für jeden spezifizierten Schritt bestanden und enthält keine sensitiven Werte.
  - Der separate Codex-Client bleibt während Login, Neustart, Erneuerung, Kontowechsel, Chat-Nutzung und Janus-Logout vollständig unverändert.
  - Produktion wird nur bei exakt passender bestandener Evidenz freigegeben.
  - Jede fehlende oder fehlerhafte Evidenz hält ChatGPT in Janus fail-closed deaktiviert.
  - API-Key-Anbieter und bestehende Providerfunktionen bleiben unverändert.
- Tests:
  - Vollständige fokussierte Python-, Electron- und headed E2E-Matrix der Tasks `.1` bis `.4`.
  - Kontrollierter manueller Zwei-Konten-End-to-End-Test mit redaktierter Evidence-Datei.
  - Wiederanlaufprüfung nach Janus- und Codex-Neustart.
  - Scoped und gesamter `git diff --check` für den Feature-Slice.
- Model: 5.6 Sol
- Reason: Finales Security-/Privacy-/Release-Gate mit externer Kontoevidenz; bei nicht verfügbarem Sol dokumentierter Fallback auf 5.6 Terra/high.

## TASK COMPLETION METADATA

### TASK-CHATGPT-DEVICE-CODE-PROVIDER.1

- **Status:** DONE
- **Final Audit:** PASS
- **Completed At:** 2026-07-15
- **Validation:** Backend lifecycle `22 passed`; Electron runtime-boundary `9 passed`; headed Settings regression `4 passed`; Python compile and scoped diff check PASS; controlled two-account login/restart/refresh/logout evidence PASS.
- **Security Boundary:** Janus-only absolute `CODEX_HOME`, keyring-backed encrypted persistence, no credential import or fallback, redacted transient values, and no observed impact on the parallel Codex account.
- **Production State:** DEFAULT-DENY; activation remains reserved for Task `.5`.
- **Evidence:** `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_final_audit.md`; `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_AUDIT_PACKAGE.md`; `documentation/test-results/TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_isolation_evidence.md`
- **Remaining Tasks:** `.4` and `.5` remain open; Task `.3` is completed separately.

### TASK-CHATGPT-DEVICE-CODE-PROVIDER.2

- **Status:** DONE
- **Final Audit:** PASS
- **Completed At:** 2026-07-15
- **Validation:** API Settings contract `11 passed`; headed mocked Settings E2E `8 passed`; Python/JavaScript syntax and scoped diff checks PASS; passive account-free Settings observation PASS.
- **Security Boundary:** Device-code values remain transient and redacted; unavailable isolated persistence is visibly disabled with no fallback; replacement is atomic; API-key providers remain unaffected.
- **Production State:** DEFAULT-DENY; chat transport and production activation remain reserved for Tasks `.4` and `.5`.
- **Evidence:** `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.2_final_audit.md`; `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.2_AUDIT_PACKAGE.md`; `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.2_execution_result.md`
- **Separate Prerequisite:** `BACKLOG-131` Settings navigation remains independently governed and is not closed by this task.

### TASK-CHATGPT-DEVICE-CODE-PROVIDER.3

- **Status:** DONE
- **Final Audit:** PASS
- **Completed At:** 2026-07-16
- **Validation:** Backend/hierarchy `17 passed`; focused headed stale-start and verified/unavailable scenarios `1 passed` each; full headed Settings E2E `10 passed`; Python compile, JavaScript syntax, and scoped diff checks PASS; production ChatGPT transport/service-provider default-deny probe PASS.
- **Security Boundary:** Provider/model eligibility derives only from the active Janus-owned current `model/list` verification; empty, failed, expired, absent, or stale verification remains fail-closed; status and UI errors stay non-sensitive.
- **Provider Safety:** Existing API-key providers, models, Settings lifecycle, and hierarchy remain unaffected; the E2E runner isolates `GET`/`PUT /api/last-used-model`; stale persisted ChatGPT selection self-heals to an existing provider/model.
- **Production State:** DEFAULT-DENY; Task `.4` owns ChatGPT transport/context/privacy and Task `.5` owns evidence-bound production activation.
- **Evidence:** `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.3_final_audit.md`; `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.3_AUDIT_PACKAGE.md`; `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.3_execution_result.md`
- **Remaining Tasks:** `.4` and `.5` remain open. The parent Feature Spec is not DONE.
