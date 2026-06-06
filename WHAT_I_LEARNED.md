# KNOWLEDGE BASE: WHAT I LEARNED

## [PATTERN] #WeatherFormatterOwnsCrossProviderParity "Weather answers should be normalized in the product formatter, not left to provider style"
- **Kontext:** BACKLOG-095 / Weather API response parity and documentation closure.
- **Problem:** GPT/HPZ and Gemini can both produce correct weather facts but wrap them in different surface styles, which creates a UX split even when the underlying data is the same.
- **Loesung:** Put the user-facing weather contract in a deterministic formatter and make the finalizer prefer the structured weather forecast text over provider-generated prose. Keep location, period, weather state, temperatures, rain probability, wind and a clear source line together in one stable layout.
- **Haertung:** Focused weather renderer and attribution tests passed; focused regression checks stayed green; live weather output now matches the shared bulletpoint format for GPT/HPZ and Gemini.
- **Tripwire:** If a future weather answer returns the same facts but different provider-specific prose, the formatter/finalizer path has drifted and should be corrected before touching provider prompts.
- **Location:** `backend/tools/weather_service.py`, `backend/renderers/implementations/weather_renderer.py`, `backend/renderers/attribution.py`, `backend/services/orchestrator/execution_engine.py`, `backend/services/orchestrator/response_finalizer.py`
- **Epic:** BACKLOG-095
- **Confidence:** High
- **Tags:** Weather, ProviderParity, Formatting, SourceAttribution, UX, DeterministicRendering

## [PATTERN] #FrontendConsoleMirrorForChatState "Renderer console logs should be mirrored to documentation/logs for chat-state debugging"
- **Kontext:** BACKLOG-096 / Chat-header new-chat persistence and observability closure.
- **Problem:** Frontend-only state regressions, especially window-local chat header overrides, are hard to diagnose when only backend stream logs are available.
- **Loesung:** Mirror renderer console output from the Electron main process into `documentation/logs/janus_frontend.log` alongside `janus_backend.log`, so UI state transitions like `createNewChat`, `loadChat`, header override sync and related warnings can be read in one place.
- **Haertung:** New log sink written via `mainWindow.webContents.on('console-message', ...)` and validated by syntax checks plus manual Janus retest. The frontend log now captures the new-chat flow needed to verify GPT and Gemini behavior side by side.
- **Tripwire:** If frontend regressions can no longer be matched against backend streams in the same log folder, the renderer log sink has been removed or broken.
- **Location:** `main.electron.cjs`, `documentation/logs/janus_frontend.log`
- **Epic:** BACKLOG-096
- **Confidence:** High
- **Tags:** Logging, Frontend, Electron, Debugging, ChatState, Observability

## [PATTERN] #LiveOllamaLibraryRecommendations "Local LLM recommendations should prefer the current Ollama library and fall back only when the live lookup fails"
- **Kontext:** BACKLOG-097 / Local LLM setup rerun and recommendation refresh.
- **Problem:** A local setup wizard can become stale if it keeps recommending a fixed model matrix instead of reflecting the current Ollama library and the user's actual hardware/tool profile.
- **Loesung:** Fetch the current Ollama search page during the hardware scan, parse model names/capabilities/size tags, prefer local tool/reasoning-capable matches within the detected hardware budget, and append a small coding-focused pair of recommendations for vibecoding workflows. Keep a deterministic fallback matrix only for live-search failure.
- **Haertung:** `backend/services/ollama_manager.py` now returns live library models, the recommendation tests validate the live path and the fallback path, and manual Janus verification showed the refreshed list changing after rerun.
- **Tripwire:** If the setup wizard again shows the same frozen recommendations after a hardware rescan, the live library lookup or the fallback merge has drifted.
- **Location:** `backend/services/ollama_manager.py`, `backend/tests/test_ollama_manager_recommendations.py`, `frontend/src/components/Settings/LocalLLMWizard.tsx`
- **Epic:** BACKLOG-097
- **Confidence:** High
- **Tags:** Ollama, LocalLLM, Recommendations, HardwareScan, ToolCalling, Vibecoding, UX
## [PATTERN] #BACKLOG-098_MailAiMustFailVisibleNotSilent "Mail-AI errors must surface as degraded state and log redaction must keep sensitive mail content out of technical traces"
- **Kontext:** BACKLOG-098 / Janus Mail bundle final audit hardening.
- **Problem:** AI thread-assist could silently fall back to heuristic outputs when provider payloads failed, and technical debug logs could expose sensitive mail details (subject/body/attachment names).
- **Loesung:** Enforce explicit degraded responses (`degraded=true`, `error_message`) for missing provider, provider failures, invalid AI payload and empty drafts. Redact technical mail logs to counters/lengths and non-sensitive IDs instead of content.
- **Haertung:** Final audit blocker resolved; targeted backend/frontend tests PASS (44 + 7), py_compile PASS, live Janus behavior kept manual mail workflow usable during AI failure.
- **Tripwire:** If an AI failure produces a normal-looking success response or technical logs again contain mail subject/body/attachment names, privacy and trust guarantees have regressed.
- **Location:** `backend/services/mail/mail_ai_assist_service.py`, `backend/services/chat_orchestrator.py`, `backend/data/schemas_mail.py`, `frontend/js/mail-modal.js`, `backend/tests/test_mail_ai_assist_service.py`
- **Epic:** BACKLOG-098
- **Confidence:** High
- **Tags:** Mail, AI, Privacy, DegradedState, Logging, AuditHardening

