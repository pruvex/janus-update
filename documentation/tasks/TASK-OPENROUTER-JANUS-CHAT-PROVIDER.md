TASK-OPENROUTER-JANUS-CHAT-PROVIDER
- Source Spec: `documentation/SPEC/Spec Done/OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md`
- Backlog Item: N/A
- Feature: OpenRouter als Janus-Chatprovider mit zertifizierten Modellen
- Generated At: 2026-07-16 18:31:00 +02:00

## Implementation Status

- Overall Feature: `DONE` (`6/6` tasks final-audit PASS or PASS WITH FIXES)
- `TASK-OPENROUTER-JANUS-CHAT-PROVIDER.1`: `DONE` - Final Audit PASS on 2026-07-16
- `TASK-OPENROUTER-JANUS-CHAT-PROVIDER.2`: `DONE` - Final Audit PASS on 2026-07-17
- `TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3`: `DONE` - Final Audit PASS on 2026-07-17
- `TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4`: `DONE` - Final Audit PASS on 2026-07-17
- `TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5`: `DONE` - Final Audit PASS WITH FIXES on 2026-07-17
- `TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6`: `DONE` - Final Audit PASS WITH FIXES on 2026-07-18; documentation-update activated four exact certified models
- Production State: `ENABLED` for the four audit-approved OpenRouter models when a `VALID` OpenRouter key is present
- Spec path: `documentation/SPEC/Spec Done/OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md`
- Task `.1` Evidence: `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.1_final_audit.md`, `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.1_AUDIT_PACKAGE.md`
- Task `.2` Evidence: `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.2_final_audit.md`, `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.2_AUDIT_PACKAGE.md`
- Task `.3` Evidence: `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3_FINAL_AUDIT.md`, `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3_AUDIT_PACKAGE.md`
- Task `.4` Evidence: `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4_FINAL_AUDIT.md`, `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4_AUDIT_PACKAGE.md`
- Task `.5` Evidence: `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5_FINAL_AUDIT.md`, `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5_AUDIT_PACKAGE.md`
- Task `.6` Evidence: `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6_FINAL_AUDIT.md`, `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6_AUDIT_PACKAGE.md`, `documentation/test-results/TEST-RUN-2026-07-17-008_results.md`, `documentation/test-results/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6_certification_evidence.md`

## Generated Tasks

### TASK-OPENROUTER-JANUS-CHAT-PROVIDER.1 Autoritativen Zertifizierungsdatensatz und Katalog-Gate bereitstellen
- Ziel: Exakt versionierte OpenRouter-Modelle nur dann als normale Janus-Chatmodelle veröffentlichen, wenn der geprüfte Janus-Update-Stand ihre vollständige Zertifizierung eindeutig autorisiert.
- Scope: Versionierter Zertifizierungsdatensatz, Lade-/Validierungslogik, Bindung aus Modell-ID, konkreter Modellversion und Batterieversion, fail-closed Invalidierung und gefilterte Katalogausgabe; keine Key-Prüfung, Chatübertragung, UI-Auswahl oder Live-Zertifizierung.
- Files: `backend/config/model_catalog.json`, `backend/config/openrouter_certified_models.json` (neu), `backend/services/model_catalog.py`, `backend/utils/config_loader.py`, `backend/api/routers/system.py`, `backend/tests/test_model_hierarchy_single_source.py`, `backend/tests/test_openrouter_certification_registry.py` (neu)
- Steps:
  1. Einen getrennten OpenRouter-Zertifizierungsdatensatz anlegen und ihn über den vorhandenen Katalogloader in die gefilterte Katalogausgabe einbinden, ohne einen Runtime-Katalogimport einzuführen.
  2. Pro Eintrag exakt Modell-ID, konkrete Modellversion, Batterieversion, bestandenen Status sowie den Nachweis vollständig bestandener Pflicht-Test- und Audit-Evidenz binden.
  3. Die Laufzeitauflösung fail-closed gestalten: fehlender oder unvollständiger Datensatz, nicht bestandener Status und jede Abweichung eines Bindungswerts ergeben `nicht zertifiziert`.
  4. Die normale Katalogausgabe auf vollständig zertifizierte OpenRouter-Einträge begrenzen; Kandidaten und durchgefallene, veraltete, uneindeutige oder `latest`-basierte IDs bleiben unsichtbar.
  5. Bestehende OpenAI-, Gemini-, Ollama- und ChatGPT-Katalogeinträge sowie deren Auswahlverhalten unverändert lassen.
