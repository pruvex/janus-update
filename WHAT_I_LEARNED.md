# KNOWLEDGE BASE: WHAT I LEARNED

## [SKIP] TASK-CHATGPT-CODEX.1 "Partial Codex runtime boundary does not yet establish a full provider pattern"
- **Kontext:** Task-scoped final-audit documentation update for the isolated official Codex App Server lifecycle boundary (2026-07-14).
- **Reason:** The validated rule is deliberately incomplete at feature level: settings UI, provider visibility, model entitlements, transport, privacy-send flow, and account UX remain separately gated Tasks `.2` through `.4`. Recording it as a general provider pattern now would overclaim unimplemented behavior.
- **Tripwire:** When a later task connects the boundary to visible provider use, re-evaluate whether the combined managed-auth, entitlement, and no-fallback behavior has enough cross-slice evidence for a durable pattern.
- **Epic:** TASK-CHATGPT-CODEX.1

## [PATTERN] #ExactChatContactFactsCanAutoApplyWhileMemoryWritesStayReviewable "Exact existing-contact chat facts can auto-apply safely when memory-origin writes stay on the proposal path"
- **Kontext:** BACKLOG-108 / bestaetigtes Kontaktwissen aus Chat landet nicht im bestehenden Adressbuchkontakt (2026-06-07).
- **Problem:** Bestätigte Kontaktfakten aus der Hintergrund-Faktenextraktion konnten bei bestehenden Kontakten unsichtbar im Memory-/Pending-Proposal-Seam hängen bleiben, obwohl der Nutzer im Chat bereits eine klare, direkte Bestätigung geliefert hatte.
- **Loesung:** Den direkten Apply-Pfad nur für den engsten sicheren Fall öffnen: `source_type="text"`, exakter bestehender Kontakt-Match, nicht-sensitive Fakten und nur `preferences`/`dislikes`. Memory-Tool-Writes, sensitive Fakten, Near-Matches und mehrdeutige Fälle bleiben weiter im bestehenden Proposal-/Review-Pfad.
- **Haertung:** Gesamtregressionen für Kontakt-/Memory-Pfade PASS; fokussierter Seam-Test für `Christoph Gier liebt Star Wars` PASS; Gegenprobe für weiter pending bleibende Memory-Tool-Suggestions PASS; Final Audit PASS mit kompaktem Audit-Package und gebundener Seam-Evidenz.
- **Tripwire:** Wenn bestehende Kontakte wieder nur ein Memory-Fakt bekommen, aber keine Kontaktmutation sehen, oder wenn spätere Memory-Tool-Writes plötzlich still direkt Kontakte verändern, ist die Trennung zwischen bestätigtem Chat-Fakt und review-pflichtigem Memory-Ursprung driftig geworden.
- **Location:** `backend/services/contact_manager.py`, `backend/tests/test_contact_manager.py`, `backend/tests/test_memory_tools.py`, `documentation/test-runs/BACKLOG-108_execution_validation.md`
- **Epic:** BACKLOG-108
- **Confidence:** High
- **Tags:** Contacts, Memory, Persistence, ProposalFlow, SafetyBoundary, Regression, Audit

## [SKIP] TASK-SPEC16 "No new cross-feature learning pattern recorded"
- **Kontext:** TASK-SPEC16 / Adressbuch-Karten Redesign und Spitzname/Besonderheiten-Struktur documentation update.
- **Reason:** Die Umsetzung erweitert ein bestehendes Adressbuch kontraktkonform um Spitzname, bereinigte Karten und den kombinierten Besonderheiten-Pfad, erzeugt aber kein neues repo-weites Muster ueber bereits dokumentierte UI-Evidence- und Compatibility-Hardening-Regeln hinaus.
- **Tripwire:** Wenn kuenftige Kontaktmigrationen persoenliche Details aus mehreren Legacy-Feldern in eine neue sichtbare Struktur ueberfuehren muessen und dabei wiederholbar dieselbe Kompatibilitaetslogik oder neue Audit-Hardening-Regeln entsteht, sollte daraus ein echtes Pattern erfasst werden.
- **Epic:** TASK-SPEC16

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

