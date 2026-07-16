TASK-CHATGPT-DEVICE-CODE-PROVIDER
- Source Spec: `documentation/SPEC/CHATGPT_OFFICIAL_DEVICE_CODE_PROVIDER_REDESIGN_FEATURE_SPEC.md`
- Backlog Item: N/A
- Feature: ChatGPT über offiziellen Codex-Device-Code als separate Janus-Provideroption
- Generated At: 2026-07-16 16:25:45 +02:00

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

### TASK-CHATGPT-DEVICE-CODE-PROVIDER.4 Sicheren App-Server-Chattransport mit Janus-Tools und Datenschutz-Gate anbinden
- Compilation Status: BLOCKED - `UPSTREAM_DYNAMIC_TOOLS_ONLY_MODE_ABSENT`
- Ziel: Die Janus-only Toolgrenze unverändert erhalten und den pro Turn temporären App-Server-Chattransport erst dann implementieren, wenn ein offizieller Runtime-Stand ausschließlich Janus-Client-Tools vor dem Modelldispatch zulässt.
- Scope: Vorgelagertes offizielles Dynamic-Tools-only- oder vollständiges Core-Tool-Allowlist-Gate; nach erfolgreichem Re-entry weiterhin experimenteller Client-Tool-Vertrag mit exakter Laufzeitkompatibilitätsprüfung, App-Server-Thread/Turn/Interrupt-Lifecycle, eigener ChatGPT-Transport und Gateway-Silo, Janus-Toolausführung, redigierter Janus-Kontext, Text-Streaming, Datenschutz-Gate, Abbruch und Fehlerisolation. Kein Codex-eigenes Tool einschließlich `update_plan`, keine Janus-gepatchte oder geforkte Runtime, keine dauerhafte Codex-Historie, kein degradierter Textmodus, kein API-Key-Fallback und keine Produktionsaktivierung vor Task `.5`.
- Files: `backend/llm_providers/codex_app_server.py`, `backend/llm_providers/transports/codex_app_server.py` (neu), `backend/llm_providers/chatgpt/gateway.py` (neu), `backend/llm_providers/runtime_llm.py`, `backend/services/llm_gateway.py`, `backend/services/chat_orchestrator.py`, `backend/data/schemas.py`, `frontend/index.html`, `frontend/js/chat.js`, `frontend/js/beta-privacy-notice.js`, `documentation/beta/BETA_PRIVACY_NOTICE.md`, `backend/tests/test_codex_app_server.py`, `backend/tests/test_context_privacy_externalization_boundary.py`, `backend/tests/test_provider_parity.py`, `backend/tests/test_provider_auth_fallback.py`, `tests/e2e/codex-connection-settings.spec.js`
- Steps:
  1. Task `.4` blockiert lassen, solange kein offizieller Runtime-Stand einen nachweisbaren Dynamic-Tools-only-Modus oder eine vollständige Core-Tool-Allowlist bereitstellt. Ein Versionsupdate, experimentelles Feld, Promptverbot, Read-only-Sandbox, Approval-Ablehnung oder Eventfilterung genügt nicht.
  2. Für einen künftigen exakten offiziellen Runtime-Stand account-frei und ausführbar belegen, dass vor dem Modelldispatch ausschließlich Janus-Client-Tools angeboten werden und weder `update_plan` noch eine andere Codex-native Aktionsoberfläche verbleibt.
  3. Erst nach dieser Evidenz einen frischen `janus-preimplementation-check` ausführen. Nur dessen grünes Ergebnis darf die nachfolgenden Implementierungsschritte freigeben; bis dahin endet der Task an diesem Gate.
  4. Nach grüner Re-entry-Freigabe die App-Server-Laufzeit zusätzlich gegen den erwarteten Thread-/Turn-, Client-Tool-Call-, Client-Tool-Response- und Interrupt-Vertrag prüfen; fehlende, veränderte oder nicht prüfbare Unterstützung macht ChatGPT vollständig nicht verfügbar.
  5. Den App-Server-Client um einen pro Janus-Turn neu erzeugten temporären Gesprächskontext, Text-Streaming, Turn-Abbruch und bereinigte Protokollfehler erweitern; keine Codex-Thread-ID oder zweite Historie persistieren.
  6. Einen ChatGPT-Transportadapter und ein eigenes Gateway-Silo in die bestehende Runtime-/Gateway-Auflösung einbinden. Die produktive Auflösung bleibt bis Task `.5` default-deny; Task `.4` darf den Pfad nur über explizit injizierte Testevidenz aktivieren.
  7. Ausschließlich die bereits von Janus ausgewählten und erlaubten Tooldefinitionen als Client-Tools anbieten. Client-Tool-Aufrufe nur über den bestehenden `ToolExecutor` und dessen Berechtigungs-/Bestätigungsregeln ausführen, unbekannte oder nicht erlaubte Tools fail-closed ablehnen und nur redigierte Ergebnisse zurückgeben.
  8. Nur Agent-Text und Janus-kontrollierte Toolstatus in das vorhandene Janus-Streaming übersetzen. Jede Codex-native Aktionsanforderung unterbricht den aktuellen Turn mit nicht-sensitiver Meldung und darf weder ausgeführt noch als Erfolg behandelt werden.
  9. Für jeden Turn ausschließlich den benötigten, von Janus zusammengestellten und redigierten Verlauf übertragen. Vor der ersten Externalisierung die aktuelle bestätigte Datenschutzinformations-Version auch am Backend-Vertrag prüfen; ohne gültigen Nachweis wird kein Thread/Turn gestartet und nichts übertragen.
  10. Die Datenschutzinformation und ihre Version so aktualisieren, dass aktuelle Nachricht, benötigter Verlauf, Janus-/Skill-Anweisungen sowie erforderliche Tool-Eingaben und -Ergebnisse ausdrücklich genannt werden. Ablehnung oder Schließen erhält Entwurf und Auswahl ohne Versand.
  11. Nutzerabbruch in einen App-Server-Turn-Abbruch übersetzen und Transport-, Vertrags-, Tool-, Authentifizierungs- und Modellfehler auf den aktuellen ChatGPT-Turn begrenzen. Keine automatische Wiederholung, doppelte Übertragung, Providerumschaltung oder Veränderung einer anderen Verbindung.
