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

- [x] Lokaler MCP-Debug-Preflight ist dokumentiert oder automatisiert.
- [x] Geschuetzte Basis-Calls wie `/api/personalities` und `/api/personalities/active` erzeugen in der MCP-Debugsession nach Preflight keine unerwarteten 401-Fehler.
- [x] Keine echten Browserprofile, Secrets oder externen Origins werden benoetigt.
- [x] Der Preflight ist klar als Dev-/Debug-only gekennzeichnet.
- [x] Security-Watchpoints sind dokumentiert.

## EVIDENCE

- MCP Console: `401 Unauthorized` fuer `http://127.0.0.1:8001/api/personalities`
- MCP Console: `401 Unauthorized` fuer `http://127.0.0.1:8001/api/personalities/active`
- Stack: `PersonalitySettings.loadPersonalities`, `PersonalitySettings.loadActivePersonality`

## IMPLEMENTATION NOTES

Vorhandene E2E-JWT/LocalStorage-Mechanik pruefen und fuer MCP-Debugging als expliziten Dev-Preflight nutzbar machen. Security-Grenze: keine produktiven Auth-Bypasses und keine Wiederverwendung echter Browser-Sessions.

## IMPLEMENTATION RESULT

Status: DONE, 2026-05-21.

Umgesetzt wurde ein lokaler Debug-Preflight unter `POST /api/debug/mcp/auth-preflight`. Der Endpunkt ist nur in explizitem Debug-/Development-Modus verfuegbar und akzeptiert nur lokale Browser-Kontexte. Er exportiert nicht den internen Janus API-Key, sondern erzeugt:

- einen normalen kurzlebigen `auth_token` fuer bestehende JWT-geschuetzte Routen
- eine kurzlebige `janus_mcp_debug_session` fuer intern-key-geschuetzte lokale API-Routen

Der globale Frontend-Fetch-Wrapper nutzt die MCP-Debug-Session nur dann, wenn keine Electron-Bridge mit internem API-Key vorhanden ist. Produktive Electron-Flows bleiben dadurch unveraendert.

Automatisierter Helper:

```powershell
node tools\mcp-debug-auth-preflight.mjs http://localhost:5173
```

Security-Watchpoints:

- Dev-only: `JANUS_ENABLE_DEBUG_ENDPOINTS=1`, `NODE_ENV=development` oder `JANUS_DEV_MODE=true`.
- Local-only: externe `Origin`/`Referer` werden abgelehnt.
- Kein Secret-Export: Response enthaelt keinen `api_key` und nicht den internen `X-Janus-Internal-Key`.
- Kurzlebig: Debug-Session laeuft nach 60 Minuten ab.
- Kein echtes Browserprofil notwendig.

Validation:

- `python -m pytest backend\tests\test_mcp_debug_auth_preflight.py -q` -> PASS 3/3
- `npx playwright test tests/e2e/mcp-debug-auth-preflight.spec.js --workers=1 --reporter=list` -> PASS 1/1
- `PYTHONIOENCODING=UTF-8 npm run build` -> PASS