## [PATTERN] #ContactPetDetailsShouldNormalizeToSingleSentence "Pet details on contact cards should collapse into one clean sentence per pet"
- **Kontext:** BACKLOG-110 / Kontakt-Wohnort landet als Besonderheit statt im Adressblock (2026-06-15).
- **Problem:** Contact cards can accumulate multiple overlapping pet snippets such as `hat einen Hund`, `Olis hund heißt tasso`, `Oli hat auch eine katze`, and `hat eine Katze`, which makes the contact card look fragmented even when the facts are all correct.
- **Loesung:** Normalize pet facts on the contact read/write path into a single sentence form per pet, prefer the named variant when it exists (`hat einen Hund namens tasso`), map owner-prefixed `auch` variants to a clean generic sentence (`hat eine Katze`), and drop weaker duplicates when a stronger named variant is already present.
- **Haertung:** `python -m py_compile backend/data/crud.py backend/tests/test_contact_card_normalization.py` PASS; `python -m pytest backend/tests/test_contact_card_normalization.py -q` PASS; live Janus retest PASS with a clean address-book view.
- **Tripwire:** If pet facts reappear as separate cluttered lines or a named pet reverts to a generic duplicate, the contact normalization layer has drifted.
- **Location:** `backend/data/crud.py`, `backend/tests/test_contact_card_normalization.py`, `documentation/test-runs/BACKLOG-110_debug_contact_apply_normalization_addendum_2026-06-14.md`
- **Epic:** BACKLOG-110
- **Confidence:** High
- **Tags:** Contacts, Normalization, Deduplication, PetFacts, UX, Regression

## [PATTERN] #ContactBackedPetOverviewMustOverrideStaleMemory "Contact-backed pet overview answers should override stale memory-only pet facts on recall and fallback paths"
- **Kontext:** BACKLOG-115 / Oliver-Kontaktkarte zeigt Duplikate und unsaubere Haustierdetails (2026-06-30).
- **Problem:** Even after the visible contact card is cleaned up, a user-facing pet overview answer can still drift if `memory.read` or a later response fallback mixes authoritative contact-backed pet facts with older free-form memory snippets such as `Garfield mag keinen Thunfisch`.
- **Loesung:** Treat the contact-backed pet facts as the authority for this query class. Normalize possessive aliases like `olis`, stop subject extraction at pet-context words, and let the response fallback render one compact per-pet summary while filtering out weak preference/dislike drift and tautological pet-type lines.
- **Haertung:** Focused recall and fallback suites PASS; direct AppData `memory.read` probe returns only the four contact-backed pet facts; direct fallback render probe returns `Über Olis Haustiere weiß ich:` plus the compact Tasso/Garfield summary; Final Audit PASS.
- **Tripwire:** If a future `was weißt du über olis haustiere?` answer again drops the cat/dog identity, revives `Garfield mag keinen Thunfisch`, or shows mojibake like `Ã...`, the contact-backed pet-overview authority chain has drifted.
- **Location:** `backend/tools/memory_tools.py`, `backend/services/orchestrator/execution_engine.py`, `backend/tests/test_memory_tools.py`, `backend/tests/integration/test_pet_recall_chat_path.py`, `backend/tests/test_provider_auth_fallback.py`
- **Epic:** BACKLOG-115
- **Confidence:** High
- **Tags:** Contacts, Recall, Memory, Fallback, PetFacts, Deduplication, Unicode, Regression
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


