# FEATURE SPEC - MCP Isolated Browser Auth Preflight fuer lokale Janus-Debugsessions

## SPEC REVIEW EXECUTION ROUTING

target_skill: SKILL_1
execution_mode: SWE_1_6
complexity_score: 34
confidence: MEDIUM
dashboard_hint: NONE
security_hint: WATCHPOINTS
reason: Developer-Experience-Fix fuer Windsurf/Playwright-MCP Debugging mit Auth-Sicherheitsgrenzen.

## TEST IDENTITY

- Feature Name: MCP Isolated Browser Auth Preflight fuer lokale Janus-Debugsessions
- Backlog Item: BACKLOG-071
- Source Input: Manual Playwright MCP inspection on 2026-05-18
- Primary Feature Goal: Lokale MCP-Debugsessions koennen Janus mit sicherem Auth-Preflight inspizieren.
- User Problem: Der isolierte MCP-Browser laedt Janus, aber geschuetzte API-Calls erzeugen `401 Unauthorized`, weil Auth/JWT/localStorage nicht initialisiert sind.
- User Value: Windsurf kann lokale Janus-UI-Probleme vollstaendiger debuggen, ohne echte Browserprofile oder Secrets zu verwenden.
- Suggested Save Path: documentation/Planned Features/backlog_BACKLOG-071_mcp_isolated_browser_auth_preflight.md

## FEATURE OBJECTIVE

Definiere und implementiere einen sicheren lokalen Preflight fuer Playwright-MCP-Debugsessions, damit isolierte Browser-Kontexte die Janus-App mit minimal notwendiger lokaler Auth inspizieren koennen.

## SCOPE

Dieses Feature umfasst:
- Analyse der bestehenden Playwright-E2E Auth-Initialisierung
- Dokumentierte MCP-Debug-Preflight-Anleitung oder kleine Helper-Route/Script fuer lokalen Dev-Kontext
- Keine echten Userprofile, keine Persistenz echter Browser-Cookies, keine externe Origins
- Retest mit MCP auf `http://localhost:5173`

Out of Scope:
- Produktive Auth-Bypasses
- Externe Website-Freigaben im MCP
- Fix fuer `marked` CDN-Abhaengigkeit (separat BACKLOG-070)

## ACCEPTANCE CRITERIA

- [ ] Lokaler MCP-Debug-Preflight ist dokumentiert oder automatisiert.
- [ ] Geschuetzte Basis-Calls wie `/api/personalities` und `/api/personalities/active` erzeugen in der MCP-Debugsession keine unerwarteten 401-Fehler.
- [ ] Keine echten Browserprofile, Secrets oder externen Origins werden benoetigt.
- [ ] Der Preflight ist klar als Dev-/Debug-only gekennzeichnet.
- [ ] Security-Watchpoints sind dokumentiert.

## EVIDENCE

- MCP Console: `401 Unauthorized` fuer `http://127.0.0.1:8001/api/personalities`
- MCP Console: `401 Unauthorized` fuer `http://127.0.0.1:8001/api/personalities/active`
- Stack: `PersonalitySettings.loadPersonalities`, `PersonalitySettings.loadActivePersonality`

## IMPLEMENTATION NOTES

Vorhandene E2E-JWT/LocalStorage-Mechanik pruefen und fuer MCP-Debugging als expliziten Dev-Preflight nutzbar machen. Security-Grenze: keine produktiven Auth-Bypasses und keine Wiederverwendung echter Browser-Sessions.