## [PATTERN] #MAIL_PERSIST_ORIGINAL_USER_TURN "Mail control replies must not overwrite the persisted user turn, and categorized attachment saves must not fall back to a blank extra folder"
- **Kontext:** BACKLOG-099 / Restart-Persistenz und kategorisierter Mail-Ordner-Flow.
- **Problem:** Der Mail-Flow ersetzt den sichtbaren Chat-Text bei Restart manchmal durch interne Auswahlwerte wie `1` oder `3`, und der kategorisierte Attachment-Save konnte versehentlich einen leeren Default-Ordner `rechnungen` anlegen.
- **Loesung:** Den originalen User-Text vor internen Mail-Flow-Overrides einfrieren, Control-Replies nicht als normale Historiennachricht persistieren und im kategorisierten Save-Flow ausschließlich die expliziten Zielordner `papierkram rechnungen`, `vodafone rechnungen` und `sonstige rechnungen` verwenden.
- **Haertung:** Finaler Re-Audit PASS WITH FIXES, gezielte Regression gegen Restart-/Reload-Darstellung und den 3-Ordner-Speicherpfad, Backend py_compile gruen.
- **Tripwire:** Wenn nach einem Mail-Account-Dialog oder einer Mehrordner-Anweisung im Verlauf nur noch eine Zahl steht oder wieder ein leerer `rechnungen`-Ordner erzeugt wird, hat Persistenz bzw. kategorisierter Save-Flow erneut den Originalturn verloren.
- **Location:** `backend/services/chat_orchestrator.py`, `documentation/backlog/BACKLOG.md`, `documentation/test-runs/BACKLOG-098_mail_bundle_reaudit_2026-05-30.md`
- **Epic:** BACKLOG-099
- **Confidence:** High
- **Tags:** Mail, Persistence, Restart, ControlReply, AttachmentSave, FolderRouting

## [PATTERN] #MAIL_PROVIDER_CATEGORY_CLARITY_FIRST "Provider-plus-category mail search must clarify ambiguity before execution and keep evidence in every hit row"
- **Kontext:** BACKLOG-100 / generische Anbieter-Mail-Suche nach Inhaltstypen.
- **Problem:** Natuerliche Mailanfragen wie "Rezepte von Anbieter X" kippen leicht in unscharfe Treffer oder falsche Fallback-Routen, wenn Anbieter oder Kategorie mehrdeutig sind.
- **Loesung:** Den Suchpfad als klare Anbieter-plus-Kategorie-Route behandeln, bei Mehrdeutigkeit gezielt nachfragen, Treffer konservativ filtern und pro Treffer eine kurze Evidenzzeile aus Betreff/Kurzinhalt ausgeben.
- **Haertung:** Final Audit PASS; py_compile PASS; fokussierte Backend-Regression PASS (39/39); Frontend-Mail-Filtertest PASS (3/3); manuelle Janus-Evidenz fuer Detailansicht und PDF-Export vorhanden.
- **Tripwire:** Wenn Treffer ohne Evidenz erscheinen, mehrere Anbieter/Kategorien stillschweigend zusammengezogen werden oder der Flow in Attachment-Suche abdriftet, ist die Route wieder unscharf.
- **Location:** `backend/services/chat_orchestrator.py`, `backend/services/orchestrator/execution_dispatcher.py`, `backend/services/orchestrator/intent_engine.py`, `backend/tools/pdf_generator.py`, `backend/services/mail/mail_keyword_result_store.py`
- **Epic:** BACKLOG-100
- **Confidence:** High
- **Tags:** Mail, IntentRouting, Ambiguity, Evidence, PDFExport, RegressionSafety