## [PATTERN] #Spec15ManualEvidenceRunner "Bounded Playwright evidence runner resolves final audit manual-evidence blockers"
- **Kontext:** Spec 15 final audit was blocked only because manual Janus UI evidence was missing, while backend regression evidence already passed. (2026-06-07).
- **Problem:** The audit had no task-bound Playwright/manual runner, so the validator could not confirm the settings address-book and chat confirmation flow even though the implementation was otherwise green.
- **Loesung:** Create a bounded Playwright runner that mocks API routes, scopes assertions to the exact contact cards and visible chat proposal message, and use it as the audit evidence path instead of stalling on generic manual evidence.
- **Haertung:** Playwright rerun passed 2/2; final audit validator passed; audit package and final audit were updated with explicit evidence paths and limitations.
- **Tripwire:** If a final audit is blocked by missing manual/UI evidence but backend suites are already green, build a bounded evidence runner immediately instead of relying on generic screenshots or waiting for a full live-provider trace.
- **Location:** tests/e2e/generated/TASK-SPEC15-address-book-ui-evidence.spec.js; documentation/tasks/TASK-SPEC15_AUDIT_PACKAGE.md; documentation/tasks/TASK-SPEC15_final_audit_validation.md; documentation/tasks/TASK-SPEC15_final_audit.md
- **Epic:** SPEC-15
- **Confidence:** High
- **Tags:** janus-final-audit,playwright,manual-evidence,ui-validation

## [PATTERN] #StructuredExecutorFallbackMustStayReviewable "Structured delegation fallback should return explicit local-reviewable state instead of hard-aborting the operator path"
- **Kontext:** TASK-SPEC17 / first structured executor slice for OR sidecar delegation (2026-06-15).
- **Problem:** A bounded structured delegation route can fail safely at the executor or validator seam and still create bad operator ergonomics if the dispatcher hard-aborts instead of surfacing a reviewable fallback result. In dirty worktrees this also weakens auditability because the failure is harder to package as one coherent bounded outcome.
- **Loesung:** Keep the structured executor narrow and deterministic, but convert unsupported or failed generator-review routes into an explicit local fallback result such as `CODEX_LOCAL_FALLBACK_REQUIRED`. Pair that with one task-scoped audit package and focused PASS-plus-expected-FAIL validation so the fallback path is auditable without pretending it is a successful delegated execution.
- **Haertung:** Executor CLI, validator PASS path, validator expected-FAIL path, dispatcher success path, dispatcher fallback path, focused pytest suite, execution-result validator and final-audit validator all passed on the bounded Spec-17 package.
- **Tripwire:** If a future structured delegation regression again aborts the operator flow without an explicit fallback state, or if final audit has only success evidence but no reviewable bounded failure artifact for the fallback seam, the structured delegation contract has drifted.
- **Location:** `documentation/codex/model-routing/scripts/codex_structured_action_executor.py`, `documentation/codex/model-routing/scripts/codex_structured_action_generator_review_runner.py`, `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`, `documentation/codex/model-routing/tests/test_codex_structured_action_executor.py`, `documentation/tasks/TASK-SPEC17_AUDIT_PACKAGE.md`, `documentation/tasks/TASK-SPEC17_final_audit.md`
- **Epic:** TASK-SPEC17
- **Confidence:** High
- **Tags:** StructuredExecutor, Fallback, AuditHardening, ORSidecar, Dispatcher, Validator, DirtyWorktree