- Acceptance Criteria:
  - Die Laufzeit besitzt genau eine aus einem geprüften Janus-Update geladene Zertifizierungsautorität für OpenRouter-Modelle.
  - Ein sichtbarer OpenRouter-Eintrag bindet exakt Modell-ID, konkrete Modellversion und Batterieversion an vollständig bestandene Pflicht-Test- und Audit-Evidenz.
  - Jede fehlende oder abweichende Bindung entfernt das Modell fail-closed aus der normalen Katalogausgabe.
  - Kandidaten, durchgefallene Modelle, uneindeutige IDs und `latest`-Aliase erscheinen nicht im normalen Chatkatalog.
  - Die Katalogausgabe bestehender Provider bleibt unverändert.
- Tests:
  - Unit-Tests für gültige Bindung, fehlende Evidenz, nicht bestandenen Status sowie Abweichungen von Modell-ID, Modellversion und Batterieversion.
  - API-Vertragstest, dass nur zertifizierte OpenRouter-Modelle in `/api/models/catalog` erscheinen.
  - Regression für bestehende Provider- und Hierarchie-Katalogverträge.
  - JSON-/Python-Syntaxprüfung und scoped `git diff --check`.
- Model: 5.6 Terra
- Reason: Deterministische Konfigurations- und Katalogarbeit mit sicherheitsrelevantem fail-closed Gate; Ausführung mit hoher Reasoning-Stufe.

### TASK-OPENROUTER-JANUS-CHAT-PROVIDER.2 Isolierten OpenRouter-Key-Lifecycle mit binären Zuständen implementieren
- Ziel: Einen OpenRouter-Key im eigenen sicheren Keyring-Namensraum verwalten und ausschließlich nach inhaltsfreier authentifizierter Prüfung als chatberechtigt markieren.
- Scope: Speichern, Ersetzen, OpenRouter-exklusives Löschen, Status `VALID`/`INVALID`/`UNVERIFIED`, inhaltsfreie Key-Statusprüfung, Fehlerredaktion und unveränderte Credentials anderer Provider; keine Chatübertragung, Modellauswahl oder Telemetrie.
- Files: `backend/api/routers/system.py`, `backend/data/schemas.py`, `frontend/index.html`, `frontend/js/settings.js`, `frontend/css/settings.css`, `backend/tests/test_openrouter_key_settings_api.py` (neu), `tests/e2e/openrouter-settings.spec.js` (neu)
- Steps:
  1. OpenRouter in den bestehenden Key-CRUD-Vertrag aufnehmen und den Key ausschließlich unter dem OpenRouter-Namensraum im vorhandenen sicheren Keyring speichern.
  2. Nach Speichern oder Ersetzen eine Prüfung ohne Chatinhalt gegen den authentifizierten OpenRouter-Key-Status ausführen.
  3. Nur erfolgreiche Authentifizierung als `VALID`, ausdrückliche Authentifizierungsablehnung als `INVALID` und technisch nicht abgeschlossene Prüfung als `UNVERIFIED` abbilden.
  4. `INVALID` und `UNVERIFIED` fail-closed von der Chatberechtigung ausschließen, ohne den gespeicherten Key oder die sichtbare Provider-/Modellauswahl automatisch zu löschen.
  5. Eine vorübergehende Provider-, Netzwerk- oder Modellstörung nicht als Key-Invalidierung behandeln.
  6. Status, Fehler, Logs und Settings-Antworten auf nicht-sensitive Werte begrenzen; kein Key darf zurückgegeben, protokolliert oder in Evidenz geschrieben werden.
- Acceptance Criteria:
  - OpenRouter-Keyoperationen lesen oder verändern ausschließlich den OpenRouter-Keyring-Namensraum.
  - Nur ein erfolgreich authentifizierter Status setzt `VALID` und kann die spätere Chatvoraussetzung erfüllen.
  - Authentifizierungsablehnung setzt `INVALID`; technische Nichtprüfbarkeit setzt `UNVERIFIED`; beide Zustände sperren Senden fail-closed.
  - Temporäre Netzwerk-, Provider- oder Modellfehler invalidieren einen zuvor bestätigten Key nicht automatisch.
  - Löschen oder Ersetzen des OpenRouter-Keys verändert keine bestehenden Provider-Credentials.
  - Weder API noch UI, Logs oder Tests offenbaren den Key.