## [PATTERN] #GeminiAttributionMustKeepPolicyAndCostSplitAligned "Gemini grounding/websearch policy evidence must stay aligned with component cost attribution"
- **Kontext:** TASK-SPEC14 final audit remediation for Gemini cost attribution and DeepDive forensics (2026-06-03).
- **Problem:** Gemini websearch can regress in three coupled ways at once: silent Pro routing without visible override, duplicated search cost between conversation and websearch components, and nested attribution metadata leaking prompt or response fragments.
- **Loesung:** Treat Gemini grounding/websearch as a shared contract across ToolExecutor, gateway persistence, and cost sanitization. Default websearch to gemini-3-flash-preview unless a visible MODEL_OVERRIDE is present, persist grounding_websearch separately from residual conversation cost inside one request group, and recursively strip sensitive nested attribution keys before storage.
- **Haertung:** Final re-audit PASS. Focused suites passed: cost-token 9/9, routing/provider-policy 10/10, websearch 102/102, model-discipline 7/7, plus py_compile and frontend node check.
- **Tripwire:** If DeepDive totals exceed the real request sum, Gemini websearch uses Pro without a visible override, or attribution metadata starts containing nested prompt/response/messages/chat_history fields, the provider-policy and attribution contract has drifted.
- **Location:** backend/services/tool_executor.py, backend/llm_providers/gemini/gateway.py, backend/services/cost_service.py, backend/tests/test_backlog_007_tool_routing_performance.py, backend/tests/test_cost_token_tracking_completeness.py, backend/tests/tools/test_websearch.py
- **Epic:** TASK-SPEC14
- **Confidence:** High
- **Tags:** Gemini, CostAttribution, DeepDive, ProviderPolicy, Privacy, Websearch, AuditHardening

## [PATTERN] #DeepDiveMustKeepCrossProviderOverviewAndForensicsTogether "A forensic deep dive should add a top-level cross-provider cost view, not replace it"
- **Kontext:** BACKLOG-101 / DeepDive Cross-Provider Transparenz und Cache-Savings nach Spec-14-Regressionsrepair.
- **Problem:** Eine forensische Spezialansicht fuer einen Provider kann fachlich korrekt sein und trotzdem die eigentliche Nutzerwahrheit verschlechtern, wenn dabei die fruehere Gesamtansicht fuer andere Provider, Modelle und Savings aus dem sichtbaren DeepDive verschwindet.
- **Loesung:** Das DeepDive in zwei explizite Ebenen teilen: oben eine provideruebergreifende Kostenuebersicht mit Provider-/Modellsplits sowie Cache-/Savings-Metriken, darunter die spezifische Forensik mit Anomalien, Billing-Abweichungen, Restposten und Request-/Komponenten-Drilldown. Keine parallele neue Billing-Oberflaeche bauen; die bestehende Modal-Surface erweitern.
- **Haertung:** Focused backend contract test stayed green, `node --check` on the modal renderer passed, and a permanent Playwright smoke now fails if GPT/OpenAI visibility, model rows, savings text or Gemini forensics disappear from the same modal.
- **Tripwire:** If a future DeepDive change again shows only one provider's forensic story but no cross-provider totals, no per-model view or no savings signal, the regression is back even if the provider-specific payload still looks internally correct.
- **Location:** `backend/data/crud.py`, `backend/api/routers/system.py`, `frontend/js/cost-visualizer.js`, `frontend/src/styles.css`, `backend/tests/test_cost_token_tracking_completeness.py`, `tests/e2e/generated/BACKLOG-101-ui-smoke.spec.js`
- **Epic:** BACKLOG-101
- **Confidence:** High
- **Tags:** DeepDive, CostTransparency, ProviderParity, Savings, UX, RegressionGuard, Gemini, OpenAI