## [PATTERN] #DelegatedWriteCandidateNeedsThreeTrustSeams "Bounded delegated write candidates need separate entry, artifact, and validation trust seams before Codex acceptance"
- **Kontext:** TASK-SPEC18 / bounded execution write apply candidate for OR sidecar delegation (2026-06-16).
- **Problem:** A delegated write candidate can look reviewable too early if allowlist entry gating, diff-plus-changed-files evidence, and local validation ownership are not enforced as separate hard seams.
- **Loesung:** Harden the path in three bounded slices: first reject any candidate without exact editable-path allowlist, touched-file cap, and delete-rename-move tripwires; then require non-empty git_diff.patch plus changed_files.txt and standard run artifacts; finally require validation_summary.json with PASS status and normalize the operator outcome to explicit Codex-owned accept-or-reject wording.
- **Haertung:** Entry-gate pytest passed 4/4, artifact-capture pytest passed 4/4, validation-acceptance pytest passed 3/3, all execution-result validators passed, and the final audit passed on the sealed Spec-18 package.
- **Tripwire:** If a future delegated write path can reach a reviewable PASS state without exact allowlist metadata, without diff plus changed-files evidence, without validation_summary.json, or while claiming final task completion instead of Codex-owned accept-or-reject authority, the bounded trust contract has drifted.
- **Location:** documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py, documentation/codex/model-routing/scripts/codex_structured_action_request_builder.py, documentation/codex/model-routing/scripts/codex_execution_write_apply_candidate_runner.py, documentation/codex/model-routing/tests/test_bounded_write_candidate_entry_gate.py, documentation/codex/model-routing/tests/test_bounded_write_candidate_artifact_capture.py, documentation/codex/model-routing/tests/test_bounded_write_candidate_validation_acceptance.py, documentation/tasks/TASK-SPEC18_AUDIT_PACKAGE.md, documentation/tasks/TASK-SPEC18_final_audit.md
- **Epic:** TASK-SPEC18
- **Confidence:** High
- **Tags:** DelegatedWrite, ORSidecar, TrustSeams, Allowlist, DiffEvidence, ValidationSummary, CodexAcceptance, AuditHardening


## [PATTERN] #RepoValidatorsOverrideSkillSummary "Repo validators outrank abbreviated skill wording for Janus handoff formats"
- **Kontext:** TASK-SPEC20.1 precheck and final-audit closeout for the first separate Dev governance home (2026-06-19).
- **Problem:** The short Janus skill instructions for precheck and final audit still described older copy-block handoff styles, while the repo validators already enforced newer Codex-native output contracts. Following the skill summary alone produced validation failure even when the audit logic and evidence were otherwise correct.
- **Loesung:** When Janus precheck or final-audit artifacts fail on format despite correct scope and evidence, inspect the repo validator scripts immediately and treat their required literals and forbidden tokens as the canonical contract. Update the artifact to the validator's Codex-native format instead of forcing the older copy-block style from abbreviated skill text.
- **Haertung:** alidate_precheck.py passed only after removing the copy block and adding the Codex-native NEXT STEP fields; alidate_final_audit.py passed only after replacing NEXT_SKILL_HANDOFF and copy-prompt style with the validator-required NEXT_STEP block.
- **Tripwire:** If a Janus precheck or final-audit artifact fails even though the scope and evidence look correct, and the text still contains tokens like BEGIN COPY, END COPY, NEXT_SKILL_HANDOFF, or Copy Prompt, the skill summary is likely older than the repo validator and the validator must win.
- **Location:** documentation/tasks/TASK-SPEC20.1_preimplementation_check.md, documentation/tasks/TASK-SPEC20.1_final_audit.md, C:\Users\pruve\.codex\skills\janus-preimplementation-check\scripts\validate_precheck.py, C:\Users\pruve\.codex\skills\janus-final-audit\scripts\validate_final_audit.py
- **Epic:** TASK-SPEC20.1
- **Confidence:** High
- **Tags:** Validators,Precheck,FinalAudit,DocumentationUpdate,Governance,Tripwire,CodexNativeFormat