- Acceptance Criteria:
  - Solange der exakte offizielle Runtime-Stand keinen nachweisbaren Dynamic-Tools-only-Modus oder keine vollständige Core-Tool-Allowlist bietet, bleibt Task `.4` blockiert und es beginnt keine Produktimplementierung.
  - Ein künftiger Re-entry ist nur zulässig, wenn account-freie ausführbare Evidenz für den exakten offiziellen Runtime-Stand belegt, dass ausschließlich Janus-Client-Tools vor dem Modelldispatch angeboten werden und kein `update_plan` oder anderes Codex-natives Aktionstool verbleibt.
  - Auch bei vorhandener Upstream-Evidenz beginnt keine Implementierung, bevor ein frischer `janus-preimplementation-check` PASS meldet.
  - Eine Janus-gepatchte oder geforkte Codex-Runtime, die Zulassung von `update_plan`, eine abgeschwächte Janus-only Grenze oder ein degradierter Ersatzpfad erfüllen das Re-entry-Gate nicht.
  - ChatGPT löst nur bei gültiger Janus-Verbindung, aktuell verifiziertem Modell, gültiger Datenschutzbestätigung, exakt kompatiblem Client-Tool-Vertrag und nachgewiesener harter Native-Aktionssperre in den testgebundenen Transport auf.
  - Fehlende, veränderte oder nicht prüfbare experimentelle Client-Tool-Unterstützung hält ChatGPT vollständig nicht nutzbar; es gibt keinen reduzierten textbasierten Ersatzmodus.
  - Jeder ChatGPT-Turn verwendet einen neuen temporären App-Server-Gesprächskontext und hinterlässt keine persistierte Codex-Thread-ID oder parallele Codex-Historie.
  - Der übertragene Kontext entspricht ausschließlich dem für denselben Turn benötigten, redigierten Janus-Kontext; der aktive Provider bleibt sichtbar.
  - ChatGPT erhält nur von Janus erlaubte Tooldefinitionen. Tool-Aufrufe laufen durch denselben `ToolExecutor` und dieselben Berechtigungs-/Bestätigungsregeln wie bei API-Key-Providern.
  - Codex-eigene Shell-, Datei-, Approval-, MCP-, App-, Web-, Subagenten- oder sonstige Agentenaktionen werden nicht ausgeführt. Eine Anforderung beendet nur den aktuellen Turn fail-closed und wird nicht als Erfolg behandelt.
  - Ohne gültige aktuelle Datenschutzbestätigung startet kein App-Server-Thread oder -Turn und es wird kein Chat-, Kontext-, Skill- oder Toolinhalt extern übertragen.
  - Die Datenschutzinformation nennt aktuelle Nachricht, benötigten Verlauf, Janus-/Skill-Anweisungen sowie erforderliche Tool-Eingaben und -Ergebnisse; unveränderte Versionen werden wiederverwendet und wesentliche Änderungen verlangen erneut Zustimmung.
  - Ablehnung, Schließen, Nutzerabbruch oder Transportfehler erhalten Janus-Verlauf, Entwurf, Providerwahl und Anmeldung; es gibt keine automatische Wiederholung, doppelte Übertragung oder API-Key-Provider-Fallback.
  - Der ChatGPT-Pfad bleibt nach Task `.4` produktiv default-deny. Nur explizit injizierte Testevidenz darf ihn in gebundenen Tests aktivieren; Task `.5` bleibt das einzige Produktions-Aktivierungsgate.
  - Bestehende API-Key-Provider, ihre Modelle, Zugangsdaten, Toolregeln und Providerwechsel verhalten sich unverändert.