- Tests:
  - Backend-Vertragstests für Speichern, Ersetzen, Löschen, erfolgreiche Prüfung, Auth-Ablehnung, Timeout/Netzwerkfehler und Credential-Isolation.
  - Settings-E2E für maskierte Keydarstellung und sichtbare, nicht-sensitive Zustände `VALID`, `INVALID` und `UNVERIFIED`.
  - Regression gegen die bestehenden API-Key-Einstellungen und den ChatGPT-Verbindungsbereich.
  - Python-/JavaScript-Syntaxprüfung und scoped `git diff --check`.
- Model: 5.6 Terra
- Reason: Credential- und Netzwerkstatusgrenze auf einer bestehenden Settings-Fläche; Ausführung mit hoher Reasoning-Stufe und fail-closed Tests.

### TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3 Eigenen fail-closed OpenRouter-Chatpfad mit voller Janus-Toolparität anbinden
- Ziel: Zertifizierte OpenRouter-Modelle über den bestehenden OpenAI-kompatiblen Transport nutzen, während Janus Redaction, Kontext, Skills, Tools, Berechtigungen und Bestätigungen vollständig kontrolliert.
- Scope: Eigenes OpenRouter-Provider-Silo, OpenAI-kompatibler Transport mit OpenRouter-Basis-URL, exakte Modellidentität, vollständiger Janus-Toolloop, aktuelle-Turn-Fehlerisolation und striktes Verbot von automatischem Janus-Retry, doppelter Übertragung, Modell- oder Provider-Fallback; keine UI, Registry-Pflege oder DeepDive-Darstellung.
- Files: `backend/llm_providers/openrouter/__init__.py` (neu), `backend/llm_providers/openrouter/service.py` (neu), `backend/llm_providers/openrouter/gateway.py` (neu), `backend/llm_providers/runtime_llm.py`, `backend/llm_providers/transports/openai_compat.py`, `backend/llm_providers/shared/tool_call_adapter.py`, `backend/llm_providers/shared/response_postprocessors.py`, `backend/services/llm_gateway.py`, `backend/services/chat_orchestrator.py`, `backend/tests/test_openrouter_provider.py` (neu), `backend/tests/test_provider_parity.py`, `backend/tests/test_provider_auth_fallback.py`
- Steps:
  1. Das OpenRouter-Silo über die vorhandene OpenAI-kompatible Transportgrenze anbinden, ohne den nativen OpenAI-Provider oder dessen Credential zu verwenden.
  2. Vor jeder Übertragung `VALID`-Key, sichtbaren Zertifizierungsdatensatz und exakte ausgewählte Modell-ID prüfen; bei fehlender Voraussetzung nichts übertragen.
  3. Dieselbe Janus-Redaction, denselben notwendigen Gesprächskontext, dieselben ausgewählten Skill-/Tooldefinitionen und denselben `ToolExecutor` mit bestehenden Berechtigungs- und Bestätigungsregeln verwenden.
  4. Provider-, Modell-, Authentifizierungs- und Transportfehler auf den aktuellen Turn begrenzen und alle Janus-seitigen automatischen Retries sowie Modell-/Provider-Fallbacks für OpenRouter ausschließen.
  5. Streaming- oder Fehlerpfade so abschließen, dass kein Turn doppelt übertragen wird und kein Teilerfolg fälschlich als vollständiger Erfolg erscheint.
  6. `response.model` exakt gegen die bewusst ausgewählte Modell-ID prüfen; jede Abweichung als fail-closed Modellfehler behandeln.
- Acceptance Criteria:
  - OpenRouter nutzt ausschließlich den eigenen Key und die OpenRouter-Basis-URL; kein bestehender Provider-Key ist Ersatz oder Fallback.
  - Ohne `VALID`-Key und sichtbaren exakten Zertifizierungsdatensatz erfolgt keine externe Übertragung.
  - Ein zertifiziertes OpenRouter-Modell erhält dieselben Janus-kontrollierten Redaction-, Kontext-, Skill-, Tool-, Berechtigungs- und Bestätigungsgrenzen wie andere externe API-Key-Provider.
  - Jeder Provider-, Modell-, Authentifizierungs- oder Transportfehler beendet nur den aktuellen Turn ohne Janus-Retry, Doppelübertragung oder Modell-/Providerwechsel.
  - Eine Abweichung von `response.model` beendet den Turn als Modellfehler.
  - Bestehende OpenAI-, Gemini-, Ollama- und ChatGPT-Pfade bleiben unverändert.