## [PATTERN] #SharedDispatcherAuditNeedsProbeAndCliFallback "Shared delegation entry seams should be audited with both direct eligibility probes and one real CLI fallback check"
- **Kontext:** TASK-SPEC21.1 / first assistive OR workhorse pilot eligibility and redaction slice (2026-06-20).
- **Problem:** A bounded delegation change can look correct in narrow unit tests around the allowed invoke paths while the shared dispatcher entry seam still silently routes legacy task classes as OR-eligible.
- **Loesung:** When auditing a shared dispatcher or eligibility boundary, pair focused unit coverage with two explicit seam checks: one direct helper probe against an out-of-scope task class, and one real CLI invocation that proves the operator-facing delegated path falls back to a local Codex-only outcome without invoking any delegated helper.
- **Haertung:** Focused unit suite passed 19 tests; direct probe confirmed `quickchange_patch_review=OR_NOT_ELIGIBLE`; the real dispatcher CLI check returned `selected_path=codex_only_pre_dispatch` and invoked no delegated helper; final audit then passed on the repaired slice.
- **Tripwire:** If a bounded OR or sidecar audit has only positive pilot-path tests but no direct legacy-class probe and no CLI fallback evidence, the shared entry seam may still be broader than the intended rollout boundary.
- **Location:** `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`, `documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py`, `documentation/tasks/TASK-SPEC21.1_AUDIT_PACKAGE.md`, `documentation/tasks/TASK-SPEC21.1_final_audit.md`
- **Epic:** TASK-SPEC21.1
- **Confidence:** High
- **Tags:** SharedDispatcher, EligibilityGate, AuditHardening, CLIFallback, PilotScope, Delegation, Tripwire


## [PATTERN] #AiderRootRepoRunsNeedIsolatedSandbox "Aider OpenRouter worker POCs should run in an isolated sandbox instead of the repo root"
- **Kontext:** TASK-SPEC27.1 final-audited docs-only Aider/OpenRouter worker POC (2026-06-30). (2026-06-30).
- **Problem:** A direct repo-root Aider run on a tiny docs-only task still scanned the full repository, attempted an out-of-scope .gitignore change, and created local .aider side artifacts, which weakened the first worker signal and required cleanup.
- **Loesung:** Keep the first worker experiments inside a dedicated sandbox, subtree, or worktree with a tiny allowlist and task file. Treat any side effect outside the allowlisted area as a failed run, even when the edited target file itself looks good.
- **Haertung:** TASK-SPEC27.1 final audit passed only after Codex removed the .gitignore/.aider side effects, kept the evidence inside development/openrouter-skill-tests/janus-worker-aider-poc/, and recorded a conditional-go verdict instead of approving root-repo use.
- **Tripwire:** If a future Aider worker run scans the full repo, proposes repo-root hygiene edits, or leaves .aider side artifacts outside the bounded sandbox, the execution surface is still too broad for casual Janus worker use.
- **Location:** development/openrouter-skill-tests/janus-worker-aider-poc/, documentation/tasks/TASK-SPEC27.1_AUDIT_PACKAGE.md, documentation/tasks/TASK-SPEC27.1_final_audit.md
- **Epic:** TASK-SPEC27
- **Confidence:** High
- **Tags:** aider,openrouter,worker,poc,sandbox,allowlist,repo-hygiene


## [PATTERN] #BenchmarkProfileMustPatchConfigReconstructionSeam "Benchmark profiles must patch config-based service reconstruction seams"
- **Kontext:** TASK-INTENT-M1.3 / auxiliary intent classifier benchmark proof (2026-07-08).
- **Problem:** The deterministic benchmark patched the module default classifier, but the production merge path called classify_sync(..., config=...), rebuilt a fresh classifier, and used the real default provider path; this contaminated latency and provider isolation evidence.
- **Loesung:** Patch the provider callable used by config-based reconstruction as well as the module singleton, and add a regression test proving deterministic benchmark mode does not call the real default provider path.
- **Haertung:** Focused pytest suite passed with 59 tests; corrected M1.3 proof report shows flag-off parity PASS and auxiliary latency P95 4.09 ms after the seam fix.
- **Tripwire:** If a future deterministic benchmark emits provider/httpx/event-loop cleanup noise or unexpectedly high latency, check whether only a singleton was patched while the live path reconstructs services from config.
- **Location:** backend/scripts/run_intent_benchmark.py; backend/tests/test_intent_benchmark.py; backend/services/orchestrator/intent_aux_classifier.py; backend/services/orchestrator/intent_engine.py
- **Epic:** TASK-INTENT-M1.3
- **Confidence:** High
- **Tags:** intent,benchmark,deterministic-provider,latency,config-reconstruction


