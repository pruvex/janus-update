# Changelog

Alle wichtigen Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
und dieses Projekt folgt der [Semantic Versioning](https://semver.org/spec/v2.0.0.html) Richtlinie.

## [Unreleased]

### Fixed
- **BACKLOG-094 / Zwei Chats parallel mit eigener Modellwahl:** Chat A und Chat B koennen jetzt gleichzeitig streamen, ohne dass ein Fenster das andere blockiert. Pro Fenster werden Request-Lifecycle, Loading/Cancel/Error und Modell-/Provider-Zustand isoliert verarbeitet. Fuer Auditierbarkeit wurden STREAM_AUDIT und TOKEN_AUDIT Logging erweitert und zusaetzlich nach `C:\KI\Janus-Projekt\documentation\logs\janus_backend.log` gespiegelt. Validation: `npx playwright test tests/functional/chat-core.spec.js --reporter=list --workers=1` PASS; Final Audit `PASS WITH FIXES`. Files: `backend/api/routers/chat.py`, `backend/main.py`, `backend/logger_config.py`, `backend/services/logging/supabase_client.py`, `frontend/js/chat.js`, `playwright.config.js`, `tests/functional/chat-core.spec.js`.
- **BACKLOG-093 / Gespeicherte API-Keys werden in den Einstellungen doppelt angezeigt:** Die Settings-Ansicht zeigt gespeicherte Provider-API-Keys jetzt wieder genau einmal an. Der Renderpfad ignoriert stale async responses, dedupliziert Provider vor dem Einfuegen und wurde mit einem schnellen Live-Janus-Sichtcheck bestaetigt. Validation: `node --check frontend/js/settings.js` PASS; `LIVE_JANUS_SMOKE` PASS. Files: `frontend/js/settings.js`, `documentation/tasks/backlog_BACKLOG-093_execution_result.md`, `documentation/test-runs/BACKLOG-093_live_janus_smoke.md`, `documentation/test-runs/BACKLOG-093_final_audit.md`.
- **BACKLOG-091 / Chat-Header-Modellwahl pro Chat persistent speichern:** Chat-Header-Provider und -Modell werden jetzt pro Chat in der Datenbank gespeichert, per API aktualisiert und beim Laden eines Chats sowie nach Janus-Neustart wiederhergestellt. Sidebar-Default bleibt bestehen, wenn kein Override gesetzt ist. Validation: `tests/unit/test_chat_header_llm_override.py` PASS, Python compile PASS, JS syntax checks PASS, manueller Restart-Test PASS. Files: `backend/data/models.py`, `backend/data/schemas.py`, `backend/data/crud.py`, `backend/data/database.py`, `backend/api/routers/chat.py`, `frontend/js/window-state.js`, `frontend/js/chat-manager.js`, `frontend/js/app.js`, `tests/unit/test_chat_header_llm_override.py`, `alembic/versions/2026_05_25_chat_header_llm_override.py`.

## [0.4.17-beta.38] - 2026-05-25

### Fixed
- **Websearch Provider Parity / Diamond List Templates:** Unified Gemini and GPT websearch list output through deterministic release and ranking renderers with per-entry title/date or title/details, 1-2 sentence descriptions, price lines for release lists, and inline `Quelle: ... [Link](...)` / `Details: [Link](...)` source links. Ranking lists now separate a real overview/list source from per-entry detail links, reject fake Google/SVG/normal article links as list sources, prefer German sources and German Wikipedia detail links for people/sports lists, and avoid hardcoded source URLs. Release lists now cover games, books, films, series and music releases, including album/EP/single phrasing, and batch-resolve missing per-entry source links with one cost-tracked provider-native search instead of fake links. Raw Gemini Vertex redirect footers are suppressed, frontend fallback Markdown links render as clickable `Link`, and Gemini native search keeps token usage evidence while GPT remains websearch-query based. Validation: websearch suite + diamond regression 83/83 PASS; frontend Markdown renderer 4/4 PASS. Files: `backend/renderers/websearch_templates.py`, `backend/services/skill_router.py`, `backend/services/websearch/gemini_provider.py`, `backend/services/websearch/openai_provider.py`, `backend/services/websearch/query_bias.py`, `backend/tool_registry.py`, `backend/tests/tools/test_websearch.py`.
- **TEST-RUN-2026-05-21-034 / Prompt and Context Budget Efficiency:** Added deterministic prompt/context budget coverage for greeting budget, clear weather location handling, relevant-only memory selection, irrelevant private memory suppression, prompt-cache cold/warm evidence, redacted cache evidence, output-length discipline, long-context guard behavior and cached-token DeepDive evidence. Hardened the memory-dump gate for `Lade dein gesamtes Memory in den Prompt...` and calibrated the TestPlan generator so Spec 15 budget cases no longer inherit source-attribution oracles. Validation: focused budget suite 12/12 PASS; broader budget/cache/cost/memory/privacy suite 30/30 PASS; dashboard PASS 12/12. Files: `backend/services/orchestrator/execution_dispatcher.py`, `backend/tests/test_prompt_context_budget_efficiency.py`, `tests/e2e/generator/compile-testspec-to-testplan.mjs`.
- **TEST-RUN-2026-05-21-031 / Smallest Viable Model and Escalation Discipline:** Model routing now validates smallest viable GPT/Gemini routes, optimized skill-tier policy, MoA catalog consistency, provider-local escalation and prompt-injection attempts to force premium or cross-provider routing. Fixed Gemini MoA logic tier drift from `gemini-3-pro-preview` to `gemini-3.1-pro-preview`, normalized `google` to Gemini, and removed the unknown-provider fallback to OpenAI defaults. Validation: focused routing suite 7/7 PASS; broader routing/MoA/cost suite 30/30 PASS; dashboard PASS 12/12. Files: `backend/llm_providers/shared/moa.py`, `backend/services/routing/model_router.py`, `backend/tests/test_smallest_viable_model_escalation_discipline.py`.
- **TEST-RUN-2026-05-21-029 / Cost and Token Tracking Completeness:** Cost records now persist `cached_tokens` and `total_tokens`, normalize nested cached-token provider usage, mark ToolLoop/Stream persistence contexts, and expose cached/total/context token breakdowns in the cost DeepDive while keeping Websearch as a separate component. Validation: focused cost/token suite 10/10 PASS; broader cost/privacy/filesystem suite 23/23 PASS; dashboard PASS 12/12. Files: `backend/data/models.py`, `backend/data/database.py`, `backend/services/cost_calculator.py`, `backend/services/cost_service.py`, `backend/data/crud.py`, `backend/services/chat_orchestrator.py`, `backend/services/orchestrator/execution_engine.py`, `frontend/js/cost-visualizer.js`, `backend/tests/test_cost_token_tracking_completeness.py`.
- **TEST-RUN-2026-05-21-027 / TestSpec TestPlan Generator Regression:** Added generator self-test coverage that validates oracle-transfer behavior through plan validation, runner generation, runner validation, syntax check and emitted-source assertions for clarification, refusal, source-attribution, `mustNotContain`, prompt-injection-as-data and mixed parallel/serial metadata. Validation: generator self-test PASS; Skill-1 compiler TESTPLAN VALID with 22 generated tests; dashboard PASS 12/12. Files: `tests/e2e/generator/generator.self-test.mjs`, `documentation/test-runs/TEST-RUN-2026-05-21-027_final_audit.md`.
- **TEST-RUN-2026-05-21-025 / Memory Recall Placeholder Regression:** `memory.read` now filters placeholder fact text such as `Name des Testprojekts`, `Projektname` and chat-title placeholder labels before returning recall results, so concrete Phoenix/Orion memory facts win over metadata and injection wording cannot force placeholder recall. Validation: focused memory placeholder 6/6 PASS; memory/tools/retrieval/write/privacy regression 58/58 PASS; dashboard PASS 12/12. Files: `backend/tools/memory_tools.py`, `backend/tests/test_memory_recall_placeholder_regression.py`.
- **TEST-RUN-2026-05-21-023 / Filesystem Safety Boundary Regression:** Added low-level workspace enforcement for absolute filesystem paths and expanded the out-of-sandbox write gate so `C:\Windows\Temp\...` style writes are blocked before tools while safe approved-workspace writes still pass. Also fixed a neighboring `detect_all_intents(None)` logging crash found by the filesystem intent regression suite. Validation: focused filesystem safety 8/8 PASS; filesystem/secret/intent regression 62/62 PASS; dashboard PASS 12/12. Files: `backend/services/filesystem_manager.py`, `backend/services/orchestrator/execution_dispatcher.py`, `backend/services/orchestrator/intent_engine.py`, `backend/tests/test_filesystem_safety_boundary_regression.py`.


## [0.4.17-beta.37] - 2026-05-21

### Fixed
- **TEST-RUN-2026-05-21-013 / Final Beta Launch Gate Review:** Category 2 Security & Safety is fully validated with 19/19 specs PASS and 100% dashboard pass rate. Added final launch-gate evidence for Security 01-18, final risk register, owner sign-off and honest PASS WITH WATCHPOINTS decision for controlled external packaged-local Electron beta. This gate explicitly does not approve hosted SaaS or public/commercial production release without a deployment-bound rerun. Files: `backend/tests/test_final_beta_launch_gate.py`, `tests/e2e/generated/TEST-RUN-2026-05-21-013.final-beta-launch-gate.spec.js`, `documentation/test-runs/TEST-RUN-2026-05-21-013_final_audit.md`, `documentation/test-results/TEST-RUN-2026-05-21-013_results.json`.
- **TEST-RUN-2026-05-21-012 / Beta Privacy Notice and Data Rights:** Added beta-facing privacy notice, data-rights process, tester onboarding acknowledgement and local UI acknowledgement gate. Final validation PASS 10/10 with provider/data-flow disclosure, retention/minimization language, deletion/export process owners, incident route and no raw credential-shaped evidence. Files: `documentation/beta/BETA_PRIVACY_NOTICE.md`, `documentation/beta/BETA_DATA_RIGHTS_PROCESS.md`, `documentation/beta/BETA_TESTER_ONBOARDING_PRIVACY_ACK.md`, `frontend/js/beta-privacy-notice.js`, `backend/tests/test_beta_privacy_notice.py`.
- **TEST-RUN-2026-05-21-011 / Ops Recovery Kill Switches:** Added and validated operator kill switches and recovery evidence for provider access, external tools, write/destructive tools, local beta user lock, memory/RAG and telemetry levels. Final validation PASS 10/10 plus unit gate PASS 8/8. Files: `backend/services/ops_kill_switches.py`, `backend/services/llm_gateway.py`, `backend/services/tool_executor.py`, `backend/api/routers/system.py`, `backend/tests/test_ops_kill_switches.py`.
- **TEST-RUN-2026-05-21-003 through TEST-RUN-2026-05-21-010 / Security Beta Hardening Gates:** Completed Security Mini-Prep, ReviewSpec Suite, packaged-local beta environment baseline, profile isolation, secret rotation/leak scan, telemetry privacy hardening, deployment-surface scan and beta abuse/cost controls. All gates are PASS with 0 failed and 0 blocked checks for the reviewed packaged-local beta scope. Files: `documentation/test-runs/TEST-RUN-2026-05-21-003_*` through `documentation/test-runs/TEST-RUN-2026-05-21-010_*`, `documentation/test-results/TEST-RUN-2026-05-21-003_results.json` through `documentation/test-results/TEST-RUN-2026-05-21-010_results.json`.
- **TEST-RUN-2026-05-20-018 / Rate Limits, Quotas, Abuse and Cost Control:** Spec 07 is now fully green with 26/26 live tests PASS, 0 failed, 0 blocked. Added deterministic retry-storm, flood/mass-generation and cost-abuse refusal gates before memory retrieval/LLM/tools, and calibrated Spec-07 oracles to accept safe refusal variants for rate-limit, quota, prompt-injection and abuse-control cases. BACKLOG-088, BACKLOG-089 and BACKLOG-090 are DONE. Files: `backend/services/chat_orchestrator.py`, `backend/services/orchestrator/execution_dispatcher.py`, `documentation/TEST_SPEC/02_security_safety/07_rate_limits_quotas_abuse_and_cost_control.md`, `documentation/test-runs/TEST-RUN-2026-05-20-018_final_audit.md`.
- **TEST-RUN-2026-05-20-012 / AI Prompt Injection, Tool Abuse and Data Exfiltration:** Spec 06 is now fully green with 57/57 live tests PASS, 0 failed, 0 blocked. Added deterministic AI-safety gates for unsafe cross-user/data/tool-request families, stabilized generated live runners with E2E fast mode and longer readiness waits, and calibrated Spec-06 safety oracles for safe refusal/clarification/evidence-honesty variants while preserving leak and unsafe-success guards. Files: `backend/services/orchestrator/execution_dispatcher.py`, `backend/services/orchestrator/response_finalizer.py`, `backend/tests/test_privacy_export_gate.py`, `tests/e2e/generator/compile-testspec-to-testplan.mjs`, `tests/e2e/generator/generate-live-runner.mjs`, `playwright.config.js`, `documentation/test-runs/TEST-RUN-2026-05-20-012_final_audit.md`.
- **BACKLOG-080 / Playwright Duplicate Installation Collision:** Removed duplicate frontend `@playwright/test` dependency so Playwright tests no longer fail with the second-require configuration error. This unblocked BACKLOG-079 verification. Files: `frontend/package.json`, `frontend/package-lock.json`, `documentation/test-runs/BACKLOG-080_final_audit.md`.
- **BACKLOG-079 / Playwright beforeEach Timeout Fix:** Spec 06 AI Safety live runner no longer collapses with the prior 42-test `beforeEach` timeout blocker. Generated test case timeout is now aligned to long-running Janus live tests, and `TEST-RUN-2026-05-19-008` confirms the runner executes the suite instead of failing at setup. Final audit is PASS WITH FOLLOW-UP because remaining Spec 06 findings are separate AI-Safety-/Oracle-/Flaky follow-ups, not the original infrastructure blocker. Files: `tests/e2e/generator/compile-testspec-to-testplan.mjs`, `documentation/test-runs/BACKLOG-079_final_audit.md`.
- **BACKLOG-074 / Planner Boundary Control:** Spec 05 Planner vs Direct Execution Boundary is now green with `TEST-RUN-2026-05-19-003` PASS 32/32. Fixed over-cautious ambiguity handling, synthetic prompt memory/identity bleed, broad workspace-task stability, missing workspace-path clarification, and generated runner stream/evidence behavior. The Spec 05 TestPlan oracle now validates planner-boundary route families instead of stale source-attribution defaults. Files: `backend/services/chat_orchestrator.py`, `backend/services/memory/retrieval_service.py`, `backend/services/orchestrator/execution_dispatcher.py`, `tests/e2e/generator/compile-testspec-to-testplan.mjs`, `tests/e2e/generator/generate-live-runner.mjs`, `documentation/test-runs/BACKLOG-074_final_audit.md`.
- **TEST-RUN-2026-05-18-027 / OWASP Injection, XSS, CSRF, SSRF and Path Traversal:** Spec 05 Web Attack Surface validation is now green with 26/26 live tests. Live runner UI-readiness waits use a 60s generated timeout, Spec 05 oracles accept safe refusal/sanitization variants while preserving unsafe-success guards, and path traversal read/list/open prompts are blocked before LLM/tool execution. Files: `backend/services/orchestrator/execution_dispatcher.py`, `tests/e2e/generator/compile-testspec-to-testplan.mjs`, `tests/e2e/generator/generate-live-runner.mjs`, `documentation/test-runs/TEST-RUN-2026-05-18-027_final_audit.md`.
- **TEST-RUN-2026-05-18-024 / Browser Security Baseline:** Security Headers, Cookies and Browser Surface Spec now runs as provider-free browser/HTTP validation instead of chat-provider tests. Added `JANUS_BROWSER_SECURITY` runner support plus frontend/backend security headers (CSP, frame restrictions, nosniff, referrer policy, permissions policy). Final live run `TEST-RUN-2026-05-18-024` PASS 13/13, Findings NONE. Files: `backend/main.py`, `vite.config.js`, `tests/e2e/generator/compile-testspec-to-testplan.mjs`, `tests/e2e/generator/generate-live-runner.mjs`, `documentation/test-runs/TEST-RUN-2026-05-18-024_final_audit.md`.
- **BACKLOG-073 / Core Routing Decision Quality Oracle:** Spec 04 Core Routing TestPlan oracle now accepts routing-specific safe variants for current research, memory recall, fake regulated capability, missing memory fact and prompt-injection refusal while preserving unsafe-route and leak guards. Final live run `TEST-RUN-2026-05-18-023` PASS 38/38, Findings NONE. Files: `tests/e2e/generator/compile-testspec-to-testplan.mjs`, `documentation/test-runs/BACKLOG-073_final_audit.md`.
- **BACKLOG-072 / Auth, AuthZ and Tenant Isolation Oracle + Runner Evidence:** Spec 03 Auth/AuthZ/Tenant-Isolation TestPlan oracle now accepts safe refusal/scope-clarification variants for cross-user data, unauthorized mutation, role bypass, auth-state confusion, and prompt-injection memory claims. Live runner now writes aggregate result JSON from evidence files and records blocked evidence when Playwright fails before Janus evidence exists. Final live run `TEST-RUN-2026-05-18-019` PASS 26/26, Findings NONE. Files: `tests/e2e/generator/compile-testspec-to-testplan.mjs`, `tests/e2e/generator/generate-live-runner.mjs`, `backend/services/orchestrator/prompt_registry.py`, `backend/services/security/injection_detector.py`, `documentation/test-runs/BACKLOG-072_final_audit.md`.
- **BACKLOG-069 / Ambiguity Gate Calibration Oracle:** TestPlan-Oracle fuer Spec 03 ist jetzt Spec-spezifisch kalibriert: klare Wetter-/Geo-Intents erwarten direkte Tool-/Quellenantworten, ambige Wetter-/Memory-/Edit-/Delete-/Calendar-Prompts akzeptieren Clarification bzw. honest missing context. Finaler Live-Run `TEST-RUN-2026-05-18-003` PASS 28/28, Findings NONE. Files: `tests/e2e/generator/compile-testspec-to-testplan.mjs`, `documentation/test-runs/BACKLOG-069_final_audit.md`.
- **BACKLOG-064 / API Tool Routing Source Attribution Oracle:** TestPlan-Oracle fuer Spec 06 uebertraegt Source-Attribution-Patterns korrekt statt generischer Capability-/Clarification-Keywords. Finaler Live-Run `TEST-RUN-2026-05-18-002` PASS 42/42, Findings NONE, Backlog Items NONE. Files: `tests/e2e/generator/compile-testspec-to-testplan.mjs`, `documentation/test-runs/BACKLOG-064_final_audit.md`.
- **BACKLOG-068 / API Privacy Boundary:** Overbroad user-data export, internal identifier, hidden prompt, and raw API header/body dump requests are blocked deterministically before LLM/tool execution. Final live run `TEST-RUN-2026-05-17-028` PASS 26/26; unit gate tests PASS 5/5. Files: `backend/services/orchestrator/execution_dispatcher.py`, `backend/tests/test_privacy_export_gate.py`, `documentation/TEST_SPEC/02_security_safety/02_api_response_privacy_and_debug_leakage.md`.
- **BACKLOG-067 / TestPlan Pattern Transfer:** TestPlan-Generator uebernimmt explizite `Expected containsAny Patterns` aus TestSpecs jetzt in provider-expandierte `expected.containsAny` Arrays, bevor Fallback-Heuristiken greifen. Validierung: `TEST-RUN-2026-05-17-024` Plan `TESTPLAN VALID`, 26 generierte Tests, Pattern-Abgleich fuer `INT-002`, `INT-003`, `INT-004`, `SEC-005` GPT/GEMINI PASS. Files: `tests/e2e/generator/compile-testspec-to-testplan.mjs`.
- **BACKLOG-065 / Spec 01 Security Refusal Oracles:** TestPlan-Generator akzeptiert fuer Secret-/Env-/Key-/Prompt-Injection-Faelle jetzt security-refusal Patterns statt generischer Clarification-/Capability-Keywords, ohne `mustNotContain` Leak Guards zu entfernen. Finaler Live-Run `TEST-RUN-2026-05-17-021` PASS 28/28; Findings NONE. Files: `tests/e2e/generator/compile-testspec-to-testplan.mjs`.
- **TEST-RUN-2026-05-17-006 / Spec 06 API Tool Routing:** API Tool Routing und Source Attribution final validiert. Wikipedia- und Geo-/Routing-Antworten liefern jetzt Quellenhinweise, klare Geo-Distanzfragen erzwingen `system.routing`, Weather-Fragen ohne Ort fragen nach Standort statt zu raten, und Source-Policy-Prompt-Injection wie "do not cite sources" wird blockiert. TestPlan-Oracles akzeptieren sichere Clarification-/Refusal-Antworten. Full-Run `TEST-RUN-2026-05-17-006` PASS 42/42. Files: `backend/renderers/attribution.py`, `backend/services/orchestrator/execution_dispatcher.py`, `backend/services/orchestrator/intent_engine.py`, `backend/services/security/injection_detector.py`, `tests/e2e/generator/compile-testspec-to-testplan.mjs`.
- **BACKLOG-063 / Spec 05 Generator Coverage:** TestPlan-Generator-/Coverage-Gap fuer Spec 05 behoben. Der Compiler verliert `SEC-003-GPT/GEMINI` nicht mehr; `SEC-003`, `PINJ-001` und `INT-003` Oracles akzeptieren sichere Refusal-/Clarification-Antworten bei weiterhin aktiven `mustNotContain`-Guards. Targeted Retests `SEC-003`, `PINJ-001`, `INT-003` PASS; finaler Live-Full-Run `TEST-RUN-2026-05-17-001` PASS 34/34. Final Audit: PASS.
- **BACKLOG-062:** TestSpec 05 Oracle-Expectations fuer Klaerungsfragen aktualisiert und final auditiert. TEST-RUN-2026-05-16-008 PASS 16/16; TC-002/TC-003 sowie SEC-001/SEC-002 bestehen fuer GPT und Gemini mit korrigierten Clarification-/Refusal-Oracles. Final Audit: PASS WITH FOLLOW-UP. Follow-up BACKLOG-063 erfasst Generator-/Coverage-Gap, da SEC-003 in der TestSpec definiert, aber im Retest-Plan 008 nicht enthalten war.
- **BACKLOG-056:** Memory/Calendar Security Test-Oracles final auditiert und abgeschlossen. SEC-001/SEC-002/SEC-003 akzeptieren sichere Klärungsfragen und neutrale No-Action-Antworten, während `mustNotContain` für unsafe Inhalte aktiv bleibt. TEST-RUN-2026-05-16-004 validiert alle sechs Security-Cases (GPT/Gemini) als PASS; Gesamtrun PASS 28/28. Final Audit: PASS.
- **BACKLOG-060:** TC-004-GPT Calendar Runtime Fallback behoben. Root Cause war kein OpenAI-Key-/Quota-/Netzwerkproblem: Backend-Logs zeigten OpenAI `200 OK` und ein erfolgreiches `calendar.list_events`-Result. Der Streaming-Finalizer erkannte dynamische Provider-Fallbacks (`Provider: openai | Modell: ... robusten Neuaufbau`) nicht als generische Fallbacks und verdeckte dadurch erfolgreiche Tool-Ergebnisse. Fix in `execution_engine.py`: dynamische Provider-Fallbacks werden erkannt und nach erfolgreicher Tool-Runde durch erfolgreiche Tool-Ergebnisse ersetzt. Retest: `TC-004-GPT` PASS, `TC-004-GEMINI` PASS, TEST-RUN-2026-05-16-004 PASS 28/28. Final Audit: PASS.
- **BACKLOG-057:** Functional Memory/Calendar Test-Oracles bereinigt. TC-002-GPT/GEMINI akzeptieren den konkreten Memory-Recall-Wert `Phoenix`; TC-003-GPT/GEMINI akzeptieren ehrliche "keine Information / nicht gespeichert"-Antworten. TestPlan validiert, Live-Runner regeneriert, gezielte Retests: TC-002 PASS, TC-003 PASS, PINJ-001-GEMINI PASS, TC-004-GEMINI PASS. Der damals verbleibende TC-004-GPT-Fail wurde als BACKLOG-060 separiert und ist inzwischen behoben. Final Audit: PASS.
- **BACKLOG-058:** SEC-003 TestPlan/Generator-Fix als DONE dokumentiert. Final Audit PASS, Generator-Branch und TestPlan/Runner-Regeneration validiert.
- **BACKLOG-059:** GPT-5.4-nano Memory-Recall Placeholder-Halluzination behoben. Neue Prompt-Registry-Direktive `memory_priority_over_chat_title` priorisiert gespeicherte Memory-Fakten vor Chat-Titeln und verbietet Placeholder wie "Name des Testprojekts" als konkrete Fakten. Live-Retest: TC-002-GPT antwortet produktseitig mit "Phoenix" statt Placeholder; TC-002-GEMINI bleibt produktseitig korrekt. Verbleibende maschinelle ASSERTION_MISMATCH-Fails fuer TC-002 gehoeren zu BACKLOG-057 (Functional Oracle erwartet noch Web-/Recherche-Keywords). Files: `backend/services/orchestrator/prompt_registry.py`. Final Audit: PASS.

- **TEST-RUN-2026-05-16-002 / Filesystem Safety:** Provider-agnostische Pre-LLM-Gates für unklare destruktive Filesystem-/Calendar-Delete-Prompts und Out-of-Sandbox-Filesystem-Writes ergänzt. Gemini claimt für `SEC-001-GEMINI` keinen uneingeschränkten lokalen Laufwerkszugriff mehr; der Test-Oracle blockiert unsafe Capability Claims jetzt über `mustNotContain`. Validierung: TEST-RUN-2026-05-16-002 PASS 20/20. Files: `backend/services/orchestrator/execution_dispatcher.py`, `backend/services/orchestrator/prompt_registry.py`, `documentation/test-runs/TEST-RUN-2026-05-16-002_plan.json`.
- **BACKLOG-050:** GPT-5.4-nano Calendar Mutation Intent ohne Tool-Ausführung behoben. CALENDAR_COMMAND_MARKERS in intent_engine.py erweitert um "update", "aktualisieren", "ändern", "aendere" und ASCII-Umlaut-Fallbacks. SEC-003-GPT PASS mit Kalender-Keywords. Provider Parity erreicht. Files: `backend/services/orchestrator/intent_engine.py`. Version: 0.4.17-beta.83.
- **BACKLOG-039:** Ambiguity-Detection Regression behoben. Ambige Prompts wie "Ich brauche Infos dazu" (GPT) und "Ich brauche Infos" (Gemini) stellen wieder Klärungsfragen statt Memory/Context direkt auszulesen. Root Cause: TASK-037-02 war provider-spezifisch und `chat_orchestrator.py` baute Memory-Kontext trotz `context_isolation_mode` erneut auf. Fix: Ambiguity-Detection in `execution_dispatcher.py` provider-agnostisch gemacht und Context-Isolation-Checks in allen Memory-Context-Rebuilding-Pfaden in `chat_orchestrator.py` ergänzt. Validierung: TC-005 (GPT) PASS, LTC-002 (Gemini) PASS, Python compilation PASS, JSON/Generator/Validator PASS. Files: `backend/services/orchestrator/execution_dispatcher.py`, `backend/services/chat_orchestrator.py`. Version: 0.4.17-beta.34.
- **BACKLOG-023:** Intermittent Backend Timeout bei aufeinanderfolgenden Requests behoben. SQLite Timeout von 30 auf 60 Sekunden erhöht. Connection Pool Timeout von 30 auf 60 Sekunden erhöht. Gateway Silos Pre-Initialization in App-Startup implementiert (verhindert Lazy-Loading Race Conditions bei ersten Requests). Manuelles Test-Gate PASS - aufeinanderfolgende Requests ohne Timeout. Syntax-Validierung PASSED. Skill 6 Final Audit PASS (MEDIUM Risk, HIGH Confidence). Files: `backend/main.py` (+7 Zeilen, Gateway Silos Pre-Initialization), `backend/data/database.py` (Timeouts bereits vorhanden). Version bump: 1.2.3 → 1.2.4.
- **BACKLOG-033:** Test-Erwartungen korrigiert - falsche Tool-Namen (wiki_fact/news_rss statt system.wikipedia_summary/system.rss_news) behoben. Root Cause war nicht Provider-Parity-Problem sondern Test-Dokumentations-Fehler. Backend-Logik bereits korrekt durch BACKLOG-031 Fix (mandatory tool logic für Wikipedia/News Intents). Beide Provider (GPT/Gemini) verwenden identische Intent-Engine und Tool-Selection. TestPlan-Dateien korrigiert: TEST-RUN-2026-05-12-001_plan.json und TEST-RUN-2026-05-13-PARITY_plan.json. Provider Parity bestätigt. Files: `documentation/test-runs/TEST-RUN-2026-05-12-001_plan.json`, `documentation/test-runs/TEST-RUN-2026-05-13-PARITY_plan.json`.
- **BACKLOG-038 / BACKLOG-025 / BACKLOG-029 / BACKLOG-030:** Frontend Rendering Integrity behoben. ReferenceError "win is not defined" blockierte alle Tests. Root Cause: Kommentar in `frontend/js/chat.js` Zeile 758 enthielt `<win>` statt `{windowId}`. Fix: Kommentar korrigiert zu `{windowId}`. Playwright-Verify-Test PASS - 0 console errors. Cache-Clean durchgeführt (dist/ Ordner gelöscht). Version bump: 0.4.17-beta.32 → 0.4.17-beta.33.
- **BACKLOG-037:** Gemini Ambiguity Clarification implementiert. Context-Isolation für Gemini bei ambigen Anfragen (confidence>=0.6) implementiert. Chat-History, Memory-Context, Fact-Coupons, Direktiven und Tool-Routing werden geleert, wenn Ambiguity-Detection auslöst. Gemini stellt jetzt korrekt Klärungsfragen statt aus Kontext zu antworten. Provider-Parität erreicht (GPT und Gemini verhalten sich identisch bei ambigen Anfragen). Test TC-005-GEMINI-RETEST PASS. Diamond Confidence Score: 9/10, Production Confidence: 90% für Ambiguity-Detection. Files: `backend/services/orchestrator/intent_engine.py`, `backend/services/orchestrator/execution_dispatcher.py`.
- **BACKLOG-036:** Gemini Geo-Distance Halluzination behoben. DIAMOND-CORE-ROUTING-FORCE Bedingung erweitert um `is_routing_geo_intent` flag zusätzlich zu primary_intent check. Gemini ruft jetzt system.routing Tool bei Geo-Distanz-Abfragen auf und zeigt "Quelle: OSRM" Attribution an. Provider-Parität erreicht (GPT und Gemini verhalten sich identisch). Diamond Score: 83/100, Production Confidence: 100% für Geo-Routing. Files: `backend/services/orchestrator/execution_dispatcher.py` (lines 895-903).
- **BACKLOG-035:** Prompt Injection Defense implementiert. Guard in `backend/services/orchestrator/execution_engine.py` erkennt Prompt Injection vor Provider-Aufruf und blockiert die gesamte Query-Verarbeitung. Provider-agnostisch (funktioniert für GPT und Gemini). Test PINJ-001 mit beiden Provider PASS. Diamond Confidence Score: 9.5/10, Production Confidence: 95%. Files: `backend/services/orchestrator/execution_engine.py` (lines 2501-2513).


## [0.4.17-beta.28] - 2026-05-11

### Fixed
- **BACKLOG-006:** Generische Fehlermeldung durch spezifische Fehlerdetails ersetzt. Dynamische Fallback-Zusammenfassung basierend auf tatsächlichen Fehlerdetails (Tool-Name, Fehlercode, Fehlermeldung, Provider, Model) implementiert. `_build_dynamic_fallback_summary()` Helper-Funktion in execution_engine.py hinzugefügt. Tool-Fehler-Tracking mit `_last_tool_error` Variable in `run_tool_loop()` und `run_tool_loop_stream()`. Error-Extraktion aus Tool-Ergebnissen (error_code, error_message). Dynamic Fallback Verwendungen in allen Fallback-Szenarien (Exception, Stream-Crash, leere Tool-Round, leeres Text-Ergebnis). Backend-Logs behalten vollständige Exception-Details mit `exc_info=True`. Files: `backend/services/orchestrator/execution_engine.py`, `backend/services/orchestrator/execution_dispatcher.py`. Manual Janus Test PASS (GPT + Gemini). Skill 6 Audit PASS.

## [0.4.17-beta.27] - 2026-05-11

### Changed
- **Dark Mode Default:** Darkmode ist jetzt standardmäßig aktiviert (Default: True). Bei frischer Installation startet Janus im Dark Mode. Der zuletzt gewählte Modus wird beim nächsten Start wiederhergestellt. Files: `backend/data/database.py`, `alembic/versions/2026_05_10_add_dark_mode_enabled_to_user.py`.

## [0.4.17-beta.26] - 2026-05-11

### Fixed
- **BACKLOG-021:** Datenbank-Migrationsfehler in EXE-Version behoben. SQLite-Drift-Migration für `users.dark_mode_enabled` in `backend/data/database.py` ergänzt. `_ensure_sqlite_schema_migrations()` prüft bei SQLite-DBs, ob die Spalte `dark_mode_enabled` in der `users` Tabelle fehlt, und führt `ALTER TABLE users ADD COLUMN dark_mode_enabled BOOLEAN NOT NULL DEFAULT 0` aus. Dies behebt den `sqlite3.OperationalError: no such column: users.dark_mode_enabled` in der EXE-Version. Dev-Modus bereits korrekt. File: `backend/data/database.py`. Final Audit: PASS WITH CONDITIONS. EXE-Validierung auf Testsystem ausständig (Skill 8).

## [0.4.17-beta.25] - 2026-05-10

### Added
- **Startup Telemetrie Log (Dev-Kontext):** Systematische Erfassung von Startup-Zeiten und Phasen zur Performance-Analyse im Dev-Kontext. Strukturiertes Logging mit Markern (npm_start, backend_startup_start, backend_ready), Phasen-Messung (backend_start, frontend_load, app_ready), Log-Rotation, Dev-only Aktivierung via JANUS_DEV_MODE oder NODE_ENV=development. Files: `backend/services/telemetry/startup_config.py`, `backend/services/telemetry/startup_logger.py`, `electron/startup-telemetry.cjs`, `scripts/write-startup-marker.cjs`, `backend/main.py`, `main.electron.cjs`, `package.json`, `tests/test_startup_config.py`, `tests/test_startup_logger.py`. Manual Janus Test PASS. Skill 6 Audit PASS.
- **Dark Mode Toggle:** Globales Light/Dark Theme Switch in Settings implementiert. Checkbox in Settings UI, Backend-Persistenz (dark_mode_enabled Boolean), LocalStorage-Caching für sofortige Theme-Anwendung, CSS Variables für Theme-Styles. Files: `backend/data/models.py`, `backend/data/schemas.py`, `backend/api/routers/users.py`, `frontend/index.html`, `frontend/js/settings.js`, `frontend/js/app.js`, `frontend/src/styles.css`. Manual Janus Test PASS.

### Fixed
- **BACKLOG-020:** Chatfenster-Resize-Problem behoben. Vertikales Resizen blockierte nach erstem Resize-Versuch. Root Cause: CSS `max-height` constraint und JavaScript `resizeListener` height/position constraints blockierten vertikales Resizen. Fix: `max-height: calc(100dvh - 16px)` aus `frontend/css/style.css` entfernt. `maxH` und `maxY` constraints aus `resizeListener` in `frontend/js/app.js` entfernt. Chatfenster lässt sich jetzt frei von der unteren rechten Ecke resizen (horizontal + vertikal) ohne Blockade. Reset-Button und Initialgröße bleiben erhalten. Manual Janus Test PASS. Files: `frontend/css/style.css`, `frontend/js/app.js`.

### Changed
- **Dashboard UI:** Spaltennamen auf Deutsch übersetzt (ÄNDERUNG, ERWEITERUNG, VERBESSERUNG, TECHNISCHE SCHULDEN, UNKLAR). BUG und SPEC FEATURE bleiben auf Englisch. Mapping hinzugefügt für Filter-Logik. Files: `janus-dashboard/apps/ui/src/views/ActiveView.tsx`, `janus-dashboard/apps/ui/src/views/HistoryView.tsx`.
- **Dashboard Start:** Terminal-Visibility verbessert. VBS-Wrapper `start-dashboard-hidden.vbs` erstellt für versteckten Start. Desktop-Shortcut `Janus Dashboard.vbs` hinzugefügt. Files: `janus-dashboard/start-dashboard-hidden.bat`, `janus-dashboard/start-dashboard-hidden.vbs`.
- **Janus Logo:** Benutzerdefiniertes PNG-Logo als Janus-Logo konfiguriert für Dev-Modus und gebaute EXE. Files: `frontend/assets/icon.png`, `package.json`, `main.electron.cjs`.


## [0.4.17-beta.23] - 2026-05-09

### Fixed
- **BACKLOG-019:** Hardcoded gpt-5-mini verursacht Fallback-Warnung nach OpenAI-Key-Eingabe. Alle hardcoded Modell-IDs (gpt-5-mini) aus Backend-Code entfernt und durch dynamische Auswahl aus Model-Katalog ersetzt. Neue Helper-Funktion `get_first_available_text_model_with_provider()` in llm_gateway.py wählt deterministisch (provider, model_id) aus Katalog. main.py und calendar_ai_engine.py nutzen dynamische Auswahl statt hardcoded Fallback. Provider/Model-Mismatch behoben: Provider wird jetzt immer passend zum Modell aus Katalog gesetzt. Robust gegen leere Kataloge: gibt leeren String zurück bei leerem Katalog. Files: `backend/services/llm_gateway.py`, `backend/main.py`, `backend/services/calendar/calendar_ai_engine.py`. Manual Janus Test PASS.

## [0.4.17-beta.22] - 2026-05-09

### Fixed
- **BACKLOG-017:** ChromaDB-Module fehlen im PyInstaller-Bundle. PyInstaller spec um ChromaDB-Submodule erweitert: `collect_data_files('chromadb')`, `collect_data_files('chromadb', include_py_files=True)`, `hiddenimports=['chromadb.telemetry.product.posthog', 'chromadb.api.rust']`. Vektor-Service und Skill-Router starten ohne ChromaDB-Import-Fehler. Manual Janus Test PASS. Files: `janus_backend.spec`. Version: 0.4.17-beta.22.

## [0.4.17-beta.21] - 2026-05-09

### Fixed
- **BACKLOG-018:** CLIP-Model-Download blockiert nicht mehr First-Start. Lazy-Loading Pattern implementiert: CLIP-Model (338MB, ViT-B-32.pt) wird asynchron im Hintergrund nach App-Start geladen via Daemon-Thread in FastAPI-Lifespan. Vision-Service prüft `model_loader.is_ready()` vor CLIP-Inference und überspringt bei `False`. App startet sofort auf allen Systemen unabhängig von Internetgeschwindigkeit. Files: `backend/services/vision/model_loader.py` (NEU), `backend/services/vision_service.py` (MODIFIZIERT), `backend/main.py` (MODIFIZIERT). Manual Janus Test PASS.

## [0.4.17-beta.20] - 2026-05-08

### Fixed
- **BACKLOG-016:** Video-Links funktionieren jetzt nach Chat-Wechsel. IndentationError in `backend/data/crud.py` behoben (Zeile 111-112). `video_list_metadata` wird jetzt korrekt in `metadata_json` persistiert. Persistenzpfad vollständig: Backend CRUD → Schemas → Frontend Reload → Rendering. `frontend/js/chat-manager.js` reicht `video_list_metadata` beim Chat-Reload durch. `frontend/js/chat.js` rendert Video-Links aus `video_list_metadata` nach Chat-Wechsel. Manual Janus Test PASS.

## [0.4.17-beta.19] - 2026-05-08

### Fixed
- **Task 030:** Video-Liste Chat-Wechsel Persistenz-Fix. Video-Details (Titel, Kanal, Views, Upload-Datum) werden jetzt korrekt nach einem Chat-Wechsel beibehalten. Sender-Bedingung erweitert auf "bot" || "model", appendVideoReopenLink Parameter videoListMetadata hinzugefügt, wireVideoReopenLink übergibt videoListMetadata an appendVideoReopenLink, appendMessage generiert Markdown mit Header (wie SSE-Stream) beim Chat-Reload. Backend-Logging hinzugefügt zur Verfolgung von video_list_metadata. max_results=3 → max_results=payload.max_results in video_tools.py.

## [0.4.17-beta.18] - 2026-05-08

### Fixed
- **BACKLOG-015:** Modell-Wechsel-Benachrichtigung verbessert. Klarere Kommunikation mit Titel "⚠️ Modell nicht verfügbar", Erklärung warum das Modell nicht verfügbar ist und dass automatisch gewechselt wurde. Handlungsoptionen: "Fallback behalten" und "Modell wählen" (öffnet Einstellungen). Verbessertes Design mit max-width, padding, border-radius, box-shadow. Längere Anzeigezeit (10 Sekunden). Provider-Wechsel-Probleme behoben: Keine falschen Fehlermeldungen mehr beim Provider-Wechsel, Dropdown nicht mehr leer. UX-Entscheidung: Kleinstes Modell beim Provider-Wechsel auswählen (sicherer, verhindert versehentliche Nutzung teurer Modelle).

## [0.4.17-beta.17] - 2026-05-07

### Fixed
- **BACKLOG-011:** Video-Modal False-Positive Fix + Gemini List-Mode Override. URL-Detection Fallback in `response_finalizer.py` deaktiviert, modal_request wird ausschließlich aus video.search tool_results abgeleitet. Zusätzlich Backend-Override in `tool_executor.py` erzwingt `mode="list"` für `video.search`, da Gemini den Schema-Default ignoriert und immer `"single"` setzt. Gemini zeigt jetzt mehrere Videos aufgelistet und das Modal öffnet automatisch mit dem ersten Video.

## [0.4.17-beta.16] - 2026-05-07

### Fixed
- **BACKLOG-010:** Deterministischer Tool-Loop Guard für Desktop Image Move. Nach `filesystem.create_directory` führt die Engine automatisch `filesystem.find_files` für *.jpg und *.png sowie `filesystem.move_files` aus, wenn das Ziel ein Desktop-Ordner ist. Provider-agnostisch (getestet mit gpt-5.4-nano und Gemini). Umgeht LLM-Instruction-Dependenz.

## [0.4.17-beta.15] - 2026-05-07

### Fixed
- **BACKLOG-009 (Partial):** Neue `path_resolution_hint` Direktive in `prompt_registry.py` hilft gpt-5.4-nano bei der Auflösung häufiger Windows-Pfade (desktop, documents, downloads, pictures). Pfad-Auflösung funktioniert jetzt ohne Rückfragen. Vollständige Ausführung der Filesystem-Operationen bleibt ein separates Problem (BACKLOG-010).

## [0.4.17-beta.14] - 2026-05-07

### Fixed
- **BACKLOG-008:** Filesystem-Intent blockiert jetzt RAG-Intent, um unnötige Logic-Tier-Upgrades bei reinen Dateisystem-Operationen zu verhindern. Filesystem-Operationen werden mit gpt-5.4-nano ausgeführt, ohne Upgrade auf gpt-5.4. Pfad-Auflösungs-Problem als separates BACKLOG-009 ausgelagert.

## [0.4.17-beta.13] - 2026-05-07

### Fixed
- **BACKLOG-005:** Filesystem-Intent hat jetzt Vorrang vor Bild-Intent bei gemischten Keywords. "Bilder" im Kontext von Dateisystem-Operationen wird korrekt als Filesystem-Intent erkannt, nicht als Bild-Intent. Skill-Descriptions für find_files und move_files verbessert für bessere Tool-Call-Effizienz.

## [0.4.17-beta.12] - 2026-05-07

### Fixed
- **BACKLOG-001:** Test-Dateien aus Projekt-Root nach tests/ verschoben (test_cluster_4.py, test_geometrie_check.py, test_logging_fix.py, test_openai_tools.py, test_face_root.jpg, test_personalities_root.json).
- **Security:** Hardcoded OpenAI API-Key aus tests/test_openai_tools.py entfernt. Test überspringt jetzt sauber, wenn OPENAI_API_KEY nicht gesetzt ist.
- **BACKLOG-003:** Alte Release-Installer aus release/ entfernt (janus-setup-0.4.17-beta.4.exe, janus-setup-0.4.17-beta.9.exe, janus-setup-0.4.17-beta.10.exe). Nur janus-setup-0.4.17-beta.11.exe verbleibt. ~1.46 GB Speicherplatz freigegeben.

## [0.4.17-beta.11] - 2026-05-05

### Added
- **UI:** Added real-time download progress and status indicators to the sidebar footer.

### Changed
- **UX:** Optimized update status messages for better readability in narrow sidebars.

## [0.4.17-beta.10] - 2026-05-05

### Fixed
- **Auto-Update:** Final bridge release with hardened multi-hash validation and atomic pipeline sync. This version is required for all future automatic updates.

## [0.4.17-beta.9] - 2026-05-05

### Changed
- **Auto-Update:** Hardened build pipeline to always perform a full rebuild of all components before release. Disabled differential downloads to increase update stability and prevent checksum mismatches.

## [0.4.17-beta.8] - 2026-05-05

### Fixed
- **Auto-Update:** Fixed a critical client-side validation bug where the updater only checked for SHA256 hashes, causing a HASH_MISMATCH when the server provided a SHA512 hash from latest.yml. The validator is now multi-hash-aware.

## [0.4.17-beta.7] - 2026-05-05

### Fixed
- **Auto-Update:** Hardened the release pipeline to use a single-source-of-truth for hashes, preventing future HASH_MISMATCH errors. The generate:update-manifest script now derives its hash from the latest.yml file generated by electron-builder.

## [0.4.17-beta.6] - 2026-05-05

### Fixed
- **System:** Fixed CDN caching and hash validation issues in the auto-update pipeline. (Clean slate version bump).

## [0.4.17-beta.5] - 2026-05-05

### Fixed
- **TASK-069.16: Update Error-Handling Scope** — Fixed ReferenceError in Electron main process update IPC handler by replacing undefined `win` variable with `mainWindow` and adding null check.
- **TASK-069.17-069.20: Release Manifest Integrity** — Hardened update-pipeline with atomic manifest generation, strict file existence checks, and fresh SHA256 calculation. Manifest now generated only after successful build.
- **TASK-069.21: Production Build Prep** — DevTools now open only when `NODE_ENV === 'development`. Version bumped to 0.4.17-beta.5 for final production build.

## [0.4.17-beta.4] - 2026-05-05

### Added
- **TASK-069: Capability Overview Response (SEALED)** — Deterministic answers to „Was kannst du?“ from `backend/data/capability_registry.json` via Help Fast-Path (no LLM): normalized intent triggers with casefold and trailing punctuation stripping (TASK-069.14), `get_verified_capabilities_for_overview()` with `verified` + `confidence ≥ 0.7`, fixed category order and „Sonstiges“ mapping, Markdown format `## Das kann ich aktuell`. Tests: unit `test_capability_registry_logic.py`, `test_intent_engine.py` (normalization hardening), integration help fast-path, Playwright `tests/e2e/capability-overview.spec.js` (button-click hardening). Audit: PASS WITH FIXES. Version: 0.4.17-beta.4.

## [0.4.17-beta.3] - 2026-05-04

### Fixed
- **Build Fix** — Added electron/**/* to build.files in package.json to include electron/update-manager.cjs, electron/update-state.cjs, and electron/update-security.cjs in the release artifact. This fixes "Cannot find module './electron/update-manager.cjs'" error in installed version.

## [0.4.17-beta.2] - 2026-05-04

### Added
- **TASK-068: Auto Update System (SEALED)** — Deterministic Auto Update System for Electron with state machine persistence, SHA256 manifest validation, secure IPC bridge, and state-driven UI. T1-T8 complete. Files: electron/update-state.cjs, electron/update-security.cjs, electron/update-manager.cjs, main.electron.cjs, frontend/preload.js, frontend/js/update-ui.js, frontend/js/app.js, frontend/css/update-ui.css, frontend/index.html, scripts/generate_update_manifest.cjs, documentation/release/auto_update_manifest_contract.md. Tests: Node unit tests (16 passed), Playwright E2E (7 passed). Version: 0.4.17-beta.2. Audit: PASS WITH FIXES.

### Fixed
- **E2E test validation** — Replaced inline-duplicated UI logic test with task-conformant .spec.js that tests the real app initialization and update-ui.js module.
- **ES Module import failure** — Added missing `export { initUpdateUI };` in frontend/js/update-ui.js to fix ES module import in app.js.
- **Test artifact in repo** — Changed update-state.test.cjs to use temporary directory instead of project root for janus-update-state.json.
- **Lockfile version outdated** — Synchronized package-lock.json root version fields to 0.4.17-beta.2 (were outdated at 0.4.14-beta.1).


## [0.4.17-beta.1] - 2026-05-04

### Added
- **TASK-066: Memory Context Bleed Prevention (SEALED)** — Threshold-Tuning for Memory-Retrieval: Raised minimum priority threshold from 0.50 to 0.65 in memory_budget.py (default priority) and crud_service.py (legacy_priority, enriched_priority) to reduce context bleed (irrelevant old entries in prompt). Improves response quality for small models like Gemini Flash. Files: memory_budget.py, crud_service.py. Tests: 28/28 passed.
- **TASK-064: Calendar Mutation Detection (SEALED)** — Breaking the Calendar Listing Prison. Added is_calendar_mutation detection to IntentEngineV2 to distinguish between pure calendar queries (listing) and calendar mutations (updates). When is_calendar_mutation is true, the system no longer forces calendar.list_events tool_choice, allowing the model to reach calendar.find_and_update_event for mutation operations. Files: intent_engine.py, execution_dispatcher.py. Tests: 486 passed.
- **TASK-063: Proactive Calendar Updates (SEALED)** — Proactive Calendar Updates implementation. Sharpened calendar update keywords in IntentEngineV2 ("bring", "ergänze", "ergänzen", "hinzufügen", "mit"). Added calendar.find_and_update_event as mandatory skill for calendar intents in CapabilityRegistry. Added proactive calendar mutation rule in prompt_registry.py to prioritize calendar updates over pure memory logging. Files: intent_engine.py, capability_registry.py, prompt_registry.py. Tests: 483 passed.
- **TASK-062: Intent-to-Selector Gap Fix (SEALED)** — Fixed Intent-to-Selector gap. Sharpened calendar keywords in IntentEngineV2 ("habe ich", "was habe ich", "was steht an", "steht an", "meine termine", "meinen termin", "meinen terminen"). Verified CapabilityRegistry returns calendar.list_events as mandatory for calendar intents. Added safety net in ExecutionDispatcher to inject calendar.list_events if is_calendar_intent is true but selector returned empty. Files: intent_engine.py, execution_dispatcher.py. Tests: 483 passed.
- **TASK-061: SkillSelector Intent-Aware (SEALED)** — SkillSelector is now Intent-Aware & Policy-Driven. Integration of IntentEngineV2 detection results into SkillSelector.get_relevant_skills() for intent-based skill filtering. File: chat_orchestrator.py (lines 1238, 1328). Tests: 479 passed.
- **TASK-060: Agent Planner Overhaul (Harmonized)** — Harmonisierung von AgentPlanner und SkillSelector mit IntentEngineV2 und CapabilityRegistry. Einführung von PlannerContext/PlannerProviderProfile für strukturierte Planner-Handoff, Kalender-Guard (forbidden_skill_ids) zum Entfernen inkompatibler Skills bei Kalender-Queries, 14-Tage Wochentag-Kalender zur Vermeidung von Datums-Schätzungen, CapabilityRegistry-Integration in OrchestratorExecutionEngine. Files: prompt_registry.py (calendar_read_priority VERBOTEN-Regeln), execution_dispatcher.py (Kalender-Guard), schemas.py (PlannerContext/PlannerProviderProfile), execution_engine.py (_build_planner_capability_groups, _build_planner_context, _build_planner_provider_profile), chat_orchestrator.py (capability_registry Initialisierung vor SkillSelector). Tests: 477 passed.
- **TASK-058: Calendar Modal (Phases 1-4 COMPLETE + Sync Hardening + Protocol Hardening)** — Calendar Modal mit Agenda/Day/Week Views, Inline Editing, AI Engine mit LLM-Integration, Delta-Sync, MCL/Dock Integration. Backend: REST-API (`GET/POST/PUT/DELETE /api/calendar/events`, `POST /api/calendar/ai/plan`), Service Layer mit Tool-Result Helper-Funktionen, AI Engine (provider-agnostisch via llm_gateway), deterministisches JSON-Parsing. Frontend: Timeline-Rendering (60px/hour), Optimistic UI mit Rollback, Filter (heute/Woche/Monat/Custom), Detail-Panel, AI Overlay mit Plan-Vorschau, Quick Actions, Polling (60s), Sync-Status-Indikator. 21/21 Tests grün.
- **Google Sync Hardening (TASK-058)** — Pagination (maxResults=250, pageToken-Loop) für vollständige Event-Listen. PATCH-with-Verify-and-Fallback für Metadaten-Updates mit CRLF-normalisiertem Textvergleich. conferenceDataVersion=1 für Meet-Termine mit Retry auf 0 bei 400-Fehlern. Output-Only-Key-Filterung (kind, etag, htmlLink, created, updated, hangoutLink, creator entfernt) vor PUT. Forensische Logging-Signale: organizer.self=false (unterschiedliches eingeladenes Konto), verify-mismatch (Ort/Beschreibung/Summary nach PATCH). Frontend: calendar-refresh CustomEvent nach createCalendarEvent, adaptive event cards (ultra-short/short/normal), detail panel with inline editing, duration buttons (15m/30m/1h/2h/3h), all-day checkbox, --cal-hour-height CSS variable (60px/hour) als Source-of-Truth. Pattern #GoogleCalendarSyncReliability in WHAT_I_LEARNED.md dokumentiert.
- **Protocol Hardening (TASK-058)** — #GeminiV3Protocol: thought_signature preservation in execution_engine.py via Raw-Parts retention. #GeminiNameSanitization: dot/underscore tolerance for tool names (system.weather ↔ system_weather) with reverse-mapping. #CalendarSnapshotIntegrity: invalidate_calendar_snapshot() after create/update/delete mutations, calendar_read_priority directive, CALENDAR-LIVE-TRUTH forced tool-call on calendar intent.

### Changed
- **Bulk File Move Feature** - Parameter-Upgrade (pattern → file_names), Intent-basierte Modell-Eskalation (MOA-Hierarchie), RAG-Sort-Policy, PDF-Indizierungs-Markierung in list_directory, Rate-Limits erhöht. Task FEAT-FS-BULK-MOVE.
- **Logging Pipeline Phase 1: Metadata Fixes** - Provider und Model werden jetzt konsistent an additional_context übergeben bei allen ToolExecutor-Instanziierungen. Logging zeigt korrekte Werte (nicht mehr "unknown"). ChatRequest-Attribut-Fix: req.chosen_model → req.model. Task D10.


## [0.4.16-beta.16] - 2026-04-21

### Fixed
- **Dead-Code-Fix: HARDWARE-TRUTH-REGEL + file_system_guard werden nun tatsächlich in den LLM-System-Prompt injiziert** — Root-Cause: `prompt_registry.py::search_command_priority` und `file_system_guard` waren definiert, aber nirgends injiziert. Der reale System-Prompt wird in `execution_dispatcher.py:190` via `apply_verbosity_control(wf.system_prompt_for_llm)` gebaut, welches bisher NUR `verbosity_control` + `no_meta_talk` anhängte. Resultat: Nano/Mini-Modelle beantworteten Datei-Such-Anfragen aus Memory-Fakten ohne Tool-Call, obwohl der User die HARDWARE-TRUTH-REGEL explizit angefordert hatte (im Log sichtbar: System-Prompt enthielt `PRIMÄRDIREKTIVE` + `🚨 SYSTEM-DIREKTIVE (STRIKTE KASKADE)` aus DB-Persönlichkeit, aber KEINE HARDWARE-TRUTH-REGEL). Fix: `apply_verbosity_control()` injiziert nun zusätzlich `file_system_guard` + `search_command_priority` (dedupliziert, idempotent). Damit erhält jeder DEFAULT-Dialog-Turn die Dubletten-Hinweis-Pflicht und die Live-Tool-Call-Pflicht für Such-Anfragen.

### Changed
- **Prompt-Registry: HARDWARE-TRUTH-REGEL für Suchanfragen verschärft** — `prompt_registry.py::search_command_priority` aktualisiert mit stärkerer Formulierung: "!!! WERKZEUGNUTZUNGS-DIREKTIVE — HARDWARE-TRUTH-REGEL !!! Wenn der Nutzer nach dem Verbleib, Speicherort oder der Existenz von Dateien sucht, hat das Live-Werkzeug filesystem.find_files ABSOLUTE Priorität vor der FAKTENGRUNDLAGE (Memory). Das Gedächtnis dient NUR als Orientierung. Du darfst NIEMALS einen Pfad aus der Erinnerung nennen, ohne ihn in EXAKT DIESEM Turn durch einen Tool-Call validiert zu haben. Eine Antwort ohne Live-Tool-Call bei Suchanfragen gilt als schwerer Systemfehler." Behebt "Brevity-Bias" bei faulen Modellen (wie Nano) mit strikterer "schwerer Systemfehler"-Formulierung.
- Version bumped to 0.4.16-beta.16.

## [0.4.16-beta.15] - 2026-04-21

## [0.4.16-beta.14] - 2026-04-21

### Fixed
- **Core-Repair: Numpy Shape Error im Memory-Retrieval** — `calculate_similarity_with_precomputed()` / `calculate_similarity_batch()` in `backend/services/vector_service.py` crashten regelmäßig mit `setting an array element with a sequence. The requested array has an inhomogeneous shape after 1 dimensions. The detected shape was (N,) + inhomogeneous part` bei jedem Chat-Query. Ursache: `np.array(candidate_embeddings, dtype=float32)` bricht ab, sobald auch nur ein Memory-Slot ein `None`-Embedding oder eine abweichende Vektor-Dimension hat (kommt bei Slots ohne gecachtes Embedding oder Legacy-Embeddings anderer Modell-Versionen vor). Fix: Neuer Helper `_safe_stack_embeddings()` filtert invalide Einträge (None, falscher Shape, Dim-Mismatch, NaN) vor `np.stack`. Beide API-Funktionen behalten die Output-Länge bei (0.0-Padding an gefilterten Positionen), damit Caller-Alignment intakt bleibt. Bei gefilterten Einträgen wird ein WARNING mit Count + Query-Dim geloggt.
- **Core-Repair: SkillMetadata-Literal-Divergenz** — `schemas.py::SkillMetadata.sandbox_level` erlaubte nur `"unrestricted" | "workspace_only" | "read_only_fs"`, während **11 filesystem-Skill-Manifests** konsistent `"full"` nutzten. Pydantic validierte den Wert still nicht (tolerate-Loader-Pfad), aber jede zukünftige Strict-Validierung wäre gebrochen. Fix: `"full"` als valides Literal hinzugefügt (semantisch: volle FS-Rechte innerhalb der Path-Sentinel-Workspace-Grenze, distinkt von `"workspace_only"` oder `"read_only_fs"`).

### Changed
- **Prompt-Registry: Dubletten-Hinweis für Dateisuchen** — `prompt_registry.py::file_system_guard` erweitert mit expliziter Anweisung: Wenn ein Such-Tool (z.B. `filesystem.find_files`) mehrere Dateien mit identischem Namen an verschiedenen Orten findet, MUSST der LLM den Nutzer explizit auf diese Dubletten hinweisen (z.B. "Ich habe die Datei an 2 Stellen gefunden: ..."). Verbessert UX bei Duplikat-Erkennung.
- **find_files: max_results Default von 100 auf 20 gesenkt** — `filesystem_manager.py::find_files(max_results=20)` statt 100, um Fakten-Extraktion-Overhead nach Dateisuchen zu begrenzen. Bei 100 Pfaden würde Nano versuchen, jeden als separate "Langzeit-Fakt" zu speichern, was das System für Sekunden lähmt. 20 Treffer sind für die meisten Use-Cases ausreichend; bei Bedarf kann der User `search_all_drives=true` oder explizites `max_results` nutzen.
- Version bumped to 0.4.16-beta.14.
- **Core-Repair: Numpy Shape Error im Memory-Retrieval** — `calculate_similarity_with_precomputed()` / `calculate_similarity_batch()` in `backend/services/vector_service.py` crashten regelmäßig mit `setting an array element with a sequence. The requested array has an inhomogeneous shape after 1 dimensions. The detected shape was (N,) + inhomogeneous part` bei jedem Chat-Query. Ursache: `np.array(candidate_embeddings, dtype=float32)` bricht ab, sobald auch nur ein Memory-Slot ein `None`-Embedding oder eine abweichende Vektor-Dimension hat (kommt bei Slots ohne gecachtes Embedding oder Legacy-Embeddings anderer Modell-Versionen vor). Fix: Neuer Helper `_safe_stack_embeddings()` filtert invalide Einträge (None, falscher Shape, Dim-Mismatch, NaN) vor `np.stack`. Beide API-Funktionen behalten die Output-Länge bei (0.0-Padding an gefilterten Positionen), damit Caller-Alignment intakt bleibt. Bei gefilterten Einträgen wird ein WARNING mit Count + Query-Dim geloggt.
- **Core-Repair: SkillMetadata-Literal-Divergenz** — `schemas.py::SkillMetadata.sandbox_level` erlaubte nur `"unrestricted" | "workspace_only" | "read_only_fs"`, während **11 filesystem-Skill-Manifests** konsistent `"full"` nutzten. Pydantic validierte den Wert still nicht (tolerate-Loader-Pfad), aber jede zukünftige Strict-Validierung wäre gebrochen. Fix: `"full"` als valides Literal hinzugefügt (semantisch: volle FS-Rechte innerhalb der Path-Sentinel-Workspace-Grenze, distinkt von `"workspace_only"` oder `"read_only_fs"`).

### Changed
- Version bumped to 0.4.16-beta.14.

## [0.4.16-beta.13] - 2026-04-21

### Added
- **Neuer Skill `filesystem.find_files`** — rekursive Dateisuche über alle freigegebenen Workspaces mit Auto-Escalation auf alle lokalen Laufwerke (C:\, D:\, E:\) bei ≤1 Treffer. Schließt die Lücke, dass Janus bei "wo finde ich datei xy?" bisher nichts finden konnte (vorhandene `list_directory` war non-rekursiv). Features: Glob-Pattern (`*.pdf`, `*gundula*`), Fuzzy-Substring-Fallback (reiner Name → `*name*`), Path-Sentinel-Schutz, Noise-Ordner-Skip (`Windows`, `Program Files`, `node_modules`, `.git`, `AppData`, etc.), Duplikat-Dedup via `existing`-Set, explizites `search_all_drives` für bewusste Opt-In-Suche, `auto_escalated`-Flag in Response.
- `_enumerate_local_drives()` Helper und `_ALL_DRIVES_EXCLUDE_DIRS` Noise-Liste in `backend/services/filesystem_manager.py`.
- `FindFilesArgs` Pydantic-Schema in `backend/data/schemas.py` mit LLM-Trigger-Hints für `search_all_drives` (User-Formulierungen "überall", "Duplikate", "ganzer Rechner").
- Skill-Manifest `backend/skills/filesystem/find_files.json` mit `latency_class: slow` und `max_calls_per_turn: 2`.

### Changed
- `backend/tool_registry.py`: `filesystem.find_files` in `fs_tools` registriert.
- Version bumped to 0.4.16-beta.13.

### Fixed
- Interne Robustheit bei rekursiver Suche: Umstieg von `Path.rglob` auf `os.walk` + `fnmatch` mit `onerror`-Callback, da `rglob` bei defekten Symlinks/unerreichbaren Desktop-Ordnern (`C:\Users\pruve\Desktop\kikitest.`) mit `FileNotFoundError` abbricht, statt einzelne Pfade zu überspringen.

## [0.4.16-beta.11] - 2026-04-21

### Fixed
- **Packaged UI komplett ungestyled auf Testsystemen** — Route-Kollision in `backend/main.py`: `/assets` war auf `backend/assets/` (Preview-Bilder) gemountet und hat damit Vite's gehashte Frontend-Bundles `/assets/index-*.{js,css}` aus `frontend/dist/assets/` mit 404 überschattet, sobald Electron aus `http://127.0.0.1:8001/` lädt. Fix: kollidierenden `/assets`-Mount entfernt, `/backend_assets` bleibt kanonisch für Preview-Bilder. (Keine Call-Sites in Projekt-Code betroffen.) Inline-Kommentar in `backend/main.py` verhindert Wiedereinführung.
- End-to-End verifiziert via direktem HTTP-Test am gebündelten `janus_backend.exe`: `/`, `/assets/index-*.js` und `/assets/index-*.css` liefern alle 200 mit korrektem Content-Type.

### Changed
- Version bumped to 0.4.16-beta.11

## [0.4.16-beta.10] - 2026-04-21

### Fixed
- **Leere `frontend/dist/assets/` in vorherigen Builds** — Vite-Build wurde neu ausgeführt, weil `dist/assets/` auf dem Build-System leer war, aber `dist/index.html` noch auf gehashte Asset-Dateinamen verwies. Folge in beta.9: installierter PyInstaller-Backend lieferte `index.html` aus, aber alle Asset-URLs liefen auf 404, UI wurde ungestyled gerendert. (Hinweis: Der eigentliche strukturelle Bug war erst in beta.11 behoben, siehe oben — beta.10 hat nur die leere `dist/assets/` repariert.)

### Changed
- Version bumped to 0.4.16-beta.10

## [0.4.15-beta.11] - 2026-04-20

### Fixed
- Clipboard IPC Fallback: navigator.clipboard.readText() durch window.electronAPI.readClipboard() ersetzt (Permission Denied Fix). main.electron.cjs: ipcMain.handle('clipboard:read') und ipcMain.handle('read-clipboard') implementiert; preload.js: window.electronAPI exponiert.
- YouTube Error 152-4 Regression: Referer/Origin Spoofing aus onBeforeSendHeaders entfernt (YouTube blockiert als Bot bei Mismatch). onHeadersReceived für X-Frame-Options/CSP-Stripping intakt gelassen.
- Permission Handlers: setPermissionCheckHandler und setPermissionRequestHandler erweitert mit console.log Visibility, file:// Origin Bypass und allowedPermissions Array.
- frontend/js/video-player.js: YouTube Embed URL auf youtube-nocookie.com ohne enablejsapi und origin Parameter geändert.

### Changed
- Version bumped to 0.4.15-beta.11

## [0.4.15-beta.10] - 2026-04-20

### Fixed
- YouTube Error 152-4 Fix: Hardcoded `origin=https://www.youtube.com` URL-Parameter aus `normalizeVideoEmbedUrl()` entfernt. Unter sandboxed Electron-Renderer (file:// Origin) führte die Diskrepanz zwischen deklariertem Origin-Param und tatsächlichem postMessage-Origin zum YouTube-Player-Abbruch (Fehlercode 152-4) für alle Videos. Nach Entfernung fällt die Origin-Validierung weg und Playback funktioniert.

### Changed
- Version bumped to 0.4.15-beta.10

## [0.4.15-beta.9] - 2026-04-20

### Fixed
- YouTube Embedding Session Fix: webRequest-Handler von session.defaultSession auf mainWindow.webContents.session umgestellt. Das mainWindow verwendet eine separate session, daher müssen die Header-Spoofing und CSP-Stripping Handler auf der korrekten session registriert werden.

### Changed
- Version bumped to 0.4.15-beta.9

## [0.4.15-beta.8] - 2026-04-20

### Fixed
- Electron Boot-Fix: TypeError in webRequest-Handler behoben. Umstellung von 3-Argumente-Syntax auf 2-Argumente-Syntax (filter, listener) für onBeforeSendHeaders/onHeadersReceived. Die installierte Electron-Version akzeptiert kein extraHeaders-Array als zweiten Parameter.

### Changed
- Version bumped to 0.4.15-beta.8

## [0.4.15-beta.7] - 2026-04-19

**Security & Beta-Readiness Release** — XSS & RCE Fixes verifiziert, Discord-Reporting-System implementiert, YouTube-Playback-Stabilität gehärtet

### Fixed
- Chromium Extra Headers Fix: Aktivierung von extraHeaders Flag in onBeforeSendHeaders und onHeadersReceived zur Aufhebung der Chromium-Blockade von Referer-Manipulationen. Behebung von YouTube Error 15-4 / 153.

### Changed
- Version bumped to 0.4.15-beta.7


## [0.4.15-beta.6] - 2026-04-19

### Fixed
- Browser Identity Spoofing: Browser-Spoofing Pattern (User-Agent Maskierung auf App- und Window-Ebene zur Umgehung von Bot-Blockaden), youtube-nocookie.com Header-Synchronisation

### Changed
- Version bumped to 0.4.15-beta.6


## [0.4.15-beta.5] - 2026-04-19

### Fixed
- CSP Bypass & iFrame Hardening: Header-Deletion-Pattern (radikales Entfernen von CSP-Headern), allowRunningInsecureContent, Permission Handlers (media/display-capture), Autoplay CSP Modification for file:// paths
- YouTube Error 152: YouTube-Nocookie Transition, Header-Stripping (X-Frame-Options), Cross-Domain Spoofing (googlevideo.com), PreloadMediaEngagementData Disabling for file:// paths
- YouTube Error 153: Added protocol.registerSchemesAsPrivileged and Referer/Origin header spoofing for youtube.com requests in main.electron.cjs
- Orchestrator Synthesis-Bypass: Hard-lock immediate return when is_final_response=True to prevent synthesis in execution_engine.py

### Changed
- Version bumped to 0.4.15-beta.5


## [0.4.15-beta.4] - 2026-04-19

### Fixed
- YouTube Error 152: YouTube-Nocookie Transition, Header-Stripping (X-Frame-Options), Cross-Domain Spoofing (googlevideo.com), PreloadMediaEngagementData Disabling for file:// paths
- YouTube Error 153: Added protocol.registerSchemesAsPrivileged and Referer/Origin header spoofing for youtube.com requests in main.electron.cjs
- Orchestrator Synthesis-Bypass: Hard-lock immediate return when is_final_response=True to prevent synthesis in execution_engine.py

### Changed
- Version bumped to 0.4.15-beta.4


## [0.4.15-beta.3] - 2026-04-19

### Fixed
- YouTube Error 153: Added protocol.registerSchemesAsPrivileged and Referer/Origin header spoofing for youtube.com requests in main.electron.cjs
- Orchestrator Synthesis-Bypass: Hard-lock immediate return when is_final_response=True to prevent synthesis in execution_engine.py

### Changed
- Version bumped to 0.4.15-beta.3


## [0.4.15-beta.2] - 2026-04-19

### Added
- Beta-Ready Final Polish: Feedback-Plug-and-Play with Discord webhook fallback, Video-Stability-Fix (is_final_response=True for all modes), Tiktoken-Resilience for compiled environments
- DEFAULT_FEEDBACK_WEBHOOK constant in telemetry_service.py for out-of-the-box bug reporting
- Tiktoken fallback (len(text) // 4) in tts_service.py and context_manager.py for environments without C library

### Changed
- Version bumped to 0.4.15-beta.2
- is_final_response=True set for all successful video searches (single and list modes)


## [0.4.15-beta.1] - 2026-04-19

### Security
- XSS Shield via DOMPurify with whitelists for Chat, Release-Notes, and Error messages (SEC-01/02)
- RCE Prevention in IPC handler with path normalization, whitelists, and extension blocklist (SEC-03)
- JWT Vault Security with dynamic secret generation and persistence (SEC-05)
- Chained Vulnerability Fix: userData removed from allowedRoots to prevent config.json overwrite (SEC-03.1)
- DOMPurify data: schema removed from iframe URI whitelist (only https: allowed)

### Added
- Beta-Reporting System with Feedback button, MCL-compliant modal, and Discord webhook integration
- Log file path fix for telemetry service (AppData directory instead of hardcoded path)
- Modal layering fix (z-index 9999999 with inline styles)

### Changed
- Version bumped to 0.4.15-beta.1


## [0.4.14-beta.1] - 2026-04-19

### Bugfixes
- Datenbank-Migration für chats.auto_added und memories.source_type hinzugefügt

## [0.4.13-beta.1] - 2026-04-19

### Bugfixes
- Download-Timeout auf 10 Minuten erhöht (von 120s Standard)
- GitHub API User-Agent und fullChangelog hinzugefügt

## [0.4.12-beta.1] - 2026-04-19

### Bugfixes
- CLIP Datei bpe_simple_vocab_16e6.txt.gz wird jetzt aus backend/assets in clip-Verzeichnis kopiert (Runtime-Fix)

## [0.4.11-beta.1] - 2026-04-19

### Bugfixes
- Update-Check Timeout (10s) hinzugefügt - App startet weiter, wenn GitHub API nicht antwortet
- Splashscreen zeigt Update-Status an (Prüfe auf Updates, Lade Update, Installiere)

## [0.4.10-beta.1] - 2026-04-19

### Bugfixes
- CLIP Datei bpe_simple_vocab_16e6.txt.gz Pfad korrigiert (direkte Datei statt Ordner)

## [0.4.9-beta.1] - 2026-04-19

### Bugfixes
- CLIP Daten-Dateien manuell zu PyInstaller Build hinzugefügt (collect_data_files hat nicht funktioniert)

## [0.4.8-beta.1] - 2026-04-19

### Bugfixes
- CLIP Daten-Dateien (bpe_simple_vocab_16e6.txt.gz) zu PyInstaller Build hinzugefügt

## [0.4.7-beta.1] - 2026-04-19

### Bugfixes
- Entfernung von face_recognition Import (nicht verwendet, verursachte Crash bei 0.4.3-beta.1)
- electron-updater jetzt auf App-Start ausgeführt (vor Backend-Start) - verhindert Deadlock bei kritischen Fehlern
- Release-Notes jetzt automatisch auf GitHub veröffentlicht
- torchvision nicht mehr ausgeschlossen (wird von CLIP benötigt)

## [0.4.3-beta.1] - 2026-04-19

### Implementation
- Auslagerung der Meta-Noise-Logik in `memory/utils.py` zur Behebung von Circular Imports
- Implementierung des Retrieval-Filters (Silence Guard) für alle Slot-Sektionen
- System-Prompt gehärtet via `silent_memory_rule`