- Tests:
  - Mock-Provider-Tests für Basis-URL, Credential-Isolation, exakte Modellidentität, Text- und Toolloop-Antworten.
  - Negativtests für fehlende Eligibility, Authfehler, Providerfehler, Modellabweichung, Streamabbruch, kein Retry, keine doppelte Übertragung und keinen Fallback.
  - Provider-Paritätstests für kanonische Tools, `ToolExecutor`, Berechtigungen, Bestätigungen und redigierten Kontext.
  - Regression für alle bestehenden Provider-Silos sowie Python-Syntaxprüfung und scoped `git diff --check`.
- Model: 5.6 Sol
- Reason: Sicherheits- und architekturkritische externe Providergrenze mit Toolparität, Übertragungsisolation und strengem No-Retry/No-Fallback-Vertrag.

### TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4 Provider-/Modellauswahl mit deaktivierter Zustandserhaltung integrieren
- Ziel: OpenRouter und ausschließlich seine sichtbaren zertifizierten Modelle in die bestehenden Dropdowns integrieren und ungültig gewordene Auswahlen sichtbar, gespeichert und deaktiviert erhalten.
- Scope: Provider-/Modell-Dropdowns, Eligibility-Anzeige, manuelle Auswahl, gespeicherter letzter Zustand, bewusste Neuwahl und Datenschutzinformation; keine Key-Netzwerklogik, Providerimplementierung oder Telemetriepersistenz.
- Files: `frontend/index.html`, `frontend/js/app.js`, `frontend/js/settings.js`, `frontend/js/chat.js`, `frontend/js/chat-manager.js`, `frontend/js/window-state.js`, `frontend/css/settings.css`, `backend/main.py`, `backend/api/routers/system.py`, `backend/data/schemas.py`, `tests/functional/chat-core.spec.js`, `tests/e2e/openrouter-settings.spec.js`
- Steps:
  1. OpenRouter in das bestehende Provider-Dropdown und zertifizierte OpenRouter-Modelle in das bestehende Modell-Dropdown integrieren.
  2. OpenRouter im Chat nur bei `VALID`-Key und mindestens einem sichtbaren zertifizierten Modell auswählbar machen; die Keyverwaltung in den Einstellungen bleibt unabhängig davon sichtbar.
  3. Provider und konkretes Modell ausschließlich durch bewusste Nutzeraktion auswählen; keine automatische OpenRouter-Modellwahl und kein MOA-Routing zwischen OpenRouter-Modellen einführen.
  4. Wird der Key ungültig oder das gewählte Modell nicht verfügbar beziehungsweise nicht zertifiziert, die gespeicherte Auswahl sichtbar beibehalten, aber Senden und Auswahlberechtigung deaktivieren.
  5. Dieselbe Auswahl automatisch erst dann wieder nutzbar machen, wenn alle ursprünglichen Voraussetzungen erneut erfüllt sind; alternativ eine bewusste gültige Neuwahl zulassen.
  6. Die Datenschutzinformation ausdrücklich um die mögliche Übermittlung über OpenRouter an den ausgewählten Modellanbieter ergänzen.
- Acceptance Criteria:
  - OpenRouter erscheint im bestehenden Chat-Dropdown nur als nutzbare Option, wenn Key und mindestens ein zertifiziertes Modell gültig sind.
  - Das Modell-Dropdown zeigt nur sichtbare zertifizierte exakte IDs und keine Kandidaten, `latest`-Aliase oder uneindeutigen Modelle.
  - Eine ungültig gewordene Auswahl bleibt nach UI-Neurendering und Janus-Neustart sichtbar gespeichert, aber deaktiviert.
  - Janus löscht die Auswahl nicht automatisch und wählt weder ein anderes OpenRouter-Modell noch einen anderen Provider.
  - Nach wiederhergestellter Gültigkeit wird dieselbe Auswahl wieder nutzbar; eine bewusste andere gültige Auswahl funktioniert ebenfalls.
  - Bestehende Provider-/Modelloptionen, Chatverlauf und Window-Overrides bleiben unverändert.
- Tests:
  - Frontend- und headed E2E-Szenarien für gültige Auswahl, fehlenden Key, leeren zertifizierten Katalog, Key-Invalidierung, Modellverlust, Neustartpersistenz, Wiederfreigabe und bewusste Neuwahl.
  - Regression für bestehende Sidebar-, Window-Header- und letzte-Modell-Persistenz.
  - Sichtprüfung der Datenschutzinformation und Regression der bestehenden Settings-Navigation.
  - JavaScript-Syntaxprüfung und scoped `git diff --check`.
