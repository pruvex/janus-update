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