- Tests:
  - Upstream-Re-entry-Evidenz für den exakt gebundenen offiziellen Runtime-Stand: account-freier ausführbarer Nachweis, dass ausschließlich Janus-Client-Tools angeboten werden und `update_plan` sowie alle anderen Codex-nativen Aktionsoberflächen fehlen; ohne PASS keine weiteren Task-Tests und keine Implementierung.
  - App-Server-Vertragstests für kompatiblen und fehlenden/veränderten Client-Tool-Vertrag, temporären Thread, Textdelta, Client-Tool-Call/Response, unerwartete Codex-Aktion, Turn-Abbruch, Protokollfehler, Redaktion und produktiven Default-Deny in `backend/tests/test_codex_app_server.py`.
  - Privacy-Externalization-Tests für Backend-vor-Thread-Gate, Erstbestätigung, Wiederverwendung, Versionsänderung, Ablehnung/Schließen und expliziten Offenlegungstext in `backend/tests/test_context_privacy_externalization_boundary.py`.
  - Provider-Paritäts- und Tooltests für Janus-Tooldefinitionen, bestehende `ToolExecutor`-Berechtigungen, redigierte Ergebnisse, unbekannte Tools, Text-Streaming und Native-Aktionssperre in `backend/tests/test_provider_parity.py`.
  - Auth-/Fallback-Regression für keine API-Key-Abhängigkeit, keine automatische Umschaltung und unveränderte OpenAI-/Gemini-/Ollama-Zugangsdaten in `backend/tests/test_provider_auth_fallback.py`.
  - Headed E2E für Providerwechsel im bestehenden Chat, Kontextfortsetzung, Privacy-Ablehnung/-Bestätigung/-Versionswechsel, sichtbaren Provider, Janus-Toolstatus, Abbruch, Transportfehler und erhaltenen Entwurf in `tests/e2e/codex-connection-settings.spec.js`.
  - Precheck-Evidenz für die offiziell unterstützte harte Abschaltung sämtlicher Codex-nativer Aktionsflächen; bei fehlendem ausführbarem Nachweis bleibt der Task blockiert.
  - Python-/JavaScript-Syntaxprüfungen, fokussierte Tests und scoped `git diff --check`; keine Konto-, Nachrichten- oder Produktionsaktion in automatisierten Gates.
- Model: 5.6 Sol
- Reason: Sicherheitskritische experimentelle App-Server-Integration bleibt wegen `UPSTREAM_DYNAMIC_TOOLS_ONLY_MODE_ABSENT` blockiert. 5.6 Sol/high ist für einen künftigen Re-entry vorgesehen; 5.6 Terra/high nur als dokumentierter Fallback, falls Sol nicht verfügbar ist.

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

### TASK-CHATGPT-DEVICE-CODE-PROVIDER.4

- **Status:** BLOCKED
- **Failure Code:** `UPSTREAM_DYNAMIC_TOOLS_ONLY_MODE_ABSENT`
- **Decision At:** 2026-07-16
- **Locked Choice:** Auf offiziellen Dynamic-Tools-only- oder vollständigen Core-Tool-Allowlist-Support warten.
- **Rejected Alternatives:** Keine Janus-gepatchte oder geforkte Runtime, keine Zulassung von `update_plan`, keine Abschwächung der Janus-only Grenze und kein degradierter Text-, Tool- oder Provider-Fallback.
- **Re-entry Gate:** Account-freie ausführbare Evidenz gegen den exakten offiziellen Runtime-Stand und danach ein frischer grüner `janus-preimplementation-check`.
- **Production State:** DEFAULT-DENY; Task `.5` bleibt der einzige spätere Produktions-Aktivierungsschritt.
- **Evidence:** `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.3_final_audit.md`; `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.3_AUDIT_PACKAGE.md`; `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.3_execution_result.md`
- **Remaining Tasks:** `.4` and `.5` remain open. The parent Feature Spec is not DONE.