- Model: 5.6 Terra
- Reason: Mehrflächige UI-/Persistenzintegration mit klaren binären Zuständen auf vorhandenen Oberflächen; Ausführung mit hoher Reasoning-Stufe.

### TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5 Autoritative OpenRouter-Telemetrie in DeepDive persistieren und anzeigen
- Ziel: Tatsächlich von OpenRouter gelieferte Turn-, Modell-, Token- und Kostenwerte feldgenau speichern und im bestehenden DeepDive ohne Schätzung oder lokale Währungsumrechnung darstellen.
- Scope: Response-Normalisierung, nullable Telemetriefelder, Turnattribution, Datenbankmigration, DeepDive-Aggregation und -Anzeige für Modell-ID, Prompt-, Completion-, Gesamt-, Cache-, Cache-Write- und Reasoning-Tokens, belastete OpenRouter-Credits und Upstream-Inferenzkosten; keine Preisberechnung oder lokale Kostenschätzung.
- Files: `backend/llm_providers/openrouter/service.py`, `backend/llm_providers/shared/response_postprocessors.py`, `backend/services/chat_orchestrator.py`, `backend/services/orchestrator/execution_engine.py`, `backend/services/cost_service.py`, `backend/data/models.py`, `backend/data/database.py`, `backend/data/crud.py`, `frontend/js/cost-visualizer.js`, `backend/tests/test_cost_token_tracking_completeness.py`, `backend/tests/test_openrouter_telemetry.py` (neu), `tests/functional/chat-core.spec.js`
- Steps:
  1. Die autoritativen OpenRouter-Felder `response.model`, `usage.prompt_tokens`, `usage.completion_tokens`, `usage.total_tokens`, Cache-/Cache-Write-/Reasoning-Details, `usage.cost` und `usage.cost_details.upstream_inference_cost` ohne lokale Neuberechnung normalisieren.
  2. Die Kostenpersistenz so erweitern, dass jedes Feld pro Janus-Turn, Provider und konkretem Modell attribuiert und seine Verfügbarkeit von einem echten Zahlenwert `0` unterscheidbar bleibt.
  3. Bestehende Datenbankmigrationen und DeepDive-Aggregationen um die erforderlichen optionalen Felder ergänzen, ohne historische Nullwerte fälschlich als gelieferte Werte zu kennzeichnen.
  4. `usage.cost` als tatsächlich belasteten Wert in OpenRouter-Credits und Upstream-Inferenzkosten getrennt darstellen; keine Euro- oder andere lokale Währungsumrechnung vornehmen.
  5. Jedes fehlende optionale Feld einzeln als `nicht verfügbar` anzeigen und weder aus Summen ableiten noch schätzen.
  6. Fachlich erfolgreiche Turns trotz fehlender Telemetriefelder als erfolgreich erhalten; Modellidentitätsabweichungen bleiben dagegen Providerfehler aus Task `.3`.
- Acceptance Criteria:
  - Jeder persistierte OpenRouter-Telemetriesatz ist eindeutig einem Janus-Turn, Provider `OpenRouter` und `response.model` zugeordnet.
  - Alle vorhandenen autoritativen Token- und Kostenfelder werden unverändert übernommen.
  - Fehlende Felder bleiben von echten Nullwerten unterscheidbar und erscheinen einzeln als `nicht verfügbar`.
  - DeepDive berechnet, schätzt oder konvertiert keine fehlenden OpenRouter-Kosten oder Tokenwerte.
  - Ein erfolgreicher Turn bleibt bei unvollständiger Telemetrie fachlich erfolgreich.
  - Bestehende DeepDive-Aggregation und Kostenanzeige anderer Provider bleiben unverändert.
- Tests:
  - Unit- und Persistenztests für vollständige, teilweise fehlende und echte Null-Telemetrie sowie Turn-/Provider-/Modellattribution.
  - Datenbank-Migrationstest von bestehendem Kostenbestand auf optionale OpenRouter-Felder ohne Bedeutungsänderung historischer Einträge.
  - DeepDive-API-/Frontend-Tests für OpenRouter-Credits, Upstream-Kosten und einzelne `nicht verfügbar`-Felder.
  - Regression der bestehenden Cross-Provider-, Cache- und Attributionsauswertungen sowie scoped `git diff --check`.
