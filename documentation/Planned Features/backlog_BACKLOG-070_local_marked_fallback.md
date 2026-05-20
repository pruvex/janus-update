# FEATURE SPEC - Lokaler marked-Fallback fuer Chat-Markdown Rendering

## SPEC REVIEW EXECUTION ROUTING

target_skill: SKILL_1
execution_mode: SWE_1_6
complexity_score: 28
confidence: HIGH
dashboard_hint: NONE
security_hint: NONE
reason: Frontend-Robustheitsfix fuer eine externe CDN-Abhaengigkeit im Chat-Renderer.

## TEST IDENTITY

- Feature Name: Lokaler marked-Fallback fuer Chat-Markdown Rendering
- Backlog Item: BACKLOG-070
- Source Input: Manual Playwright MCP inspection on 2026-05-18
- Primary Feature Goal: Chat-Markdown Rendering funktioniert ohne harte CDN-Abhaengigkeit.
- User Problem: Browser-Blocker, Policies oder Offline/CDN-Ausfall koennen `marked` blockieren und Chat-Rendering mit `ReferenceError: marked is not defined` brechen.
- User Value: Janus Chat bleibt auch in restriktiven Browser-Kontexten, MCP-Debugsessions und offline-naeheren Umgebungen stabil.
- Suggested Save Path: documentation/Planned Features/backlog_BACKLOG-070_local_marked_fallback.md

## FEATURE OBJECTIVE

Janus soll `marked` lokal/bundled laden oder einen sicheren Fallback verwenden. Externe CDN-Blockaden duerfen die Chat-UI nicht crashen.

## SCOPE

Dieses Feature umfasst:
- Analyse des aktuellen `marked`-Ladepfads im Frontend
- Umstellung auf lokale/bundled `marked`-Auslieferung oder lokales Asset
- Guard im Chat-Renderer, falls `marked` dennoch nicht verfuegbar ist
- Minimaler Frontend-/Playwright-/MCP-Retest fuer fehlende `marked is not defined` Fehler

Out of Scope:
- Aenderungen am LLM-/Backend-Verhalten
- Vollstaendige Markdown-Renderer-Neuentwicklung
- Auth-Setup fuer MCP-Debugsessions (separat BACKLOG-071)

## ACCEPTANCE CRITERIA

- [ ] `marked` wird nicht mehr ausschliesslich von `https://cdn.jsdelivr.net/...` benoetigt.
- [ ] Wenn `marked` nicht verfuegbar ist, crasht `chat.js` nicht.
- [ ] Chat-Nachrichten werden weiterhin lesbar gerendert.
- [ ] MCP/Playwright Console zeigt keinen `ReferenceError: marked is not defined`.
- [ ] Keine neuen externen Runtime-CDN-Abhaengigkeiten fuer Chat-Markdown.

## EVIDENCE

- MCP Console: `Failed to load resource: net::ERR_BLOCKED_BY_CLIENT` fuer `https://cdn.jsdelivr.net/npm/marked/marked.min.js`
- MCP Console: `ReferenceError: marked is not defined` in `http://localhost:5173/js/chat.js:173:1`

## IMPLEMENTATION NOTES

Bevorzugt `marked` als Projektdependency oder lokales Frontend-Asset ausliefern. Der Fallback darf Plain Text sein, muss aber HTML-Injection sicher behandeln.
