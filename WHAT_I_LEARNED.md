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