- Model: 5.6 Terra
- Reason: Persistenz- und Datenwahrheitsänderung über Backend und DeepDive mit klarer Feldzuordnung; Ausführung mit hoher Reasoning-Stufe.

### TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6 Versionierte Conformance-Batterie und initiales Vier-Familien-Kandidatenpaket ausliefern
- Ziel: Genau je einen aktuellen, exakt versionierten Kandidaten aus Claude, GLM, DeepSeek und Qwen gegen eine versionierte vollständige Janus-Batterie prüfen und ausschließlich vollständig bestandene Modelle als Update-Daten freigeben.
- Scope: Versionierte Pflichtfall-Batterie, ausführbarer Conformance-Runner, vier exakte Kandidateneinträge, redaktierte Test-/Audit-Evidenz und Update-Datensatz; keine Laufzeit-Zertifizierung, kein vollständiger Katalogimport, keine Release-, Publish- oder Produktionsaktivierung.
- Files: `backend/services/conformance/openrouter_conformance_runner.py` (neu), `backend/services/conformance/fixtures/openrouter/` (neu), `backend/config/openrouter_certified_models.json`, `backend/tests/test_openrouter_conformance.py` (neu), `documentation/test-results/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6_certification_evidence.md` (neu)
- Steps:
  1. Vor der Kandidatenbindung die vier aktuellen exakten Modell-IDs gegen die offizielle OpenRouter-Verfügbarkeit prüfen und genau je einen Kandidaten aus Claude, GLM, DeepSeek und Qwen in den geprüften Update-Datensatz aufnehmen.
  2. Eine benannte und versionierte Pflichtfall-Batterie bereitstellen, die für jedes Kandidatenmodell die in der Spec gebundene volle Janus-Funktion prüft: Chat, Redaction, notwendiger Kontext, Skills, Tools, Berechtigungen, Bestätigungen, Fehlerisolation und Telemetrieverträge.
  3. Den Runner so gestalten, dass jeder Pflichtfall pro exakter Modell-ID und Batterieversion ein reproduzierbares PASS/FAIL-Ergebnis erzeugt und keine Credentials oder privaten Inhalte in Evidenz schreibt.
  4. Nur Kandidaten mit vollständig bestandenen Pflichtfällen sowie vollständig bestandener Test- und Audit-Evidenz im ausgelieferten Zertifizierungsdatensatz als bestanden markieren.
  5. Den Providerstart bereits ab dem ersten vollständig bestandenen Kandidaten erlauben; übrige nicht bestandene oder noch nicht geprüfte Kandidaten bleiben verborgen.
  6. Änderungen von Modell-ID, konkreter Modellversion oder Batterieversion als neue vollständige Zertifizierung behandeln; keine Laufzeit- oder Hot-Pull-Freigabe einführen.
- Acceptance Criteria:
  - Der Update-Datensatz enthält genau einen exakt versionierten Kandidaten je Claude, GLM, DeepSeek und Qwen.
  - Jeder bestandene Eintrag besitzt reproduzierbare vollständige Pflicht-Test- und Audit-Evidenz für exakt dieselbe Modell-ID, Modellversion und Batterieversion.
  - Ein Kandidat mit einem fehlenden oder fehlgeschlagenen Pflichtfall bleibt als nicht zertifiziert verborgen.
  - Sobald mindestens ein Kandidat vollständig besteht, kann der Zertifizierungsdatensatz genau die bestandenen Modelle sichtbar machen, ohne auf alle vier zu warten.
  - Credentials, Gesprächsinhalte und private Testdaten erscheinen nicht in der Evidenz.
  - Der Task aktiviert weder Release noch Produktion und führt keinen Runtime-Katalogimport ein.
- Tests:
  - Runner-Tests für vollständigen PASS, einzelnen Pflichtfall-FAIL, fehlende Evidenz, Batterieversionswechsel, Modellversionswechsel und redaktierte Ausgabe.
  - Strukturtest für genau vier Familienkandidaten und ausschließlich exakte, aliasfreie IDs.
  - Integrationsnachweis, dass der Task-.1-Katalog nur vollständig bestandene Zertifizierungsdatensätze ausliefert.
  - Scoped `git diff --check`, Python-Syntaxprüfung und redaktierte Zertifizierungsevidenz.
- Model: 5.6 Sol
- Reason: Externe Modellzertifizierung mit Security-/Privacy-, Toolparitäts- und Auditgrenzen; keine Produktionsfreigabe in diesem Task.