## [PATTERN] #CodexPickerVisibilityNeedsRuntimeEntitlementCheck "Codex model picker visibility requires a runtime entitlement check"
- **Kontext:** BACKLOG-124 GPT-5.6 model-matrix closeout (2026-07-10).
- **Problem:** A model can be selectable in the Codex picker while backend execution for the active ChatGPT account rejects it, so a hard model requirement can dead-end a bound audit.
- **Loesung:** Treat picker availability as a candidate signal only. Attempt the required run, record the exact entitlement failure, and use the documented local fallback without changing audit authority.
- **Haertung:** Official Codex availability guidance was checked; the active account returned the Sol unsupported error; governance, audit templates, and final-audit PASS now require SOL_UNAVAILABLE_FOR_CHATGPT_CODEX_ACCOUNT with 5.6 Terra/high fallback.
- **Tripwire:** If a skill requires Sol merely because it is visible in the picker, or a Sol rejection stops a valid audit instead of producing the explicit Terra fallback, the model-routing contract has drifted.
- **Location:** AGENTS.md, documentation/codex/CODEX_PROJECT_PROFILE.md, documentation/codex/CODEX_WORKFLOW_PLAYBOOK.md, documentation/tasks/BACKLOG-124_final_audit.md
- **Epic:** BACKLOG-124
- **Confidence:** High
- **Tags:** codex,gpt56,model-routing,runtime-entitlement,audit-fallback


## [PATTERN] #CursorComposerTimeoutNeedsTieredWallClockBudget "Cursor Composer tool runs need a tiered wall-clock budget and one-attempt fallback"
- **Kontext:** Cursor Composer timeout analysis for Janus bounded delegation (2026-07-10).
- **Problem:** A 120-second wall-clock cap terminates valid Composer shell/tool loops before their final JSON response, which can look like a broken integration even though the agent is still working.
- **Loesung:** For live Composer tool lanes, set 240 seconds for one allowlisted file and 300 seconds for two files or debug with shell. Make one critical-path attempt, inspect cursor-worker-run artifacts, and on CURSOR_AGENT_TIMEOUT implement locally in Codex instead of repeated retries.
- **Haertung:** cursor_delegation_log evidence records successful runs at 124, 194, and 215 seconds; HANDOFF_CURSOR_COMPOSER_TIMEOUT_ANALYSIS_2026-07-10.md documents the runner's bounded timeout behavior, artifact expectations, and failure taxonomy.
- **Tripwire:** If a Composer timeout is called an integration failure without checking the configured cap and run artifacts, if a 120-second cap is used for tool work, or if the same package is retried repeatedly on the critical path, the delegation operating contract has drifted.
- **Location:** documentation/codex/model-routing/HANDOFF_CURSOR_COMPOSER_TIMEOUT_ANALYSIS_2026-07-10.md, documentation/codex/model-routing/scripts/janus_cursor_worker_runner.py, documentation/codex/model-routing/cursor_delegation_log.jsonl
- **Epic:** Track B H-003
- **Confidence:** High
- **Tags:** cursor,composer,timeout,delegation,wall-clock,track-b


## [PATTERN] #SemanticRoutineReuseMustBindFreshRequestConstraints "Semantic routine reuse must bind fresh request constraints and fail closed"
- **Kontext:** TASK-WORKFLOW-M3.4 semantic calendar-plus-weather routine reuse (2026-07-10).
- **Problem:** Matching only a saved multi-skill signature can reuse a routine with stale or mismatched city/date values, producing a plausible but wrong result.
- **Loesung:** Keep explicit triggers first, then allow bounded semantic reuse only for a matching saved signature whose current request constraints are complete and compatible. Reject unrelated, missing, conflicting, or explicitly different city/date requests instead of executing a stale routine.
- **Haertung:** M3.4 live GPT and Gemini validation passed; focused routine/offer/chat-finalize regression passed 40 tests, including semantic reuse, explicit trigger preservation, unrelated-request rejection, city/date mismatch rejection, and natural user-facing rendering.
- **Tripwire:** If a semantic routine executes for a different weather city/date, with missing constraints, or without a transparent routine-use note, the reuse contract has drifted.
- **Location:** backend/services/workflow/routine_runner.py, backend/services/orchestrator/intent_engine.py, backend/tests/test_routine_runner.py, documentation/tasks/TASK-WORKFLOW-M3.4_final_audit.md
- **Epic:** TASK-WORKFLOW-M3.4
- **Confidence:** High
- **Tags:** workflow,routine,semantic-reuse,fail-closed,weather


