# TEST-RUN-2026-05-21-001 Evidence

## Scope

TestSpec: `documentation/TEST_SPEC/03_tools_skills/09_api_external_tool_fallback_honesty.md`

Validated external-tool fallback honesty for:

- `system.weather`
- `system.websearch`
- `system.rss_news`
- `system.wikipedia_summary`
- `system.routing`
- `system.price_comparison`

## Product Changes

- Websearch now returns `WEBSEARCH_UNAVAILABLE` for provider timeout/error/unavailable statuses instead of surfacing them as successful current-data answers.
- Websearch now rejects current-data answers with text but no source list via `WEBSEARCH_NO_SOURCES`.
- RSS fallback now treats empty/timeout websearch fallback as failure and returns `RSS_AND_WEB_FAILED` with explicit no-invented-headlines wording.
- RSS preserves source attribution even when feed content contains source-suppression text.
- Wikipedia API failures now name Wikipedia as the unavailable source and avoid pretending a summary is sourced.
- Weather `wttr.in` fallback now checks HTTP status and empty responses before returning success.
- Geo route failures now return `ROUTING_UNAVAILABLE` and explicitly avoid precise distance/route claims.
- Price comparison now distinguishes unavailable price/search sources from ordinary no-match cases via `PRICE_SOURCE_UNAVAILABLE`.

## Verification

Commands run from `C:\KI\Janus-Projekt`:

```powershell
python -m pytest backend\tests\tools\test_external_tool_fallback_honesty.py -q
```

Result: `7 passed`

```powershell
python -m pytest backend\tests\tools\test_external_tool_fallback_honesty.py backend\tests\tools\test_system_skills_diamond.py::TestWebsearchService backend\tests\tools\test_system_skills_diamond.py::TestWikipediaService backend\tests\test_distance_tool.py -q
```

Result: `18 passed`

```powershell
python -m pytest backend\tests\tools\test_system_skills_diamond.py::TestWeatherService backend\tests\tools\test_system_skills_diamond.py::TestRssNewsService backend\tests\tools\test_external_tool_fallback_honesty.py -q
```

Result: `16 passed`

```powershell
python -m py_compile backend\tool_registry.py backend\tools\rss_service.py backend\tools\wiki_service.py backend\tools\weather_service.py backend\tools\geo_service.py backend\tools\finance_tools.py backend\tests\tools\test_external_tool_fallback_honesty.py
```

Result: pass

```powershell
node tests/e2e/generator/compile-testspec-to-testplan.mjs --spec documentation/TEST_SPEC/03_tools_skills/09_api_external_tool_fallback_honesty.md
```

Result: `TESTPLAN VALID`, generated `TEST-RUN-2026-05-21-001` with 22 generated live-plan tests.

## Residual Risk

Full Playwright chat/provider live execution for GPT and Gemini was not run in this pass. The fallback honesty contract is covered deterministically at tool/wrapper level with controlled unavailable-source simulations, which is the preferred isolation method for this spec.