## [PATTERN] #GeminiStreamUsageMustNotDoublePersistAttributedCosts "Gemini stream final usage costs must not be persisted a second time outside the attributed gateway path"
- **Kontext:** BACKLOG-102 / Gemini streaming attribution gap after Spec-14 cost forensics and DeepDive rollout. (2026-06-04).
- **Problem:** A generic stream-final-usage persistence path can silently create extra unscoped Gemini cost rows after the Gemini gateway already saved request-attributed cost components, which reappears in DeepDive as a fake attribution gap instead of a real billing residual.
- **Loesung:** Keep Gemini request cost persistence single-owned by the Gemini gateway attribution path. The generic stream_final_usage persistence helper should skip gemini/google so that only providers without their own request-attribution contract continue using that fallback row.
- **Haertung:** Focused cost-token regression suite passed 10/10, including a provider guard test that excludes gemini/google from generic stream persistence while leaving openai/anthropic enabled.
- **Tripwire:** If new Gemini DeepDive entries again show unattributed stream_final_usage rows without attribution_request_id, or Gemini totals exceed the gateway-attributed request sum, a second persistence path has leaked back in.
- **Location:** backend/services/orchestrator/execution_engine.py, backend/tests/test_cost_token_tracking_completeness.py
- **Epic:** BACKLOG-102
- **Confidence:** High
- **Tags:** Gemini,CostAttribution,Streaming,DeepDive,DuplicatePersistence,RegressionGuard

## [PATTERN] #DevRuntimeLogsNeedOneDocumentedSink "Local dev start paths should share one documented runtime log folder instead of growing root-level log files"
- **Kontext:** BACKLOG-105 / Monthly healthcheck repo-hygiene hardening for recurring backend and Vite logs.
- **Problem:** Local dev helper paths can silently normalize bad hygiene if they keep creating ad-hoc `.log` files in the repository root. Even when those files are ignored by Git, they still drag system health down and make the workspace feel dirtier than the actual code state.
- **Loesung:** Route versioned local dev start paths through one shared helper that mirrors stdout/stderr to the console while writing runtime logs into a dedicated folder such as `debug_logs/`. Document that folder in the dev runbook so the intended sink is explicit and auditable, not just implied by code.
- **Haertung:** `start-vite` now runs through `scripts/run-vite-dev.cjs`, backend dev runs use the shared log helper, syntax checks passed for all touched scripts, and the final re-audit passed only after the `debug_logs/` target path was documented in `CODEX_DEV_ENVIRONMENT_RUNBOOK.md`.
- **Tripwire:** If new recurring backend or Vite `.log` files start appearing in the repo root again, either a versioned start path bypassed the shared helper or the documented log-sink rule drifted out of sync with the scripts.
- **Location:** `package.json`, `scripts/run-backend-dev.cjs`, `scripts/run-vite-dev.cjs`, `scripts/dev-log-utils.cjs`, `documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md`
- **Epic:** BACKLOG-105
- **Confidence:** High
- **Tags:** Logging, DevEnvironment, RepoHygiene, RuntimeLogs, Vite, Backend, AuditHardening


## [PATTERN] #StartupTelemetryAndHealthcheckMustShareDocumentedLogContract "Startup telemetry and monthly healthcheck should share one documented log-path contract"
- **Kontext:** BACKLOG-107 / script output path hardening and root suspicious reduction (2026-06-06).
- **Problem:** Startup telemetry can silently drift into ad-hoc folders while monthly hygiene checks still treat old root logs as fresh suspicious artifacts, which makes repo health look worse even when current versioned script paths are already fixed.
- **Loesung:** Keep dev startup telemetry on one documented repo-local path such as documentation/logs/janus_startup_telemetry.log and teach the monthly health snapshot to classify known historical root log families separately from genuinely new suspicious root files.
- **Haertung:** Node syntax checks, Python py_compile, startup_config pytest, monthly health_snapshot PASS, and final audit PASS confirmed the shared contract and left root_suspicious empty for the known recurring legacy log family.
- **Tripwire:** If startup markers start writing into a new ad-hoc folder again or monthly health checks reintroduce the same old root log names under root_suspicious, the telemetry path contract and healthcheck classification have drifted apart.
- **Location:** scripts/write-startup-marker.cjs, backend/services/telemetry/startup_config.py, electron/startup-telemetry.cjs, backend/main.py, documentation/codex/skills/janus-health-check/scripts/health_snapshot.py, documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md
- **Epic:** BACKLOG-107
- **Confidence:** High
- **Tags:** Logging, StartupTelemetry, RepoHygiene, Healthcheck, LegacyArtifacts, Observability