## [PATTERN] #SessionSearchMustFilterEchoCandidatesAndSecrets "Session search must filter echo candidates and password-like content before recall output"
- **Kontext:** TASK-MEM-M4.1 / Memory Phase C Session-Search FTS5 closeout (2026-07-11). (2026-07-11).
- **Problem:** Natural recall prompts with punctuation could produce weak FTS candidates, repeated user-question rows could outrank the earlier fact, and password-like rows needed stronger fail-closed filtering.
- **Loesung:** Normalize bounded FTS query candidates, collect a bounded fallback candidate pool, suppress exact question echoes for natural recall, and apply session-search-specific password-like filtering before snippets reach the tool output.
- **Haertung:** Focused store and tool tests PASS (4 plus 5); memory regression PASS (20); direct enabled-runtime Janus proof returned Acme GmbH through session_search and refused the password phrasing.
- **Tripwire:** If a natural recall question returns its own text instead of the prior fact, FTS parsing fails on punctuation, or a password-like snippet reaches tool output, recheck query normalization, candidate pooling, echo suppression, and secret filtering together.
- **Location:** backend/services/memory/session_fts_store.py, backend/services/memory/session_search_service.py, backend/tests/test_session_fts_store.py, backend/tests/test_session_search_tools.py
- **Epic:** TASK-MEM-M4.1
- **Confidence:** High
- **Tags:** memory,session-search,fts5,recall,secret-suppression


## [PATTERN] #GeminiStreamDuplicateToolDeltaMustBeDedupedAtEmission "Gemini stream function-call retransmits must be deduplicated at emission"
- **Kontext:** BACKLOG-129 / M6 master-integration Gemini Berlin-weather smoke (2026-07-13). (2026-07-13).
- **Problem:** Gemini can emit the same first Function-Call chunk twice in one streaming response. History buffering may deduplicate persistence while the event loop still forwards both tool deltas, causing the cross-round hard-loop breaker to abort before tool execution.
- **Loesung:** Track Function-Call fingerprints per Gemini provider streaming response and suppress only an identical retransmitted tool delta before it reaches the orchestrator. Keep distinct arguments and the existing hard-loop breaker unchanged.
- **Haertung:** Focused Gemini stream and duplicate-guard regression passed (21 total); bound M6 matrix PASS; manual default-off Gemini Berlin-weather smoke PASS.
- **Tripwire:** If a Gemini request logs a registered and blocked identical tool call before any executor line, inspect duplicate stream-delta emission before weakening the hard-loop breaker or diagnosing missing tool results.
- **Location:** backend/llm_providers/gemini/service.py; backend/tests/llm_providers/test_gemini_service.py; backend/tests/test_execution_dispatcher_wikipedia_guard.py
- **Epic:** BACKLOG-129
- **Confidence:** High
- **Tags:** Gemini,streaming,tool-calls,hard-loop-breaker,provider-runtime


## [PATTERN] #CodexAppServerCredentialIsolationNeedsHomeDerivedStoreAndLiveNonInterference "Codex App Server credential isolation needs a home-derived store plus live non-interference evidence"
- **Kontext:** TASK-CHATGPT-DEVICE-CODE-PROVIDER.1 official device-code isolation foundation (2026-07-15). (2026-07-15).
- **Problem:** A nominally separate auth flow can still affect Codex Desktop, CLI, or IDE sessions when credential identity is shared, storage falls back, or logout and refresh are not proven against a dedicated namespace.
- **Loesung:** Use only the official App Server device-code contract with an absolute Janus-only CODEX_HOME, force keyring-backed persistence, strip API-key and shared-session fallbacks, keep transient codes redacted, and retain production default-deny until the complete feature evidence task passes.
- **Haertung:** Backend lifecycle 22 passed, Electron runtime-boundary 9 passed, headed Settings regression 4 passed, compile and scoped diff checks passed, and a controlled Account-B login/restart/refresh/logout sequence left Account A unchanged after every step; independent Final Audit PASS.
- **Tripwire:** If Janus imports an existing Codex credential, allows file/auto/ephemeral fallback, exposes a transient code, changes another Codex client during login/refresh/logout, or sets production activation before the later release-evidence task, the credential-isolation boundary has drifted.
- **Location:** backend/llm_providers/codex_app_server.py; backend/tests/test_codex_app_server.py; tests/electron/codex-runtime-boundary.test.cjs; documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_final_audit.md
- **Epic:** TASK-CHATGPT-DEVICE-CODE-PROVIDER.1
- **Confidence:** High
- **Tags:** codex-app-server device-code credential-isolation keyring CODEX_HOME redaction two-account default-deny


## [PATTERN] #SettingsButtonMustKeepSingleStatefulNavigationPath "Settings button navigation must keep one stateful binding"
- **Kontext:** BACKLOG-131 delayed Settings-handler replacement closeout (2026-07-15) (2026-07-15).
- **Problem:** A delayed legacy handler clone replaced the visible Settings button listener, bypassed appState synchronization and show-settings dispatch, and could reinitialize the app back to chat.
- **Loesung:** Bind the visible Settings button once after DOM readiness with a dataset guard; update appState.currentView, switch views, and dispatch show-settings. Keep the modal fallback separate and never rebind the sidebar button later.
- **Haertung:** Independent Final Audit PASS; app.js and runner syntax PASS; Settings API 11 passed; headed E2E 8 passed through real Einstellungen to API Keys controls; committed diff and worktree checks PASS.
- **Tripwire:** If any delayed code clones or replaces #settings-btn, calls forceOpenSettings for sidebar navigation, or re-runs initializeApp after Settings open, treat it as a state-navigation regression and retest the full headed Settings suite.
- **Location:** frontend/js/app.js; tests/e2e/codex-connection-settings.spec.js; documentation/tasks/BACKLOG-131_final_audit.md
- **Epic:** BACKLOG-131
- **Confidence:** High
- **Tags:** settings,navigation,appstate,e2e,regression


## [PATTERN] #ChatgptStaleSelectionMustValidatePersistedStateAfterCatalog "Stale ChatGPT selection must validate persisted state after catalog refresh"
- **Kontext:** TASK-CHATGPT-DEVICE-CODE-PROVIDER.3 current-session model verification and provider-picker integration. (2026-07-16).
- **Problem:** An E2E runner wrote mocked last-used-model state into the operator configuration; startup removed unavailable ChatGPT from the catalog and then restored the stale persisted provider/model, leaving the native provider select without a matching option.
- **Loesung:** Isolate E2E GET and PUT last-used-model state in memory. On startup, restore a persisted ChatGPT selection only when it remains present in the current verified catalog; otherwise choose an existing non-ChatGPT provider/model.
- **Haertung:** Focused headed stale-start scenario, verified/unavailable scenario, full headed Settings E2E 10 passed, backend/hierarchy 17 passed, passive real-shell restart PASS, and Final Audit PASS.
- **Tripwire:** If the provider select has a persisted ChatGPT value without a matching option, or an E2E route can touch operator last-used-model storage, stop and add isolation plus a startup-order regression.
- **Location:** frontend/js/app.js; tests/e2e/codex-connection-settings.spec.js
- **Epic:** TASK-CHATGPT-DEVICE-CODE-PROVIDER.3
- **Confidence:** High
- **Tags:** chatgpt,provider-selection,e2e-isolation,stale-state,fail-closed
